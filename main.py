import ffmpy
import os
import sys
import argparse
import json
from webdriver import WebBrowser
from infohandler import *
from downloader import *
from exceptions import EchoDownloaderExceptions
# from selenium import webdriver# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# global section
DEBUG = True
LOGGER = logging.getLogger(__name__)


def handle_args():
    parser = argparse.ArgumentParser(
        description="Downloa lectures from Echo360Cloud.",
    )

    parser.add_argument(
        "url",
        help="The url of Course home page.",

    )

    parser.add_argument(
        "--output",
        "-o",
        help="Path to the desired output directory. The output director \
            must exist. Otherwise the default directory is used.",
    )

    parser.add_argument(
        "--entry-email",
        '-e',
        help="Your email for accessing the echo360 Cloud login page. \
            Usually it's in format: 'name@student.unsw.edu.au'.",

    )

    parser.add_argument(
        "--username",
        '-u',
        help="username for echo360. (eg.zid@ad.unsw.edu.au)",
    )

    parser.add_argument(
        "--password",
        '-p',
        help="Your passwrd for echo360 account.",
    )

    parser.add_argument(
        "--interactive",
        '-i',
        action="store_true",
        default=False,
        help="Interactively pick the lectures you want, instead of download all \
                              (default) or based on dates .",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable extensive logging and debug mode.",
    )

    parser.add_argument(
        "--cmd-line-mode",
        action="store_true",
        default=False,
        help="Don't pop up the browser. All the actions will happen in the terminal. \
            uni_email, echo username and password must be provided!"
    )

    parser.add_argument(
        "--file",
        '-f',
        help="Download from the media description file. The file shoulbe be named \
            with .echo extension."
    )

    parser.add_argument(
        "--dump-to",
        "-d",
        help="Dumping all videos to json which can be fed into downloader later."
    )

    parser.add_argument(
        "--single-thread-mode",
        action="store_true",
        default=False,
        help="Downloading videos and audios one after one."
    )

    parser.add_argument(
        "--no-downloading-mode",
        action="store_true",
        default=False,
        help="Only extracting media info without downloading."
    )

    args = vars(parser.parse_args())
    course_homepage_url = args["url"]

    output_path = (
        os.path.expanduser(args["output"])
        if args["output"] is not None
        else None
    )

    # video/audio output path
    if output_path:
        output_path = output_path if os.path.isdir(output_path) else \
            None

    domain_name = extractor.get_domain_name(course_homepage_url)
    uuid = extractor.get_uuid(course_homepage_url)

    user_email = args["entry_email"]
    user_name = args["username"]

    echo_file_path = os.path.expanduser(
        args["file"]) if args["file"] else None

    # echo media file output path
    dump_path = os.path.expanduser(
        args["dump_to"]) if args["dump_to"] else None

    return (course_homepage_url,
            domain_name,
            uuid,
            user_email,
            user_name,
            output_path,
            echo_file_path,
            dump_path,
            args["interactive"],
            args["debug"],
            args["cmd_line_mode"],
            args["single_thread_mode"],
            args["no_downloading_mode"])


def main():
    (course_homepage_url,
     domain_name,
     uuid,
     user_email,
     user_name,
     output_path,
     echo_file_path,
     dump_path,
     mode_interactive,
     mode_debug,
     mode_cmdl,
     mode_single_thread,
     mode_no_downloading) = handle_args()

    # regular check
    if not domain_name or not uuid:
        print("No correct domain name or uuid found. Please make sure the url is \
            correct and belongs to Echo360 Cloud.")

    login_mode = "browser"
    if mode_cmdl:
        if not user_email or not user_name:
            print("Credentials must be provided in cmd-line mode.")
            # TODO(Andy): add erro code system
            return -1
        login_mode = "cmd"

    DEBUG = mode_debug

    # if echo file provided, we need to parse the echo file,
    # and download from it directly.

    # init web driver
    web_browser = WebBrowser()
    web_driver = web_browser.web_driver
    if not web_driver:
        print("Can't initialize the web driver.")
        raise EchoDownloaderExceptions("Driver not installed.")

    # login
    res = web_browser.login(course_homepage_url,
                            user_email,
                            user_name,
                            mode=login_mode)

    if not res:
        print("Can't log in successfully.")
        return -1

    # retrieve the video info
    web_browser.browse_to("{0}/section/{1}/syllabus".format(domain_name, uuid))
    Media = EchoCloudMedia(domain_name, uuid, web_driver)
    videos_list = Media.retrieve_videos_list()
    m3u8_urls = Media.retrieve_m3u8_urls()
    Media.retrieve_media_urls(m3u8_urls)

    if dump_path:
        try:
            with open(dump_path, 'w') as f:
                print(
                    f"Dumping the media info to {str(dump_path)}")
                # do dump
                f.write(json.dumps(
                    Media.medias,
                    indent=2)
                )
        except Exception as e:
            LOGGER.error(
                f"Failed to dump to path {dump_path}\n with error: {e}")
            print("Can't dump the media info file. Please examine the log file.")

    downloader = Downloader()
    downloader.config_dowloader(session=Media.session, output_dir=output_path)

    if not mode_no_downloading:
        do_download(Media, downloader, mode_single_thread)
        do_convert(Media, downloader)


