import scrapy
from scrapy_splash import SplashRequest

class HepsiburadaLaptopSpider(scrapy.Spider):
    name = "hepsiburada_laptops"
    allowed_domains = ["hepsiburada.com"]
    start_urls = [
        'https://www.hepsiburada.com/laptop-notebook-dizustu-bilgisayarlar-c-98'
    ]

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 2,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'ROBOTSTXT_OBEY': False,
        'SPLASH_URL': 'http://localhost:8050',
    }

    lua_script = """
    function main(splash, args)
        splash:set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        splash:init_cookies(splash.args.cookies)
        assert(splash:go(args.url))
        splash:wait(5)

        local scroll_to = splash:jsfunc("window.scrollTo")
        local get_height = splash:jsfunc("function() {return document.body.scrollHeight;}")
        local prev_height = 0
        local curr_height = get_height()
        local scroll_attempts = 0
        local max_scroll_attempts = 10
        local prev_ul_count = 0

        -- Function to count the number of <ul> elements with class 'productListContent-frGrtf5XrVXRwJ05HUfU'
        local function count_ul_elements()
            return splash:evaljs("document.querySelectorAll('ul.productListContent-frGrtf5XrVXRwJ05HUfU').length")
        end

        -- Keep track of the <ul> count and stop when no new <ul> is loaded
        while scroll_attempts < max_scroll_attempts do
            scroll_to(0, curr_height)  -- Scroll down
            splash:wait(5)  -- Wait for new products to load
            
            -- Check the number of <ul> elements with class 'productListContent-frGrtf5XrVXRwJ05HUfU'
            local ul_count = count_ul_elements()
            
            -- Stop if the <ul> count doesn't increase after scrolling
            if ul_count == prev_ul_count then
                break
            end

            -- Update scroll height and <ul> count
            prev_ul_count = ul_count
            prev_height = curr_height
            curr_height = get_height()

            scroll_attempts = scroll_attempts + 1
        end

        return {html = splash:html()}
    end
    """

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(
                url, 
                self.parse, 
                endpoint='execute', 
                args={'lua_source': self.lua_script}, 
                splash_url='http://localhost:8050'
            )

    def parse(self, response):
        # This part ensures we scrape all products from each <ul> element
        product_links = []

        # Find all <ul> elements that load products
        ul_elements = response.css('ul.productListContent-frGrtf5XrVXRwJ05HUfU')
        
        for ul in ul_elements:
            # Get all product links from within each <ul> element
            for item in ul.css('li.productListContent-zAP0Y5msy8OHn5z7T_K_'):
                link = item.css('a.moria-ProductCard-gyqBb::attr(href)').get()
                if link:
                    product_links.append(response.urljoin(link))

        # Check if no product links were found
        if not product_links:
            self.logger.warning("No product links found on the page!")
        else:
            self.logger.info(f"Found {len(product_links)} product links on the page.")
            
        # Limit the number of product links to 208
        product_links = product_links[:208]

        # Yield the links as items
        for link in product_links:
            yield {
                'product_link': link
            }
