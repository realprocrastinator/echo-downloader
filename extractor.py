import re


def get_domain_name(url):
    res = re.search("https?:[/]{2}[^/]*", url)
    return res.group() if res else ""


def get_uuid(url):
    res = re.search("[^/]([0-9a-zA-Z]+[-])+[0-9a-zA-Z]+")
    return res.group() if res else ""


def get_subject_name(sbj_json):
    try:
        name = sbj_json['data'][0]['lesson']['lesson']['name'].split()[0]
    except KeyError or IndexError:
        name = "UNKNOWN_COURSE"
    return name


def get_a_v_chunk_urls(http_m3u8):
    lines = http_m3u8.split('\n')
    m3u8_v = ""
    m3u8_a = ""

    i = 1
    # hard coded here to use the high reolution
    # TODO(Andy): make it configurable
    for l in lines[1:]:
        if l and not l.startswith('#'):
            if "RESOLUTION" in lines[i - 1]:
                m3u8_v = l
            else:
                m3u8_a = l
        i += 1
    return m3u8_a, m3u8_v


def media_files_from(http_m3u8):
    return {e for e in http_m3u8.split() if not e.startswith('#')}
