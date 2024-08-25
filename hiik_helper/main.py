from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from spiders.hiik_default_spider import HIIKDefaultSpider


def main():
    start_urls = ["https://karennews.org/"]
    allowed_domains = ["karennews.org"]
    settings = get_project_settings()

    settings.set(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    )

    runner = CrawlerProcess(settings=settings)
    runner.crawl(
        HIIKDefaultSpider,
        start_urls=start_urls,
        allowed_domains=allowed_domains,
    )
    runner.start()


if __name__ == "__main__":
    main()
