from exceptions import EchoDownloaderExceptions
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from collections import defaultdict
import logging
import requests
import json
import extractor
import sys
import re


def display_video_retrieval_progress(cur, tot):
    prefix = ">> Retrieving echo360 Course Info... "
    status = f"{cur}/{tot} videos"
    # using carriage return to refresh the progress bar
    text = f"\r{prefix} {status} "
    sys.stdout.write(text)
    sys.stdout.flush()


class EchoCloud(object):
    def __init__(self, domain_name, uuid, driver):
        self._uuid = uuid
        self._domain_name = domain_name
        self._web_driver = driver
        self._logger = logging.getLogger(__name__)
        self._session = requests.Session()

        # setup cookies
        self.renew_cookies()

    def renew_cookies(self):
        if self._web_driver:
            for cookie in self._web_driver.get_cookies():
                self._session.cookies.set(cookie["name"], cookie["value"])
        else:
            raise EchoDownloaderExceptions("Webdriver Not Installed yet!")

    # for debugging

    def dump_to(self, obj, path):
        with open(path, 'w') as f:
            f.write(obj)
            f.write('\n')

    @property
    def uuid(self):
        return self._uuid

    @property
    def session(self):
        return self._session

    @property
    def domain_name(self):
        return self._domain_name

    @property
    def web_driver(self):
        if not self._web_driver:
            raise EchoDownloaderExceptions("Webdriver Not Installed yet!")
        return self._web_driver

    @web_driver.setter
    def web_driver(self, driver):
        self._web_driver = driver


class EchoCloundSubject(EchoCloud):
    def __init__(self, *args, **kwargs):
        super(EchoCloundSubject, self).__init__(*args, **kwargs)
        self._subject_name = None
        self._subject_data = None

    @property
    def subject_name(self):
        return self._subject_name

    @property
    def subject_json_data(self):
        return self._subject_data

    @property
    def subject_info_url(self):
        if not self._uuid or not self._domain_name:
            raise EchoDownloaderExceptions("Empty uuid or domain name given!")
        return "{0}/section/{1}/syllabus".format(self._domain_name, self._uuid)

    def retrieve_subject_info(self):
        # get syllabus json file
        subject_url = self.subject_info_url
        try:
            self._web_driver.get(subject_url)
            self._logger.debug(f"Found course syllabus url {subject_url} \
                                 with content: {self._web_driver.page_source}")
            # retrieving data
            # session = requests.Session()
            # # load cookies
            # for cookie in self._web_driver.get_cookies():
            #     session.cookies.set(cookie["name"], cookie["value"])
            self.renew_cookies()

            response = self.session.get(subject_url)
            if not response.ok:
                self._logger.error(
                    f"Can't get response from url: {subject_url} with response state: {response.status_code}.")
                raise EchoDownloaderExceptions("Failed to retieve JSON!")

            self._logger.debug(f"Syllabus JSON: \n{response.text}")
            self._subject_data = json.loads(response.text)
            self._subject_name = extractor.get_subject_name(self._subject_data)

        except ValueError as e:
            self._logger.error(
                f"Can't retrieve JSON from url: {subject_url}.")

        return self._subject_data


