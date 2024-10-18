import scrapy
from scrapy_splash import SplashRequest

class HepsiburadaLaptopSpider(scrapy.Spider):
    name = "hepsiburada_laptops"
    allowed_domains = ["hepsiburada.com"]
    start_urls = [
        'https://www.hepsiburada.com/laptop-notebook-dizustu-bilgisayarlar-c-98?sayfa=5'
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
      splash:wait(3)

      local scroll_to = splash:jsfunc("window.scrollTo")
      local get_height = splash:jsfunc("function() {return document.body.scrollHeight;}")
      local prev_height = 0
      local curr_height = get_height()
      local scroll_count = 0

      -- Sayfanın sonuna kadar kaydır ve 47 ürün alınıncaya kadar devam et
      while curr_height > prev_height and scroll_count < 20 do
          scroll_to(0, curr_height)
          splash:wait(3)
          prev_height = curr_height
          curr_height = get_height()
          scroll_count = scroll_count + 1
      end
      
      return {html = splash:html()}
    end
    """

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, endpoint='execute', args={'lua_source': self.lua_script}, splash_url='http://localhost:8050')

    def parse(self, response):
        # Get all product links from the <li> elements with the specified class
        product_list_items = response.css('li.productListContent-zAP0Y5msy8OHn5z7T_K_')
        product_links = []
        
        for item in product_list_items:
            link = item.css('a.moria-ProductCard-gyqBb::attr(href)').get()
            if link:
                product_links.append(response.urljoin(link))

        if not product_links:
            self.logger.warning("No product links found on the page!")
        else:
            self.logger.info(f"Found {len(product_links)} product links on the page.")
            
        # Limit the number of product links to 47
        product_links = product_links[:47]

        # Save product links to JSON
        for link in product_links:
            yield {
                'product_link': link
            }
