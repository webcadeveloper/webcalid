import scrapy


class EoirSpiderSpider(scrapy.Spider):
    name = "eoir_spider"
    allowed_domains = ["acis.eoir.justice.gov"]
    start_urls = ["https://acis.eoir.justice.gov"]

    def parse(self, response):
        pass
