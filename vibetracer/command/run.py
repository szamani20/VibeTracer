import sys
import os
import ast
import importlib.abc
import importlib.util

# Will hold the folder containing the script you're tracing
PROJECT_ROOT = None


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
    def __init__(self, project_sub_folders):
        self.project_sub_folders = project_sub_folders

    def find_spec(self, fullname, path, target=None):
        parts = fullname.split('.')
        origin = None
        is_pkg = False

        # try each possible suffix of the fullname
        # TODO: This is inefficient. We should skip paths that do not belong to project
        for i in range(len(parts)):
            tail = parts[i:]
            pkg_init = os.path.join(PROJECT_ROOT, *tail, "__init__.py")
            mod_file = os.path.join(PROJECT_ROOT, *tail) + ".py"

            if os.path.isfile(pkg_init):
                origin = pkg_init
                is_pkg = True
                break
            if os.path.isfile(mod_file):
                origin = mod_file
                break

        if origin is None:
            # not in your project tree, let someone else import it
            return None

        # build a spec that uses our loader
        loader = VibeLoader(fullname, origin)
        spec = importlib.util.spec_from_loader(fullname, loader, origin=origin)
        if is_pkg:
            spec.submodule_search_locations = [os.path.dirname(origin)]
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
    sys.meta_path.insert(0, VibeFinder(project_sub_folders))

    # load & exec the main script through our loader
    loader = VibeLoader('__main__', script_path)
    spec = importlib.util.spec_from_loader('__main__', loader, origin=script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules['__main__'] = module
    loader.exec_module(module)
