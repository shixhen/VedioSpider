# =======================================================
# Bilibili Downloader
# Copyright (c) 2022 chaziming
# All rights reserved.
#
# 本开源程序遵循 Apache License 2.0 协议
# =======================================================

"""
说明：一.需要ffmpeg并设置环境变量以完成视频合成
二.本程序优点：1.只需输入哔哩哔哩网址就可爬取视频，最高支持高清1080P画质
2.个性化进度条展示
缺点：1.不是gui编程
三：具体消息/更新内容请浏览下方announcement()函数
"""

import re
import sys

from datetime import timedelta
from json import loads
from os import remove, path
from subprocess import Popen
from time import time
from lxml import etree
from requests import Session
from requests.exceptions import RequestException

__version__ = 'v0.2.2'
__author__ = 'chaziming'

session = Session()


def get_html(url):
    global session
    head = {
        "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.56'
    }
    try:
        response = session.get(url=url, headers=head)
        if response.status_code == 200:
            return response.text
    except RequestException:
        print("请求失败")
        quit()


def get_title(url):
    while True:
        try:
            html = get_html(url)
            title = etree.HTML(html)
            title = title.xpath('//div[@id="viewbox_report"]/h1/span/text()')[0]
            break
        except IndexError:
            html = get_html(url)
            title = etree.HTML(html)
            title = title.xpath('//div[@id="viewbox_report"]/h1/span/text()')[0]
            break
    title = re.sub('[/\\\\:*;?"<>\\]|\\[] ', '', title)
    title = re.sub(' ', '', title)
    print('您当前正在下载：', title)
    return title


