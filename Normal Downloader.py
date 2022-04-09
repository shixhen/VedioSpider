# =======================================================
# Normal Downloader
# Copyright (c) 2022 chaziming
# All rights reserved.
#
# 本开源程序遵顼 Apache License 2.0 协议
# =======================================================

"""
说明：一。本程序适用于已知完整的、直接的视频地址，并且视频没有任何的拆分，加密。
二.本程序优点：1.个性化进度条展示
缺点：1.不是gui程序
三.具体消息/更新内容请浏览下方announcement()函数
"""

__version__ = 'v0.1.0'
__author__ = 'chaziming'

import sys
from datetime import timedelta
import os
from time import time
from requests import Session
from requests.exceptions import RequestException

session = Session()

def announcement():
    title = 'Normal Downloader' + ' '*3
    author = 'chaziming'
    version = 'v0.1.0'
    dividing_line = '-' * 40 + '\n'
    explanation = '本程序适用于已知完整的、直接的视频地址，并且视频没有任何的拆分，加密'
    fix_bugs = '暂无'
    optimization = '优化：暂无\n'
    spread = 'more see: https://github.com/chaziming/Video-Downloader\n'
    print('\033[1;34m' + dividing_line + title, version, 'by', author)
    print('说明：' + explanation)
    print('公告：\n' + fix_bugs + optimization + spread + dividing_line + '\033[0m')
    return


def get_html(url):
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


def file_download(video_url):
    headers = {
        "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.56'}
    chunk_size = 1024 * 1024
    headers['Range'] = 'bytes=' + '0' + '-'
    video_res = session.get(url=video_url, stream=True, headers=headers)
    video_size = int(video_res.headers['content-length'])
    t = time()
    speed = 0.0
    size = 0
    print('开始下载视频')
    with open(os.path.join(r'C:\Users\Administrator\Videos', '原始时代.mp4'), 'ab') as f:
        for data in video_res.iter_content(chunk_size=chunk_size):  # 每次只获取一个chunk_size大小
            f.write(data)  # 每次只写入data大小
            tt = time() - t
            t = time()
            size = len(data) + size
            # 'r'每次重新从开始输出，end = ""是不换行
            percentage = int(size / video_size * 40)
            if speed < 5.0:
                color = '\033[1;31m'
            else:
                color = '\033[1;32m'
            if speed == 0.0 or round((video_size - size) / chunk_size / speed) > 1800:
                eta = '\033[1;31m' + ' >30min'
            else:
                eta = '\033[1;34m' + ' eta ' + str(timedelta(seconds=round((video_size - size) / chunk_size / speed)))
            print('\r\t' + "\033[1;35m" + percentage * '━' + '\033[0m' + (40 - percentage) * '━' + '\033[1;35m',
                  str(round(size / chunk_size, 1)) + '/' + str(round(video_size / chunk_size, 1)), "MB" + color,
                  str(speed), 'MB/s' + eta, flush=True,
                  end='')
            sys.stdout.flush()
            last_speed = speed
            speed = round(float(chunk_size / 1024 / 1024) / tt, 1)

        if last_speed < 5.0:
            color = '\033[1;31m'
        else:
            color = '\033[1;32m'
        print('\r\t''\033[1;32m' + 40 * '━' + '\033[1;32m',
              str(round(size / chunk_size, 1)) + '/' + str(round(video_size / chunk_size, 1)), "MB" + color,
              str(speed), 'MB/s' + '\033[1;34m', 'eta', '0:00:00' + '\033[0m', flush=True)


def main():
    announcement()
    url = input('请输入完整的、直接的视频地址：')
    file_download(url)


if __name__ == "__main__":
    main()