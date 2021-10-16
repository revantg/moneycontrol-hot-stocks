import datetime
import json
import time
import requests
from loguru import logger

REQUEST_PADDING_S = 8
TIME_LAST_REQUESTED = datetime.datetime.now() - datetime.timedelta(
    seconds=REQUEST_PADDING_S
)


def stringify(obj: dict) -> dict:
    """turn every value in the dictionary to a string"""
    # yaha se chhapa h https://stackoverflow.com/a/59078968
    for k, v in obj.items():
        if isinstance(v, dict):
            # if value is a dictionary, stringifiy recursively
            stringify(v)
            continue
        if not isinstance(v, str):
            if isinstance(v, bool):
                # False/True -> false/true
                obj[k] = str(v).lower()
            else:
                obj[k] = str(v)
    return obj


session = requests.session()
with open("cookies.json", "r") as cookies_file:
    cookies_list = json.loads(cookies_file.read())
    cookie_jar = requests.utils.cookiejar_from_dict(stringify(cookies_list[0]))
    for cookie in cookies_list[1:]:
        requests.utils.add_dict_to_cookiejar(cookie_jar, stringify(cookie))
    session.cookies = cookie_jar


def get(request_url, headers=None, cookies=None, query_params=None):
    global TIME_LAST_REQUESTED
    current_time = datetime.datetime.now()
    if (current_time - TIME_LAST_REQUESTED).seconds < REQUEST_PADDING_S:
        time.sleep(REQUEST_PADDING_S - (current_time - TIME_LAST_REQUESTED).seconds)
    logger.info(
        f"Firing a GET request to {request_url} with headers={headers} cookies={cookies} query_params={query_params}"
    )
    response = session.get(
        request_url, headers=headers, params=query_params, cookies=cookies
    )
    TIME_LAST_REQUESTED = datetime.datetime.now()
    logger.debug(f"Received response = {response.text[:500]}...")
    return response.text
