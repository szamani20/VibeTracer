import sys
import os
import ast
import importlib.abc
import importlib.util
from importlib.machinery import PathFinder
import sysconfig
from pathlib import Path

# Will hold the folder containing the script you're tracing
PROJECT_ROOT = None


def _collect_third_party_prefixes(project_root: str) -> set[str]:
    """
    Return absolute path prefixes that must be treated as *outside* the project.
    A directory becomes a prefix when

      • it is Python’s own site-packages / dist-packages directory
      • it is the running interpreter’s prefix/base_prefix
      • it is (or contains) a **virtual-environment root**, identified structurally
        by either:
            – a file   named  'pyvenv.cfg'   (PEP-405 venv / virtualenv)
            – a folder named  'conda-meta'   (Conda environments)
    """
    prefixes: set[str] = {
        os.path.abspath(sysconfig.get_path(k))
        for k in ("purelib", "platlib")
        if sysconfig.get_path(k)
    }

    prefixes.add(os.path.abspath(sys.prefix))
    prefixes.add(os.path.abspath(getattr(sys, "base_prefix", sys.prefix)))

    # hunt for venv/conda roots *inside* the project tree
    for dirpath, dirnames, filenames in os.walk(project_root):
        if "pyvenv.cfg" in filenames or "conda-meta" in dirnames:
            prefixes.add(os.path.abspath(dirpath))
            # no need to walk any deeper into that env
            dirnames.clear()

    return prefixes


class TracingTransformer(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        deco = ast.Call(
            func=ast.Name(id='info_decorator', ctx=ast.Load()),
            args=[], keywords=[]
        )
        node.decorator_list.insert(0, deco)
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        deco = ast.Call(
            func=ast.Name(id='info_decorator', ctx=ast.Load()),
            args=[], keywords=[]
        )
        node.decorator_list.insert(0, deco)
        return self.generic_visit(node)


class VibeLoader(importlib.abc.Loader):
    def __init__(self, fullname, path):
        self.fullname = fullname
        self.path = path

    def create_module(self, spec):
        # use default module creation
        return None

    def exec_module(self, module):
        source = open(self.path, 'r', encoding='utf-8').read()
        # 1) parse
        tree = ast.parse(source, filename=self.path)
        # 2) inject our decorator import
        tree.body.insert(0,
                         ast.ImportFrom(
                             module='vibetracer.trace.tracer',
                             names=[ast.alias(name='info_decorator', asname=None)],
                             level=0
                         )
                         )
        # 3) transform all functions
        tree = TracingTransformer().visit(tree)
        ast.fix_missing_locations(tree)
        # 4) compile + exec
        code = compile(tree, self.path, 'exec')
        # ensure correct loader metadata
        module.__loader__ = self
        exec(code, module.__dict__)


class VibeFinder(importlib.abc.MetaPathFinder):
    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)
        self._third_party = _collect_third_party_prefixes(self.project_root)

    def _inside_project(self, file_path: str) -> bool:
        """
        Instrument only when:
        1) the file lives under PROJECT_ROOT, *and*
        2) no ancestor directory up to PROJECT_ROOT is a recognised virtual-env
           root, *and*
        3) the path is not contained in any known third-party/site prefix, and
        4) no path component is 'site-packages' or 'dist-packages'.
        """
        p = Path(file_path).resolve()

        # 1) must physically live under the declared project tree
        try:
            if os.path.commonpath([self.project_root, str(p)]) != self.project_root:
                return False
        except ValueError:
            return False

        # 2) skip anything inside a recognised third-party prefix
        for prefix in self._third_party:
            if str(p).startswith(prefix + os.sep):
                return False

        # 3) quick bail-out if the path *itself* contains site-packages/dist-packages
        if any(part in ("site-packages", "dist-packages") for part in p.parts):
            return False

        # 4) walk upward until we reach PROJECT_ROOT; if we meet venv markers, skip
        for parent in p.parents:
            if parent == Path(self.project_root):
                break
            if (parent / "pyvenv.cfg").is_file() or (parent / "conda-meta").is_dir():
                return False

        return True

    def find_spec(self, fullname, path=None, target=None):
        """
        Delegate the heavy lifting to importlib.machinery.PathFinder *but*
        accept the result only when it resolves to a file that sits inside
        the project tree.  This avoids all accidental mixing with the
        current working directory and eliminates the N-squared path probes.
        """
        search_locations = path or [self.project_root]

        spec = PathFinder.find_spec(fullname, search_locations, target)
        if spec is None or spec.origin in (None, 'built-in', 'namespace'):
            return None

        if not self._inside_project(spec.origin):
            return None  # third-party or stdlib module

        # Replace the loader with our instrumenting loader
        spec.loader = VibeLoader(fullname, spec.origin)

        # For a package, make sure sub-modules keep working
        if (spec.submodule_search_locations is None
                and spec.origin.endswith('__init__.py')):
            spec.submodule_search_locations = [os.path.dirname(spec.origin)]

        return spec


def list_subfolders(folder_path):
    """
    Return a list of all sub-folders (recursively) inside `folder_path`,
    with absolute paths.
    """
    folder_path = os.path.abspath(folder_path)
    subfolders = set()
    for dirpath, dirnames, _ in os.walk(folder_path):
        for dirname in dirnames:
            subfolders.add(os.path.join(dirpath, dirname))
    subfolders.add(folder_path)
    return subfolders


def run_script(script_path):
    global PROJECT_ROOT
    script_path = os.path.abspath(script_path)
    if not script_path.endswith('.py') or not os.path.isfile(script_path):
        print(f"Error: '{script_path}' is not a Python file", file=sys.stderr)
        sys.exit(1)

    PROJECT_ROOT = os.path.dirname(script_path)
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    project_sub_folders = list_subfolders(PROJECT_ROOT)

    # install our finder first so all imports get rewritten
    sys.meta_path.insert(0, VibeFinder(PROJECT_ROOT))

    # load & exec the main script through our loader
    loader = VibeLoader('__main__', script_path)
    spec = importlib.util.spec_from_loader('__main__', loader, origin=script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules['__main__'] = module

    cwd = os.getcwd()
    # Change CWD to PROJECT_ROOT to avoid messing with relative paths used in project code
    os.chdir(PROJECT_ROOT)
    loader.exec_module(module)
    # Change CWD back to what it was to be able to access the sqlite db if needed
    os.chdir(cwd)
