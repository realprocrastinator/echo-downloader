import ffmpy
import os
import sys
import argparse
from webdriver import WebBrowser
from infohandler import *
from downloader import *
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# global section
DEBUG = True


def parse_args():
    pass


def main():
    pass


def convert_to_mp4(faudio, fvideo, fout):
    if os.path.exists(fout):
        os.remove(fout)

    ff = ffmpy.FFmpeg(
        global_options="-loglevel panic",
        inputs={fvideo: None, faudio: None},
        outputs={fout: ['-c:v', 'copy', '-c:a', 'ac3']}
    )

    ff.run()


if __name__ == "__main__":
    # log in

    # uni test
    domain_name = "https://echo360.org.au"
    uuid = "7779731f-9279-4ec7-8460-e5604d92245a"
    user_email = "jiawei.gao@student.unsw.edu.au"
    user_name = "z5242283@ad.usnw.edu.au"
    pwd = "kmh961127_"

    opts = Options()
    opts.add_argument("--no-sandbox")
    # opts.add_argument("--no-startup-window")

    driver = webdriver.Chrome(options=opts)
    driver.get("{0}/section/{1}/syllabus".format(domain_name, uuid))

    # for debugging
    # ele = driver.find_elements_by_id(
    #     "email")
    # if not ele:
    #     print("Can't find such element with 'email' id.")
    # errors = ele[0].send_keys(user_email)
    # e_msg = "Incorrect username or password."
    # if errors:
    #     print(f"[!] Login failed with reason: {e_msg}")
    # else:
    #     print("[+] Login successful")

    # ele = driver.find_element_by_id("submitBtn").click()
    # errors = driver.find_elements_by_id(
    #     "addId").send_keys(user_email)

    # retrieve the video info and m3u8 urls
    Media = EchoCloudMedia(domain_name, uuid, driver)
    videos_list = Media.retrieve_videos_list()
    m3u8_urls = Media.retrieve_m3u8_urls()
    Media.retrieve_media_urls(m3u8_urls)

    # download!
    downloader = Downloader()
    downloader.config_dowloader(session=Media.session)

    print("> Downloading...")
    for video in Media.videos:
        # create workers
        for k, v in video.media.items():
            # a{video_name}_s010.ms4
            for url in v:
                output_file = str(k) + str(video.name) + "_" + \
                    str(url.split('/')[-1])
                downloader.create_workers(
                    group=video.name, target=downloader.download, args=(url, output_file))
                # init progress
                # downloader.init_progress(url)
                # downloader.display_progress_bar()

    if DEBUG:
        downloader.start_all(groups=[Media.videos[0].name])
    else:
        downloader.start_all()

    # clear screen
    # downloader.cls()

    # while any(w.is_alive() for g in downloader.workers.values() for w in g):
    #     while not downloader.status.empty():
    #         id, current, total = downloader.status.get()
    #         downloader.progress[id] = downloader.update_progress_bar(
    #             id, current, total)
    #         downloader.display_progress_bar()

    # not need to call this
    # downloader.barrier(groups=[Media.videos[0].name])

    print("> Converting to mp4 file...")
    # convert to ffmpeg
    for v in Media.videos:
        # check if downloading completed
        print(f"Converting {v.name}")

        # TODO(Andy): how to handle multiple a/v files?
        in_audio = None
        in_video = None

        # get audio file
        for url in v.media['a']:
            if url in downloader.downloaded:
                in_audio = downloader.downloaded[url]
            else:
                print(f"Missing autio file of {v.name} from url: {url}")

        # get video file
        for url in v.media['v']:
            if url in downloader.downloaded:
                in_video = downloader.downloaded[url]
            else:
                print(f"Missing vedio file of {v.name} from url: {url}")

        # actual convert
        if in_audio and in_video:
            convert_to_mp4(in_audio, in_video, os.path.join(
                downloader._output_dir, v.name + ".mp4"))

        if DEBUG:
            break
