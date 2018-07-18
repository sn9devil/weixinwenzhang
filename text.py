from bs4 import BeautifulSoup
import requests

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4,zh-TW;q=0.2,mt;q=0.2',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Cookie': 'CXID=1B446AEB1D516FD5C765CE37868DCA1D; SUID=8C9E10743565860A5B4C06780003B8C5; SUV=00504AE374109E5F5B4D680A993BF652; ABTEST=0|1531819884|v1; IPLOC=CN4451; SNUID=D71998F3888DF6A614EEF7B3889DAD9A; JSESSIONID=aaahykvTDvD8R-ZaY7Gsw; ad=Iyllllllll2bFlBclllllVH2CFYlllllNxjW0lllll9lllll9ylll5@@@@@@@@@@; weixinIndexVisited=1; sct=1; ppinf=5|1531884187|1533093787|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZTowOnxjcnQ6MTA6MTUzMTg4NDE4N3xyZWZuaWNrOjA6fHVzZXJpZDo0NDpvOXQybHVDdzFUdmVWN2tVaTEyRk5WcndlLWV3QHdlaXhpbi5zb2h1LmNvbXw; pprdig=JKKPygKv7H7Co6cneyKbsXQ8QUUG1LwoV5MgwIaMBBFBV2rEuyGbkhtgql1UoHqJz5SyY5mCnPPUWZqtD6pgw--LWoYRTXTqCeyNamhAEW4EVYs5XW_MLh0OcUkXgv7DjiwCqNj3F7bxIpOjyE_RKMiBAP_OHlBre9MtNgwQwOs; sgid=25-36102587-AVtOsptgowqxnSJe555xWxw; ppmdig=15318841870000009e352764fcb282cd58c77e54dc783fdb',
    'Host': 'weixin.sogou.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
}

response = requests.get('http://weixin.sogou.com/weixin?query=NBA&type=2&page=10&ie=utf8',headers=headers)
# print(response.text)
doc = BeautifulSoup(response.text, 'lxml')
c = doc.select('#sogou_next')[0]['href']
print(c)