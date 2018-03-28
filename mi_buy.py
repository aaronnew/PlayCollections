# coding=utf-8


import requests


class MiBuy(object):
    ADD_CART_URL = 'https://m.mi.com/v1/cart/add'
    SEL_CART_URL = 'https://m.mi.com/v1/cart/selcart'
    DEL_CART_URL = 'https://m.mi.com/v1/cart/del'
    SUBMIT_ORDER_URL = 'https://m.mi.com/v1/order/submitPay'
    session = requests.Session()

    def __init__(self, client_id, cookie):
        self.client_id = client_id
        self.cookie = cookie
        self.session.headers.update({
            "Host": "m.mi.com",
            "User-Agent": "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Cookie": self.cookie
        })

    def __make_referer__(self, cookie, referer):
        self.session.headers.update({
            "Referer": referer,
        })

    def __post__(self, url, referer, payload={}):
        self.__make_referer__(cookie, referer)
        if payload is None:
            payload = {}
        payload['client_id'] = self.client_id
        payload['webp'] = 0
        return self.session.post(url, data=payload)

    def add_cart(self, product_id, referer):
        payload = {
            "product_id": product_id
        }
        resp = self.__post__(self.ADD_CART_URL, referer, payload).json()
        if resp.get('code', -1) != 0:
            print("商品加入购物车失败,原因:{}".format(resp.get('description')))
            return False
        else:
            print("商品加入购物车成功,目前数量是{}".format(resp.get("data", dict()).get('count', -1)))
        return True

    def sel_cart(self, product_id):
        payload = {
            "sel_itemid_list": [product_id+"_0_buy"],
            "sel_status": 1
        }
        referer = 'https://m.mi.com/cart'
        resp = self.__post__(self.SEL_CART_URL, referer, payload).json()
        if resp.get('code', -1) != 0:
            print("勾选商品失败,原因:{}".format(resp.get('description')))
            return False
        return True

    def del_cart(self, product_id):
        referer = 'https://m.mi.com/cart'
        payload = {
            "itemId": product_id + '_0_buy',
        }
        resp = self.__post__(self.DEL_CART_URL, referer, payload).json()
        if resp.get('code', -1) != 0:
            print("购物车删除失败,原因:{}".format(resp.get('description')))
            return False
        else:
            print('购物车删除成功')
            return True

    def show_cart(self):
        url = 'https://m.mi.com/v1/cart/index'
        referer = 'https://m.mi.com/user'
        self.__post__(url, referer)

    def submit_order(self):
        # 提交订单前需要先访问我的购物车页面, 以获取最新cookie
        self.show_cart()
        referer = 'https://m.mi.com/order/checkout?address_id='
        payload = {
            'address_id': 10170406550072356,
            'best_time': 1,
            'channel_id': 0,
            'pay_id': 1,
            'paymethod': 'alipaywap',
            'invoice_email': 'tenlee2012@163.com',
            'invoice_tel': '176****7879',
            'invoice_title': '个人',
            'invoice_type': '4',
        }
        resp = self.__post__(self.SUBMIT_ORDER_URL, referer, payload).json()
        if resp.get('code', -1) != 0:
            print("订单提交失败,原因:{}".format(resp.get('description')))
            return False
        else:
            print('订单提交成功，请到APP或者web页面查看')
            return True


if __name__ == '__main__':
    # 黑色 6+64 2181000001
    # 白色 6+64 2181000002
    # 黑色 6+128 2181000003
    # 白色 6+128 2181000004
    # 黑色 8+256 2181000005
    # 白色 8+256 2181000006
    good_id = input("输入商品ID:")
    cookie = input("输入Cookie(从浏览器复制):")
    client_id = 180100031051
    mi_buy = MiBuy(client_id, cookie)

    # 先将该商品从购物车清空
    mi_buy.del_cart(good_id)

    # 加入购物车
    referer = 'https://m.mi.com/commodity/detail/7153'
    mi_buy.add_cart(good_id, referer)

    # 提交订单
    mi_buy.submit_order()

