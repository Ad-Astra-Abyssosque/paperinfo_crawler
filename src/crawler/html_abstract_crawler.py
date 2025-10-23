import logging
from abc import abstractmethod
from .base_abstract_crawler import BaseAbstractCrawler
import requests
from bs4 import BeautifulSoup
from src.settings import req_headers
from src.request_wrap import make_request


class HtmlAbstractCrawler(BaseAbstractCrawler):

    def __init__(self, interval: float):
        super().__init__(interval)
        self._abs_session = requests.Session()
        self.__logger = logging.getLogger("HtmlAbstractCrawler")

    @property
    @abstractmethod
    def css_selector(self) -> str:
        pass

    def stop(self):
        self._abs_session.close()

    def crawl(self, url: str) -> str:
        css_selector = self.css_selector
        abstract = self._request_and_parse(url, css_selector)
        return abstract

    def _request_and_parse(self, url: str, css_selector: str) -> str:
        abstract = ''

        if url == "":
            return ''

        # self.__logger.debug(f"request: {url}")
        self.__logger.debug(f"css selector: {css_selector}")
        res = make_request(self._abs_session, url, headers=req_headers)
        # 请求失败
        if res is None:
            return ''

        if res.status_code != 200:
            self.__logger.warning(
                "Cannot access {} , status code: {}.".format(url, res.status_code)
            )
        else:
            abs_soup = BeautifulSoup(res.text, "html.parser")
            abs_tags = abs_soup.select(css_selector)
            if abs_tags:
                abstract = " ".join([abs_tag.get_text() for abs_tag in abs_tags])

        return abstract
