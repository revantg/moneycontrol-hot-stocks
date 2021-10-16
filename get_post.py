import os
import request_utils
import json
from bs4 import BeautifulSoup
from loguru import logger


def get_number(string):
    return "".join(list(filter(lambda x: x == "." or x.isnumeric(), string)))


def get_stock_symbols(soup):
    try:
        string = (
            soup.find("div", class_="content_wrapper arti-flow")
            .find_all("script")[0]
            .text.split("\n", 2)[0]
        )

        string = string[string.index("[") : string.index("]") + 1]
        stocks_data = json.loads(string)
        logger.info(f"MoneyControl stock symbol data = {stocks_data}")
        return stocks_data
    except Exception as E:
        logger.exception(E)
        logger.exception(E.__traceback__)
        return None


def get_metadata(soup):
    for script in soup.find_all("script")[:4]:
        try:
            json_data = json.loads(script.text.replace("\r", "").replace("\n", ""))
            if "articleBody" in json_data[0]:
                logger.debug(f"Found metadata={json_data}")
                return json_data
            else:
                raise ValueError()
        except Exception as E:
            logger.debug(E.__traceback__)
            continue
    logger.error("Did not find any metadata")
    return None


def get_tags(soup):
    tags = soup.find("div", class_="tags_first_line").find_all("a")
    logger.debug(f"Found {tags=}")
    return [{"name": tag.text, "link": tag.attrs.get("href")} for tag in tags]


def get_author(soup):
    name = soup.find("div", "article_author").text.strip()
    designation = soup.find("div", class_="designation")
    designation = designation.text if designation else None
    logger.debug(f"Author details: {name=} {designation=}")
    return {"name": name, "designation": designation}


def get_related_stories(soup):
    related_stories = soup.find("div", class_="related_stories_left_block").ul.find_all(
        "li"
    )
    logger.debug(f"Found {related_stories=}")
    return [
        {"link": story.a.attrs.get("href"), "title": story.a.attrs.get("title")}
        for story in related_stories
    ]


def get_call_data(call_element):
    parts = call_element.text.split("|")
    logger.debug(f"Split into parts={parts}")
    if len(parts) <= 2:
        logger.debug(f"Did not find any call data. Split parts <= 2. {parts=}")
        return {}

    link = call_element.attrs.get("href")
    if link is None:
        logger.debug(f"Did not find any link in {call_element}")
        return None
    logger.debug(f"Link found = {link}")

    call_type = None
    ltp = None
    target = None
    stop_loss = None
    upside_potential = None

    stock_name = parts[0]
    if "buy" in parts[1].lower() or "sell" in parts[1].lower():
        call_type = "buy" if "buy" in parts[1].lower() else "sell"
        ltp = get_number(parts[2])
        target = get_number(parts[3])
        stop_loss = get_number(parts[4])
        upside_potential = parts[5]
    else:
        call_type = "buy"
        ltp = get_number(parts[1])
        target = get_number(parts[2])
        stop_loss = get_number(parts[3])
        upside_potential = parts[4]

    logger.debug(
        f"{call_type=} {stock_name=} {ltp=} {target=} {stop_loss=} {upside_potential=}"
    )

    return {
        "call_type": call_type,
        "stock_name": stock_name,
        "ltp": ltp,
        "target": target,
        "stop_loss": stop_loss,
        "upside_potential": upside_potential,
    }


def get_calls(soup):
    stock_calls = soup.find_all("strong")
    stock_calls = soup.find_all(
        "a",
        {
            "href": lambda x: x
            and x.startswith("https://www.moneycontrol.com/india/stockpricequote/")
        },
    )

    calls_data = []
    for stock in stock_calls:
        logger.debug(f"Getting calls for {stock}")
        # call_element = stock.find('a')
        call_element = stock
        if call_element is None:
            logger.debug(
                f"Did not find any call in {stock}. Did not find any anchor element"
            )
            return {}
        calls_data.append(get_call_data(call_element))

    return calls_data


def get_post(post_data):
    response = request_utils.get(post_data.get("post_link"))
    soup = BeautifulSoup(response)

    content = soup.find("div", class_="content_wrapper arti-flow")
    author = get_author(soup)
    title = soup.find("h1", class_="article_title artTitle").text
    description = soup.find("h2", class_="article_desc").text
    published_at = soup.find("div", class_="article_schedule").text
    metadata = get_metadata(soup)
    tags = get_tags(soup)
    related_stories = get_related_stories(soup)
    moneycontrol_stock_ids = get_stock_symbols(content)

    calls_data = get_calls(content)
    # stock_calls = content.find_all("strong")

    # calls_data = [get_call_data(call_string) for call_string in stock_calls]
    assert len(calls_data) > 0

    return {
        "metadata": metadata,
        "author": author,
        "title": title,
        "description": description,
        "published_at": published_at,
        "tags": tags,
        "related_stories": related_stories,
        "moneycontrol_stock_ids": moneycontrol_stock_ids,
        "calls_data": calls_data,
    }


with open("all_posts_data.json", "r") as f:
    posts_data = json.loads(f.read())

for post in posts_data:
    logger.info(f"Getting data for {post}")
    if f"{post['post_id']}.json" in os.listdir("success") or post['post_id'] in ['6876331']:
        logger.info(f"skipping {post['post_id']} as it has already succeeded")
        continue
    logger_id = logger.add(
        f"all_logs/{post['post_id']}.log", backtrace=True, diagnose=True
    )
    try:
        scraped_data = get_post(post)
        with open(f"success/{post['post_id']}.json", "w") as f:
            json.dump(scraped_data, f)
    except Exception as E:
        logger.exception(E)
        logger.exception(E.__traceback__)
        with open(f"failed/{post['post_id']}", "w") as f:
            f.write("")
    logger.remove(logger_id)
