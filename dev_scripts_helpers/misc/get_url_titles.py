import time
from html.parser import HTMLParser
from typing import Optional

import requests
from bs4 import BeautifulSoup


def get_page_title(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title_tag = soup.find("title")
        return title_tag.string.strip() if title_tag else "No <title> tag found"
    except requests.RequestException as e:
        return f"Request failed: {e}"


# #############################################################################
# TitleParser
# #############################################################################


class TitleParser(HTMLParser):

    def __init__(self) -> None:
        super().__init__()
        self.in_title: bool = False
        self.title: Optional[str] = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, Optional[str]]]
    ) -> None:
        if tag.lower() == "title":
            self.in_title = True

    def handle_data(self, data: str) -> None:
        if self.in_title and self.title is None:
            self.title = data.strip()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False


def get_title_streaming(url: str) -> str:
    try:
        with requests.get(url, stream=True, timeout=10) as r:
            r.raise_for_status()
            parser = TitleParser()
            for chunk in r.iter_content(chunk_size=1024, decode_unicode=True):
                parser.feed(chunk)
                if parser.title:
                    break
            return parser.title if parser.title else "No <title> tag found"
    except requests.RequestException as e:
        return f"Request failed: {e}"


if __name__ == "__main__":
    files: str = """
https://news.ycombinator.com/item?id=34336386
https://news.ycombinator.com/item?id=29671450
https://news.ycombinator.com/item?id=22778089
https://news.ycombinator.com/item?id=23331989
https://news.ycombinator.com/item?id=34801636
https://news.ycombinator.com/item?id=30371723
https://news.ycombinator.com/item?id=26953352
https://news.ycombinator.com/item?id=23209142
    """
    url_list: list[str] = files.split("\n")

    for url in url_list:
        # title = get_page_title(url)
        title: str = get_title_streaming(url)
        print("%s,%s" % (url, title))
        time.sleep(2)
