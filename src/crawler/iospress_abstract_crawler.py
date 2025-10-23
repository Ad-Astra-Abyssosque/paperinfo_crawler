from .uiautomation_abstract_crawler import UiAutomationAbstractCrawler
from .factory import CrawlerFactory


@CrawlerFactory.register("iospress")
class IospressAbstractCrawler(UiAutomationAbstractCrawler):

    async def _crawl_by_uiautomation(self, url: str) -> str:
        button_css_selector = "button[id='onetrust-reject-all-handler']"
        css_selector = "section[id='abstract'] > div[role='paragraph']"

        tab = await self._driver.get(url)
        await tab.wait(5)

        if await tab.query_selector(button_css_selector) is not None:
            cookie_policy_button = await tab.select(button_css_selector)
            await cookie_policy_button.click()

        await tab.wait_for(selector=css_selector, timeout=self._timeout)
        await tab.get_content()

        abs_elems = await tab.select_all(css_selector)
        abstract = " ".join(abs_elem.text_all for abs_elem in abs_elems)
        return abstract