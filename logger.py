import threading
import random
import time
import sys
import queue
import collections

if __name__ == "__main__":

    def do_work(id, status):
        time.sleep(random.randint(1, 5))
        for i in range(10):
            time.sleep(1)
            text = '\rHello ' + str(id) + " " + str(i) + '\n'
            status.put((id, text))

    def do_print(progress):
        sys.stdout.write('\033[2J\033[H')  # clear screen
        for id, text in progress.items():
            sys.stdout.write(text)
        sys.stdout.flush()

    def simple(id, s):
        print(2)

    status = queue.Queue()
    progress = collections.OrderedDict()
    workers = []

    for i in range(3):
        workers.append(threading.Thread(target=do_work, args=(i, status)))
        progress[i] = "Waiting..."

    for w in workers:
        w.start()

    while any(w.is_alive() for w in workers):
        while not status.empty():
            id, text = status.get()
            progress[id] = text
            do_print(progress)

for w in workers:
    w.join()


# import time
# import random
# import sys
# import collections
# # from multiprocessing import Process as Task, Queue
# from threading import Thread as Task
# from queue import Queue


# def download(status, filename):
#     count = random.randint(5, 30)
#     for i in range(count):
#         status.put([filename, (i+1.0)/count])
#         time.sleep(0.1)


# def print_progress(progress):
#     sys.stdout.write('\033[2J\033[H')  # clear screen
#     for filename, percent in progress.items():
#         bar = ('=' * int(percent * 20)).ljust(20)
#         percent = int(percent * 100)
#         sys.stdout.write("%s [%s] %s%%\n" % (filename, bar, percent))
#     sys.stdout.flush()


# def main():
#     status = Queue()
#     progress = collections.OrderedDict()
#     workers = []
#     for filename in ['test1.txt', 'test2.txt', 'test3.txt']:
#         child = Task(target=download, args=(status, filename))
#         child.start()
#         workers.append(child)
#         progress[filename] = 0.0
#     while any(i.is_alive() for i in workers):
#         time.sleep(0.1)
#         while not status.empty():
#             filename, percent = status.get()
#             progress[filename] = percent
#             print_progress(progress)
#     print('all downloads complete')


# main()
