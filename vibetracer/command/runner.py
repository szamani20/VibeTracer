import sys
import os
import ast
import types
import importlib.abc
import importlib.util
from importlib.machinery import PathFinder

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
    def find_spec(self, fullname, path, target=None):
        # 1) Check if this fullname maps to a .py or package __init__.py under PROJECT_ROOT
        parts = fullname.split('.')
        pkg_init = os.path.join(PROJECT_ROOT, *parts, "__init__.py")
        mod_file = os.path.join(PROJECT_ROOT, *parts) + ".py"

        if os.path.isfile(pkg_init):
            origin = pkg_init
            is_pkg = True
        elif os.path.isfile(mod_file):
            origin = mod_file
            is_pkg = False
        else:
            # Not one of your own modules—let other finders handle it
            return None

        # 2) Instrument it via our loader
        loader = VibeLoader(fullname, origin)
        spec = importlib.util.spec_from_loader(fullname, loader, origin=origin)
        if is_pkg:
            # ensure it's recognized as a package
            spec.submodule_search_locations = [os.path.dirname(origin)]
        return spec


def run_script(script_path):
    global PROJECT_ROOT
    script_path = os.path.abspath(script_path)
    if not script_path.endswith('.py') or not os.path.isfile(script_path):
        print(f"Error: '{script_path}' is not a Python file", file=sys.stderr)
        sys.exit(1)

    PROJECT_ROOT = os.path.dirname(script_path)
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    # install our finder first so all imports get rewritten
    sys.meta_path.insert(0, VibeFinder())

    # load & exec the main script through our loader
    loader = VibeLoader('__main__', script_path)
    spec = importlib.util.spec_from_loader('__main__', loader, origin=script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules['__main__'] = module
    loader.exec_module(module)


def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'run':
        print("Usage: vibetracer run path/to/script.py", file=sys.stderr)
        sys.exit(1)
    run_script(sys.argv[2])


if __name__ == "__main__":
    main()
