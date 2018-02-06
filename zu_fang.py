# coding: utf-8

import requests
from pymongo import MongoClient
import json
import time
from bs4 import BeautifulSoup
from raven import Client
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
}

client = MongoClient()
db = client.house
collection = db.room


def get_mogo():
    """
    蘑菇公寓
    :return:
    """
    url = 'http://www.mogoroom.com/list'
    page = 1
    id = 1
    headers['cookies'] = 'gr_user_id=b9aa0347-8938-4de8-9ebc-c97c8d21b7fe; UM_distinctid=15f6baa20f659-07fcf34b9d40b5-31657c00-13c680-15f6baa20f723a; hadoop_renter_key=c8e1d53f-d676-4d3b-b9fc-d42cb09870ae; sajssdk_2015_cross_new_user=1; nice_id9d030e80-e73e-11e5-b771-11c8f335ec09=c5bb52b3-bd2f-11e7-b1e7-c31ba49b12da; qimo_seosource_9d030e80-e73e-11e5-b771-11c8f335ec09=%E7%AB%99%E5%86%85; qimo_seokeywords_9d030e80-e73e-11e5-b771-11c8f335ec09=; accessId=9d030e80-e73e-11e5-b771-11c8f335ec09; JSESSIONID=61296B508A6847287558EAB51544BBBF-n1; CNZZDATA1253147438=957311629-1509334538-null%7C1509361566; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2215f6baa8dc78da-037606a33820c2-31657c00-1296000-15f6baa8dc89ba%22%2C%22%24device_id%22%3A%2215f6baa8dc78da-037606a33820c2-31657c00-1296000-15f6baa8dc89ba%22%2C%22props%22%3A%7B%22%24latest_referrer%22%3A%22%22%2C%22%24latest_referrer_host%22%3A%22%22%7D%7D; gr_session_id_aca7dc2ea0f02f49=44df7ed7-429b-4494-a71a-7a8f6ae2a98e; JSESSIONID=61296B508A6847287558EAB51544BBBF-n1'
    while True:
        # time.sleep(3)
        params = {"page": page}
        response = requests.post(url, headers=headers, timeout=100, params=params)
        print("url", response.url)
        d = json.loads(response.text, encoding="UTF-8")
        if d is None or (not d.get('roomInfos')) or len(d.get('roomInfos', [])) == 0:
            break

        for room in d['roomInfos']:

            room['origin'] = 'mogo'
            room['rentType'] = room['rentType']['value']
            collection.update({'roomId': room['roomId']}, room, True)
        id += 1
        page += 1
    print("id = {}, page = {}".format(id, page))


def get_ziroom():
    url = 'http://sh.ziroom.com/z/nl/z2.html'
    page = 1
    while True:
        if page >= 50:
            break

        params = {'p': page}
        resp = requests.get(url, headers=headers, timeout=100, params=params)
        print("url", resp.url)
        if resp.status_code != 200 or not resp.text:
            raise RuntimeError('返回数据失败,page={},status={},html={}'.format(page, resp.status_code, resp.text))
        with open('a.html', 'w') as f:
            f.write(resp.text)
        soup = BeautifulSoup(resp.text, 'html.parser')
        house_list = soup.select("ul#houseList > li.clearfix")
        for house in house_list:
            if house.find(class_='clearfix zry'):
                continue

            room = {
                'roomId': re.findall(r'(\d+)', house.select_one('.txt h3 a')['href'])[0],
                'title': house.select_one('.txt h3 a').text,
                'detail': {
                    "area": house.select('.txt .detail span')[0].text,
                    'floor': house.select('.txt .detail span')[1].text,
                    'houseType': house.select('.txt .detail span')[2].text,
                },
                'rentType': house.select('.txt .detail span')[3].text,
                'metroInfo': [house.select('.txt .detail span')[4].text],
                'showPrice': re.findall(r'(\d+)', house.select_one('.priceDetail .price').text)[0],
                'districtName': re.findall(r'\[(\S+)\]', house.select_one('.txt h4').text)[0],
                'image': house.select_one('.img.pr a img')['_src'],
                'origin': 'ziroom',
            }

            collection.update({'roomId': room['roomId']}, room, True)

        time.sleep(3)
        page += 1


def main():
    total = collection.count()
    print("total", total)
    while True:
        get_ziroom()
        get_mogo()
        count = collection.count()
        print("total", total)
        if total == count or count > 100000:
            break
        total = count


def update():
    rooms = collection.find({'origin': 'ziroom'})
    for room in rooms:
        room['rentType'] = room['rentType'][0]
        collection.save(room)


if __name__ == '__main__':
    client = Client('https://409c169cc67c461cbdcc7bafa2655446:e1d36cde7b6341448d2dbe06dca64b18@sentry.io/237753')
    main()
    # update()
