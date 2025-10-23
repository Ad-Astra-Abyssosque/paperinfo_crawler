from .uiautomation_abstract_crawler import UiAutomationAbstractCrawler
from .factory import CrawlerFactory


@CrawlerFactory.register("ieee")
class IEEEAbstractCrawler(UiAutomationAbstractCrawler):

    def __init__(self, interval: float):
        super().__init__(interval)
        # self._headless_browser: bool = True

    async def _crawl_by_uiautomation(self, url: str) -> str:
        # "Show More" button of abstract
        button_css_selector = "a.abstract-text-view-all"
        css_selector = "div[xplmathjax]"

        # 访问目标网页
        tab = await self._driver.get(url)
        await tab.wait(5)
        await tab.wait_for(selector=css_selector, timeout=self._timeout)

        if await tab.query_selector(button_css_selector) is not None:
            show_more_button = await tab.select(button_css_selector)
            await show_more_button.click()
            await tab.wait(3)
            await tab.get_content()

        abs_elem = await tab.select(css_selector)
        abstract = abs_elem.text_all
        return abstract
