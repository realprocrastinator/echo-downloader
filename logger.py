import threading
import random
import time
import sys
import queue
import collections


def update_progress_bar(current, total, bar_len=20):
    title = "> Progress"
    status = f"{current}/{total}"
    progress = float(current) / float(total)

    if progress <= 0:
        progress = 0
        status = " Waiting..."
    elif progress >= 1:
        progress = 1
        status += " Done!\n"

    block = "=" * int(round(bar_len * progress))
    if len(block) < bar_len:
        block += ">"

    progress_bar = block + " " * (bar_len - len(block))

    text = f"\r{title}: [{progress_bar}] {progress * 100:.2f}% {status}"
    return text


def move(y, x):
    print("\033[%d;%dH" % (y, x))

# move(0, 0)


if __name__ == "__main__":
    import random
    import time
    import sys

    bar_num = 3

    def do_simulate(total):
        cur = 0
        text = update_progress_bar(cur, total)
        sys.stdout.write(text)
        sys.stdout.flush()

        while (cur < total):
            time.sleep(0.3)
            cur += random.randint(1, 5)
            if cur >= total:
                cur = total
            text = update_progress_bar(cur, total)
            sys.stdout.write(text)
            sys.stdout.flush()

    sys.stdout.write('\033[2J\033[H')  # clear screen

    for i in range(bar_num):
        do_simulate(random.randint(10, 20))
        move(i+1, 0)

    # sys.stdout.write("Hi")
    # move(2, 0)
    # sys.stdout.write("Hi")
    # move(3, 0)
    # sys.stdout.write("Hi\n")

    # def do_work(id, status):
    #     time.sleep(random.randint(1, 5))
    #     for i in range(10):
    #         time.sleep(1)
    #         text = '\rHello ' + str(id) + " " + str(i) + '\n'
    #         status.put((id, text))

    # def do_print(progress):
    #     sys.stdout.write('\033[2J\033[H')  # clear screen
    #     for id, text in progress.items():
    #         sys.stdout.write(text)
    #     sys.stdout.flush()

    # def simple(id, s):
    #     print(2)

    # status = queue.Queue()
    # progress = collections.OrderedDict()
    # workers = []

    # for i in range(10):
    #     workers.append(threading.Thread(target=do_work, args=(i, status)))
    #     progress[i] = "Waiting..."

    # for w in workers:
    #     w.start()

    # while any(w.is_alive() for w in workers):
    #     while not status.empty():
    #         id, text = status.get()
    #         progress[id] = text
    #         do_print(progress)

    # for w in workers:
    #     w.join()

    # import sys
    # import time
    # sys.stdout.write("Hello\nWorld\r")
    # sys.stdout.flush()

    # def move(y, x):
    #     print("\033[%d;%dH" % (y, x))

    # move(0, 0)
    # time.sleep(1)
    # sys.stdout.write("I'm\nAndy\n\r")
    # sys.stdout.flush()

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
