from .html_abstract_crawler import HtmlAbstractCrawler
from .factory import CrawlerFactory


@CrawlerFactory.register("ndss")
class NDSSAbstractCrawler(HtmlAbstractCrawler):

    @property
    def css_selector(self) -> str:
        return "div.entry-content > div.paper-data > p:nth-child(2) > p"



