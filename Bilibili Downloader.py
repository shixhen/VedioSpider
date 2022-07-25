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

import os
import re
import sys
import time
import json
import datetime
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog
# 需要的第三方库：requests, lxml
import requests
from lxml import etree

__version__ = 'v0.2.4'
__author__ = 'chaziming'


def announcement():
    title = 'Bilibili Downloader' + ' '
    author = __author__
    version = __version__
    dividing_line = '-' * 40 + '\n'
    feature = '本程序特点：优点：1.拥有个性化进度条，让您对下载进度了如指掌\n' \
              '缺点：1.不是gui程序\n'
    optimization = '优化：1.优化代码底层逻辑\n' \
                   '2.缩短了代码长度，压缩了一些重复的代码\n' \
                   '3.优化了检测用户输入的代码，使代码不会因为用户的恶意输入导致报错\n' \
                   '4.优化进度条显示逻辑，使其显示更加稳定\n'
    fix_bugs = '修复了在下载系列视频时出现的一些bug'
    spread = 'more see: https://github.com/chaziming/Video-Downloader\n'
    print('\033[1;34m' + dividing_line + title, version, 'by', author)
    print(feature + '公告：\n' + fix_bugs + optimization + spread + dividing_line + '\033[0m')
    return


# 需要的全局变量及其类型

path: str  # 文件保存路径
session = requests.Session()
headers = {
    "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62'
}


def get_url():
    """
    获取用户输入的网址并判断平台
    :return: url
    """
    while True:
        url = input('请输入视频的地址：')
        if 'bilibili.com' in url:
            try:
                url = re.findall('(.*?\\?)', url)[0]
                print('\033[1;34m' + '检测到您输入的是哔哩哔哩的网址')
                break
            except IndexError:
                print('\033[1;31m' + '请您输入一个正确的哔哩哔哩网址')
            if 'BV' not in url:
                print('\033[1;31m' + '请您输入一个正确的哔哩哔哩网址')
        else:
            print('\033[1;31m' + '您输入的网址有误，请输入一个正确的bilibili网址')
    return url


def get_path():
    """
    获取用户输入视频保存地址
    :return: 视频保存路径
    """
    print('请在弹出的窗口中选择视频位置')
    time.sleep(1)
    root = tk.Tk()
    root.withdraw()
    folder_path = tk.filedialog.askdirectory()
    print('您所选择的路径为：', folder_path)
    return folder_path


def crawl(url, stream=None):
    """
    封装好请求API
    :param stream: 设置是否延迟下载
    :param url: url
    :return: 返回的response
    """
    request_counts = 0
    while True:
        try:
            response = session.get(url=url, headers=headers, stream=stream, timeout=5)
            if response.status_code == 200 or response.status_code == 206:
                break
        except requests.exceptions.RequestException or requests.exceptions.ReadTimeout:
            request_counts += 1
            print(f'请求失败，正在帮您重新请求（请求次数：{request_counts}）')
            time.sleep(1)
    return response


