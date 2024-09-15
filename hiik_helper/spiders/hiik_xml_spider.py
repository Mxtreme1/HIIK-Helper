import scrapy
import json
import re
import datetime
import logging

import scrapy.spiders

logger = logging.getLogger(__name__)


from zoneinfo import ZoneInfo
from scrapy.linkextractors import LinkExtractor
from scrapy.signals import spider_closed
from scrapy.signalmanager import dispatcher


class HiikXmlSpider(scrapy.spiders.XMLFeedSpider):
    name = "HIIK XML Spider"

    def __init__(
        self, start_urls: list[str], allowed_domains: list[str], *args, **kwargs
    ):
        logger.info("Initializing spider")
        super(scrapy.spiders.XMLFeedSpider, self).__init__(*args, **kwargs)
        # Add spider close handler to save the found articles to a JSON file
        dispatcher.connect(self.spider_closing, signal=spider_closed)

        self.start_urls: list[str] = start_urls
        self.allowed_domains: list[str] = allowed_domains

        # Define the iterator and tag name
        # iterator = "iternodes"  # This is actually unnecessary, since it's the default value
        itertag = "item"  # Adjust this to match your XML structure
        # namespaces = [("ns", "http://example.com/namespace")]  # Example namespace

    # def parse_node(self, response, node):
    #     # Save all links from the XML feed
    #     links = node.xpath("ns:link/text()", namespaces=self.namespaces).getall()

    #     yield {
    #         "title": node.xpath("ns:title/text()", namespaces=self.namespaces).get(),
    #         "link": node.xpath("ns:link/text()", namespaces=self.namespaces).get(),
    #     }

    def parse_node(self, response, node):
        self.logger.info(
            "Hi, this is a <%s> node!: %s", self.itertag, "".join(node.getall())
        )

        return {
            "title": node.xpath("ns:title/text()", namespaces=self.namespaces).get(),
            "link": node.xpath("ns:link/text()", namespaces=self.namespaces).get(),
        }
    
    def spider_closing(self):
        # logger.info("Saving found articles to JSON")
        # with open("found_articles.json", "w") as f:
        #     json.dump(self.found_articles, f)
        # logger.info("Saved found articles to JSON")
        pass
