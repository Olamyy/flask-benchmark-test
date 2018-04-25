import csv
import json
import logging
import multiprocessing
import threading
import time

import elasticsearch
import pymongo
from kafka import KafkaConsumer, KafkaProducer

# 172.21.0.2

es = elasticsearch.Elasticsearch(['172.21.0.2'], port=9200)
client = pymongo.MongoClient('172.21.0.3', 27017, connect=False)
database = client['merged_collection']
collection = database.mongo_consumer

time_taken = {}


def parametrized(dec):
    def layer(*args, **kwargs):
        def repl(f):
            return dec(f, *args, **kwargs)

        return repl

    return layer


@parametrized
def timeit(f, dec_arg):
    def timed(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', f.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print("{0} {1} : {2} ms".format(args[0], dec_arg, (te - ts) * 1000))
        return result

    return timed


def csv_dict_list(path):
    # Open variable-based csv, iterate over the rows and map values to a list of dictionaries containing key/value pairs

    reader = csv.DictReader(open(path, 'rt'))
    dict_list = []
    for line in reader:
        dict_list.append(line)
    return dict_list


class Producer(threading.Thread):
    def __init__(self, filename):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.filename = filename

    def stop(self):
        self.stop_event.set()

    @timeit("producer")
    def run(self):
        producer = KafkaProducer(bootstrap_servers='localhost:9095', value_serializer=lambda m: json.dumps(m).encode('ascii'))
        while not self.stop_event.is_set():
            file_object = csv_dict_list(self.filename)
            for i in file_object:
                for k, v in i.items():
                    producer.send("merged_collection", {k: v})
            time.sleep(1)
        producer.close()


class Consumer(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.stop_event = multiprocessing.Event()

    def stop(self):
        self.stop_event.set()

    @timeit("consumer")
    def run(self, **kwargs):
        consumer = KafkaConsumer(bootstrap_servers='localhost:9095',
                                 auto_offset_reset='earliest',
                                 consumer_timeout_ms=1000)
        consumer.subscribe(['merged_collection'])

        while not self.stop_event.is_set():
            for message in consumer:
                data = {"key": message.key, "value": message.value}
                es.index(index="merged_collection", doc_type='data', id=1, body=data)
                collection.insert(data)
                if self.stop_event.is_set():
                    break

        consumer.close()


def main():
    housing = Producer("housing.csv")
    rating = Producer("rating.csv")
    merged = Producer("xaa")

    tasks = [
        Consumer()
    ]

    filenames = ["housing.csv", "rating.csv"]
    for i in filenames:
        tasks.append(Producer(i))

    for t in tasks:
        t.start()

    time.sleep(10)

    for task in tasks:
        task.stop()

    for task in tasks:
        task.join()


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s',
        level=logging.INFO
    )
    main()
