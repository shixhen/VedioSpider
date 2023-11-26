# -*- coding:utf-8 -*-


import re
import os
import json

from urllib import parse
import tkinter as tk
from tkinter import filedialog

import requests

from utils.log import Log
from utils.download import file_download

log = Log()

if os.path.exists('config.json'):
    with open('config.json') as json_file:
        # 加载JSON数据
        try:
            data = json.load(json_file)
            COOKIE = data["douyin_cookie"]
            api_cookie = data["douyin_api_cookie"]
        except json.decoder.JSONDecodeError:
            log.e('获取data时错误')


# api_cookie,主要包含三个参数，msToken，odin_tt, bd_ticket_guard_client_data



headers = {
    "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62'
}
headers.update({'cookie': COOKIE})

api_headers = {
    "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
    'cookie': api_cookie,
    'referer': "https://www.douyin.com/"
}

session = requests.Session()


class Douyin:

    def __init__(self):
        self.video_url_dict = {}  # 存放视频url的字典,key = 文案,value = url
        self.picture_url_dict = {}  # 存放图片url的字典,key = 文案,value = url
        self.homepage_url = None  # homepage的url
        self.path = None  # 保存的路径
        # self.page_html = None  # 主页的html
        self.nick_name = None  # 用户的名称
        self.secUid = None  # 用户的secUid
        self.update_list = []

    def get_url(self):
        """
        获取url
        :return:
        """
        while True:
            url = input('请输入抖音url:')
            if 'douyin.com' in url:
                if 'modal' in url:
                    url = 'https://www.douyin.com/video/' + re.findall(r'modal_id=(\d+)', url)[0]
                self.homepage_url = url
                return
            else:
                print('请输入正确的抖音url')

    def get_path(self):
        """
        获取保存的路径
        :return:
        """
        choose = input('请输入视频保存位置,回车以选择桌面，键入任意键弹出窗口选择目录')
        if choose == '':
            self.path = os.path.join(os.path.expanduser("~"), 'Desktop')
        else:
            try:
                root = tk.Tk()
                root.withdraw()
                root.title = '请选择视频保存位置'
                folder_path = filedialog.askdirectory()

                self.path = folder_path
            except Exception as e:
                log.e(e)
                print('弹窗出错,请重新选择')
                self.get_path()

        if self.nick_name is not None:
            self.path = os.path.join(self.path, self.nick_name)
        print(self.path)

    def get_data_from_page(self):
        """
        获取主要的data
        :return:
        """
        page = session.get(self.homepage_url, headers=headers).text
        if '验证码中间页' in page:
            print('您遇到了验证码')
            self.process_verification()
        else:
            page_html = page
            # 处理主页的html，获取RENDER_DATA的字典
            pattern = r'<script id="RENDER_DATA" type="application/json">(.*?)</script>'
            # 通过正则表达式寻找
            data = re.findall(pattern, page_html)[0]
            # url解码,并将json转换为python的字典
            return json.loads(parse.unquote(data))

    def process_video_detail_page(self):
        """
        处理视详情页
        :return:
        """
        data = self.get_data_from_page()
        video_detail = data['74931a6b75e09238f154ab1577c994c9']['aweme']['detail']
        desc = video_detail['desc']

        # 判断是否为视频,如果时长duration为0，则为图片
        self.video_url_dict[desc] = 'http:' + \
                                    video_detail['video']['playAddr'][0]['src']

    @staticmethod
    def process_verification():
        """
        处理验证码的方法
        :return:
        """
        print('目前没有处理验证码的方法')
        quit()

    def process_homepage(self):
        """
        分为几步：
        1.获取相应的data字典
        2.获取用户基本信息
        3.保存用户基本信息
        4.获取最开始的视频
        5.用api获取剩下的视频
        获取的视频和图片的url将保存在对应的字典里
        :return: None
        """
        #  1.获取相应的data字典
        data = self.get_data_from_page()
        #  2.获取用户基本信息
        save_user_information = self.get_user_information(data)
        #  3.保存用户基本信息
        self.save_user_information(save_user_information)
        #  4.获取最开始的视频
        # self.get_original_video_url(data)
        #  5.用api获取剩下的视频
        self.get_videos()

    def save_user_information(self, save_user_information):
        """
        保存抖音视频作者的一些相关信息
        :param save_user_information: 用来保存作者信息的字典
        :return:
        """

        # 打开保存的文件，并读取之前的数据
        with open('../temp.json', 'r', encoding='utf-8') as f:
            content = f.read()
        save_data = json.loads(content)

        # 保存用户信息
        if self.secUid not in list(save_data['user_dict'].values()):
            save_data['user_dict'][self.nick_name] = self.secUid
            save_data['user_information'][self.nick_name] = save_user_information
            with open("../temp.json", 'w', encoding='utf-8') as write_f:
                json.dump(save_data, write_f, indent=4, ensure_ascii=False)
        # 下载过此用户的视频
        else:
            is_update = input(
                '检测到您已经下载过该用户的视频，如果要下载该用户更新的视频，请直接回车，如仍要下载该用户的所有视频，请键入任意键')
            if is_update == '':
                self.update_one_user(self.secUid)
            else:
                self.update_user_information(save_user_information, save_data)

    def get_user_information(self, data):
        """
        获取作者的信息
        :param data: 获取的data
        :return:
        """
        # 获取用户信息
        save_user_information = {}
        user_information = data['2839d7ee742bba02fd563b25e3576c64']['user']['user']
        self.secUid = user_information['secUid']  # secUid
        self.nick_name = user_information['nickname']  # 昵称
        save_user_information['secUid'] = user_information['secUid']  # secUid
        save_user_information['nick_name'] = user_information['nickname']  # 昵称
        save_user_information['awemeCount'] = user_information['awemeCount']  # 视频数量
        save_user_information['age'] = user_information['age']  # 年龄
        save_user_information['desc'] = user_information['desc']  # 主页描述
        save_user_information['followerCount'] = user_information['followerCount']  # 粉丝数量
        save_user_information['totalFavorited'] = user_information['totalFavorited']  # 点赞总数
        save_user_information['avatarUrl'] = user_information['avatarUrl']  # 头像100*100
        save_user_information['avatar300Url'] = user_information['avatar300Url']  # 头像300*300
        # 获取用户最新的视频的Id
        aweme_list = []
        # data_list = list(data.values())[1]['post']['data']
        # for each in data_list:
        #     aweme_list.append(each['awemeId'])
        save_user_information['aweme_list'] = aweme_list
        return save_user_information

    def get_videos(self):
        """
        调用api获取作者所有的视频
        :return:
        """
        has_more = 1
        max_cursor = 0

        while has_more == 1:
            api_url = self._get_x_bogus_url(max_cursor)
            # 获取请求api得到的数据
            aweme = json.loads(requests.get(api_url, headers=api_headers).text)
            aweme_list = aweme['aweme_list']
            # 解析aweme_list
            log.i(f'获取到更多的{len(aweme_list)}个视频或图片')
            for each in aweme_list:

                desc = each['desc']
                n = 1
                # 判断是否为视频，若时长为0，则为图片
                if each['duration'] == 0:
                    while desc in self.picture_url_dict:
                        n += 1
                        desc += f'({n})'
                    self.picture_url_dict[desc] = each['images']

                else:
                    # 避免重名
                    while desc in self.picture_url_dict:
                        n += 1
                        desc += f'({n})'
                    self.video_url_dict[desc] = each['video']['play_addr']['url_list'][0]

            # 判断是否有更多的视频
            has_more = aweme['has_more']
            max_cursor = aweme['max_cursor']

    def _get_x_bogus_url(self, max_cursor):
        """
        通过API来获取带有x_bogus参数的api的url
        :param max_cursor: max_cursor
        :return: api的url
        """
        # 使用api获取X-Bogus参数，并生成最终的api的url
        api_parameters = {"url": f'https://www.douyin.com/aweme/v1/web/aweme/post/?'
                                 'aid=6383&'
                                 f'sec_user_id={self.secUid}&'
                                 f'max_cursor={max_cursor}&'
                                 'count=10',
                          'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                                        'Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62'}
        response = requests.post('https://tiktok.iculture.cc/X-Bogus', json=api_parameters)
        api_url = json.loads(response.text)['param']

        return api_url

    def download(self):
        """
        下载视频和图片
        :return:
        """
        # 创建相关文件夹
        os.makedirs(self.path, exist_ok=True)  # 判断有没有文件夹，没有则创建。

        self.download_video()
        self.download_picture()

    def download_picture(self):
        os.makedirs(self.path + '/' + '图片', exist_ok=True)
        for i in list(self.picture_url_dict.keys()):
            illegal_chars = r'[<>:"/\\|?*\x00-\x1F]'
            # 将非法字符替换为空字符串
            filename = re.sub(illegal_chars, '', i)
            a = 1
            for j in self.picture_url_dict[i]:
                if os.path.exists(os.path.join(self.path + '/' + '图片', filename + f'{a}.jpeg')):
                    log.w(f'文件{os.path.join(self.path + "/" + "图片", filename)}{a}.jpeg已存在')
                else:
                    with open(os.path.join(self.path + '/' + '图片', filename + f'{a}.jpeg'),
                              'wb') as f:
                        if 'urlList' in j:
                            f.write(requests.get(j['urlList'][0], headers=headers).content)
                            log.i('成功下载:' + i + f'{a}.jpeg')
                        else:
                            f.write(requests.get(j['url_list'][0], headers=headers).content)
                            log.i('成功下载:' + i + f'{a}.jpeg')
                a += 1

    def download_video(self):
        os.makedirs(self.path + '/' + '视频', exist_ok=True)
        a = 0
        for i in list(self.video_url_dict.keys()):
            illegal_chars = r'[<>:"/\\|?*\x00-\x1F]'
            # 将非法字符替换为空字符串
            filename = re.sub(illegal_chars, '', i)
            if os.path.exists(os.path.join(self.path + '/' + '视频', filename + '.mp4')):
                log.w(f'文件{os.path.join(self.path + "/" + "视频", filename)}.mp4已存在')
            else:
                file_download(self.video_url_dict[i],
                              os.path.join(self.path + "/" + "视频", filename + '.mp4'))
                a += 1
                log.i('成功下载:' + i + '.mp4')
                log.i('已下载视频数量：' + str(a) + '/' + str(len(list(self.video_url_dict.keys()))))

    def update_one_user(self, uid):
        """
        更新本地的一个作者的视频
        :param uid: 每个作者的专属的uid
        :return:
        """
        self.homepage_url = 'https://www.douyin.com/user/' + uid

        data = self.get_data_from_page()
        # 获取用户最新的视频的Id
        save_user_information = self.get_user_information(data)
        with open('../temp.json', 'r', encoding='utf-8') as f:
            content = f.read()
        save_data = json.loads(content)
        self.update_user_information(save_user_information, save_data)
        self.get_update_video_url(data)
        for each in self.update_list:
            print(each)
        self.get_path()
        self.download()

    def update_user_information(self, save_user_information, save_data):
        """
        更新一个用户的信息
        :param save_user_information: 要保存的信息字典
        :param save_data: 之前保存的信息
        :return:
        """
        # 检测并处理改名
        if self.nick_name not in list(save_data['user_dict'].keys()):
            primary_name = [key for key, value in save_data['user_dict'].items() if
                            value == self.secUid]
            print(primary_name, '改名了')
            print('改成名为：', self.nick_name)
            # 更改键名
            save_data['user_dict'][self.nick_name] = save_data['user_dict'].pop(
                primary_name)
            save_data['user_information'][self.nick_name] = save_data[
                'user_information'].pop(
                primary_name)
        # 检测是否有更新视频
        if save_data['user_information'][self.nick_name]['aweme_list'] != \
                save_user_information['aweme_list']:
            print(self.nick_name, '更新了')
            # 将更新的视频放入self.update_list中
            for each in save_user_information['aweme_list']:
                if each not in save_data['user_information'][self.nick_name]['aweme_list']:
                    self.update_list.append(each)

            save_user_information['aweme_list'] = save_user_information['aweme_list']
            print(save_data['user_information'][self.nick_name], '=>' + '\n',
                  save_user_information)
            save_data['user_information'][self.nick_name] = save_user_information
        # 将更新好的数据保存在文件里
        with open("../temp.json", 'w', encoding='utf-8') as write_f:
            json.dump(save_data, write_f, indent=4, ensure_ascii=False)

    def get_update_video_url(self, data):
        self.get_videos()
        data_list = list(data.values())[1]['post']['data']
        for each in data_list:
            if each['awemeId'] not in self.update_list:
                continue
            desc = each['desc']
            n = 1
            # 判断是否为视频,如果时长duration为0，则为图片
            if each['video']['duration'] == 0:
                while desc in self.picture_url_dict:
                    n += 1
                    desc += f'({n})'
                self.picture_url_dict[desc] = each['images']
            else:
                while desc in self.picture_url_dict:
                    n += 1
                    desc += f'({n})'
                self.video_url_dict[desc] = 'http:' + \
                                            each['video']['bitRateList'][0]['playAddr'][0]['src']

    def update_all_user(self):
        """
        更新抖音作者的视频和信息
        :return:
        """
        # 获取保存的抖音用户的信息
        with open('../temp.json', 'r', encoding='utf-8') as f:
            content = f.read()
        save_data = json.loads(content)
        for each_uid in list(save_data['user_dict'].values()):
            self.update_one_user(each_uid)
            # 初始化
            self.__init__()

    @classmethod
    def download_all_videos_of_one(cls):
        """
        获取一个抖音用户的所有的视频和图片
        :return: None
        """
        douyin = cls()
        douyin.get_url()
        douyin.process_homepage()
        douyin.get_path()
        douyin.download()
        log.i('共下载图片数量：' + str(len(list(douyin.picture_url_dict.keys()))))
        log.i('共下载视频数量：' + str(len(list(douyin.video_url_dict.keys()))))

    @classmethod
    def update_douyin(cls):
        """
        更新已保存的抖音作者的视频和信息
        :return:None
        """
        douyin = cls()
        douyin.update_all_user()

    @classmethod
    def download_one_video(cls):
        while True:
            douyin = cls()
            douyin.get_url()
            douyin.process_video_detail_page()
            douyin.get_path()
            douyin.download_video()

    @classmethod
    def download_douyin(cls):
        while True:
            douyin = cls()
            douyin.get_url()
            if 'video/' in douyin.homepage_url:
                douyin.process_video_detail_page()
                douyin.get_path()
                douyin.download_video()
            else:
                douyin.process_homepage()
                douyin.get_path()
                douyin.download()
                log.i('共下载图片数量：' + str(len(list(douyin.picture_url_dict.keys()))))
                log.i('共下载视频数量：' + str(len(list(douyin.video_url_dict.keys()))))


if __name__ == '__main__':
    Douyin.download_douyin()
