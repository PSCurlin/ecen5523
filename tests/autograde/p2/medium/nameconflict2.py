x = 7

def y():
    f = 7

def f():
    x = 2
    return lambda y: x + y

print(f()(3))