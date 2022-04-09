# =======================================================
# Bilibili Downloader
# Copyright (c) 2022 chaziming
# All rights reserved.
#
# 本开源程序遵顼 Apache License 2.0 协议
# =======================================================

"""
说明.一.本程序优点：1.吊打其他m3u8下载器，拥有防止卡死，自动重连，多线程功能，速度非常快
2.连续性强，即使程序运行时关掉再打开，只需重新输入相同的m3u8地址就可以接着上次的进度继续
缺点：1.不是gui程序
二.具体消息/更新内容请浏览下方announcement()函数
"""

__version__ = 'v0.2.0'
__author__ = 'chaziming'

import requests
import re
from Crypto.Cipher import AES
from multiprocessing.dummy import Pool
from urllib.parse import urljoin
import os
from subprocess import Popen
import time
import tkinter as tk
from tkinter import filedialog


class M3U8_Downloader:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/100.0.4896.60 Safari/537.36 Edg/100.0.1185.29 '
    }
    session = requests.Session()

    def __init__(self):
        self.ts_url = []
        self.content = None
        self.m3u8_url = None
        self.cryptor = None
        self.quantity = None
        self.path = None
        self.name = None
        self.announcement()
        self.get_url()
        self.process_m3u8()
        if "EXT-X-KEY" in self.content:
            self.get_key()
        self.get_path()
        self.get_name()
        self.run()
        self.combine()

    @staticmethod
    def announcement():
        title = 'm3u8 Downloader' + ' ' * 5
        author = 'chaziming'
        version = 'v0.2.0'
        dividing_line = '-' * 40 + '\n'
        feature = '本程序特点：优点：1.吊打其他m3u8下载器，拥有防止\n' \
                  '卡死，自动重连，多线程功能，速度非常快\n' \
                  '2.连续性强，即使程序运行时关掉再打开，只需重新输\n' \
                  '入相同的m3u8地址就可以接着上次的进度继续\n' \
                  '缺点：1.不是gui程序\n'
        fix_bugs = '修复bug：暂无\n'
        optimization = '优化：1.新增了自定义路径功能\n' \
                       '2.新增了自定义线程数功能\n' \
                       '3.优化了底层逻辑，使运行更加顺畅\n' \
                       '4.增加了自动重连的时间，防止网速慢而导致频繁重连\n'
        spread = 'more: \nhttps://github.com/chaziming/Video-Downloader\n'
        print('\033[1;34m' + dividing_line + title, version, 'by', author)
        print(feature + '公告：\n' + fix_bugs + optimization + spread + dividing_line + '\033[0m')

    def get_url(self):
        while True:
            try:
                m3u8_url = input('请输入m3u8地址：')
                print('开始获取m3u8内容')
                m = 1
                while True:
                    try:
                        response = self.session.get(m3u8_url, headers=self.headers, timeout=10)
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
                self.m3u8_url = m3u8_url
                self.content = content
                break

    def process_m3u8(self):
        ts_list = re.findall('EXTINF:.*,\n(.*)\n#', self.content)
        for i in ts_list:
            each_url = urljoin(self.m3u8_url, i)
            self.ts_url.append(each_url)
        self.quantity = len(self.ts_url)
        print('您下载的视频片段总共有', self.quantity)
        return

    def get_path(self):
        print('请在弹出的窗口中选择视频位置')
        time.sleep(2)
        root = tk.Tk()
        root.withdraw()
        folder_path = filedialog.askdirectory()
        self.path = folder_path

    def get_name(self):
        name = input('请填写本次下载的文件名（可空，默认为当前时间戳）')
        if name == '':
            name = round(time.time())
        self.name = name
        os.makedirs(self.path + f'/{self.name}', exist_ok=True)

    def get_key(self):
        key_url = re.sub('hls(/.*?.m3u8)', 'hls/key.key', self.m3u8_url)
        i = 1
        while True:
            try:
                key = self.session.get(url=key_url, headers=self.headers, timeout=3).text.encode('utf-8')
                break
            except requests.exceptions.ReadTimeout:
                print(f'获取密钥超时，正在帮您重新获取（第{i}次尝试）')
                i += 1
        self.cryptor = AES.new(key, AES.MODE_CBC, key)

    def encrypted_download(self, url):
        a = 1 + self.ts_url.index(url)
        i = 1
        while True:
            try:
                res = self.session.get(url=url, headers=self.headers, timeout=5)
                break
            except requests.exceptions.ReadTimeout:
                print(f'获取第{a}个视频片段超时，正在帮您重新获取（第{i}次尝试）')
                i += 1
        cont = self.cryptor.decrypt(res.content)
        if os.path.isfile(self.path + f'/{self.name}/' + '%05d.ts' % a):
            pass
        with open(self.path + f'/{self.name}/%05d.ts' % a, 'wb') as f:
            f.write(cont)

    def normal_download(self, url):
        a = 1 + self.ts_url.index(url)
        i = 1
        while True:
            try:
                res = self.session.get(url=url, headers=self.headers, timeout=5)
                break
            except requests.exceptions.ReadTimeout:
                print(f'获取第{a}个视频片段超时，正在帮您重新获取（第{i}次尝试）')
                i += 1
        if os.path.isfile(self.path + f'/{self.name}/' + '%05d.ts' % a):
            pass
        else:
            with open(self.path + f'/{self.name}/%05d.ts' % a, 'wb') as f:
                f.write(res.content)

    def encrypted_check(self):
        print('正在帮您检查是否有遗漏的视频片段')
        for a in range(len(self.ts_url)):
            a += 1
            if os.path.isfile(self.path + f'/{self.name}/' + '%05d.ts' % a):
                pass
            else:
                print(f'检测到您第{a}个视频片段有遗漏，正在帮您重新获取')
                url = self.ts_url[a - 1]
                i = 1
                while True:
                    try:
                        res = self.session.get(url=url, headers=self.headers, timeout=5)
                        break
                    except requests.exceptions.ReadTimeout:
                        print(f'获取第{a}个视频片段超时，正在帮您重新获取（第{i}次尝试）')
                        i += 1
                with open(self.path + f'/{self.name}/%05d.ts' % a, 'wb') as f:
                    cont = self.cryptor.decrypt(res.content)
                    f.write(cont)
        print('检查完毕，开始合并')

    def normal_check(self):
        print('正在帮您检查是否有遗漏的视频片段')
        for a in range(len(self.ts_url)):
            a += 1
            if os.path.isfile(self.path + f'/{self.name}/' + '%05d.ts' % a):
                pass
            else:
                print(f'检测到您第{a}个视频片段有遗漏，正在帮您重新获取')
                url = self.ts_url[a - 1]
                i = 1
                while True:
                    try:
                        res = self.session.get(url=url, headers=self.headers, timeout=5)
                        break
                    except requests.exceptions.ReadTimeout:
                        print(f'获取第{a}个视频片段超时，正在帮您重新获取（第{i}次尝试）')
                        i += 1
                with open(self.path + f'/{self.name}/%05d.ts' % a, 'wb') as f:
                    f.write(res.content)
        print('检查完毕，开始合并')

    def run(self):
        threads = input('请输入线程数（可空，默认10个）')
        if threads:
            pool = Pool(int(threads))
        else:
            pool = Pool(10)
        if "EXT-X-KEY" not in self.content:
            pool.map(self.normal_download, self.ts_url)
            self.normal_check()
        else:
            pool.map(self.encrypted_download, self.ts_url)
            self.encrypted_check()

    def combine(self):
        command = 'copy /b ' + self.path + f'/{self.name}/' + '*.ts ' + self.path + f'/{self.name}/{self.name}'\
                  + '.mp4 '
        Popen(command, shell=True)
        print('合并完毕，请查收')
        while True:
            if os.path.isfile(self.path + f'/{self.name}/{self.name}' + '.mp4'):
                time.sleep(30)
                for a in range(self.quantity):
                    a += 1
                    os.remove(self.path + f'/{self.name}/%05d.ts' % a)
                break
        print('成功删除所有视频片段')


if __name__ == "__main__":
    m3u8_downloader = M3U8_Downloader()
