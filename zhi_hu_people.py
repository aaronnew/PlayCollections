# coding=utf-8
from selenium import webdriver
from bs4 import BeautifulSoup
import urllib.request
import html.parser


class UserImages:
    """
    根据知乎用户username，下载该用户所有回答中的图片
    """

    driver = webdriver.PhantomJS()  # 打开浏览器
    base_url = "https://www.zhihu.com"
    base_answer_url = base_url + '/people/{username}/answers'
    base_page_url = base_url + '/people/{username}/answers?page={page}'
    answer_urls = []
    count = 0

    @classmethod
    def __get_html(cls, url):
        print("fetch url -->", url)
        cls.driver.get(url)
        return cls.driver.page_source

    @classmethod
    def __get_page_number(cls, htm):
        html_soup = BeautifulSoup(htm, 'html.parser')
        pages = html_soup.find_all("button", class_="PaginationButton")
        if len(pages) > 0:
            return int(pages[-2].text)
        return 1

    @classmethod
    def __get_answer_url(cls, htm):
        html_soup = BeautifulSoup(htm, 'html.parser')
        answers = html_soup.find_all(attrs={"data-za-detail-view-element_name": "Title"})
        urls = []
        for ans in answers:
            urls.append(cls.base_url + ans.attrs['href'])
        return urls

    @classmethod
    def get_all_answer_url(cls, username):
        url = cls.base_answer_url.format(username=username)
        htm = cls.__get_html(url)
        cls.answer_urls += cls.__get_answer_url(htm)

        number = cls.__get_page_number(htm)
        for index in range(2, number + 1):
            htm = cls.__get_html(cls.base_page_url.format(username=username, page=index))
            cls.answer_urls += cls.__get_answer_url(htm)
        print("all answers url is ", cls.answer_urls)

    @classmethod
    def find_and_save_images(cls, url):
        result_raw = cls.__get_html(url)  # 这是原网页 HTML 信息
        result_soup = BeautifulSoup(result_raw, 'html.parser')

        no_script_nodes = result_soup.find_all('noscript')  # 找到所有<noscript>node
        no_script_inner_all = ""
        for no_script in no_script_nodes:
            no_script_inner = no_script.get_text()  # 获取<noscript>node内部内容
            no_script_inner_all += no_script_inner + "\n"

        no_script_all = html.parser.unescape(no_script_inner_all)  # 将内部内容转码并存储

        img_soup = BeautifulSoup(no_script_all, 'html.parser')
        img_nodes = img_soup.find_all('img')
        for img in img_nodes:
            if img.get('src') is not None:
                img_url = img.get('src')
                print("save image --> ", img_url)
                cls.count += 1
                urllib.request.urlretrieve(img_url, "./output/image/" + str(cls.count) + ".jpg")  # 一个一个下载图片

    @classmethod
    def get_all_images(cls, username):
        cls.get_all_answer_url(username)
        for url in cls.answer_urls:
            cls.find_and_save_images(url)

if __name__ == '__main__':
    UserImages.get_all_images("wu-yue-38-96")
