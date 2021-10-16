import request_utils
import json
import time
from bs4 import BeautifulSoup
from loguru import logger

FIRST_PAGE = "https://www.moneycontrol.com/news/tags/hot-stocks.html"
INDEX_URL = "https://www.moneycontrol.com/news/tags/hot-stocks.html/page-{page_number}/"
TOTAL_PAGES = 10  # todo: change this to exact number of changes


def get_index_page_posts(page_num):
    page_url = INDEX_URL.format(page_number=page_num) if page_num > 1 else FIRST_PAGE
    response = request_utils.get(page_url)
    soup = BeautifulSoup(response)
    items = soup.find("div", class_="topictabpane").ul.find_all("li", class_="clearfix")
    hotstocks_items = []
    for post in items:
        post_date = post.find("span").get_text()
        post_title = post.find("h2").a.attrs.get("title")
        post_link = post.find("h2").a.attrs.get("href")
        post_body = post.find("p").get_text()
        post_thumbnail_url = post.find("img").attrs.get("data")

        post_data = {
            "post_date": post_date,
            "post_title": post_title,
            "post_link": post_link,
            "post_body": post_body,
            "post_thumbnail_url": post_thumbnail_url,
        }
        logger.info(post_data)
        hotstocks_items.append(post_data)

    return hotstocks_items


def get_all_posts():
    all_posts = []
    for page_num in range(1, TOTAL_PAGES):
        all_posts += get_index_page_posts(page_num)

    with open("all_posts_data.json", "w") as f:
        json.dump(all_posts, f)


get_all_posts()
