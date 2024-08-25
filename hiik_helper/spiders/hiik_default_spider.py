import scrapy
import re
from scrapy.linkextractors import LinkExtractor
from urllib import parse


class HIIKDefaultSpider(scrapy.Spider):
    name = "HIIK Default Spider"

    def __init__(
        self, start_urls: list[str], allowed_domains: list[str], *args, **kwargs
    ):
        super(HIIKDefaultSpider, self).__init__(*args, **kwargs)
        self.start_urls: list[str] = start_urls
        self.allowed_domains: list[str] = allowed_domains
        self.article_link_domains: list[str] = [
            "karennews.org/category/article",
            # "karennews.org/202",
        ]
        self.found_articles: list[str] = []
        self.content_class_article = "entry-content entry clearfix"
        self.content_class_list = "entry-content"

    def parse(self, response):
        article_links: set = set()

        # Get content of the article on the page
        article_content = self.parse_article(response)

        if self.current_page_is_article(response):
            # Add the article content to the list of found articles

            for supposed_article in article_content:
                # Get all paragraphs of the article
                paragraphs = response.xpath("//p")
                article_text = "\n".join(paragraphs.getall())

                # Add the article to the list of found articles
                self.found_articles.append(article_text)

        elif self.current_page_is_list(response):
            for supposed_article in article_content:
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

    def link_is_article(self, url):
        # Check if the link is an article
        for article_link_domain in self.article_link_domains:
            if article_link_domain in url:
                return True

    def save_found_articles_to_json(self):
        # Save the found articles to a JSON file
        # Mocked implementation
        with open("found_articles.json", "w") as f:
            f.write(self.found_articles)

    def parse_article(self, response):
        # Parse the article content
        # Mocked implementation
        return response.xpath(f'//div[@class="{self.content_class}"]').getall()

    def article_contains_more_link(self, article):
        # Check if the article contains a more link
        # Mocked implementation
        return "more-link button" in article

    def get_url_in_article(self, article):
        # Get the more link in the article
        url = re.findall(r'href="([^"]*)"', article)[0]
        return url
