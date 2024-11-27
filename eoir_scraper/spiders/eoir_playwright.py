import scrapy
from scrapy_playwright.page import PageCoroutine

class EoirPlaywrightSpider(scrapy.Spider):
    name = "eoir_playwright"
    allowed_domains = ["acis.eoir.justice.gov"]
    start_urls = ["https://acis.eoir.justice.gov/en/"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_coroutines": [PageCoroutine("wait_for_selector", ".some-selector")]
                },
                callback=self.parse
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        await page.wait_for_selector(".some-selector")

        title = response.css("title::text").get()
        links = response.css("a::attr(href)").getall()

        yield {
            "title": title,
            "links": links,
            "url": response.url,
        }
