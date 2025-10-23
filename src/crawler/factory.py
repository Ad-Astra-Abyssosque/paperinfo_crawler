from .base_abstract_crawler import BaseAbstractCrawler


class CrawlerFactory:
    _crawlers = {}

    @classmethod
    def register(cls, name: str):
        def wrapper(crawler_class):
            if not issubclass(crawler_class, BaseAbstractCrawler):
                raise ValueError(f"{crawler_class} 必须继承自 BaseAbstractCrawler")
            cls._crawlers[name.lower()] = crawler_class
            return crawler_class

        return wrapper

    @classmethod
    def get_crawler(cls, crawler_type: str, **kwargs) -> BaseAbstractCrawler:
        crawler_type = crawler_type.lower()
        if crawler_type not in cls._crawlers:
            supported = list(cls._crawlers.keys())
            raise ValueError(f"不支持的爬虫类型: {crawler_type}. 支持的类型: {supported}")

        return cls._crawlers[crawler_type](**kwargs)


# 创建工厂单例
crawler_factory = CrawlerFactory()
get_crawler = crawler_factory.get_crawler