def file_download(url, video_url, audio_url, title):
    global session

    headers = {
        "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.56'}
    headers.update({'Referer': url})
    headers['Range'] = 'bytes=' + '0' + '-'

    chunk_size = 1024 * 1024
    video_res = session.get(url=video_url, stream=True, headers=headers)
    video_size = int(video_res.headers['content-length'])
    audio_res = session.get(url=audio_url, stream=True, headers=headers)
    audio_size = int(audio_res.headers['content-length'])
    total_size = video_size + audio_size
    t = time()
    speed = 0.0
    size = 0
    print('开始下载视频')

    with open('%s_video.mp4' % title, 'ab') as f:
        for data in video_res.iter_content(chunk_size=chunk_size):  # 每次只获取一个chunk_size大小
            f.write(data)  # 每次只写入data大小
            tt = time() - t
            t = time()
            size = len(data) + size
            # 'r'每次重新从开始输出，end = ""是不换行
            percentage = int(size / total_size * 40)
            if speed < 5.0:
                color = '\033[1;31m'
            else:
                color = '\033[1;32m'
            if speed == 0.0 or round((total_size - size) / chunk_size / speed) > 1800:
                eta = '\033[1;31m' + ' >30min'
            else:
                eta = '\033[1;34m' + ' eta ' + str(timedelta(seconds=round((total_size - size) / chunk_size / speed)))
            print('\r\t' + "\033[1;35m" + percentage * '━' + '\033[0m' + (40 - percentage) * '━' + '\033[1;35m',
                  str(round(size / chunk_size, 1)) + '/' + str(round(total_size / chunk_size, 1)), "MB" + color,
                  str(speed), 'MB/s' + eta, flush=True,
                  end='')
            sys.stdout.flush()
            try:
                speed = round(float(chunk_size / 1024 / 1024) / tt, 1)
            except ZeroDivisionError:
                speed = '错误'

    speed = 0

    with open('%s_audio.mp4' % title, 'ab') as f:
        for data in audio_res.iter_content(chunk_size=chunk_size):  # 每次只获取一个chunk_size大小
            f.write(data)  # 每次只写入data大小
            tt = time() - t
            t = time()
            size = len(data) + size
            # 'r'每次重新从开始输出，end = ""是不换行
            percentage = int(size / total_size * 40)
            if speed < 5.0:
                color = '\033[1;31m'
            else:
                color = '\033[1;32m'
            if speed == 0.0 or round((total_size - size) / chunk_size / speed) > 1800:
                eta = '\033[1;31m' + ' >30min'
            else:
                eta = '\033[1;34m' + ' eta ' + str(timedelta(seconds=round((total_size - size) / chunk_size / speed)))
            print('\r\t' + "\033[1;35m" + percentage * '━' + '\033[0m' + (40 - percentage) * '━' + '\033[1;35m',
                  str(round(size / chunk_size, 1)) + '/' + str(round(total_size / chunk_size, 1)), "MB" + color,
                  str(speed), 'MB/s' + eta, flush=True,
                  end='')
            last_speed = speed
            sys.stdout.flush()
            try:
                speed = round(float(chunk_size / 1024 / 1024) / tt, 1)
            except ZeroDivisionError:
                speed = '错误'

    if last_speed < 5.0:
        color = '\033[1;31m'
    else:
        color = '\033[1;32m'
    print('\r\t''\033[1;32m' + 40 * '━' + '\033[1;32m',
          str(round(size / chunk_size, 1)) + '/' + str(round(total_size / chunk_size, 1)), "MB" + color,
          str(speed), 'MB/s' + '\033[1;34m', 'eta', '0:00:00' + '\033[0m', flush=True)
    combine(title)


def get_url(url):
    quality_dict = {
        '1': '高清 1080P',
        '2': '高清 720P60',
        '3': '清晰 480P',
        '4': '流畅 360P',
    }

    html = get_html(url)
    pattern = r'\<script\>window\.__playinfo__=(.*?)\</script\>'
    result = re.findall(pattern, html)[0]
    temp = loads(result)

    print(re.sub('[{}\',]', '', str(quality_dict)))
    quality = int(input('请选择视频画质：'))
    accept_quality = temp['data']['accept_description'][quality]
    video_time = temp['data']['dash']['duration']
    video_minute = video_time // 60
    video_second = video_time % 60
    print('当前视频清晰度为{}，时长{}分{}秒'.format(accept_quality, video_minute, video_second))
    video_url = temp['data']['dash']['video'][quality * 2 - 2]['baseUrl']
    audio_url = temp['data']['dash']['audio'][0]['baseUrl']
    return video_url, audio_url


def get_number(url):
    html = get_html(url)
    pattern = r'\<script\>window\.__INITIAL_STATE__=(.*?)\</script\>'
    result = re.findall(pattern, html)[0]
    result = re.findall('"pages":(\\[.*?])', result)[0]
    temp = loads(result)
    return len(temp)


def combine(title):
    print('processing')
    command = 'ffmpeg -i %s_video.mp4 -i %s_audio.mp4 -c copy %s.mp4 -y -loglevel quiet' % (
        title, title, title)
    Popen(command, shell=True)
    while True:
        try:
            if path.exists('%s.mp4' % title):
                remove('%s_video.mp4' % title)
                remove('%s_audio.mp4' % title)
                break
        except PermissionError:
            pass


def announcement():
    title = 'Bilibili Downloader' + ' '
    author = 'chaziming'
    version = 'v0.2.2'
    dividing_line = '-' * 40 + '\n'
    fix_bugs = '暂无'
    optimization = '一.新增功能：1.增强了在下载系列视频时的体验\n'
    spread = 'more see: https://github.com/chaziming/Video-Downloader\n'
    print('\033[1;34m' + dividing_line + title, version, 'by', author)
    print('公告：\n' + fix_bugs + optimization + spread + dividing_line + '\033[0m')
    return


def main():
    announcement()
    print('欢迎使用bilibili下载器')
    print('\033[1;31m' + '请确保已下载ffmpeg并设置好了环境变量，否则到最后将无法合成视频！！！' + '\033[0m')
    url = re.findall('(.*?\\?)', input('请输入视频的网址：'))[0]
    print(url)
    print('正在解析网页......')
    number = get_number(url)
    if number > 1:
        print(f'检测到您正在下载系列视频，且该系列视频共有{number}个')
        p = input('请输入您要爬取的集数（目前只支持输入一个，如果要爬取全部请输入0）：')
        url = re.findall('http.*?BV.*?\\?', url)[0]
        if p == '0':
            for i in range(number):
                video_url, audio_url = get_url(url + 'p=' + i+1)
                file_download(url, video_url, audio_url, get_title(url))
            print('视频下载成功，请查收')
            input('按回车以结束程序')
            quit()
        else:
            video_url, audio_url = get_url(url + 'p=' + p)
            file_download(url, video_url, audio_url, get_title(url))
            print('视频下载成功，请查收')
            input('按回车以结束程序')
            quit()
    else:
        video_url, audio_url = get_url(url)
        file_download(url, video_url, audio_url, get_title(url))
        print('视频下载成功，请查收')
        input('按回车以结束程序')
        quit()


if __name__ == "__main__":
    main()
