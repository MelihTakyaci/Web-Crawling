import scrapy
from scrapy_splash import SplashRequest

class HepsiburadaLaptopSpider(scrapy.Spider):
    name = "hepsiburada_laptops"
    allowed_domains = ["hepsiburada.com"]
    base_url = 'https://www.hepsiburada.com/laptop-notebook-dizustu-bilgisayarlar-c-98?sayfa='
    start_page = 5  # Start page
    end_page = 15  # End page
    max_total_products = 500  # Stop after collecting 500 products
    total_products_collected = 0  # Track total collected products

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
        splash:wait(5)

        local click_more_button = splash:select('.moria-Button-bzoChi')
        local collected_products = 0
        local max_products = 500
        local scroll_to = splash:jsfunc("window.scrollTo")
        local product_loaded = false

        -- Continue clicking the button and scraping the products until we reach 500 items
        while collected_products < max_products and click_more_button do
            -- Click the "Load More" button
            click_more_button:mouse_click()
            splash:wait(5)  -- Wait for new content to load

            -- Scroll a little to ensure the new content is visible
            scroll_to(0, 1000)
            splash:wait(3)

            -- Check again if the button is still present
            click_more_button = splash:select('.moria-Button-bzoChi')

            -- Evaluate the number of products on the page (this part will count the <li> elements with the product class)
            collected_products = splash:evaljs("document.querySelectorAll('li.productListContent-zAP0Y5msy8OHn5z7T_K_').length")
        end

        -- Return the HTML after scrolling and clicking
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
        # Scrape data from product page
        product_url = response.meta['product_url']

        # Fetching child(1), child(9), and child(17) from the required div
        product_details = response.css('div.jkj4C4LML4qv2Iq8GkL3')

        # Get the required children (child(1), child(9), child(17))
        child_1 = product_details.css('div:nth-child(1)::text').get()
        child_9 = product_details.css('div:nth-child(9)::text').get()
        child_17 = product_details.css('div:nth-child(17)::text').get()

        yield {
            'product_url': product_url,
            'child_1': child_1.strip() if child_1 else None,
            'child_9': child_9.strip() if child_9 else None,
            'child_17': child_17.strip() if child_17 else None,
        }