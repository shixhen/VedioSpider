# -*- coding:utf-8 -*-
# =======================================================
# Bilibili Downloader
# Copyright (c) 2022 chaziming
# All rights reserved.
#
# 本开源程序遵循 Apache License 2.0 协议
# =======================================================

"""
说明：一.需要ffmpeg并设置环境变量以完成视频合成
二.本程序优点:1.只需输入哔哩哔哩网址就可爬取视频,最高支持高清1080P画质
2.个性化进度条展示
缺点:1.不是gui编程
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

# 需要的第三方库：requests, lxml
import requests
from lxml import etree

__version__ = 'v0.2.6'
__author__ = 'shihen'


def announcement():
    """
    公告函数
    """
    title = 'Bilibili Downloader' + ' '
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
    fix_bugs = '更新了下载720P及以上视频的下载体验,加了更多的注释\n'
    spread = 'more see: https://github.com/shihen-root/Video-Downloader\n抖音、bilibili关注拾痕！！！\n'
    print('\033[1;34m' + dividing_line + title, version, 'by', author)
    print(feature + '\r' + '公告：\n' + fix_bugs +
          spread + dividing_line + '\033[0m')


# 需要的全局变量及其类型

session = requests.Session()
headers = {
    "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62'
}
VIP_COOKIE = 'buvid3=DFA26D9B-518A-4145-8758-888B72993D8F148799infoc; ' \
             'i-wanna-go-back=-1; ' \
             'CURRENT_BLACKGAP=0; ' \
             'LIVE_BUVID=AUTO1016452613863719; ' \
             'nostalgia_conf=-1; buvid_fp_plain=undefined; ' \
             'blackside_state=0; ' \
             'b_ut=5; fingerprint3=5a97a8f930b1074ac7357c0ee89cb3fa; ' \
             'hit-dyn-v2=1; ' \
             'buvid4=21E8E608-FE86-570B-EC52-C0CA318A2DEF65231-022012119-' \
             'TxfVXHJp3qfb+SCCWd0yMA==; ' \
             'CURRENT_QUALITY=80; DedeUserID=1068621305; ' \
             'DedeUserID__ckMd5=247502fb66fdaa13; ' \
             'is-2022-channel=1; ' \
             'b_nut=100; _uuid=36325A87-B114-34A10-EA710-95110D496F54533599infoc; ' \
             'rpdid=0zbfAHVZbH|AfUglCw0|zmE|3w1OZ9zY; ' \
             'hit-new-style-dyn=0; ' \
             'fingerprint=78208089161326e760f875fff21b8084; ' \
             'buvid_fp=78208089161326e760f875fff21b8084; ' \
             'CURRENT_FNVAL=4048; bsource=search_bing; ' \
             'SESSDATA=b930b292,1688186738,9bd88*11; ' \
             'bili_jct=1f53edfff034a1ccb4d52918ad957a54; ' \
             'sid=6in3dpol; innersign=1; ' \
             'bp_video_offset_1068621305=745730705040867500; ' \
             'PVID=2; b_lsid=2C910A10F8_185712549DD '


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
            print('\033[1;31m' + '您输入的网址有误,请输入一个正确的bilibili网址')
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
        # noinspection PyBroadException
        try:
            response = session.get(
                url=url, headers=headers, stream=stream, timeout=5)
            if response.status_code == 200 or response.status_code == 206:
                break
        except requests.exceptions.RequestException:
            request_counts += 1
            print(f'请求失败，正在帮您重新请求(请求次数：{request_counts})')
            time.sleep(1)
    return response


class BilibiliDownloader:
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
        temp, title = crawl(url).text  # 获取temp和标题
        BilibiliDownloader.get_duration(temp)  # 获取视频时长
        video_url, audio_url = BilibiliDownloader.get_video_and_audio_url(temp, url)  # 获取视频和音频的url
        path = get_path()
        BilibiliDownloader.download(title, url, video_url, path)  # 下载视频
        BilibiliDownloader.download(title, url, audio_url, path)  # 下载音频
        BilibiliDownloader.combine(title, path)  # 合并
        return

    @staticmethod
    def get_temp_and_title(url):
        """
        获取当前页面的temp字典
        :param url:url
        :return: temp字典和标题
        """
        html = crawl(url).text
        pattern = r'\<script\>window\.__playinfo__=(.*?)\</script\>'
        result = re.findall(pattern, html)[0]
        temp = json.loads(result)
        title = BilibiliDownloader._get_title(html, url)
        return temp, title

    @staticmethod
    def get_duration(temp):
        """
        从temp中获取视频时长
        :param temp: temp
        :return: None
        """
        video_time = temp['data']['dash']['duration']
        print(f'视频时长为{datetime.timedelta(seconds=video_time)}')

    @staticmethod
    def get_video_and_audio_url(temp, url):
        """
        :param temp: temp
        :param url: 用户最初输入的url，在这里运用的目的是为了获取适当的清晰度而重新请求。
        :return:
        """
        # 因为音频文件的url最好获取，所以先获取音频文件的url
        audio_url = temp['data']['dash']['audio'][0]['base_url']

        # 开始获取视频的url，因为要根据用户选择的url来获取所以有点困难，另外要获取1080P等画质，需要输入cookie，这里有点复杂，所以接下来的注释会有点多。
        # 1.先获取视频所拥有的所有清晰度
        accept_quality_list = temp['data']['accept_description']
        # 2.再根据根据视频拥有的所有的清晰度判断是否要用户输入cookie
        # 如果视频拥有720P及以上画质，则要供用户选择是否要输入cookie以下载720P以及上画质的视频
        # 所以判断依据是视频是否拥有720P的画质
        if '高清 720P' in accept_quality_list:
            # 3.询问让用户选择填cookie
            # 这里是视频拥有720P及以上画质的情况
            # 这时告知用户，再询问用户是否要输入cookie以下载720P以及上画质的视频
            # 因为用户输入的cookie可能有误，所以要循环，直到用户的操作足以获得视频的url
            while True:
                print(
                    '现在bilibili只有登录才能下载1080P的视频了，\n所以想下载720P及以上清晰度的请填写你的账号cookie，'
                    '或者VIP密码，\n如果你不想下载720P'
                    '及以上清晰度的视频，请直接跳过（目前不支持大会员）')
                cookie = input(
                    '请输入你的账号cookie，或者VIP密码，\n如果你不想下载720P及以上清晰度的视频，\n请直接跳过'
                    '（输入自己的cookie的时候别再首末添加任何符号，我们不会收集您的cookie，请放心输入）：')
                # 4.判断用户有没有填cookie
                # 5.再根据用户的选择做相应的处理
                if cookie == '':
                    # 这里是用户没填cookie的情况
                    # 调用函数获取视频url
                    video_url = BilibiliDownloader._get_video_url(temp)
                    # 返回视频和音频的url
                    return video_url, audio_url
                else:
                    # 这是用户填了cookie的情况，此时又有两种情况，一是用户使用了VIP密钥，二是用户填的是自己的cookie
                    if cookie == '666':
                        # 这是用户填了VIP密钥的情况
                        print('您是VIP，请选择视频拥有的除1080P高码率及以上的任何清晰度')
                        # 为用户加入VIP专属cookie
                        headers.update({'cookie': VIP_COOKIE})
                        # 然后再次请求，获取新的temp, 这里弃用了title，因为已经获取过了
                        html = crawl(url).text
                        pattern = r'\<script\>window\.__playinfo__=(.*?)\</script\>'
                        result = re.findall(pattern, html)[0]
                        temp = json.loads(result)
                        # （1）先获取重新请求能够选择的视频清晰度列表
                        available_quality_list = BilibiliDownloader._get_available_quality_list(
                            temp)
                        # (2)再判断是否含有720P及以上画质
                        if 64 in available_quality_list:
                            # (3)如果有，则开始获取视频对应的url
                            # 调用函数获取视频url
                            video_url = BilibiliDownloader._get_video_url(temp)
                            # 返回视频和音频的url
                            return video_url, audio_url
                        else:
                            # (3)如果没有，则做以下处理
                            # 这是没有720P及以上画质的情况，这可能是因为cookie是失效了。
                            # 先给用户道歉
                            print('\033[1;31m' + '抱歉,该cookie已失效,正在让您重新选择' + '\033[0m')
                            # 再让用户重新选择
                            # 这里直接再次循环
                    else:
                        # 这里是用户填了自己的cookie的情况
                        print('猜测您输入的是您自己的cookie，请确保您输入的cookie是准确的，否则将无法下载720P及以上清晰度的视频')
                        # 先根据用户填的cookie重新请求
                        headers.update({'cookie': cookie})
                        # 然后再次请求，获取新的temp, 这里弃用了title，因为已经获取过了
                        html = crawl(url).text
                        pattern = r'\<script\>window\.__playinfo__=(.*?)\</script\>'
                        result = re.findall(pattern, html)[0]
                        temp = json.loads(result)
                        # (1)先获取重新请求能够选择的视频清晰度列表
                        available_quality_list = BilibiliDownloader._get_available_quality_list(
                            temp)
                        # (2)再判断是否含有720P及以上画质
                        if 64 in available_quality_list:
                            # 3.如果有，则开始获取视频对应的url
                            # 调用函数获取视频url
                            video_url = BilibiliDownloader._get_video_url(temp)
                            # 返回视频和音频的url
                            return video_url, audio_url
                        else:
                            # (3)如果没有，则做以下处理
                            # 这是没有720P及以上画质的情况，这可能是因为用户所输入的cookie是无效的。
                            # 先向用户说明原因
                            print('\033[1;31m' + '抱歉,该cookie已失效,正在让您重新选择' + '\033[0m')
                            # 再让用户选择是否要重新输入cookie
                            print('检测到您输入的cookie无效')
                            while True:
                                try:
                                    choose = input('想重新选择请按1,想直接开始下载的请按2')
                                    if choose == '1' or choose == '2':
                                        break
                                    else:
                                        print('请输入正确的，在范围内的序号')
                                except ValueError:
                                    print('请输入正确的，在范围内的序号')
                            # 然后再根据用户的选择做出相应的处理
                            if choose == '1':
                                # 这里是用户想重新选择的情况
                                print('您选择了，重新选择，正在让您重新选择')
                                # 这里直接再次循环
                            if choose == '2':
                                # 这里是用户想直接开始下载的情况
                                # 调用函数获取视频url
                                video_url = BilibiliDownloader._get_video_url(temp)
                                # 返回视频和音频的url
                                return video_url, audio_url

        else:
            # 3.如果视频没有720P及以上清晰度的视频，程序就会运行到这，直接获取视频的url
            # 调用函数获取视频url
            video_url = BilibiliDownloader._get_video_url(temp)
            # 返回视频和音频的url
            return video_url, audio_url

    @staticmethod
    def show_progress_bar(file_size, downloaded_size, interval_time, interval_downloaded):
        """
        进度条显示
        :param file_size: 文件大小
        :param downloaded_size: 已下载的大小
        :param interval_time: 中间间隔时间
        :param interval_downloaded: 中间下载的大下
        :return: None
        """
        chunk_size = 1024 * 1024

        percentage = int(downloaded_size / file_size * 40)  # 计算已下载的百分比
        # 显示的进度条
        show_percentage = '\033[1;35m' + percentage * '━' + '\033[0m' + (
                40 - percentage) * '━' + '\033[1;35m '
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
        print('\r\t' + show_percentage, show_downloader_size + '/' + show_file_size, 'MB',
              show_speed,
              'MB/s', show_eta, flush=True, end='')
        sys.stdout.flush()  # 刷新缓冲区，防止显示的进度条闪烁

    @staticmethod
    def show_end_bar(file_size, downloaded_size, total_time):
        """
        下载结束的进度条显示
        :param file_size: 文件大小
        :param downloaded_size: 已下载大小
        :param total_time: 下载总用时
        :return: None
        """
        chunk_size = 1024 * 1024
        show_percentage = '\033[1;32m' + 40 * '━'  # 显示的进度条
        average_speed = file_size / total_time / chunk_size  # 平均速度
        # 显示的平均速度
        if average_speed < 5.0:
            show_average_speed = '\033[1;31m' + str(round(average_speed, 1))
        else:
            show_average_speed = '\033[1;32m' + str(round(average_speed, 1))
        print('\r\t' + show_percentage,
              str(round(downloaded_size / chunk_size, 1)) + '/' + str(
                  round(file_size / chunk_size, 1)),
              'MB', show_average_speed, 'MB/s', '\033[1;34m', 'eta', '0:00:00', '下载总用时：',
              str(round(total_time, 1)) + 's' + '\033[0m',
              flush=True)

    @staticmethod
    def download(title, url, file_url, path):
        """
        下载方法
        :param title: 视频标题
        :param url: url
        :param file_url: 文件的url
        :param path: path
        :return: None
        """
        file_res, file_size = BilibiliDownloader._get_file_information(url, file_url)
        downloaded_size = 0  # 已下载的文件大小
        the_last_downloader_size = 0
        if os.path.exists(f'{path}/{title}_video.mp4'):
            file_path = f'{path}/{title}_audio.mp4'
        else:
            file_path = f'{path}/{title}_video.mp4'
        with open(file_path, 'ab') as file:
            total_timing = time.time()
            timing = total_timing
            for data in file_res.iter_content(chunk_size=1024):
                file.write(data)  # 每次只写入data大小
                downloaded_size += len(data)
                if downloaded_size == file_size:
                    BilibiliDownloader.show_end_bar(file_size, downloaded_size,
                                                    time.time() - total_timing)
                if time.time() - timing > 0.5:
                    interval_downloaded = downloaded_size - the_last_downloader_size
                    BilibiliDownloader.show_progress_bar(file_size, downloaded_size,
                                                         time.time() - timing,
                                                         interval_downloaded)
                    timing = time.time()
                    the_last_downloader_size = downloaded_size

    @staticmethod
    def combine(title, path):
        """
        合成视频
        :param title: 视频标题
        :param path: path
        :return: None
        """
        print('正在合成视频和音频')
        command = f'ffmpeg -i {path}/{title}_video.mp4 -i {path}/{title}_audio.mp4 ' \
                  f'-c copy {path}/{title}.mp4 -y -loglevel quiet '
        subprocess.Popen(command, shell=True)
        while True:
            try:
                if os.path.exists(f'{path}/{title}.mp4'):
                    os.remove(f'{path}/{title}_video.mp4')
                    os.remove(f'{path}/{title}_audio.mp4')
                    break
            except PermissionError:
                pass
        print('合成完毕')
        return

    @staticmethod
    def _get_title(html, url):
        """
        获取视频标题
        :param html: html
        :param url: url
        :return: 视频标题
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
                print(f'获取标题失败，正在帮您重新请求(请求次数：{request_counts})')
                html = crawl(url)
        # 标题违规字符处理，防止文件名报错
        title = re.sub('[\\\\:*;?/"<>\\]|\\[] ', '', title)
        title = re.sub(' ', '', title)
        print('获取成功')
        print('您当前正在下载：', title)
        return title

    @staticmethod
    def _get_video_url(temp):
        """
        获取视频的url
        :param temp: temp
        :return: 视频的url
        """
        # 1.先获取当前能够选择的视频清晰度列表
        available_quality_list = BilibiliDownloader._get_available_quality_list(temp)
        # 2.再根据列表生成一个供用户选择的字典
        choose_dice = BilibiliDownloader._get_choose_dict(available_quality_list)
        # 3.然后让用户选择,获取对应的id
        video_id = BilibiliDownloader._get_choose(choose_dice)
        # 4.最后根据id来获取视频对应的url
        videos = temp['data']['dash']['video']
        for each in videos:
            if video_id == each['id']:
                video_url = each['base_url']
                return video_url

    @staticmethod
    def _get_choose(choose_dict):
        """
        根据用户选择的清晰度，获取当前要下载的视频的清晰度对应的id
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
                    choose_id = contrast_dict[choose_dict[quality]]
                    break
                else:
                    print('请输入正确的，在范围内的序号')
            except ValueError:
                print('请输入正确的，在范围内的序号')
        return choose_id

    @staticmethod
    def _get_choose_dict(available_quality_list):
        """
        选择清晰度的字典
        :param available_quality_list: 当前能够选择的清晰度列表
        :return: 选择的字典，例如：{1: '高清 1080P', 2: 64: '高清 720P'}
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
        i = 0
        for each in available_quality_list:
            i += 1
            choose_dict[i] = contrast_dict[each]
        return choose_dict

    @staticmethod
    def _get_available_quality_list(temp):
        """
        获取当前能够下载的视频清晰度
        :param temp: temp
        :return: 返回一个列表，包含当前能够下载的视频清晰度
        """
        all_quality_list = [120, 116, 80, 64, 32, 16]
        available_quality_list = []
        videos = temp['data']['dash']['video']
        for each in videos:
            each_id = each['id']
            if each_id in all_quality_list and each_id not in available_quality_list:
                available_quality_list.append(each_id)
        return available_quality_list

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


def run():
    """
    运行的主方法
    :return: None
    """
    announcement()
    url = get_url()
    if 'bilibili.com' in url:
        BilibiliDownloader.run(url)


if __name__ == "__main__":
    run()
