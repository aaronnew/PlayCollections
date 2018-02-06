#!/usr/bin/pyhton3
# coding=utf-8

import requests
from pymongo import MongoClient
import re
import datetime
import time

client = MongoClient(host='mongo')
db = client.meituan
db_meishi = db.meishi
db_log = db.log

base_url = 'http://sh.meituan.com'
detail_url = 'http://www.meituan.com/meishi/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36'}

# 先将需要提取的那一片信息的代码块抽取出来
reg_detailInfo = re.compile(r'"detailInfo":{(.*?),"extraInfos":', re.S)
# 所有的这种类似匹配都可以用非贪婪匹配。也就是.*?,括号()里面就是对应要匹配的内容。
reg_name = re.compile(r'"name":"(.*?)"', re.S)  # 店名
reg_address = re.compile(r'"address":"(.*?)"', re.S)  # 地址
reg_phone = re.compile(r'"phone":"(.*?)"', re.S)  # 号码
reg_openTime = re.compile(r'"openTime":"(.*?)"', re.S)  # 营业时间


def get_page():
    api_url = base_url + '/meishi/api/poi/getPoiList'
    page = 1
    while True:
        params = {'cityName': '上海', 'page': page}
        s = requests.Session()
        s.get(base_url, headers=headers)
        resp = s.get(api_url, headers=headers, params=params)

        save_log(resp)

        page += 1
        resp_json = resp.json()
        data = resp_json.get('data')
        if not data or not data.get('poiInfos'):
            print("Complete!")
            break
        poi_infos = data.get('poiInfos')
        get_list(poi_infos)


def get_list(poi_infos):
    if poi_infos is None:
        return
    for info in poi_infos:
        get_detail(info)


def get_detail(info):
    if info is None or info.get('poiId') is None:
        return
    url = detail_url + str(info.get('poiId'))
    s = requests.Session()
    s.get(base_url, headers=headers)
    resp = s.get(url, headers=headers)

    save_log(resp)

    detail_info = reg_detailInfo.findall(resp.text)

    if detail_info:
        # name = reg_name.findall(detail_info[0])
        # address = reg_address.findall(detail_info[0])
        phone = reg_phone.findall(detail_info[0])
        open_time = reg_openTime.findall(detail_info[0])

        info['phone'] = phone
        info['openTime'] = open_time
        save_db(info)


def save_db(info):
    db_meishi.update({'poiId': info['poiId']}, info, True)


def save_log(response):
    print('fetch url -> {}'.format(response.url))
    info = {
        'url': response.url,
        'statusCode': response.status_code,
        'content': response.text,
        'uuid': response.cookies.get('uuid'),
        'date': datetime.datetime.now().isoformat()
    }
    db_log.save(info)
    time.sleep(0.5)


def run():
    get_page()


if __name__ == '__main__':
    print('start meituan spider...')
    run()
