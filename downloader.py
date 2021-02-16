import threading
import random
import sys
import os
import requests
import queue
import tqdm
from infohandler import EchoCloud
from exceptions import EchoDownloaderExceptions
from collections import defaultdict, OrderedDict


class Downloader(object):
    def __init__(self):
        self._session = None
        self._chunk_size = 1024
        self._succeeded = dict()
        self._failed = dict()
        self._output_dir = None
        self._workers = defaultdict(list)
        self._status = queue.Queue()
        self._progress = OrderedDict()

    def update_status(self, id, current, total):
        # update status
        self._status.put((id, current, total))

    def update_progress_bar(self, id, current, total, bar_len=20):
        title = "> Progress"
        status = f"{current}/{total}"
        progress = float(current) / float(total)

        if progress <= 0:
            progress = 0
            status = " Waiting\r\n"
        elif progress >= 1:
            progress = 1
            status += " Done!\r\n"

        block = "=" * int(round(bar_len * progress))
        if len(block) < bar_len:
            block += ">"

        progress_bar = block + " " * (bar_len - len(block))

        text = f"{title}: [{progress_bar}] {progress * 100:.2f}% {status}\n"
        return text

    def init_progress(self, worker_id):
        self._progress[worker_id] = "Waiting\r\n"

    def cls(self):
        sys.stdout.write('\033[2J\033[H')  # clear screen

    def display_progress_bar(self):
        # A hacky way to move the cursor :)
        def move(y, x):
            print("\033[%d;%dH" % (y, x))

        for pos, (id, text) in enumerate(self.progress.items()):
            move(pos, 0)
            sys.stdout.write(text)

        sys.stdout.flush()

    @property
    def workers(self):
        return self._workers

    @property
    def status(self):
        return self._status

    @property
    def progress(self):
        return self._progress

    @property
    def downloaded(self):
        return self._succeeded

    def create_workers(self, group, target, args, *, name=None):
        print("Start thread")
        if not name:
            name = "faker_" + chr(random.randint(0x61, 0x61 + 25)) + \
                chr(random.randint(0x61, 0x61 + 25))
        worker = threading.Thread(name=name, target=target, args=args)
        self._workers[group].append(worker)

    def d_start_single(self):
        self._workers[0].start()
        self._workers[0].join()

    def start_all(self, groups=None):
        if not groups:
            for g in self._workers.keys():
                for w in self._workers[g]:
                    w.start()

        elif not isinstance(groups, (list, tuple)):
            print("groups must be a list or tuple object.")
            raise ValueError
        else:
            # start a group of workers
            for g in groups:
                for w in self._workers[g]:
                    w.start()

    def barrier(self, groups=None):
        if not groups:
            for g in self._workers.keys():
                for w in self._workers[g]:
                    w.join()

        elif not isinstance(groups, (list, tuple)):
            print("groups must be a list or tuple object.")
            raise ValueError
        else:
            # start a group of workers
            for g in groups:
                for w in self._workers[g]:
                    w.join()

    def config_dowloader(self, *, session, chunk_size=None, output_dir=None):
        if not session:
            print("Invalid configuration for the Dowloader.")
            return False

        self._session = session

        if chunk_size:
            self._chunk_size = chunk_size

        if output_dir:
            self._output_dir = output_dir
        else:
            root_path = os.path.dirname(
                os.path.abspath(__file__))
            output_path = os.path.join(root_path, "Videos")
            if not os.path.exists(output_path):
                os.mkdir(output_path)
            self._output_dir = output_path

        return True

    def download(self, url, output_file, retry=3):
        if not self._session:
            raise EchoDownloaderExceptions(
                "No avalaible session found! Please configure the downloader first.")

        while retry:
            try:
                r = self._session.get(url)
                if not r.ok:
                    print(
                        f"Can't access via url: {url} with status code: {r.status_code}")
                    return False

                total_size = int(r.headers.get('content-length', 0))
                current_size = 0
                # self.update_progress_bar(url, current_size, total_size)

                self.update_status(url, current_size, total_size)
                output_path = os.path.join(self._output_dir, output_file)

                with tqdm.tqdm(total=total_size, unit='iB', unit_scale=True) as pbar:
                    with open(output_path, "wb") as f:
                        for chunk in r.iter_content(self._chunk_size):
                            f.write(chunk)
                            current_size += self._chunk_size
                            # self.update_progress_bar(url, current_size, total_size)
                            # self.update_status(url, current_size, total_size)
                            pbar.update(len(chunk))

                # success! list object is thread-safe
                self._succeeded[url] = output_path
                return

            except EnvironmentError as e:
                print(f"Failed to write to file with exception:\n {e}")
            except Exception as e:
                retry -= 1
                print(f"Exception happened due to {e}. Retrying...")

        print(
            f"Downloading file {output_file} failed after retry {retry} times.")
        # failed after retry
        self._failed[url] = output_file


if __name__ == "__main__":
    # unit test downloader thread
    # w = Downloader()
    # import time
    # for i in range(5):
    #     w.create_worker(w.download, (i,))

    # unit test progress bar
    # total = 50

    # for i in range(total):
    #     update_progress_bar(i, total)
    #     time.sleep(2)
    #     i += 5

    # unit test
    # uni test
    domain_name = "https://echo360.org.au"
    uuid = "7779731f-9279-4ec7-8460-e5604d92245a"

    # from selenium import webdriver
    # from selenium.webdriver.chrome.options import Options
    # import requests

    # opts = Options()
    # opts.add_argument("--no-sandbox")

    # driver = webdriver.Chrome(options=opts)

    # driver.get("{0}/section/{1}/syllabus".format(domain_name, uuid))

    # session = requests.Session()
    # for cookie in driver.get_cookies():
    #     session.cookies.set(cookie["name"], cookie["value"])

    # d = Downloader()
    # d.config_dowloader(session=session)
    # url = "https://content.echo360.org.au/0000.1eced04d-17e2-4cc3-affa-0643f089cf31/ca21422e-d0d6-49ae-98f1-8bbb98f6c984/1/s0q0.m4s"
    # d.create_workers(d.download, (url, "test_1"))
    # d.d_start_single()