def do_download(Media, downloader, single_thread=False):

    print("> Downloading...")
    # TODO: single downloading mode and multithreding downloading mode.
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

    # TODO(Andy): add group feature so that we can download a group of videos
    if DEBUG:
        downloader.start_all(groups=[Media.videos[0].name])
    else:
        downloader.start_all()

    # not need to call this
    if DEBUG:
        downloader.barrier(groups=[Media.videos[0].name])
    else:
        downloader.barrier()


def convert_to_mp4(faudios, fvideos, fout):
    if os.path.exists(fout):
        os.remove(fout)

    ff = ffmpy.FFmpeg(
        global_options="-loglevel panic",
        inputs={f: None for f in fvideos + faudios},
        outputs={fout: ['-c:v', 'copy', '-c:a', 'ac3']}
    )

    ff.run()


def do_convert(Media, downloader):
    print("> Converting to mp4 file...")
    # convert to ffmpeg
    for v in Media.videos:
        # check if downloading completed
        print(f"Converting {v.name}")

        # TODO(Andy): how to handle multiple a/v files?
        in_audios = []
        in_videos = []

        # get audio file
        for url in v.media['a']:
            if url in downloader.downloaded:
                in_audios.append(downloader.downloaded[url])
            else:
                print(f"Missing autio file of {v.name} from url: {url}")

        # get video file
        for url in v.media['v']:
            if url in downloader.downloaded:
                in_videos.append(downloader.downloaded[url])
            else:
                print(f"Missing vedio file of {v.name} from url: {url}")

        # actual convert
        if in_audios and in_videos:
            convert_to_mp4(in_audios, in_videos, os.path.join(
                downloader._output_dir, v.name + ".mp4"))

        if DEBUG:
            break


if __name__ == "__main__":
    # # log in

    # # uni test
    # domain_name = "https://echo360.org.au"
    # uuid = "7779731f-9279-4ec7-8460-e5604d92245a"
    # user_email = "jiawei.gao@student.unsw.edu.au"
    # user_name = "z5242283@ad.usnw.edu.au"
    # pwd = "kmh961127_"

    # opts = Options()
    # opts.add_argument("--no-sandbox")
    # # opts.add_argument("--no-startup-window")

    # driver = webdriver.Chrome(options=opts)
    # driver.get("{0}/section/{1}/syllabus".format(domain_name, uuid))

    # # for debugging
    # # ele = driver.find_elements_by_id(
    # #     "email")
    # # if not ele:
    # #     print("Can't find such element with 'email' id.")
    # # errors = ele[0].send_keys(user_email)
    # # e_msg = "Incorrect username or password."
    # # if errors:
    # #     print(f"[!] Login failed with reason: {e_msg}")
    # # else:
    # #     print("[+] Login successful")

    # # ele = driver.find_element_by_id("submitBtn").click()
    # # errors = driver.find_elements_by_id(
    # #     "addId").send_keys(user_email)

    # # retrieve the video info and m3u8 urls
    # Media = EchoCloudMedia(domain_name, uuid, driver)
    # videos_list = Media.retrieve_videos_list()
    # m3u8_urls = Media.retrieve_m3u8_urls()
    # Media.retrieve_media_urls(m3u8_urls)

    # # download!
    # downloader = Downloader()
    # downloader.config_dowloader(session=Media.session)

    # print("> Downloading...")
    # for video in Media.videos:
    #     # create workers
    #     for k, v in video.media.items():
    #         # a{video_name}_s010.ms4
    #         for url in v:
    #             output_file = str(k) + str(video.name) + "_" + \
    #                 str(url.split('/')[-1])
    #             downloader.create_workers(
    #                 group=video.name, target=downloader.download, args=(url, output_file))
    #             # init progress
    #             # downloader.init_progress(url)
    #             # downloader.display_progress_bar()

    # if DEBUG:
    #     downloader.start_all(groups=[Media.videos[0].name])
    # else:
    #     downloader.start_all()

    # # clear screen
    # # downloader.cls()

    # # while any(w.is_alive() for g in downloader.workers.values() for w in g):
    # #     while not downloader.status.empty():
    # #         id, current, total = downloader.status.get()
    # #         downloader.progress[id] = downloader.update_progress_bar(
    # #             id, current, total)
    # #         downloader.display_progress_bar()

    # # not need to call this
    # # downloader.barrier(groups=[Media.videos[0].name])

    # print("> Converting to mp4 file...")
    # # convert to ffmpeg
    # for v in Media.videos:
    #     # check if downloading completed
    #     print(f"Converting {v.name}")

    #     # TODO(Andy): how to handle multiple a/v files?
    #     in_audio = None
    #     in_video = None

    #     # get audio file
    #     for url in v.media['a']:
    #         if url in downloader.downloaded:
    #             in_audio = downloader.downloaded[url]
    #         else:
    #             print(f"Missing autio file of {v.name} from url: {url}")

    #     # get video file
    #     for url in v.media['v']:
    #         if url in downloader.downloaded:
    #             in_video = downloader.downloaded[url]
    #         else:
    #             print(f"Missing vedio file of {v.name} from url: {url}")

    #     # actual convert
    #     if in_audio and in_video:
    #         convert_to_mp4(in_audio, in_video, os.path.join(
    #             downloader._output_dir, v.name + ".mp4"))

    #     if DEBUG:
    #         break
    main()
