#!/usr/bin/pyhton3
# coding=utf-8

import aiohttp
import json
import asyncio
import datetime


class TicketMonitor:
    """
    火车票监控，可监控多个
    """
    @staticmethod
    def start(args):
        """
        参数格式为: [{'from': 'BJP', 'to': 'SHH', 'date': '2017-10-10'}]
        :param args:
        :return:
        """
        loop = asyncio.get_event_loop()
        tasks = []
        for arg in args:
            tasks.append(asyncio.ensure_future(TicketMonitor(arg['from'], arg['to'], arg['date']).start_monitor()))

        loop.run_until_complete(asyncio.wait(tasks))

    def __init__(self, from_station, to_station, date):
        self.base_url = 'http://mobile.12306.cn/weixin/leftTicket/query?leftTicketDTO.train_date={}' \
                        '&leftTicketDTO.from_station={}&leftTicketDTO.to_station={}&purpose_codes=ADULT'
        self.from_station = from_station
        self.to_station = to_station
        self.date = date
        self.url = self.base_url.format(date, from_station, to_station)
        self.continue_find = True
        self.base_msg = '你关注的日期为{} 车次 {} 的 {}有票了\n'
        self.msg = ''
        self.count = 0
        self.try_number = 5
        self.error_count = 0
        self.seat_dict = {
            'gg_num': '--',
            'gr_num': '高软',
            'qt_num': '--',
            'rz_num': '软座',
            'tz_num': '--',
            'wz_num': '无座',
            'yb_num': '--',
            'yw_num': '硬卧',
            'yz_num': '硬座',
            'ze_num': '二等座',
            'zy_num': '一等座',
            'swz_num': '商务座'
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'}

    async def fetch(self):
        self.count += 1
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.url, headers=self.headers) as resp:
                    print('{}第{}次监控,状态{}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                 self.count, resp.status))
                    return await resp.text()
            except Exception as e:
                print(e)
                if self.error_count <= self.try_number:
                    self.error_count += 1
                    self.fetch()
                else:
                    self.continue_find = False
                    print(e)
                    return str(e)

    @staticmethod
    def validate_response(html):
        try:
            json_html = json.loads(html)
        except Exception as e:
            print(e)
            return False
        else:
            if json_html['data'] is None:
                return False
        return True

    async def parse(self):
        html = await self.fetch()
        print(html)
        # 验证数据
        while not self.validate_response(html):
            self.error_count += 1
            if self.error_count > self.try_number:  # 错误尝试次数过多，停止监控
                self.continue_find = False
                self.msg = "数据异常,数据结果为<{}>".format(html)
                return

        json_html = json.loads(html)
        self.error_count = 0

        for ticket_info in json_html['data']:
            self.has_ticket(ticket_info)

    def has_ticket(self, ticket_info):
        for key in self.seat_dict.keys():
            if ticket_info[key] != '无' and ticket_info[key] != '--':  # 软卧
                self.msg = self.msg + self.base_msg.format(self.date, ticket_info['station_train_code'],
                                                           self.seat_dict.get(key))
                self.continue_find = False

    async def start_monitor(self):
        while self.continue_find:
            await asyncio.sleep(0.25)
            await self.parse()
        print(self.msg)
        self.send_mail()

    def send_mail(self):
        from email.header import Header
        from email.mime.text import MIMEText
        from email.utils import parseaddr, formataddr

        import smtplib

        smtp_server = 'smtp.163.com'
        from_addr = 'admin@qq.com'
        password = '*****'
        to_addr = 'admin@qq.com'

        def _format_addr(s):
            name, addr = parseaddr(s)
            return formataddr((Header(name, 'utf-8').encode(), addr))

        msg = MIMEText(self.msg, 'plain', 'utf-8')
        msg['From'] = _format_addr('余票监控 <%s>' % from_addr)
        msg['To'] = _format_addr('<%s>' % to_addr)

        if self.error_count >= self.try_number:  # 错误
            msg['Subject'] = Header('火车票监控出错了...', 'utf-8').encode()
        else:
            msg['Subject'] = Header('你关注的火车票有票了...', 'utf-8').encode()

        server = smtplib.SMTP(smtp_server, 25)
        server.set_debuglevel(1)
        server.login(from_addr, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())
        server.quit()


if __name__ == '__main__':
    TicketMonitor.start([{'from': 'BJP', 'to': 'SHH', 'date': '2017-10-07'}])
