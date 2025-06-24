from vibetracer import info_decorator


@info_decorator()
def add(a, b):
    return a + b


@info_decorator()
def multiply(x, y=2):
    return x * y


@info_decorator()
def nested_operations(n):
    total = 0
    for i in range(n):
        total = add(total, multiply(i))
    return total


@info_decorator()
def may_fail(flag):
    if not flag:
        raise ValueError("Flag must be True!")
    return "Success"


@info_decorator()
def orchestrator(n, flag):
    # Nested calls + exception handling
    total = nested_operations(n)
    try:
        status = may_fail(flag)
    except ValueError:
        status = "Recovered"
    return {"total": total, "status": status}


class Service:
    @info_decorator()
    def process(self, data):
        # List comprehension with nested decorated calls
        return [self._transform(x) for x in data]

    @info_decorator()
    def _transform(self, x):
        if x == 0:
            raise ZeroDivisionError("Cannot transform zero")
        return 100 / x


@info_decorator()
def factorial(n):
    # Recursive decorated function
    return 1 if n <= 1 else n * factorial(n - 1)


@info_decorator()
def make_incrementor(step):
    # Closure example
    def inc(x):
        return x + step

    return inc


@info_decorator()
def use_incrementor(step, value):
    inc = make_incrementor(step)
    return inc(value)


def main():
    print("Orchestrator result:", orchestrator(5, False))
    svc = Service()
    try:
        print("Service result:", svc.process([5, 0, 2]))
    except ZeroDivisionError:
        print("Caught error in Service.process")
    print("Factorial(4):", factorial(4))
    print("Increment via closure:", use_incrementor(7, 3))


if __name__ == "__main__":
    main()
