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
import time
import tkinter as tk
from tkinter import filedialog
from datetime import timedelta
from json import loads
from os import remove, path
from subprocess import Popen
# 需要的第三方库
from lxml import etree
from requests import Session
from requests.exceptions import RequestException

__version__ = 'v0.2.3'
__author__ = 'chaziming'


class Bilibili_Downloader:
    session = Session()
    headers = {
        "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.56',
        'Referer': 'https://www.bilibili.com',
        'Range': 'bytes=' + '0' + '-'

    }

    def __init__(self):
        self.url = None
        self.path = None
        self.html = None
        self.number = None
        self.title = None
        self.video_url = None
        self.audio_url = None
        self.run()

    @staticmethod
    def announcement():
        title = 'Bilibili Downloader' + ' '
        author = 'chaziming'
        version = 'v0.2.3'
        dividing_line = '-' * 40 + '\n'
        feature = '本程序特点：优点：1.拥有个性化进度条，让您对下载进度了如指掌\n' \
                  '缺点：1.不是gui程序\n'
        optimization = '优化：1.Bilibili Downloader全新升级，重写了代码，使代码更加具有逻辑性\n' \
                       '2.为代码添加了更多注释\n' \
                       '3.优化了底层逻辑，使运行更加顺畅\n'
        fix_bugs = '修复了在下载系列视频时出现的一些bug'
        spread = 'more see: https://github.com/chaziming/Video-Downloader\n'
        print('\033[1;34m' + dividing_line + title, version, 'by', author)
        print(feature + '公告：\n' + fix_bugs + optimization + spread + dividing_line + '\033[0m')
        return

    def get_url(self):
        """
        获取用户输入的哔哩哔哩网址
        :return: None
        """
        while True:
            url = input('请输入视频的网址：')
            if 'bilibili.com' not in url:
                print('请输入正确的哔哩哔哩的网址')
            else:
                url = re.findall('(.*?\\?)', url)[0]
                self.url = url
                break
        return

    def get_path(self):
        """
        获取用户输入视频保存地址
        :return: None
        """
        print('请在弹出的窗口中选择视频位置')
        time.sleep(1.5)
        root = tk.Tk()
        root.withdraw()
        folder_path = filedialog.askdirectory()
        print('您所选择的路径为：', folder_path)
        self.path = folder_path
        return

    def get_html(self):
        """
        获取网页源代码
        :return: None
        """
        while True:
            request_counts = 0
            try:
                response = self.session.get(url=self.url, headers=self.headers)
                if response.status_code == 200:
                    self.html = response.text
                    break
            except RequestException:
                request_counts += 1
                print(f'请求失败，正在帮您重新请求（请求次数：{request_counts}）')
            return

    def get_title(self):
        """
        获取视频标题
        :return : None
        """
        request_counts = 0
        while True:
            try:
                title = etree.HTML(self.html)
                title = title.xpath('//div[@id="viewbox_report"]/h1/text()')[0]
                break
            except IndexError:
                request_counts += 1
                print(f'获取标题失败，正在帮您重新请求（请求次数：{request_counts}）')
                self.get_html()
        # 标题违规字符处理，防止文件名报错
        title = re.sub('[/\\\\:*;?"<>\\]|\\[] ', '', title)
        title = re.sub(' ', '', title)
        print('您当前正在下载：', title)
        self.title = title
        return

    def get_number(self):
        """
        获取视频集数（针对系列视频）
        :return: None
        """
        pattern = r'\<script\>window\.__INITIAL_STATE__=(.*?)\</script\>'
        result = re.findall(pattern, self.html)[0]
        result = re.findall('"pages":(\\[.*?])', result)[0]
        temp = loads(result)
        self.number = len(temp)
        return

    def get_video_and_audio_url(self):
        """
        获取视频和音频的url
        :return: None
        """
        quality_dict = {
            '1': '高清 1080P',
            '2': '高清 720P60',
            '3': '清晰 480P',
            '4': '流畅 360P',
        }
        pattern = r'\<script\>window\.__playinfo__=(.*?)\</script\>'
        result = re.findall(pattern, self.html)[0]
        temp = loads(result)
        print(re.sub('[{}\',]', '', str(quality_dict)))
        quality = int(input('请选择视频画质：'))
        accept_quality = temp['data']['accept_description'][quality]
        video_time = temp['data']['dash']['duration']
        video_minute = video_time // 60
        video_second = video_time % 60
        print('当前视频清晰度为{}，视频时长为{}分{}秒'.format(accept_quality, video_minute, video_second))
        video_url = temp['data']['dash']['video'][quality * 2 - 2]['baseUrl']
        audio_url = temp['data']['dash']['audio'][0]['baseUrl']
        self.video_url = video_url
        self.audio_url = audio_url
        return

    def file_download(self):
        """
        下载视频和音频
        :return: None
        """
        chunk_size = 1024 * 1024  # 每次下载的大小，单位为字节,这里表示1MB
        video_res = self.session.get(url=self.video_url, stream=True, headers=self.headers)  # 视频设置延迟
        audio_res = self.session.get(url=self.audio_url, stream=True, headers=self.headers)  # 同上，音频设置延迟下载
        video_size = int(video_res.headers['content-length'])  # 获取视频文件大小
        audio_size = int(audio_res.headers['content-length'])  # 获取音频文件大小
        total_size = video_size + audio_size  # 视频和音频文件大小相加，单位为字节
        downloader_size = 0  # 已下载的文件大小
        print('开始下载')
        timing = time.time()  # 计时
        # 先下载视频再下载音频
        with open('%s_video.mp4' % (self.path + '/' + self.title), 'ab') as f:
            for data in video_res.iter_content(chunk_size=chunk_size):  # 每次只获取一个chunk_size大小，即1MB
                f.write(data)  # 每次只写入data大小
                interval_time = time.time() - timing  # 计算间隔时间
                timing = time.time()  # 重新计时
                downloader_size = len(data) + downloader_size  # 计算已下载的文件大小
                percentage = int(downloader_size / total_size * 40)  # 计算已下载的百分比
                show_percentage = '\033[1;35m' + percentage * '━' + '\033[0m' + (40 - percentage) * '━' + '\033[1;35m'
                show_downloader_size = str(round(downloader_size / chunk_size, 1))
                show_total_size = str(round(total_size / chunk_size, 1))
                try:
                    speed = 1 / interval_time
                except ZeroDivisionError:  # 防止除零错误
                    speed = '错误'
                # 给显示的速度加上颜色，如果速度小于5.0MB则显示红色，反之，显示绿色
                if speed < 5.0:
                    show_speed = '\033[1;31m' + str(round(speed, 1))
                else:
                    show_speed = '\033[1;32m' + str(round(speed, 1))
                eta = round((total_size - downloader_size) / chunk_size / speed)  # 计算预计剩余时间
                # 给显示的预计剩余时间加上颜色，如果预计剩余时间大于30分钟则显示红色，反之，显示蓝色
                if speed == 0.0 or eta > 1800:
                    show_eta = '\033[1;31m' + ' >30min'
                else:
                    show_eta = '\033[1;34m' + ' eta ' + str(timedelta(seconds=eta))
                    # 'r'每次重新从开始输出，end = ''是不换行
                print('\r\t' + show_percentage, show_downloader_size + '/' + show_total_size, 'MB', show_speed,
                      'MB/s', show_eta, flush=True, end='')
                sys.stdout.flush()  # 刷新缓冲区，防止显示的进度条闪烁

        # 开始下载音频，代码和下载视频的代码基本一样，故不再多做注释
        with open('%s_audio.mp4' % (self.path + '/' + self.title), 'ab') as f:
            for data in audio_res.iter_content(chunk_size=chunk_size):
                f.write(data)
                interval_time = time.time() - timing
                timing = time.time()
                downloader_size = len(data) + downloader_size
                percentage = int(downloader_size / total_size * 40)
                show_percentage = '\033[1;35m' + percentage * '━' + '\033[0m' + (40 - percentage) * '━' + '\033[1;35m'
                show_downloader_size = str(round(downloader_size / chunk_size, 1))
                show_total_size = str(round(total_size / chunk_size, 1))
                try:
                    speed = 1 / interval_time
                except ZeroDivisionError:
                    speed = '错误'
                if speed < 5.0:
                    show_speed = '\033[1;31m' + str(round(speed, 1))
                else:
                    show_speed = '\033[1;32m' + str(round(speed, 1))
                eta = round((total_size - downloader_size) / chunk_size / speed)
                if speed == 0.0 or eta > 1800:
                    show_eta = '\033[1;31m' + ' >30min'
                else:
                    show_eta = '\033[1;34m' + ' eta ' + str(timedelta(seconds=eta))
                print('\r\t' + show_percentage, show_downloader_size + '/' + show_total_size, 'MB', show_speed,
                      'MB/s', show_eta, flush=True, end='')
                sys.stdout.flush()

        # 最后下载完成进度条要显示绿色，故重新显示一遍
        if speed < 5.0:
            color = '\033[1;31m'
        else:
            color = '\033[1;32m'
        print('\r\t''\033[1;32m' + 40 * '━' + '\033[1;32m',
              str(round(downloader_size / chunk_size, 1)) + '/' + str(round(total_size / chunk_size, 1)), "MB" + color,
              str(round(speed, 1)), 'MB/s' + '\033[1;34m', 'eta', '0:00:00' + '\033[0m', flush=True)
        return

    def combine(self):
        """
        合成视频
        :return: None
        """
        print('processing')
        command = 'ffmpeg -i %s_video.mp4 -i %s_audio.mp4 -c copy %s.mp4 -y -loglevel quiet' % (
            self.path + '/' + self.title, self.path + '/' + self.title, self.path + '/' + self.title)
        Popen(command, shell=True)
        while True:
            try:
                if path.exists('%s.mp4' % (self.path + '/' + self.title)):
                    remove('%s_video.mp4' % (self.path + '/' + self.title))
                    remove('%s_audio.mp4' % (self.path + '/' + self.title))
                    break
            except PermissionError:
                pass
        return

    def run(self):
        """
        运行程序
        :return: None
        """
        self.announcement()
        self.get_url()
        self.get_html()
        self.get_path()
        self.get_number()
        if self.number > 1:
            print(f'检测到您正在下载系列视频，且该系列视频共有{self.number}个')
            p = input('请输入您要爬取的集数（目前只支持输入一个，如果要爬取全部请输入0）：')
            if p == '0':
                for i in range(self.number):
                    self.url += 'p=' + str(i + 1)
                    self.get_html()
                    self.get_title()
                    self.title += str(i + 1)
                    self.get_video_and_audio_url()
                    self.file_download()
                    self.combine()
                print('视频下载成功，请查收')
                input('按回车以结束程序')
                quit()
            else:
                self.url += 'p=' + p
                self.get_html()
                self.get_title()
                self.get_video_and_audio_url()
                self.file_download()
                self.combine()
                print('视频下载成功，请查收')
                input('按回车以结束程序')
                quit()
        else:
            self.get_title()
            self.get_video_and_audio_url()
            self.file_download()
            self.combine()
            print('视频下载成功，请查收')
            input('按回车以结束程序')
            quit()
        return


if __name__ == "__main__":
    bilibili_downloader = Bilibili_Downloader()
