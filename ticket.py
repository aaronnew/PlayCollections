#!/usr/bin/pyhton3
# coding=utf-8

import aiohttp
import json
import asyncio
import datetime

HTTP_STATUS_CODES_TO_RETRY = [500, 502, 503, 504]


class FailedRequest(Exception):
    """
    A wrapper of all possible exception during a HTTP request
    """
    code = 0
    message = ''
    url = ''
    raised = ''

    def __init__(self, *, raised='', message='', code='', url=''):
        self.raised = raised
        self.message = message
        self.code = code
        self.url = url

        super().__init__("code:{c} url={u} message={m} raised={r}".format(
            c=self.code, u=self.url, m=self.message, r=self.raised))


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
            tasks.append(
                asyncio.ensure_future(
                    TicketMonitor(arg['from'], arg['to'], arg['date'], arg.get('train')).start_monitor()))

        loop.run_until_complete(asyncio.wait(tasks))

    def __init__(self, from_station, to_station, date, train):
        self.base_url = 'https://train.qunar.com/dict/open/s2s.do?dptStation={}' \
                        '&arrStation={}&date={}&user=neibu&source=site'
        self.from_station = from_station
        self.to_station = to_station
        self.date = date
        self.url = self.base_url.format(from_station, to_station, date)
        self.continue_find = True
        self.base_msg = '你关注的日期为{} 车次 {} 的 {}有票了, 还剩 {} 张\n'
        self.msg = ''
        self.count = 0
        self.try_number = 5
        self.error_count = 0
        self.filter_train = train
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.35'
        }

    async def fetch(self):
        self.count += 1

        attempt = 5
        read_timeout = 5
        raised_exc = None
        async with aiohttp.ClientSession() as session:
            while attempt != 0:
                try:
                    with aiohttp.Timeout(timeout=read_timeout):
                        async with session.get(self.url, headers=self.headers) as response:
                            print('{}第{}次监控,状态{}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                         self.count, response.status))
                            if response.status == 200:
                                return await response.text()
                            elif response.status in HTTP_STATUS_CODES_TO_RETRY:
                                raise aiohttp.errors.HttpProcessingError(
                                    code=response.status, message=response.reason)
                            else:
                                return await response.text()
                except (aiohttp.ClientError,
                        aiohttp.ClientOSError,
                        aiohttp.ServerTimeoutError,
                        asyncio.TimeoutError) as exc:
                    try:
                        code = exc.code
                    except AttributeError:
                        code = ''
                    raised_exc = FailedRequest(code=code, message=exc, url=self.url,
                                               raised=exc.__class__.__name__)
                else:
                    raised_exc = None
                    break
                attempt -= 1
        if raised_exc:
            self.msg = "error,{}".format(raised_exc)
            self.send_mail()
            raise raised_exc

    @staticmethod
    def validate_response(html):
        try:
            json_html = json.loads(html)
            if json_html['data'] is None or json_html['data']['s2sBeanList'] is None:
                return False
        except Exception as e:
            return False
        return True

    async def parse(self):
        html = await self.fetch()
        print(html)
        # 验证数据
        if not self.validate_response(html):
            self.error_count += 1
            if self.error_count > self.try_number:  # 错误尝试次数过多，停止监控
                self.continue_find = False
                self.msg = "数据异常,数据结果为<{}>".format(html)
            return

        json_html = json.loads(html)
        self.error_count = 0

        for ticket_info in json_html['data']['s2sBeanList']:
            self.has_ticket(ticket_info)

    def has_ticket(self, ticket_info):
        seats = ticket_info['seats']
        for seat_type in seats.keys():
            seat_num = seats[seat_type].get('count', 0)

            if self.filter_train:  # 开启了过滤车次
                if self.filter_train.get(ticket_info['trainNo']):  # 当前车次是过滤车次
                    if len(self.filter_train.get(ticket_info['trainNo']).keys()) != 0:  # 监控特定坐席
                        tmp = self.filter_train[ticket_info['trainNo']].get(seat_type, -1)
                        if seat_num <= tmp:  # 是否为当前车次
                            self.msg = self.msg + self.base_msg.format(self.date, ticket_info['trainNo'],
                                                                       seat_type, seat_num)
                            self.continue_find = False
                            break
                    else:  # 不监控特定坐席
                        if seat_num > 0:
                            self.msg = self.msg + self.base_msg.format(self.date, ticket_info['trainNo'],
                                                                       seat_type, seat_num)
                            self.continue_find = False
                            break
            else:  # 未开启过滤车次
                if seat_num > 0:
                    self.msg = self.msg + self.base_msg.format(self.date, ticket_info['trainNo'],
                                                               seat_type, seat_num)
                    self.continue_find = False
                    break

    async def start_monitor(self):
        while self.continue_find:
            await asyncio.sleep(1)
            await self.parse()
        print(self.msg)
        self.send_mail()

    def send_mail(self):
        from email.header import Header
        from email.mime.text import MIMEText
        from email.utils import parseaddr, formataddr

        import smtplib

        smtp_server = '*****'
        from_addr = '*****'
        password = '****'
        to_addr = '*****'

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
    TicketMonitor.start([
        {'from': '北京', 'to': '上海', 'date': '2017-10-07'},
        {'from': '北京', 'to': '上海', 'date': '2017-10-09',
         'train': {
             'K1108': {
                 '硬座': 100  # 硬座剩余数量低于100 大于 0报警, 默认只要大于0就报警
             }
         }
         }
    ])
