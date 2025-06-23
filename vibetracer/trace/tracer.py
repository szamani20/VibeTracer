import time
import inspect
import threading
import traceback
import json
from functools import wraps
from sqlmodel import Session, select

from vibetracer.database.models import Function, Call, Argument

# Thread-local storage for nested call tracking
_call_stack = threading.local()


def info_decorator(engine):
    """
    Decorator factory to trace function calls, record metadata, arguments,
    timing, return values, and exceptions into the database.
    """

    def decorator(func):
        # Persist function metadata at decoration time
        sig = inspect.signature(func)
        code_obj = func.__code__

        annotations_json = json.dumps(func.__annotations__, default=str)
        defaults_json = (
            json.dumps(func.__defaults__, default=str)
            if func.__defaults__ else None
        )
        kwdefaults_json = (
            json.dumps(func.__kwdefaults__, default=str)
            if func.__kwdefaults__ else None
        )

        closure_vars_json = None
        if func.__closure__:
            closure_dict = {
                name: cell.cell_contents
                for name, cell in zip(code_obj.co_freevars, func.__closure__)
            }
            closure_vars_json = json.dumps(closure_dict, default=str)

        with Session(engine) as session:
            stmt = (
                select(Function)
                .where(
                    Function.module == func.__module__,
                    Function.qualname == func.__qualname__,
                    Function.filename == code_obj.co_filename,
                    Function.lineno == code_obj.co_firstlineno
                )
            )
            existing = session.exec(stmt).one_or_none()
            if existing is None:
                existing = Function(
                    module=func.__module__,
                    qualname=func.__qualname__,
                    filename=code_obj.co_filename,
                    lineno=code_obj.co_firstlineno,
                    signature=str(sig),
                    annotations=annotations_json,
                    defaults=defaults_json,
                    kwdefaults=kwdefaults_json,
                    closure_vars=closure_vars_json
                )
                session.add(existing)
                session.commit()
                session.refresh(existing)

        func_id = existing.id

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Initialize per-thread call stack
            if not hasattr(_call_stack, "stack"):
                _call_stack.stack = []
            parent = _call_stack.stack[-1] if _call_stack.stack else None

            start = time.time()
            tid = threading.get_ident()
            is_coro = inspect.iscoroutinefunction(func)

            bound = inspect.signature(func).bind_partial(*args, **kwargs)

            # Determine if method or function
            method_type = "function"
            class_name = None
            if "." in func.__qualname__ and bound.arguments:
                first = next(iter(bound.arguments.values()))
                if inspect.isclass(first):
                    method_type = "classmethod"
                    class_name = first.__name__
                elif hasattr(first, "__class__"):
                    method_type = "instancemethod"
                    class_name = first.__class__.__name__

            # Insert initial Call record
            with Session(engine) as session:
                call_record = Call(
                    function_id=func_id,
                    parent_call_id=parent,
                    timestamp=start,
                    thread_id=tid,
                    is_coroutine=is_coro,
                    method_type=method_type,
                    class_name=class_name
                )
                session.add(call_record)
                session.commit()
                session.refresh(call_record)
                call_id = call_record.id
                _call_stack.stack.append(call_id)

                # Record each argument
                for name, val in bound.arguments.items():
                    arg = Argument(
                        call_id=call_id,
                        name=name,
                        value=json.dumps(val, default=str)
                    )
                    session.add(arg)
                session.commit()

            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                elapsed = (time.time() - start) * 1000
                tb_text = traceback.format_exc()
                with Session(engine) as session:
                    db_call = session.get(Call, call_id)
                    db_call.duration_ms = elapsed
                    db_call.exception_type = type(exc).__name__
                    db_call.exception_message = str(exc)
                    db_call.tb = tb_text
                    session.add(db_call)
                    session.commit()
                _call_stack.stack.pop()
                raise
            else:
                elapsed = (time.time() - start) * 1000
                with Session(engine) as session:
                    db_call = session.get(Call, call_id)
                    db_call.duration_ms = elapsed
                    db_call.return_value = json.dumps(result, default=str)
                    session.add(db_call)
                    session.commit()
                _call_stack.stack.pop()
                return result

        return wrapper

    return decorator
