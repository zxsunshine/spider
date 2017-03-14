#encoding=utf-8
import requests
import math

from information import Information
from bs4 import BeautifulSoup

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import os.path

from tornado.options import define, options
define("port", default=8102, help="run on the given port", type=int)


class SpiderPageHandler(tornado.web.RequestHandler):
    def get(self):
        #记录来访者ip地址
        file = open('ip.txt', 'a')
        file.write(self.request.remote_ip + "\n")
        file.close()
        display_data =  get_beauty_data()
        self.render('display.html', result_data = display_data)

def get_beauty_data():
    #get请求的url
    get_url = "http://news.family.baidu.com/topicComments?id=161988"
    #post请求的url
    post_url = "http://news.family.baidu.com/topicComments/commentlistpage"
    #请求的cookies字符串
    cookies_string = "BAIDUID=7C531FFC36A7174A4A31123722939D03:FG=1; BIDUPSID=7C531FFC36A7174A4A31123722939D03; PSTM=1483511531; BDUSS=UZ6ODJGT3FSUDB6cUluN35VTGp2NVd-NGI2b0FtSWx0dXdNZ2JzR0ZFT1B3NVpZSVFBQUFBJCQAAAAAAAAAAAEAAAC6~n8~eni3yczs0KHJ8cjLAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAI82b1iPNm9Ya; BDSFRCVID=XuKsJeCCxG3mLqnixyRMKnyO68FOsHk2Bc183J; H_BDCLCKID_SF=tRk8oIDaJCvbfP0k24rKhP4Dqxby26RtbIjdQb7a-JOq-JopMtOhJRL3hJnLK430bCD_QnT8MJnhHJuI5JOVBPt_hq3Ka4bXqCr03R722Ck2E4bRy4oTLnk1DUc8KUT0LD7PaRAbyCJiObjLqtjEqt0UQlteBjIqtn-t_I0hf-oqebT4btbMqRtthf5KeJ3KaKrKW5rJabC3o-5oKU6qLUtbQNbLWnoX26b8bq6catTcMCnDXnb1MTDY-NLOJMIEK5r2SCPbJDoP; MCITY=-214%3A131%3A; BDRCVFR[feWj1Vr5u3D]=I67x6TjHwwYf0; pgv_pvi=175635456; pgv_si=s6994757632; PSINO=1; H_PS_PSSID=1458_21127_21311_22035_20719; express.sid=s%3AFaBxxhq1Y_bQYGayOjze6PYtQOwXjEaN.thNrEM%2F4wRjJjvRrAhKuEfQdXwokhk1WWe4r34acEZU; Hm_lvt_e5c8f30b30415b1fc94d820ba9d4d08c=1488332177,1488356770,1488361174,1488361240; Hm_lpvt_e5c8f30b30415b1fc94d820ba9d4d08c=1488524690"
    cookies = {}
    for parameter in cookies_string.split(';'):
        name, value = parameter.strip().split('=', 1)
        cookies[name] = value
    #帖子评论首页的内容
    first_page_content = requests.get(get_url, timeout=30, cookies=cookies)
    first_page_soup = BeautifulSoup(first_page_content.text)
    comment_count = first_page_soup.select('input[name="commentCount"]')[0]['value']
    #分页数（向上取整）
    page_num = int(math.ceil(int(comment_count)/10.0))
    #初始化评论数组
    information_array = []
    first_page_comments = first_page_soup.select('div[class="list"]')[0]
    first_page_comments_list = first_page_comments.select('div[class="item"]')
    for first_page_comment in first_page_comments_list:
        extract_information =  extract_data(first_page_comment)
        if(extract_information==None):
            continue
        information_array.append(extract_information)
    loop_index = 2
    while loop_index<=page_num:
        send_data = {'page': loop_index, 'articleId':161988, 'pageSize':10}
        page_content = requests.post(post_url, timeout=30, cookies=cookies, data=send_data)
        page_soup = BeautifulSoup(page_content.text)
        page_comments = page_soup.select('div[class="list"]')[0]
        page_comments_list = page_comments.select('div[class="item"]')
        for page_comment in page_comments_list:
            extract_information = extract_data(page_comment)
            if(extract_information==None):
                continue
            information_array.append(extract_information)
        loop_index+=1
    information_array.sort(compare)
    return information_array

def extract_data(comment_data):
    #有些评论没有'title'属相。。。。这太匪夷所思了
    if 'title' in comment_data.select('span[class="name"]')[0].attrs:
        user_information = comment_data.select('span[class="name"]')[0]['title'] + '_' + comment_data.select('span[class="name"]')[0].string
    else:
        user_information = comment_data.select('span[class="name"]')[0].string
    user_floor = comment_data.select('span[class="floor"]')[0].string
    #用户评论目前不太好取出来，所以暂且不取评论内容，只将用户上传的图片取出来
    user_img_list = comment_data.select('img')
    #如果该用户没有上传图片，则不统计
    if(len(user_img_list)==0):
        return
    img_urls = []
    for img in user_img_list:
        img_urls.append(img['src'])
    liked_num = int(comment_data.select('span[class="supportComment"]')[0].select('em')[0].string)
    return Information(user_information, img_urls, liked_num, user_floor)

def compare(commentA, commentB):
    return commentB.getLikedNum() - commentA.getLikedNum()

if __name__ == '__main__':
    print('BEGIN SPIDER')
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[(r'/', SpiderPageHandler)],
        template_path=os.path.join(os.path.dirname(__file__), "templates")
    )
    http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()