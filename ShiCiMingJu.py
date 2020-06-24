# -*- coding: utf-8 -*-
# @Time    : 2020/6/24 16:34
# @Author  : ZHALONG
# @FileName: ShiCiMingJu.py
# @Software: PyCharm

'''
    任务：获取网站收录的13033位诗人信息及作品
        1、个人简介（姓名，年代(若无为空)，简介）
        2、所有作品（诗词名称，诗词内容，解析）
'''

import requests
from queue import Queue
from faker import Faker
from parsel import Selector
from concurrent.futures import ThreadPoolExecutor

user_agent = Faker("zh-CN").user_agent()
def get_headers():
    headers = {
        "user-agent": user_agent
    }
    return headers

class SCMJ(object):
    def __init__(self):
        self.queue = Queue()
        self.base_url = "http://www.shicimingju.com"

    def get_url(self):
        for page in range(1, 13036):
            url = f"http://www.shicimingju.com/chaxun/zuozhe/{page}.html"
            self.queue.put(url)

    def get_response(self, url):
        try:
            response = requests.get(url=url, headers=get_headers())
            response.encoding = "utf-8"
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(e.args)

    def get_author(self, response):
        selector = Selector(response)
        author = selector.xpath("//div[@class='des']/a[1]/text()").get()
        year = selector.xpath("//div[@class='aside_val']/a/text()").get()
        _intro = selector.xpath("//div[@class='des']//text()").getall()
        intro = "".join(_intro).strip()
        _sc_count = selector.xpath("//div[@class='aside_right']/div[2]/a/text()").get()
        sc_count = _sc_count.replace("首","")

        if int(sc_count) % 20 != 0:
            page = int(sc_count) // 20 + 1
        else:
            page = int(sc_count) / 20
        return author, year, intro, page

    def zp_urls(self, zz_url, page):
        for i in range(1, page + 1):
            zp_url = zz_url.replace(".html","") + f"_{i}" + ".html"
            zp_res = self.get_response(zp_url)
            selector = Selector(zp_res)
            zp_urls = selector.xpath("//div[@class='shici_list_main']/h3/a/@href").getall()
            zp_url = [self.base_url + url for url in zp_urls]
            for url in zp_url:
                res = self.get_response(url)
                sc, comments = self.zp(res)
                # print(sc[0:10])

    def zp(self, response):
        selector = Selector(response)
        _sc = selector.xpath("//div[@class='item_content']/text()").getall()
        sc = "".join(_sc).strip()

        _comments = selector.xpath("//div[@class='shangxi_content']//text()").getall()
        comments = "".join(_comments).strip()
        return sc, comments

    def parse(self):
        while not self.queue.empty():
            zz_url = self.queue.get()
            print(zz_url)
            zz_res = self.get_response(url=zz_url)
            author, year, intro, page = self.get_author(zz_res)
            self.zp_urls(zz_url, page)

    def run(self):
        self.get_url()
        self.parse()
        loop = ThreadPoolExecutor()
        for _ in range(5):
            loop.submit(self.parse())

if __name__ == '__main__':
    spider = SCMJ()
    spider.run()