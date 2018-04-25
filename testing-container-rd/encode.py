import csv
import base64

import time


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r :  %2.2f ms' % \
                  (method.__name__, (te - ts) * 1000))
        return result

    return timed


@timeit
def benchmark_encode():
    with open('rating.csv', 'rb') as f:
        csv_data = f.read()
        encoded_data = base64.b64encode(csv_data)
        decoded_data = base64.b64decode(encoded_data)
    return encoded_data


a = benchmark_encode()

print(a)