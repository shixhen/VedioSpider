# =======================================================
# m3u8 Downloader
# Copyright (c) 2022 chaziming
# All rights reserved.
#
# 本开源程序遵顼 Apache License 2.0 协议
# =======================================================

import requests
import re
from Crypto.Cipher import AES
from multiprocessing.dummy import Pool
from urllib.parse import urljoin
import os


__version__ = 'v0.1.0'
__author__ = 'chaziming'


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/100.0.4896.60 Safari/537.36 Edg/100.0.1185.29 '
}
session = requests.Session()
ts_url = []


title = 'm3u8 Downloader' + ' '*5
author = 'chaziming'
version = 'v0.1.0'
dividing_line = '-' * 40 + '\n'
fix_bugs = '修复bug：暂无\n'
optimization = '说明：本版本为此程序的第一版本，存在一些缺点，后续会慢慢优化，下载好的视频在电脑的视频文件夹中\n' \
                '特点：1.吊打其他m3u8下载器，拥有防止卡死，自动重连的功能\n' \
                '2.多线程，速度非常快\n' \
                '3.bug较少\n' \
                '缺点：不是gui程序\n'
print('\033[1;34m' + dividing_line + title, version, 'by', author)
print('公告：\n' + fix_bugs + optimization + dividing_line + '\033[0m')

while True:
    try:
        m3u8_url = input('请输入m3u8地址：')
        print('开始获取m3u8内容')
        m = 1
        while True:
            try:
                response = session.get(m3u8_url, headers=headers, timeout=3)
                if response.status_code == 200:
                    break
            except requests.exceptions.ReadTimeout:
                print(f'\033[1;31m连接超时，正在帮您自动重连，（第 \033[1;36m{m}\033[1;31m次重连）\033[0m ')
                m += 1
        content = response.text
        print('成功获取m3u8文件内容')
    except requests.exceptions.RequestException:
        print("您输入的m3u8地址有误或服务器拒绝连接，请重新输入")
        continue
    if "#EXTM3U" not in content:
        print("这不是一个m3u8的视频链接！请重新输入")
        continue
    else:
        break


def process_m3u8():
    global ts_url
    ts_list = re.findall('EXTINF:.*,\n(.*)\n#', content)
    for i in ts_list:
        each_url = urljoin(m3u8_url, i)
        ts_url.append(each_url)
    quantity = len(ts_url)
    print('您下载的视频片段总共有', quantity)
    return


def encrypted_download(url):
    key_url = re.sub('hls(/.*?.m3u8)', 'hls/key.key', m3u8_url)
    i = 1
    while True:
        try:
            key = session.get(url=key_url, headers=headers, timeout=3).text.encode('utf-8')
            break
        except requests.exceptions.ReadTimeout:
            print(f'获取密钥超时，正在帮您重新获取（第{i}次尝试）')
            i += 1

    cryptor = AES.new(key, AES.MODE_CBC, key)
    a = 1 + ts_url.index(url)
    i = 1
    while True:
        try:
            res = session.get(url=url, headers=headers, timeout=3)
            break
        except requests.exceptions.ReadTimeout:
            print(f'获取第{a}个视频片段超时，正在帮您重新获取（第{i}次尝试）')
            i += 1
    cont = cryptor.decrypt(res.content)
    with open(os.path.join(r'C:\Users\Administrator\Videos', '%05d.ts' % a), 'wb') as f:
        f.write(cont)


def normal_download(url):
    a = 1 + ts_url.index(url)
    i = 1
    while True:
        try:
            res = session.get(url=url, headers=headers, timeout=3)
            break
        except requests.exceptions.ReadTimeout:
            print(f'获取第{a}个视频片段超时，正在帮您重新获取（第{i}次尝试）')
            i += 1
    with open(os.path.join(r'C:\Users\Administrator\Videos', '%05d.ts' % a), 'wb') as f:
        f.write(res.content)


def check(s):
    print('正在帮您检查是否有遗漏的视频片段')
    for a in range(len(ts_url)):
        a += 1
        if os.path.isfile(r'C:\Users\Administrator\Videos\%05d.ts' % a):
            pass
        else:
            print(f'检测到您第{a}个视频片段有遗漏，正在帮您重新获取')

            url = ts_url[a - 1]
            i = 1
            while True:
                try:
                    res = session.get(url=url, headers=headers, timeout=3)
                    break
                except requests.exceptions.ReadTimeout:
                    print(f'获取第{a}个视频片段超时，正在帮您重新获取（第{i}次尝试）')
                    i += 1
            with open(os.path.join(r'C:\Users\Administrator\Videos', '%05d.ts' % a), 'wb') as f:
                if s == 1:
                    key_url = re.sub('hls(/.*?.m3u8)', 'hls/key.key', m3u8_url)
                    while True:
                        try:
                            key = session.get(url=key_url, headers=headers, timeout=3).text.encode('utf-8')
                            break
                        except requests.exceptions.ReadTimeout:
                            pass
                    cryptor = AES.new(key, AES.MODE_CBC, key)
                    cont = cryptor.decrypt(res.content)
                    f.write(cont)
                else:
                    f.write(res.content)
    print('检查完毕，开始合成')


def run():
    process_m3u8()
    pool = Pool(10)
    if "EXT-X-KEY" not in content:
        pool.map(normal_download, ts_url)
        check(0)
    else:
        pool.map(encrypted_download, ts_url)
        check(1)


if __name__ == "__main__":
    run()
