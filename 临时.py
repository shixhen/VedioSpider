# -*- coding: utf-8 -*-
# =======================================================
# Bilibili Downloader
# Copyright (c) 2022 shihen-root
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
import subprocess
import tkinter as tk
from tkinter import filedialog
# 需要的第三方库：requests, lxml
import requests
from lxml import etree

__version__ = 'v0.0.2'
__author__ = 'shihen'

# 需要的全局变量及其类型

path: str  # 文件保存路径


def announcement():
    title = 'Universal Downloader'
    author = __author__
    version = __version__
    dividing_line = '-' * 40 + '\n'
    feature = """
     ━━━━━━━━   |         |   *       |         |   ━━━━━━━━    ━━━━━━━━━
    |           |         |   |       |         |  |        |  |         |
    |           |         |   |       |         |  |        |  |         |
     ━━━━━━━━   |━━━━━━━━ |   |       |━━━━━━━━ |   ━━━━━━━━   |         |
             |  |         |   |       |         |  |           |         |
             |  |         |   |       |         |  |           |         |
     ━━━━━━━━                                       ━━━━━━━━\n
    """
    fix_bugs = '修复了在下载系列视频时出现的一些bug\n'
    spread = 'more see: https://github.com/chaziming/Video-Downloader\n抖音、bilibili关注拾痕！！！\n'
    print('\033[1;34m' + dividing_line + title, version, 'by', author)
    print(feature + '\r' + '公告：\n' + fix_bugs + spread + dividing_line + '\033[0m')
    return


session = requests.Session()
headers = {
    "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62'
}


def show_log():
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    return


def get_url():
    """
    获取用户输入的网址并判断平台
    :return: url
    """
    while True:
        url = input('请输入视频的地址（目前只支持bilibili、m3u8）：')
        if 'bilibili.com' in url:
            try:
                url = re.findall('(.*?\\?)', url)[0]
                print('\033[1;34m' + '检测到您输入的是哔哩哔哩的网址')
                break
            except IndexError:
                print('\033[1;31m' + '请您输入一个正确的哔哩哔哩网址')
            if 'BV' not in url:
                print('\033[1;31m' + '请您输入一个正确的哔哩哔哩网址')
        elif 'm3u8.index' in url:
            print('\033[1;34m' + '检测到您输入的是m3u8地址')
            break
        else:
            print('\033[1;31m' + '您输入的网址有误，请输入一个正确的bilibili、m3u8地址')
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
            print(requests.exceptions.RequestException.errno)
            request_counts += 1
            print(f'请求失败，正在帮您重新请求（请求次数：{request_counts}）')
            time.sleep(3)
    return response


