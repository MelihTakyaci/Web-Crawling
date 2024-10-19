import scrapy
from scrapy_splash import SplashRequest

class HepsiburadaLaptopSpider(scrapy.Spider):
    name = "hepsiburada_laptops"
    allowed_domains = ["hepsiburada.com"]
    base_url = 'https://www.hepsiburada.com/laptop-notebook-dizustu-bilgisayarlar-c-98?sayfa='
    start_page = 5  # Start page
    end_page = 20  # End page
    max_total_products = 500  # Stop after collecting 500 products
    total_products_collected = 0  # Track total collected products

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 5,  # Daha uzun bekleme süresi
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 5,
        'AUTOTHROTTLE_MAX_DELAY': 60,  # Maksimum bekleme süresi artırıldı
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,  # Aynı anda daha az istek gönder
        'HTTPPROXY_ENABLED': False,
        'HTTPPROXY_PROXY': 'http://your_proxy_address:port',
        'ROBOTSTXT_OBEY': False,
        'SPLASH_URL': 'http://localhost:8050',
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
        -- Set headers to mimic real browser behavior
        splash:set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        splash:set_custom_headers({
            ['Accept-Language'] = 'en-US,en;q=0.9',
            ['Referer'] = 'https://www.google.com',
        })
        splash:init_cookies(splash.args.cookies)
        assert(splash:go(args.url))
        splash:wait(8)

        return {html = splash:html()}
    end
    """

    def start_requests(self):
        # Iterate over pages from ?sayfa=5 to ?sayfa=15
        for page_number in range(self.start_page, self.end_page + 1):
            url = f"{self.base_url}{page_number}"
            yield SplashRequest(
                url,
                self.parse,
                endpoint='execute',
                args={'lua_source': self.lua_script},
                splash_url='http://localhost:8050',
                headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.google.com',
                }
            )

    def parse(self, response):
        # Find all <ul> elements containing product lists
        ul_elements = response.css('ul.productListContent-frGrtf5XrVXRwJ05HUfU')
        
        # Collect product links from each <li> inside the <ul>
        for ul in ul_elements:
            li_elements = ul.css('li.productListContent-zAP0Y5msy8OHn5z7T_K_')
            for item in li_elements:
                if self.total_products_collected >= self.max_total_products:
                    return  # Stop once 500 products are collected

                # Extract the product link
                link = item.css('a.moria-ProductCard-gyqBb::attr(href)').get()
                if link:
                    self.total_products_collected += 1
                    # Follow the product link to scrape more data from the product page
                    product_url = response.urljoin(link)
                    yield SplashRequest(
                        url=product_url,
                        callback=self.parse_product_details,
                        endpoint='execute',
                        args={'lua_source': self.lua_script},
                        splash_url='http://localhost:8050',
                        headers={
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Referer': response.url,
                        },
                        meta={'product_url': product_url}
                    )

    def parse_product_details(self, response):
        product_url = response.meta['product_url']

        # Initialize the variables to store the extracted data
        islemci_tipi = None
        ssd_kapasitesi = None
        ram_sistem_bellek = None

        # Loop through each detail block
        product_details = response.css('div.jkj4C4LML4qv2Iq8GkL3')


        for detail in product_details:
            # Extract the label (text1)
            label = detail.css('div.OXP5AzPvafgN_i3y6wGp::text').get()
            value = detail.css('div.AxM3TmSghcDRH1F871Vh a::attr(title)').get()

            self.logger.info(f"Label: {label}, Value: {value}")

            if label and value:
                label = label.strip()
                value = value.strip()

                # If the label is "İşlemci Tipi", "SSD Kapasitesi" or "Ram (Sistem Belleği)", save the value
                if label == 'İşlemci Tipi':
                    islemci_tipi = value
                elif label == 'SSD Kapasitesi':
                    ssd_kapasitesi = value
                elif label == 'Ram (Sistem Belleği)':
                    ram_sistem_bellek = value

        # Yield the results
        yield {
            'product_url': product_url,
            'İşlemci Tipi': islemci_tipi,
            'SSD Kapasitesi': ssd_kapasitesi,
            'Ram (Sistem Belleği)': ram_sistem_bellek,
        }
