import time


def parametrized(dec):
    def layer(*args, **kwargs):
        def repl(f):
            return dec(f, *args, **kwargs)

        return repl

    return layer


@parametrized
def timeit(f, method):
    def timed(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', f.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print(method)
            print(args, kw)
            print(f"{method} {f.__name__} : {(te - ts) * 1000}")
        return result

    return timed


@timeit("h3llo")
def printed_ones(name):
    print(name)


printed_ones("Hello")