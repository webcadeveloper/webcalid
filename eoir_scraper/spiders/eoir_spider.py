import scrapy
from scrapy_playwright.page import PageMethod

class EoirSpider(scrapy.Spider):
    name = 'eoir_spider'
    start_urls = ['https://acis.eoir.justice.gov']

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_playwright.middleware.PlaywrightMiddleware': 1,
        },
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {'headless': True},
    }

    async def parse(self, response):
        page = response.meta['playwright_page']

        # Espera a que el contenido dinámico se cargue (ajusta el selector según necesites)
        await page.wait_for_selector('selector_del_elemento')

        # Obtén el contenido de la página después de la carga dinámica
        content = await page.content()

        # Ahora parsea el contenido HTML como normalmente lo harías en Scrapy
        response = scrapy.Selector(text=content)

        # Aquí puedes extraer los datos que necesitas
        # Ejemplo de cómo extraer datos, ajusta los selectores a lo que necesites
        item = {
            'titulo': response.css('h1::text').get(),
            'fecha': response.css('span.fecha::text').get(),
            # Agrega más campos según los datos que quieras obtener
        }

        yield item

        # Si tienes múltiples páginas o quieres seguir enlaces, usa la lógica correspondiente
        # Por ejemplo:
        # next_page = response.css('a.next::attr(href)').get()
        # if next_page:
        #     yield response.follow(next_page, self.parse)
