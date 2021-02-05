import ffmpy
import os
import sys
from infohandler import *
from downloader import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

DEBUG = True


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

    opts = Options()
    opts.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=opts)
    driver.get("{0}/section/{1}/syllabus".format(domain_name, uuid))

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
                downloader.init_progress(url)
                downloader.display_progress_bar()

    if DEBUG:
        downloader.start_all(groups=[Media.videos[0].name])
    else:
        downloader.start_all()

    while any(w.is_alive() for g in downloader.workers.values() for w in g):
        while not downloader.status.empty():
            id, current, total = downloader.status.get()
            downloader.progress[id] = downloader.update_progress_bar(
                id, current, total)
            downloader.display_progress_bar()

    # not need to call this
    downloader.barrier(groups=[Media.videos[0].name])

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
            convert_to_mp4(in_audio, in_video, v.name + ".mp4")

        if DEBUG:
            break
