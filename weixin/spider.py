from requests import Session
from weixin.config import *
from weixin.db import RedisQueue
from weixin.mysql import MySQL
from weixin.request import WeixinRequset
from urllib.parse import urlencode
import requests
from bs4 import BeautifulSoup
from requests import ReadTimeout, ConnectionError


class Spider():
    base_url = 'http://weixin.sogou.com/weixin'
    keyword = 'NBA'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4,zh-TW;q=0.2,mt;q=0.2',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': 'CXID=1B446AEB1D516FD5C765CE37868DCA1D; SUID=8C9E10743565860A5B4C06780003B8C5; SUV=00504AE374109E5F5B4D680A993BF652; ABTEST=0|1531819884|v1; IPLOC=CN4451; SNUID=D71998F3888DF6A614EEF7B3889DAD9A; JSESSIONID=aaahykvTDvD8R-ZaY7Gsw; ad=Iyllllllll2bFlBclllllVH2CFYlllllNxjW0lllll9lllll9ylll5@@@@@@@@@@; weixinIndexVisited=1; sct=1; ppinf=5|1531884187|1533093787|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZTowOnxjcnQ6MTA6MTUzMTg4NDE4N3xyZWZuaWNrOjA6fHVzZXJpZDo0NDpvOXQybHVDdzFUdmVWN2tVaTEyRk5WcndlLWV3QHdlaXhpbi5zb2h1LmNvbXw; pprdig=JKKPygKv7H7Co6cneyKbsXQ8QUUG1LwoV5MgwIaMBBFBV2rEuyGbkhtgql1UoHqJz5SyY5mCnPPUWZqtD6pgw--LWoYRTXTqCeyNamhAEW4EVYs5XW_MLh0OcUkXgv7DjiwCqNj3F7bxIpOjyE_RKMiBAP_OHlBre9MtNgwQwOs; sgid=25-36102587-AVtOsptgowqxnSJe555xWxw; ppmdig=153190021100000074f921db30dd23e8562dd7af293cd8fb',
        'Host': 'weixin.sogou.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:54.0) Gecko/20100101 Firefox/54.0'
    }
    session = Session()
    queue = RedisQueue()
    mysql = MySQL()

    def get_proxy(self):
        """
        从代理池获取代理
        :return:
        """
        try:
            response = requests.get(PROXY_POOL_URL)
            if response.status_code == 200:
                print('Get Proxy', response.text)
                return response.text
            return None
        except requests.ConnectionError:
            return None

    def parse_index(self, response):
        """
        解析索引页
        :param response: 响应
        :return: 新的响应
        """
        doc = BeautifulSoup(response.text, 'lxml')
        items = doc.select('h3 a')
        for item in items:
            url = item['href']
            weixin_request = WeixinRequset(url=url, callback=self.parse_detail)
            yield weixin_request
        print(response.text)
        next = doc.select('#sogou_next')[0]['href']
        print(next)
        if next:
            url = self.base_url + str(next)
            weixin_request = WeixinRequset(url=url, callback=self.parse_index, need_proxy=True)
            yield weixin_request

    def parse_detail(self, response):
        """
        解析详情页
        :param response:响应
        :return: 微信公众号文章
        """
        doc = BeautifulSoup(response.text, 'lxml')
        data = {
            'title': doc('.rich_media_title').text(),
            'content': doc('.rich_media_content').text(),
            'date': doc('#post-date').text(),
            'nickname': doc('#js_profile_qrcode > div > strong').text(),
            'wechat': doc('#js_profile_qrcode > div > p:nth-child(3) > span').text()
        }
        yield data

    def start(self):
        """
        初始化工作
        :return:
        """
        self.session.headers.update(self.headers)
        start_url = self.base_url + '?' + urlencode({'query': self.keyword, 'type': 2})
        weixin_request = WeixinRequset(url=start_url, callback=self.parse_index, need_proxy=True)
        # 添加第一个请求
        self.queue.add(weixin_request)

    def request(self, weixin_request):
        """
        执行请求
        :param weixin_request: 请求
        :return: 响应
        """
        try:
            if weixin_request.need_proxy:
                proxy = self.get_proxy()
                if proxy:
                    proxies = {
                        'http': 'http://' + proxy,
                        'https': 'https://' + proxy,
                    }
                    return self.session.send(weixin_request.prepare(),
                                             timeout=weixin_request.timeout, allow_redirects=False, proxies=proxies)

            return self.session.send(weixin_request.prepare(), timeout=weixin_request.timeout, allow_redirects=False)
        except (ConnectionError) as e:
            print(e.args)
            return False

    def error(self, weixin_request):
        """
        错误处理
        :param weixin_request:
        :return:
        """
        weixin_request.fail_time = weixin_request.fail_time + 1
        print('Request Failed', weixin_request.fail_time, 'Times', weixin_request.url)
        if weixin_request.fail_time < MAX_FAILED_TIME:
            self.queue.add(weixin_request)

    def schedule(self):
        """
        调度请求
        :return:
        """
        while not self.queue.empty():
            weixin_request = self.queue.pop()
            callback = weixin_request.callback
            print('Schedule', weixin_request.url)
            response = self.request(weixin_request)
            print(response)
            # print(type(response))
            # print(response.text)
            # print('11111111')
            if response and response.status_code in VALID_STATUSES:
                results = list(callback(response))
                if results:
                    for result in results:
                        print('New Result', type(result))
                        if isinstance(result, WeixinRequset):
                            self.queue.add(result)
                        if isinstance(result, dict):
                            self.mysql.insert('articles', result)
                else:
                    self.error(weixin_request)
            else:
                self.error(weixin_request)

    def run(self):
        """

        :return:
        """
        self.start()
        self.schedule()

if __name__ == '__main__':
    spider = Spider()
    spider.run()
