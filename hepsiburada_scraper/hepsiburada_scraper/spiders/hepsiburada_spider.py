import scrapy
from scrapy_splash import SplashRequest

class HepsiburadaLaptopSpider(scrapy.Spider):
    name = "hepsiburada_laptops"
    allowed_domains = ["hepsiburada.com"]
    base_url = 'https://www.hepsiburada.com/laptop-notebook-dizustu-bilgisayarlar-c-98?sayfa='
    start_page = 5
    end_page = 20
    max_total_products = 500
    total_products_collected = 0

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 2,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'HTTPPROXY_ENABLED': True,
        'HTTPPROXY_PROXY': 'http://your_proxy_address:port',
        'ROBOTSTXT_OBEY': False,
        'SPLASH_URL': 'http://localhost:8051',  # Portu kontrol edin
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 1,
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
            'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
        },
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'FEED_EXPORT_ENCODING': 'utf-8',
    }

    lua_script = """
    function main(splash, args)
        splash:set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        splash:set_custom_headers({
            ['Accept-Language'] = 'en-US,en;q=0.9',
            ['Referer'] = 'https://www.google.com',
        })
        splash:init_cookies(splash.args.cookies)
        assert(splash:go(args.url))
        splash:wait(5)

        local click_more_button = splash:select('.moria-Button-bzoChi')
        local collected_products = 0
        local max_products = 500
        local scroll_to = splash:jsfunc("window.scrollTo")

        while collected_products < max_products and click_more_button do
            click_more_button:mouse_click()
            splash:wait(5)
            scroll_to(0, 1000)
            splash:wait(3)
            click_more_button = splash:select('.moria-Button-bzoChi')
            collected_products = splash:evaljs("document.querySelectorAll('li.productListContent-zAP0Y5msy8OHn5z7T_K_').length")
        end

        return {html = splash:html()}
    end
    """

    def start_requests(self):
        for page_number in range(self.start_page, self.end_page + 1):
            url = f"{self.base_url}{page_number}"
            yield SplashRequest(
                url,
                self.parse,
                endpoint='execute',
                args={'lua_source': self.lua_script},
                splash_url=self.custom_settings['SPLASH_URL'],
                headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.google.com',
                }
            )

    def parse(self, response):
        try:
            ul_elements = response.css('ul.productListContent-frGrtf5XrVXRwJ05HUfU')
            for ul in ul_elements:
                li_elements = ul.css('li.productListContent-zAP0Y5msy8OHn5z7T_K_')
                for item in li_elements:
                    if self.total_products_collected >= self.max_total_products:
                        return  # Stop once 500 products are collected

                    link = item.css('a.moria-ProductCard-gyqBb::attr(href)').get()
                    if link:
                        self.total_products_collected += 1
                        product_url = response.urljoin(link)
                        yield SplashRequest(
                            url=product_url,
                            callback=self.parse_product_details,
                            endpoint='execute',
                            args={'lua_source': self.lua_script},
                            splash_url=self.custom_settings['SPLASH_URL'],
                            headers={
                                'Accept-Language': 'en-US,en;q=0.9',
                                'Referer': response.url,
                            },
                            meta={'product_url': product_url}
                        )
        except Exception as e:
            self.logger.error(f"Hata parse ederken oluştu: {e}")

    def parse_product_details(self, response):
        try:
            product_url = response.meta['product_url']
            product_details = response.css('div.jkj4C4LML4qv2Iq8GkL3')

            child_1 = product_details.css('div:nth-child(1)::text').get()
            child_9 = product_details.css('div:nth-child(9)::text').get()
            child_17 = product_details.css('div:nth-child(17)::text').get()

            yield {
                'product_url': product_url,
                'child_1': child_1.strip() if child_1 else None,
                'child_9': child_9.strip() if child_9 else None,
                'child_17': child_17.strip() if child_17 else None,
            }
        except Exception as e:
            self.logger.error(f"Hata parse_product_details fonksiyonunda oluştu: {e}")