class EchoCloudMedia(EchoCloundSubject):
    def __init__(self, *args, **kwargs):
        super(EchoCloudMedia, self).__init__(*args, **kwargs)
        self._num_vedios = None
        self._videos = []
        self._m3u8_urls_all = []
        self._medias_all = defaultdict(lambda: defaultdict(list))

    def video_url(self, video_id):
        return f"{self.domain_name}/lesson/{video_id}/classroom"

    @property
    def m3u8_urls_all(self):
        return self._m3u8_urls_all

    @property
    def medias(self):
        return self._medias_all

    @property
    def videos(self):
        return self._videos

    def _get_video_id_and_time(self, video_json):
        video_id = "Unknown_ID"
        start_date = "Unknown_Date"
        video_name = "Unknown_Name"

        try:
            # get vedio id
            video_id = str(video_json["lesson"]["lesson"]["id"])
        except KeyError:
            self._logger.warning("Can't find the correct entry of vedio id")

        try:
            # get date info
            # ignore the error when parsing the date
            start_date = str(video_json["lesson"]["lesson"]["createdAt"])
        except:
            self._logger.warning("Can't find the correct entry of time")

        try:
            # get vedio name
            video_name = str(video_json["lesson"]["lesson"]["name"].split()[0]) + \
                '_' + re.sub("[^0-9a-zA-Z-_]", "_", start_date)
        except KeyError:
            self._logger.warning("Can't find the correct entry of vedio name")

        return video_id, video_name, start_date

    def retrieve_videos_list(self, groups=None):
        subject_data = self.retrieve_subject_info()
        try:
            videos_json = subject_data["data"]
            self._num_vedios = len(videos_json)
            display_video_retrieval_progress(0, self._num_vedios)

            for i, video_jason in enumerate(videos_json):
                # construct vedio
                if "lessons" in video_jason:
                    # TODO(Andy): handle multiple parts logic
                    self._logger.info("This vedio contains multiple parts.")
                else:
                    # pass in the jason file and let the vedio class handle it
                    v_id, v_name, v_time = self._get_video_id_and_time(
                        video_jason)
                    if v_id:
                        if not v_name:
                            v_name = "video_" + str(i)

                        video = Video(v_id, v_time, v_name)
                        video.url = self.video_url(v_id)
                        self._videos.append(video)

                    else:
                        self._logger.warning(
                            f"The {i}th entry's Vedio ID not found!")

                # update the progress bar
                display_video_retrieval_progress(i+1, self._num_vedios)

        except Exception as e:
            self._logger.error("Exception happened when processing media data")
            self._logger.error(e)

    def retrieve_m3u8_urls(self):
        print()
        for video in self._videos:
            print(f"Attempt to retrieve video with name: {video.name}")

            if video.url:
                video.m3u8_urls = self._retrieve_single_m3u8_url(video.url)
                # just for ez debugging and usage in the future
                self._m3u8_urls_all += video.m3u8_urls
            else:
                print("No url found for this vedio.")

        print("\nRetrieving all m3u8 urls done!")
        return self._m3u8_urls_all

    def _retrieve_single_m3u8_url(self, v_url, max_attempts=5):

        refresh_attempt = 1
        stale_attempt = 1

        self._logger.debug("Parsing pagesour to find m3u8 urls.")

        while True:
            self._web_driver.get(v_url)

            try:
                # the replace is for reversing the escape by the escapped js in the page source
                # add "content" avoiding aws s3 format
                urls = set(re.findall(
                    'https://content[^,"]*?[.]{}'.format("m3u8"),
                    self._web_driver.page_source.replace("\/", "/"))
                )
                break

            except TimeoutException:
                if refresh_attempt >= max_attempts:
                    print(
                        f'\r\nERROR: Connection timeouted for {max_attempts} attempts... \
                              Possibly internet problem?')
                else:
                    refresh_attempt += 1

            except StaleElementReferenceException:
                if stale_attempt >= max_attempts:
                    print(
                        '\r\nERROR: Elements are not stable to retrieve after {} attempts... \
                            Possibly internet problem?'.format(max_attempts))
                else:
                    stale_attempt += 1

        m3u8_urls = [url for url in urls if url.endswith("av.m3u8")]

        if not m3u8_urls:
            print("No audio+video m3u8 files found! Skipping...\n")
            return None
        else:
            # usually the video contains two resolution, low quality and high quality with
            # format s1q1.m3u8, s1q2.m3u8,etc. While the audio file usually begins with s0 in UNSW
            # We hard coded here for convinience and prefer the high resolution!
            # TODO(Andy): make it configurable
            m3u8_urls = list(reversed(m3u8_urls))
            return m3u8_urls[:2]

    def retrieve_media_urls(self, m3u8urls):
        for video in self._videos:
            for m3u8url in video.m3u8_urls:
                r = self.session.get(m3u8url)

                if not r.ok:
                    print(
                        f"Error accessing the page with status code: {r.status_code}")
                    # TODO(Andy): add error code systems
                    return False

                try:
                    chunk_a, chunk_v = \
                        extractor.get_a_v_chunk_urls(
                            r.content.decode("utf-8"))

                    base_url = re.sub("\w+[^/].m3u8", "", m3u8url)
                    chunk_url_a, chunk_url_v = base_url + chunk_a, base_url + chunk_v,

                    video.set_chunk_a_v_urls_dic(chunk_url_a, chunk_url_v)

                    # get chunk list from the current m3u8
                    a_chunk_files, v_chunk_files = self.get_chunk_files(video)

                    video.media['a'] += [base_url + str(e)
                                         for e in a_chunk_files]
                    video.media['v'] += [base_url + str(e)
                                         for e in v_chunk_files]

                except Exception as e:
                    self._logger.error(
                        f"Can't retrieve byte chunk files from url:\n {m3u8url}")
                    self._logger.error(
                        f"Exception occured: {e}")

        # return all the downloadable links
        for v in self.videos:
            self._medias_all[str(v.name)]['audio'] = list(set(v.media['a']))
            self._medias_all[str(v.name)]['video'] = list(set(v.media['v']))

        return self._medias_all

    def get_chunk_files(self, video):
        v_urls = video._chunk_urls["v"]
        a_urls = video._chunk_urls["a"]

        if not v_urls:
            print("Can't find the video chunk url")
            return None

        if not a_urls:
            print("Can't find the audio chunk url")
            return None

        # get video
        v = set()
        for url in v_urls:
            r = self.session.get(url)
            if not r.ok:
                print(
                    f"Error accessing chunk files with status code: {r.status_code}")

                return None
            v = v.union(extractor.media_files_from(r.content.decode('utf-8')))

        # get audio
        a = set()
        for url in a_urls:
            r = self.session.get(url)
            if not r.ok:
                print(
                    f"Error accessing chunk files with status code: {r.status_code}")
                return None
            a = a.union(extractor.media_files_from(r.content.decode('utf-8')))

        return list(a), list(v)


