import logging
from abc import abstractmethod
from .base_abstract_crawler import BaseAbstractCrawler
import asyncio
import zendriver as zd
from src.settings import chrome_path, cookie_path
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from zendriver import Browser


class UiAutomationAbstractCrawler(BaseAbstractCrawler):

    def __init__(self, interval):
        super().__init__(interval)
        self._headless_browser:bool = False
        self._need_webdriver: bool = True
        self._driver: Optional[Browser] = None
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(False)
        self._timeout: int = 60
        self.__logger = logging.getLogger("UiAutomationAbstractCrawler")

    def prepare(self):
        if self._need_webdriver:
            self.__logger.debug(f"cookie: {cookie_path}")
            self.__logger.debug(f"chrome: {chrome_path}")
            browser_config = zd.Config(
                headless=self._headless_browser,
                user_data_dir=cookie_path,
                browser_executable_path=chrome_path,
                no_sandbox=True,
            )
            self._driver = self.loop.run_until_complete(zd.start(config=browser_config))

    def stop(self):
        if self._need_webdriver and self._driver and not self._driver.stopped:
            self.loop.run_until_complete(self._driver.stop())

    def crawl(self, url: str) -> str:
        if url == '':
            return ''

        res = ''
        max_tries = 3
        for i in range(0, max_tries):
            try:
                res = self.loop.run_until_complete(self._crawl_by_uiautomation(url))
            except asyncio.TimeoutError:
                self.__logger.warning(f"Time out when requesting {url}")
            except zd.core.connection.ProtocolException as e:
                self.__logger.warning(f"{e}")

            if len(res) > 0:
                break
            else:
                self.__logger.info("Try another time")
        return res

    @abstractmethod
    async def _crawl_by_uiautomation(self, url: str) -> str:
        pass
