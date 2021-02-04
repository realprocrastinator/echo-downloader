# Scraping Echo360 cloud videos

## Background

##### How do we obtain media files from Echo360?

- Our web browser will send a request asking for the m3u8 file for each video which we can obtain by scanning the page source of the echo360 home page.

  For example like such *url*: `\"https:\/\/content.echo360.org.au\/0000.1eced04d-17e2-4cc3-affa-0643f089cf31\/ca21422e-d0d6-49ae-98f1-8bbb98f6c984\/1\/s1_v.m3u8` which was in a escaped *json* format.

  Once we download get m3u8 file, we can scan the file to obtain the related video and audio m3u8 files. For example, like `s0q0.m3u8` etc. We can obtain the byte chunk description file  by substituting the  of above *url* with `s0q0.m3u8`. And here we go we obtain the description file. Once we had the description file we can obtain the actual video and audio file by finding file with extension `.m4s`

## Modules

### Downloader

Responsible for downloading the audio and video files from the given url.

### Extractor

Responsible for extracting and parsing the info into human readable format.

### Subjects

Responsible for maintaining the course info and the videos info.

### SessionMgr

Responsible for logging into the web session and credentials etc.

### Exceptions

Responsible for handle exceptions.