class Video(object):
    def __init__(self, id, time, name):
        self._id = id
        self._url = None
        self._start_time = time
        self._name = name
        self._m3u8_urls = None
        self._chunk_urls = {'v': [], 'a': []}
        # TODO(Andy): if it is possible that one video can be seperated into several parts
        self._media = {'v': [], 'a': []}

    @ property
    def id(self):
        return self._id

    @ property
    def url(self):
        return self._url

    @ url.setter
    def url(self, url):
        self._url = url

    @ property
    def time(self):
        return self._start_time

    @ property
    def name(self):
        return self._name

    @ property
    def m3u8_urls(self):
        return self._m3u8_urls

    @ m3u8_urls.setter
    def m3u8_urls(self, url):
        self._m3u8_urls = url

    @ property
    def chunk_a_v_urls_dic(self):
        return self._chunk_urls['a'], self._chunk_urls['v']

    def set_chunk_a_v_urls_dic(self, a, v):
        self._chunk_urls['a'].append(a)
        self._chunk_urls['v'].append(v)

    @ property
    def media(self):
        return self._media

    @ media.setter
    def media(self, media):
        self._media = media


if __name__ == "__main__":
    # uni test
    domain_name = "https://echo360.org.au"
    uuid = "7779731f-9279-4ec7-8460-e5604d92245a"

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    opts = Options()
    opts.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=opts)

    driver.get("{0}/section/{1}/syllabus".format(domain_name, uuid))

    Media = EchoCloudMedia(domain_name, uuid, driver)

    # info = subject.retrieve_subject_info()

    # subject.dump(json.dumps(subject.subject_json_data), "./syllabus.json")

    videos_list = Media.retrieve_videos_list()
    m3u8_urls = Media.retrieve_m3u8_urls()
    print(Media.retrieve_media_urls(m3u8_urls))
