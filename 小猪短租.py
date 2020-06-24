# -*- coding: utf-8 -*-
# @Time    : 2020/6/19 8:51
# @Author  : ZHALONG
# @FileName: 小猪短租.py
# @Software: PyCharm

import requests
import os
import csv
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from parsel import Selector

queue = Queue()

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36"
}
def get_response(url):
    """

    :param url: 链接
    :return:
    """
    try:
        if "Citys" in url:
            headers["xsrf-token"] = "13d35bb2c85ffd2fc53be0d9612980d0"
        response = requests.get(url, headers=headers)
        response.encoding = "utf-8"
        response.raise_for_status()
        return response
    except Exception as e:
        return e.args

def get_citys(response):
    """

    :param response: 城市列表页的内容
    """
    content = response.json()
    all_citys = content["sucmsg"]["internalAllCity"]

    for name, value in all_citys.items():
        for i in range(len(value)):
            city = value[i].get("short_name")
            city_domain = value[i].get("domain")
            total_count = value[i].get("lucount")
            with open('城市.csv', 'a', encoding='utf-8', newline="") as f:
                f.write(city + "," + city_domain + ',' + total_count + "\n")

def get_hotel_url(city_file):
    """

    :param city_file: 城市文件
    """
    # count = 0
    with open(city_file, "r", encoding="utf-8") as f:
        for info in f.readlines():
            city_domain = info.split(",")[1]
            total_count = info.split(",")[2]
            # count = count + (int(total_count) // 24) * 24
            hotel_page = int(total_count) // 24
            for page in range(hotel_page):
                hotel_url = f"https://{city_domain}.xiaozhu.com/search-duanzufang-p{page}-0/"
                queue.put(hotel_url)

def get_hotel_info(hotel_url, writer):
    """

    :param hotel_url: 每一页的链接
    :param writer: CSV编辑
    """
    response = requests.get(hotel_url, headers=headers)
    response.encoding = "utf-8"
    selector = Selector(response.text)
    li_list = selector.xpath("//ul[@class='pic_list clearfix list_code']/li")
    for li in li_list:
        hotel_href = li.xpath("./a/@href").get() # 短租链接
        hotel_title = li.xpath("./a/img/@title").get()  # 短租标题
        hotel_price = li.xpath(".//span[@class='result_price']/i/text()").get() # 短租价格
        hotel_info = li.xpath(".//em[@class='hiddenTxt']/text()").get().strip()
        if len(hotel_info.split("/")) == 3:
            hotel_kind = hotel_info.split("/")[0]   # 短租还是整租
            hotel_cbed = hotel_info.split("/")[1]   # 床数
            hotel_num_people = hotel_info.split("/")[2] # 宜居人数
            hotel_type = None # 户型
        else:
            hotel_kind = hotel_info.split("/")[0]
            hotel_cbed = hotel_info.split("/")[2]
            hotel_num_people = hotel_info.split("/")[3]
            hotel_type = hotel_info.split("/")[1]
        hotel_num_comment = li.xpath(".//span[@class='commenthref']/text()").get().strip().replace("- ","").replace("条点评","")  # 评论数
        writer.writerow([hotel_title,hotel_href,hotel_type,hotel_kind,hotel_cbed,hotel_num_people,hotel_price,hotel_num_comment])


def main():
    city_url = "https://www.xiaozhu.com/ajaxRequest/Ajax_SearchCitys"
    city_response = get_response(url=city_url)
    if not os.path.exists("城市.csv"):
        get_citys(response=city_response)
    get_hotel_url(city_file="城市.csv")

    file = open("小猪短租.csv", "a", encoding="utf-8", newline="")
    writer = csv.writer(file)
    writer.writerow(["短租标题","短租链接","户型","短租还是整租","床数","宜居人数","短租价格","评论数"])

    pool = ThreadPoolExecutor()
    [pool.submit(get_hotel_info, queue.get(), writer) for _ in range(queue.qsize())]

main()