class Bilibili_Downloader:
    """
    bilibili下载器的类
    """

    @staticmethod
    def run(url):
        """
        bilibili 下载器运行的总函数，步骤如下：
        1.先解析用户输入的url，获取标题
        2.获取视频支持的清晰度，让用户选择一个清晰度
        3.根据用户选择的清晰度来获取对应的视频url，以及视频的时长等信息
        4.分别下载视频和音频
        5.合成
        :param url: url
        :return: None
        """
        temp, title = crawl(url).text  # 获取html
        title = Bilibili_Downloader.get_title(html, url)  # 获取标题
        quality = Bilibili_Downloader.get_quality(html, url)  # 获取用户选择的清晰度
        Bilibili_Downloader.get_duration(html)  # 获取视频时长
        video_url, audio_url = Bilibili_Downloader.get_video_and_audio_url(html, quality)  # 获取视频和音频的url
        Bilibili_Downloader.download(title, url, video_url)  # 下载视频
        Bilibili_Downloader.download(title, url, audio_url)  # 下载音频
        Bilibili_Downloader.combine(title)  # 合并
        return

    @staticmethod
    def get_temp_and_title(url):
        """
        获取当前页面的temp字典
        :param url:url
        :return: temp字典
        """
        html = crawl(url).text
        pattern = r'\<script\>window\.__playinfo__=(.*?)\</script\>'
        result = re.findall(pattern, html)[0]
        temp = json.loads(result)
        title = Bilibili_Downloader._get_title(html, url)
        return temp, title

    @staticmethod
    def _get_title(html, url):
        print('正在获取视频标题')
        request_counts = 0
        while True:
            try:
                title = etree.HTML(html)
                title = title.xpath('//div[@id="viewbox_report"]/h1/text()')[0]
                break
            except IndexError:
                request_counts += 1
                print(f'获取标题失败，正在帮您重新请求(请求次数：{request_counts})')
                html = crawl(url)
        # 标题违规字符处理，防止文件名报错
        title = re.sub('[\\\\:*;?/"<>\\]|\\[] ', '', title)
        title = re.sub(' ', '', title)
        print('获取成功')
        print('您当前正在下载：', title)
        return title

    @staticmethod
    def get_quality(temp, url):
        """
        获取用户输入的画质
        :return: 用户选择的画质序号
        """
        contrast_dict = {
            120: '4K',
            116: '高清 1080P60',
            80: '高清 1080P',
            64: '高清 720P',
            32: '清晰 480P',
            16: '清晰 360P'
        }
        choose_dict = {}
        accept_quality_dict = Bilibili_Downloader._get_accept_quality_dict(temp)
        Bilibili_Downloader._get_available_quality_list(temp)
        if len(accept_quality_dict) > 2:
            print(
                '现在bilibili只有登录才能下载1080P的视频了，\n所以想下载720P及以上清晰度的请填写你的账号cookie，'
                '或者VIP密码，\n如果你不想下载720P'
                '及以上清晰度的视频，请直接跳过（目前不支持大会员）')
            cookie = input(
                '请输入你的账号cookie，或者VIP密码，\n如果你不想下载720P及以上清晰度的视频，\n请直接跳过'
                '（输入自己的cookie的时候别再首末添加任何符号，我们不会收集您的cookie，请放心输入）：')
            if cookie == '':
                print('您选择了不填cookie，这将导致您只能选择480P和360P清晰的的视频')
                while True:
                    try:
                        quality = int(input('请选择视频画质：'))
                        if quality == '1' or quality == '2':
                            if quality == '1':
                                quality = '清晰 480P'
                            if quality == '2':
                                quality = '流畅 360P'
                                return quality
                            break
                        else:
                            print('请输入正确的，在范围内的序号')
                    except ValueError:
                        print('请输入正确的，在范围内的序号')
            else:
                if cookie == '666':
                    headers.update({'cookie': "_uuid=1057210A5E-4958-F1DB-572E-8D310CB2432DE84489infoc; "
                                              "buvid3=DFA26D9B-518A-4145-8758-888B72993D8F148799infoc; "
                                              "b_nut=1636794084; "
                                              "rpdid=|( "
                                              "J~RYk|mYul0J'uYJY)Ym)Yk; video_page_version=v_old_home; "
                                              "i-wanna-go-back=-1; CURRENT_BLACKGAP=0; "
                                              "LIVE_BUVID=AUTO1016452613863719; nostalgia_conf=-1; "
                                              "buvid_fp_plain=undefined; blackside_state=0; "
                                              "b_ut=5; fingerprint3=5a97a8f930b1074ac7357c0ee89cb3fa; hit-dyn-v2=1; "
                                              "buvid4=21E8E608-FE86-570B-EC52-C0CA318A2DEF65231-022012119-TxfVXHJp3qfb"
                                              "%2BSCCWd0yMA%3D%3D; "
                                              "CURRENT_QUALITY=80; PVID=1; DedeUserID=1068621305; "
                                              "DedeUserID__ckMd5=247502fb66fdaa13; "
                                              "is-2022-channel=1; fingerprint=7e7ee53a3a5971e69bc9b95234872e2a; "
                                              "b_nut=100; "
                                              "buvid_fp=7e7ee53a3a5971e69bc9b95234872e2a; "
                                              "bp_video_offset_1068621305=725683678873649200; "
                                              "SESSDATA=11bfaff5%2C1683359831%2Cc11e4%2Ab1; "
                                              "bili_jct=a39ec65fbad8a559b461606a7232dfcd; sid=7k6079j9; "
                                              "CURRENT_FNVAL=4048; b_lsid=55D384AD_18455036E9D; theme_style=light "
                                    })
                    print('您是VIP，请选择视频拥有的除1080P高码率及以上的任何清晰度')
                    # 重新请求
                    html = crawl(url).text  #
                    result = re.findall(pattern, html)[0]
                    temp = json.loads(result)

                    quality_dict_2 = Bilibili_Downloader._get_accept_quality_dict(temp)
                    if quality_dict_1 == quality_dict_2:
                        print('抱歉,该cookie已失效,正在让您重新选择')
                        while True:
                            try:
                                choose = int(input('是否继续,是请按1,想重新选择请按2'))
                                if choose == '2':
                                    video_url, audio_url = Bilibili_Downloader.get_quality(html, url)
                                    return video_url, audio_url
                                if choose == '1':
                                    break
                                else:
                                    print('请输入正确的，在范围内的序号')
                            except ValueError:
                                print('请输入正确的，在范围内的序号')

                    print(re.sub('[{}\',]', '', str(quality_dict_2)))
                    while True:
                        try:
                            quality = int(input('请选择视频画质：'))
                            if quality <= len(quality_dict_2):
                                video_url = temp['data']['dash']['video'][quality-1]['baseUrl']
                                audio_url = temp['data']['dash']['audio'][0]['baseUrl']
                                return video_url, audio_url
                            else:
                                print('请输入正确的，在范围内的序号')
                        except ValueError:
                            print('请输入正确的，在范围内的序号')

                else:
                    print('猜测您输入的是您自己的cookie，请确保您输入的cookie是准确的，否则将无法下载720P及以上清晰度的视频')
                    headers.update({'cookie': cookie})
                    # 重新请求
                    html = crawl(url).text  #
                    result = re.findall(pattern, html)[0]
                    temp = json.loads(result)

                    quality_dict_2 = Bilibili_Downloader._get_accept_quality_dict(temp)
                    if quality_dict_1 == quality_dict_2:
                        print('检测到您输入的cookie无效')
                        while True:
                            try:
                                choose = int(input('是否继续,是请按1,想重新选择请按二'))
                                if choose == '2':
                                    video_url, audio_url = Bilibili_Downloader.get_quality(html, url)
                                    return video_url, audio_url
                                if choose == '1':
                                    break
                                else:
                                    print('请输入正确的，在范围内的序号')
                            except ValueError:
                                print('请输入正确的，在范围内的序号')

                    print(re.sub('[{}\',]', '', str(quality_dict_2)))
                    while True:
                        try:
                            quality = int(input('请选择视频画质：'))
                            if quality <= len(quality_dict_2):
                                video_url = temp['data']['dash']['video'][quality - 1]['baseUrl']
                                audio_url = temp['data']['dash']['audio'][0]['baseUrl']
                                return video_url, audio_url

                            else:
                                print('请输入正确的，在范围内的序号')
                        except ValueError:
                            print('请输入正确的，在范围内的序号')
        else:
            if len(quality_dict_1) == 2:
                print('检测到视频只有以下两个清晰度')
                print('1: 清晰 480P 2: 流畅 360P')
                while True:
                    try:
                        quality = int(input('请选择视频画质：'))
                        if quality == '1' or quality == '2':
                            if quality == '1':
                                quality = '清晰 480P'
                            if quality == '2':
                                quality = '流畅 360P'
                            break
                        else:
                            print('请输入正确的，在范围内的序号')
                    except ValueError:
                        print('请输入正确的，在范围内的序号')
            if len(quality_dict_1) == 1:
                print('检测到视频只有一个清晰度，将为您默认下载此清晰度的视频')
                quality = '流畅 360P'
            return quality

    @staticmethod
    def _get_accept_quality_dict(temp):
        quality_dict = {}
        quality = temp['data']['accept_description']
        i = 0
        for each in quality:
            i += 1
            quality_dict[i] = each
        return quality_dict

    @staticmethod
    def _get_choose_dict(available_quality_list):
        """
        获取选择清晰度的字典
        :param available_quality_list: 当前能够选择的清晰度
        :return: 选择的字典
        """
        contrast_dict = {
            120: '4K',
            116: '高清 1080P60',
            80: '高清 1080P',
            64: '高清 720P',
            32: '清晰 480P',
            16: '清晰 360P'
        }
        choose_dict ={}
        i = 0
        for each in available_quality_list:
            i += 1
            choose_dict[i] = contrast_dict[each]
        return choose_dict

    @staticmethod
    def _get_choose(choose_dict):
        """
        获取用户选择的视频清晰度
        :param choose_dict: 选择的字典
        :return: 用户选择的清晰度的id
        """
        contrast_dict = {
            '4K': 120,
            '高清 1080P60': 116,
            '高清 1080P': 80,
            '高清 720P': 64,
            '清晰 480P': 32,
            '清晰 360P': 16
        }
        print(re.sub('[{}\',]', '', str(choose_dict)))
        while True:
            try:
                quality = int(input('请选择视频画质：'))
                if quality <= len(choose_dict):
                    choose_id = choose_dict[quality]
                    break
                else:
                    print('请输入正确的，在范围内的序号')
            except ValueError:
                print('请输入正确的，在范围内的序号')
        return choose_id

    @staticmethod
    def _get_available_quality_list(temp):
        """
        获取当前能够下载的视频清晰度
        :param temp: temp
        :return: 当前能够下载的视频清晰度
        """
        all_quality_list = [120, 116, 80, 64, 32, 16]
        available_quality_list = []
        videos = temp['data']['dash']['video']
        for each in videos:
            each_id = each['id']
            if each_id in all_quality_list:
                available_quality_list.append(each_id)
        return available_quality_list

    @staticmethod
    def get_duration(temp):
        """
        用xpath从html中提取响应的视频的时长
        :param temp: temp
        :return: None
        """
        video_time = temp['data']['dash']['duration']
        print(f'视频时长为{datetime.timedelta(seconds=video_time)}')
        return None

    @staticmethod
    def get_video_and_audio_url(html, quality):
        """
        根据用户选择的画质用xpath从html中提取响应的视频和音频的地址
        :param html: html
        :param quality: 用户选择的视频画质
        :return: 视频和音频的地址
        """
        video_url_list = {
            '高清 1080P60': '30116.m4s',
            '高清 1080P': '30080.m4s',
            '高清 720P': '30064.m4s',
            '清晰 480P': '30032.m4s',
            '清晰 360P': '30016.m4s'
        }
        pattern = r'\<script\>window\.__playinfo__=(.*?)\</script\>'
        result = re.findall(pattern, html)[0]
        temp = json.loads(result)
        audio_url = temp['data']['dash']['audio'][0]['baseUrl']
        for i in range(len(temp['data']['dash']['video'])):
            print(i)
            video_url = temp['data']['dash']['video'][i]['baseUrl']
            print(video_url)
            if video_url_list[quality] in video_url:
                return video_url, audio_url
        return

    @staticmethod
    def show_progress_bar(file_size, downloaded_size, interval_time, interval_downloaded):
        chunk_size = 1024 * 1024

        percentage = int(downloaded_size / file_size * 40)  # 计算已下载的百分比
        # 显示的进度条
        show_percentage = '\033[1;35m' + percentage * '━' + '\033[0m' + (40 - percentage) * '━' + '\033[1;35m'
        show_file_size = str(round(file_size / chunk_size, 1))  # 显示的文件大小
        show_downloader_size = str(round(downloaded_size / chunk_size, 1))  # 显示的已下载文件大小
        # 计算速度
        speed = interval_downloaded / interval_time / chunk_size
        if speed < 5.0:
            show_speed = '\033[1;31m' + str(round(speed, 1))
        else:
            show_speed = '\033[1;32m' + str(round(speed, 1))
        # 计算预计剩余时间
        try:
            eta = round((file_size - downloaded_size) / chunk_size / speed)
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

    @staticmethod
    def show_end_bar(file_size, downloaded_size, total_time):
        chunk_size = 1024 * 1024
        show_percentage = '\033[1;32m' + 40 * '━'  # 显示的进度条
        average_speed = file_size / total_time / chunk_size  # 平均速度
        # 显示的平均速度
        if average_speed < 5.0:
            show_average_speed = '\033[1;31m' + str(round(average_speed, 1))
        else:
            show_average_speed = '\033[1;32m' + str(round(average_speed, 1))
        print('\r\t' + show_percentage,
              str(round(downloaded_size / chunk_size, 1)) + '/' + str(round(file_size / chunk_size, 1)),
              'MB', show_average_speed, 'MB/s', '\033[1;34m', 'eta', '0:00:00', '下载总用时：',
              str(round(total_time, 1)) + 's' + '\033[0m',
              flush=True)

    @staticmethod
    def _get_file_information(url, file_url):
        """
        获取文件信息以及下载的视频流
        :param url:url
        :param file_url:文件url
        :return: None
        """
        headers.update({'origin': 'https://www.bilibili.com',
                        'referer': url,
                        'Range': 'bytes=' + '0' + '-'})
        file_res = crawl(url=file_url, stream=True)  # 视频设置延迟
        file_size = int(file_res.headers['content-length'])  # 获取视频文件大小
        return file_res, file_size

    @staticmethod
    def download(title, url, file_url):
        file_res, file_size = Bilibili_Downloader._get_file_information(url, file_url)
        downloaded_size = 0  # 已下载的文件大小
        the_last_downloader_size = 0
        if os.path.exists('%s_video.mp4' % (path + '/' + title)):
            file_path = '%s_audio.mp4' % (path + '/' + title)
        else:
            file_path = '%s_video.mp4' % (path + '/' + title)
        with open(file_path, 'ab') as f:
            total_timing = time.time()
            timing = total_timing
            for data in file_res.iter_content(chunk_size=1024):
                f.write(data)  # 每次只写入data大小
                downloaded_size += len(data)
                if downloaded_size == file_size:
                    Bilibili_Downloader.show_end_bar(file_size, downloaded_size, time.time() - total_timing)
                if time.time() - timing > 0.5:
                    interval_downloaded = downloaded_size - the_last_downloader_size
                    Bilibili_Downloader.show_progress_bar(file_size, downloaded_size, time.time() - timing,
                                                          interval_downloaded)
                    timing = time.time()
                    the_last_downloader_size = downloaded_size
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
    url = 'https://www.bilibili.com/video/BV1HG4y1V7Vk/?spm_id_from=333.1007.tianma.1-1-1.click&vd_source=c0cf2580a585c8420a1dea832f177ba6'
    path = 'C:/Users/Administrator/Desktop'
    if 'bilibili.com' in url:
        Bilibili_Downloader.run(url)
    elif 'm3u8.index' in url:
        print('正在开发中，请您使用m3u8_Downloader')


# https://www.bilibili.com/video/BV1Ae4y1n7pF/?spm_id_from=333.999.0.0&vd_source=c0cf2580a585c8420a1dea832f177ba6
if __name__ == "__main__":
    run()
