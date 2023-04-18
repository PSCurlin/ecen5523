def compose(f, g):
    def _compose(x):
        return f(g(x))
    return _compose

def f(x):
    return x + 1

def g(x):
    return x + -1

print(compose(f, g)(23))