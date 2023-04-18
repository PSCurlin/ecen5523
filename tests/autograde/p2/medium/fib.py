def fib(n):
    return 0 if n == 0 else 1 if n == 1 else fib(n + -1) + fib(n + -2)

print(fib(6))