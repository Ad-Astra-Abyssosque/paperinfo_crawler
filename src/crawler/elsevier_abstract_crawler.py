from .uiautomation_abstract_crawler import UiAutomationAbstractCrawler
from .factory import CrawlerFactory


@CrawlerFactory.register("elsevier")
class ElsevierAbstractCrawler(UiAutomationAbstractCrawler):

    async def _crawl_by_uiautomation(self, url: str) -> str:
        css_selector = "div.abstract.author > div > div"

        # 访问目标网页
        tab = await self._driver.get(url)
        await tab.wait(5)
        await tab.wait_for(selector=css_selector, timeout=self._timeout)
        await tab.get_content()

        abs_elems = await tab.select_all(css_selector)
        abstract = " ".join(abs_elem.text_all for abs_elem in abs_elems)
        return abstract


