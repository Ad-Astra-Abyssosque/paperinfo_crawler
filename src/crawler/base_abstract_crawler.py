from abc import ABC, abstractmethod


class BaseAbstractCrawler(ABC):
    def __init__(self, interval: float):
        self._req_itv: float = interval

    def prepare(self):
        pass

    @abstractmethod
    def crawl(self, url: str) -> str:
        pass

    def stop(self):
        pass

