# coding=utf-8


import requests
import logging
import time

logging.basicConfig(
    # filename='mi_buy.log',
    level=logging.INFO,
    format='%(levelname)s:%(asctime)s:%(message)s'
)


class MiBuyError(IOError):
    pass


class MiBuy(object):
    ADD_CART_URL = 'https://m.mi.com/v1/cart/add'
    SEL_CART_URL = 'https://m.mi.com/v1/cart/selcart'
    DEL_CART_URL = 'https://m.mi.com/v1/cart/del'
    SUBMIT_ORDER_URL = 'https://m.mi.com/v1/order/submitPay'
    ADDRESS_URL = 'https://m.mi.com/v1/address/list'
    CHECKOUT_URL = 'https://m.mi.com/v1/order/checkout'
    session = requests.Session()

    def __init__(self, client_id, cookie):
        self.cookie = cookie
        self.client_id = client_id
        self.address_id = None
        self.paymethod = 'alipaywap'
        self.invoice_email = None
        self.invoice_tel = None
        self.invoice_title = None
        self.invoice_type = None
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
        resp = self.session.post(url, data=payload)
        logging.debug("url=[{}],status_code=[{}],data=[{}]".format(resp.url, resp.status_code, resp.text))
        return resp

    def add_cart(self, product_id, referer):
        payload = {
            "product_id": product_id
        }
        resp = self.__post__(self.ADD_CART_URL, referer, payload).json()
        if resp.get('code', -1) != 0:
            raise MiBuyError("商品加入购物车失败,原因:{}".format(resp.get('description')))
        logging.info("商品加入购物车成功,目前数量是{}".format(resp.get("data", dict()).get('count', -1)))

    def sel_cart(self, product_id):
        payload = {
            "sel_itemid_list": [product_id+"_0_buy"],
            "sel_status": 1
        }
        referer = 'https://m.mi.com/cart'
        resp = self.__post__(self.SEL_CART_URL, referer, payload).json()
        if resp.get('code', -1) != 0:
            raise MiBuyError("勾选商品失败,原因:{}".format(resp.get('description')))

    def del_cart(self, product_id):
        referer = 'https://m.mi.com/cart'
        payload = {
            "itemId": product_id + '_0_buy',
        }
        resp = self.__post__(self.DEL_CART_URL, referer, payload).json()
        if resp.get('code', -1) != 0:
            raise MiBuyError("购物车删除失败,原因:{}".format(resp.get('description')))
        logging.info('购物车删除成功')

    def show_cart(self):
        url = 'https://m.mi.com/v1/cart/index'
        referer = 'https://m.mi.com/user'
        self.__post__(url, referer)

    def show_all_address(self):
        referer = 'https://m.mi.com/order/checkout?address_id='
        resp = self.__post__(self.ADDRESS_URL, referer).json()
        if resp.get('code', -1) != 0 or not resp.get('data'):
            raise MiBuyError("获取收货地址失败,原因:{}".format(resp.get('description')))
        data = resp.get('data')
        print('请选择收货地址(输入收货地址ID):')
        for address in data:
            print("ID:{address_id},地址:{province} {city} {district} {area} {address} {consignee} {tel}".format(**address))
        self.address_id = input()

    def get_delivery(self):
        '''
        获取配送地址，发票信息
        :return:
        '''
        referer = 'https://m.mi.com/cart?from=product&address_id='
        resp = self.__post__(self.CHECKOUT_URL, referer).json()
        if resp.get('code', -1) != 0:
            raise MiBuyError("获取收货地址发票失败,原因:{}".format(resp.get('description')))
        else:
            data = resp.get('data', {})
            self.address_id = data.get('address', {}).get('address_id')
            address = data.get('address', {}).get('address')
            self.invoice_email = data.get('default_invoice_email')
            self.invoice_tel = data.get('default_invoice_tel')
            self.invoice_title = data.get('default_invoice_title')
            self.invoice_type = data.get('default_invoice_type')
            logging.info('获取收货地址发票成功,地址为{},发票邮箱:{},抬头:{}'.format(address, self.invoice_email, self.invoice_title))

    def submit_order(self):
        # 提交订单前需要先访问我的购物车页面, 以获取最新cookie
        self.show_cart()
        referer = 'https://m.mi.com/order/checkout?address_id='
        payload = {
            'address_id': self.address_id,
            'best_time': 1,
            'channel_id': 0,
            'pay_id': 1,
            'paymethod': self.paymethod,
            'invoice_email': 'tenlee2012@163.com',
            'invoice_tel': '176****7879',
            'invoice_title': '个人',
            'invoice_type': '4',
        }
        resp = self.__post__(self.SUBMIT_ORDER_URL, referer, payload).json()
        if resp.get('code', -1) != 0:
            raise MiBuyError("订单提交失败,原因:{}".format(resp.get('description')))
        else:
            logging.info('订单提交成功，请到APP或者web页面查看并付款')

    def buy(self, product_id, product_url):
        while True:
            try:
                # 先将该商品从购物车清空
                mi_buy.del_cart(product_id)

                # 加入购物车
                mi_buy.add_cart(product_id, product_url)

                # 获取默认地址发票等
                mi_buy.get_delivery()

                # 提交订单
                mi_buy.submit_order()
            except MiBuyError as e:
                print(e)
            else:
                break
            time.sleep(0.5)


if __name__ == '__main__':
    # mix 2s 黑色     6+64   2181000001
    # mix 2s 白色     6+64   2181000002
    # mix 2s 黑色     6+128  2181000003
    # mix 2s 白色     6+128  2181000004
    # mix 2s 黑色     8+256  2181000005
    # mix 2s 白色     8+256  2181000006
    # mix 2  黑色陶瓷 6+64   2174200042
    input("订单配送地址为设置的默认收货地址，发票也为默认的发票信息，如果不同修改请至小米商城修改(ps:订单提交成功后,也是支持修改收货地址的),如果你已悉知，请输入任意字符")
    cookie = input("输入cookie:")
    client_id = input("输入clientId:")
    mi_buy = MiBuy(client_id, cookie)
    product_id = input("输入购买的商品ID:")
    product_id = '2174200042'
    product_url = 'https://m.mi.com/commodity/detail/7153'
    mi_buy.buy(product_id, product_url)



