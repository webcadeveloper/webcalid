# settings.py

# Configuración general de Scrapy
BOT_NAME = 'eoir_scraper'

SPIDER_MODULES = ['eoir_scraper.spiders']
NEWSPIDER_MODULE = 'eoir_scraper.spiders'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Usar Playwright como el downloader middleware
DOWNLOADER_MIDDLEWARES = {
    'scrapy_playwright.middleware.PlaywrightMiddleware': 1,
}

# Usar Chromium para el scraping
PLAYWRIGHT_BROWSER_TYPE = 'chromium'
PLAYWRIGHT_LAUNCH_OPTIONS = {'headless': True}

# Configuración de Scrapy para manejar el contenido dinámico
DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS = 8
FEED_EXPORT_ENCODING = 'utf-8'

# Exportar los resultados a un archivo JSON
FEED_FORMAT = 'json'
FEED_URI = 'results.json'

# Configuración de caché para evitar descargar la misma página repetidamente
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400
HTTPCACHE_IGNORE_HTTP_CODES = [403, 500, 502, 503, 504]

# Activar AutoThrottle para limitar la tasa de peticiones
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