class Bilibili_Downloader:
    quality_dict = {
        '1': '高清 1080P',
        '2': '高清 720P60',
        '3': '清晰 480P',
        '4': '流畅 360P',
    }
    file_size: int
    file_path: str
    downloaded_size = 0  # 已下载的文件大小
    file_res: requests.models.Response

    def __init__(self, url):
        self.url = url
        html = crawl(url).text
        title = self.get_title(html)
        quality = self.get_quality()
        self.get_duration(html, quality)
        video_url, audio_url = self.get_video_and_audio_url(html, quality)
        print('正在下载视频')
        self.file_download(video_url, title)
        print('下载完成')
        print('正在下载音频')
        self.file_download(audio_url, title)
        print('下载完成')
        self.combine(title)

    def get_title(self, html):
        """
        获取视频标题
        :return : title
        """
        print('正在获取视频标题')
        request_counts = 0
        while True:
            try:
                title = etree.HTML(html)
                title = title.xpath('//div[@id="viewbox_report"]/h1/text()')[0]
                break
            except IndexError:
                request_counts += 1
                print(f'获取标题失败，正在帮您重新请求（请求次数：{request_counts}）')
                html = crawl(self.url)
        # 标题违规字符处理，防止文件名报错
        title = re.sub('[/\\\\:*;?"<>\\]|\\[] ', '', title)
        title = re.sub(' ', '', title)
        print('获取成功')
        print('您当前正在下载：', title)
        return title

    def get_quality(self):
        """
        获取用户输入的画质
        :return: 用户选择的画质序号
        """
        print(re.sub('[{}\',]', '', str(self.quality_dict)))
        while True:
            try:
                quality = int(input('请选择视频画质：'))
                if quality == 1 or quality == 2 or quality == 3 or quality == 4:
                    break
                else:
                    print('请输入正确的序号')
            except ValueError:
                print('请输入正确的序号')

        return quality

    @staticmethod
    def get_duration(html, quality):
        """
        用xpath从html中提取响应的视频的时长
        :param html: html
        :param quality: 用户选择的视频画质
        :return: None
        """
        pattern = r'\<script\>window\.__playinfo__=(.*?)\</script\>'
        result = re.findall(pattern, html)[0]
        temp = json.loads(result)
        accept_quality = temp['data']['accept_description'][quality]
        video_time = temp['data']['dash']['duration']
        print('当前视频清晰度为{}，视频时长为{}'.format(accept_quality, datetime.timedelta(seconds=video_time)))
        return None

    @staticmethod
    def get_video_and_audio_url(html, quality):
        """
        根据用户选择的画质用xpath从html中提取响应的视频和音频的地址
        :param html: html
        :param quality: 用户选择的视频画质
        :return: 视频和音频的地址
        """
        pattern = r'\<script\>window\.__playinfo__=(.*?)\</script\>'
        result = re.findall(pattern, html)[0]
        temp = json.loads(result)
        video_url = temp['data']['dash']['video'][quality * 2 - 2]['baseUrl']
        audio_url = temp['data']['dash']['audio'][0]['baseUrl']
        return video_url, audio_url

    def show_progress_bar(self):
        timing = time.time()
        chunk_size = 1024 * 1024
        file_size = self.file_size
        the_last_downloader_size = 0
        while True:
            time.sleep(0.5)
            interval_downloaded = self.downloaded_size - the_last_downloader_size
            the_last_downloader_size = self.downloaded_size
            if self.downloaded_size == self.file_size:
                show_percentage = '\033[1;32m' + 40 * '━'
                download_time = time.time() - timing
                average_speed = self.file_size / download_time / chunk_size
                if average_speed < 5.0:
                    show_average_speed = '\033[1;31m' + str(round(average_speed, 1))
                else:
                    show_average_speed = '\033[1;32m' + str(round(average_speed, 1))
                print('\r\t' + show_percentage,
                      str(round(self.downloaded_size / chunk_size, 1)) + '/' + str(round(file_size / chunk_size, 1)),
                      'MB', show_average_speed, 'MB/s', '\033[1;34m', 'eta', '0:00:00' + '\033[0m', flush=True)
                break
            else:
                percentage = int(self.downloaded_size / file_size * 40)  # 计算已下载的百分比
                show_percentage = '\033[1;35m' + percentage * '━' + '\033[0m' + (40 - percentage) * '━' + '\033[1;35m'
                show_downloader_size = str(round(self.downloaded_size / chunk_size, 1))
                show_file_size = str(round(file_size / chunk_size, 1))
                speed = interval_downloaded / chunk_size
                if speed < 5.0:
                    show_speed = '\033[1;31m' + str(round(speed, 1))
                else:
                    show_speed = '\033[1;32m' + str(round(speed, 1))

                try:
                    eta = round((file_size - self.downloaded_size) / chunk_size / speed)  # 计算预计剩余时间
                except ZeroDivisionError:
                    eta = 2000  # 如果当前下载速度为零则直接默认2000秒
                # 给显示的预计剩余时间加上颜色，如果预计剩余时间大于30分钟则显示红色，反之，显示蓝色
                if speed == 0.0 or eta > 1800:
                    show_eta = '\033[1;31m' + ' >30min'
                else:
                    show_eta = '\033[1;34m' + ' eta ' + str(datetime.timedelta(seconds=eta))
                    # 'r'每次重新从开始输出，end = ''是不换行
                print('\r\t' + show_percentage, show_downloader_size + '/' + show_file_size, 'MB', show_speed,
                      'MB/s', show_eta, flush=True, end='')
                sys.stdout.flush()  # 刷新缓冲区，防止显示的进度条闪烁
        return

    def get_file_information(self, file_url):
        """
        获取文件信息以及下载的视频流变量
        :param file_url:文件url
        :return: None
        """
        headers.update({'origin': 'https://www.bilibili.com',
                        'referer': self.url,
                        'Range': 'bytes=' + '0' + '-'})
        self.file_res = crawl(url=file_url, stream=True)  # 视频设置延迟
        self.file_size = int(self.file_res.headers['content-length'])  # 获取视频文件大小
        return

    def save_file(self):
        with open(self.file_path, 'ab') as f:
            for data in self.file_res.iter_content(chunk_size=1024):
                f.write(data)  # 每次只写入data大小
                self.downloaded_size = self.downloaded_size + len(data)
        return

    def file_download(self, file_url, title):
        """
        文件下载
        :param title: 视频标题
        :param file_url: 文件地址
        :return: None
        """
        # 确定好文件名
        if os.path.exists('%s_video.mp4' % (path + '/' + title)):
            self.file_path = '%s_audio.mp4' % (path + '/' + title)
        else:
            self.file_path = '%s_video.mp4' % (path + '/' + title)

        self.get_file_information(file_url)
        threading.Thread(target=self.save_file).start()
        threading.Thread(target=self.show_progress_bar()).start()
        self.downloaded_size = 0
        return

    @staticmethod
    def combine(title):
        """
        合成视频
        :param title: 视频标题
        :return: None
        """
        print('正在合成视频和音频')
        command = 'ffmpeg -i %s_video.mp4 -i %s_audio.mp4 -c copy %s.mp4 -y -loglevel quiet' % (
            path + '/' + title, path + '/' + title, path + '/' + title)
        subprocess.Popen(command, shell=True)
        while True:
            try:
                if os.path.exists('%s.mp4' % (path + '/' + title)):
                    os.remove('%s_video.mp4' % (path + '/' + title))
                    os.remove('%s_audio.mp4' % (path + '/' + title))
                    break
            except PermissionError:
                pass
        print('合成完毕')
        return


def run():
    global path

    announcement()
    url = get_url()
    path = get_path()
    Bilibili_Downloader(url)


if __name__ == "__main__":
    run()
