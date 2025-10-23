from .html_abstract_crawler import HtmlAbstractCrawler
from .factory import CrawlerFactory


@CrawlerFactory.register("usenix")
class UsenixAbstractCrawler(HtmlAbstractCrawler):

    @property
    def css_selector(self) -> str:
        return "div.content > div.field.field-name-field-paper-description.field-type-text-long.field-label-above:nth-child(2) > div.field-items > div.field-item.odd > p"



