import scrapy
import json
import re
import datetime
import logging

logger = logging.getLogger(__name__)


from zoneinfo import ZoneInfo
from scrapy.linkextractors import LinkExtractor
from scrapy.signals import spider_closed
from scrapy.signalmanager import dispatcher


class HIIKDefaultSpider(scrapy.Spider):
    name = "HIIK Default Spider"

    def __init__(
        self, start_urls: list[str], allowed_domains: list[str], *args, **kwargs
    ):
        logger.info("Initializing spider")
        super(HIIKDefaultSpider, self).__init__(*args, **kwargs)
        # Add spider close handler to save the found articles to a JSON file
        dispatcher.connect(self.spider_closing, signal=spider_closed)

        self.start_urls: list[str] = start_urls
        self.allowed_domains: list[str] = allowed_domains
        self.article_link_domains: list[str] = [
            "karennews.org/category/article",
            "karennews.org/2024",
        ]

        self.found_articles: dict[str, dict[str, str]] = {}
        self.content_class_article = "entry-content entry clearfix"
        self.content_class_list = "entry-content"

        self.visited_urls_this_scrape = set()

        logger.info("Loading visited URLs from JSON")
        # Load JSON file with URLs that we have already visited
        with open("visited_urls.json", "r") as f:
            self.visited_json_urls = json.load(f)

        logger.info("Spider initialized")

    def parse(self, response):
        article_links: set = set()

        url = response.url

        if (
            self.current_page_is_article(response)
            and url not in self.visited_json_urls
            and url not in self.visited_urls_this_scrape
        ):
            # Get content of the article on the page
            article_content = self.parse_article(response)

            # Add the article content to the list of found articles

            for supposed_article in article_content:
                # Get article:modified_time from meta property
                article_modified_time = response.xpath(
                    "//meta[@property='article:published_time']/@content"
                ).get()

                # Get the headline of the article
                headline = response.xpath("//h1/text()").get()

                # Get subheadline of the article
                subheadline = response.xpath("//h2/text()").get()

                # Get all paragraphs of the article
                paragraphs = response.xpath("//p/text()").getall()
                paragraph_text = "\n\n".join(paragraphs)

                # Add the article to the list of found articles
                article_dict = {
                    "url": url,
                    "accessing-date": str(datetime.datetime.now(datetime.UTC)),
                    "last-modification": article_modified_time,
                    "headline": headline,
                    "subheadline": subheadline,
                    "paragraphs": paragraph_text,
                }
                self.found_articles[url] = article_dict

                self.visited_urls_this_scrape.add(url)

        elif self.current_page_is_list(response):
            # Get content of the article on the page
            article_list = self.parse_article_list(response)

            for supposed_article in article_list:
                # Get the more link of the article
                more_link_url = self.get_url_in_article(supposed_article)
                if self.link_is_article(more_link_url):
                    article_links.add(more_link_url)

        # Extract all links from the page to find new article pages
        extracted_links = LinkExtractor(
            allow_domains=self.allowed_domains
        ).extract_links(response)
        # Filter out the article links
        article_links = article_links.union(
            set([link for link in extracted_links if self.link_is_article(link.url)])
        )

        # Follow the next article link
        for link in article_links:
            yield response.follow(link, callback=self.parse)

    def current_page_is_article(self, response):
        # Check if the current page is an article
        if response.xpath(f'//div[@class="{self.content_class_article}"]'):
            return True
        return False

    def current_page_is_list(self, response):
        # Check if the current page is a list of articles
        if response.xpath(f'//div[@class="{self.content_class_list}"]'):
            return True
        return False

    def parse_article(self, response):
        # Parse the article content
        # Mocked implementation
        return response.xpath(f'//div[@class="{self.content_class_article}"]').getall()

    def parse_article_list(self, response):
        # Parse the article content
        # Mocked implementation
        return response.xpath(f'//div[@class="{self.content_class_list}"]').getall()

    def link_is_article(self, url):
        # Check if the link is an article
        for article_link_domain in self.article_link_domains:
            if article_link_domain in url:
                return True

    def article_contains_more_link(self, article):
        # Check if the article contains a more link
        # Mocked implementation
        return "more-link button" in article

    def get_url_in_article(self, article):
        # Get the more link in the article
        url = re.findall(r'href="([^"]*)"', article)[0]
        return url

    def clean_text_from_html(self, text):
        # Clean the text from HTML tags
        # Mocked implementation
        return re.sub(r"<[^>]*>", "", text)

    def save_found_articles_to_json(self):
        json_file_name = "found_articles.json"

        # Save the found articles to a JSON file
        with open(json_file_name, "r") as f:
            data = json.load(f)

        data.update(self.found_articles)

        with open(json_file_name, "w") as f:
            json.dump(data, f, indent=4)

    def save_visited_urls_to_json(self):
        json_file_name = "visited_urls.json"

        self.visited_json_urls.extend(self.visited_urls_this_scrape)

        # Save the visited URLs to a JSON file
        with open(json_file_name, "w") as f:
            json.dump(list(self.visited_json_urls), f, indent=4)

    def spider_closing(self, spider):
        logger.info("Spider closing")

        logger.info(f"Saving visited URLs to JSON")
        self.save_visited_urls_to_json()

        logger.info(f"Saving found articles to JSON")
        self.save_found_articles_to_json()
