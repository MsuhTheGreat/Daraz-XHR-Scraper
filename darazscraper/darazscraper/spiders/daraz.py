import scrapy
from urllib.parse import quote, urlencode
import logging
from darazscraper.settings import SCRAPING_ANT_API_KEY as API_KEY
from darazscraper.items import DarazscraperItem

logger = logging.getLogger(__name__)


class DarazSpider(scrapy.Spider):
    name = "daraz"
    allowed_domains = ['daraz.pk', 'api.scrapingant.com']
    
    search = "ear pods"
    modified_search = quote(search)
    target_url = f'https://daraz.pk/catalog/?q={modified_search}'

    page_no = 0
    
    selectors = {
        'products': '//div[@data-qa-locator="product-item"] | //div[@data-tracking="product-card"]',
        'title': './/a[not(./img)]/@title',
        'id': './@data-item-id',
        'price': './/span[contains(text(), "Rs")]',
        'sales': './/span[contains(text(), "sold")]',
        'region': './/div[.//span[contains(text(), "sold")]]/span',
        'url': './/a[not(./img)]/@href',
        'last_page': '//li[contains(@class, "ant-pagination-item")]'
    }


    def get_proxy_url(self, target_url):
        endpoint = "https://api.scrapingant.com/v2/general"
        
        params = [
            ("url", target_url),
            ("x-api-key", API_KEY),
            ("wait_until", "networkidle"),
            ("wait_for_selector", 'div[data-qa-locator="product-item"], div[data-tracking="product-card"]'),
            ("block_resource", "stylesheet"),
            ("block_resource", "image"),
            ("block_resource", "media"),
            ("block_resource", "font"),
            ("block_resource", "manifest"),
        ]
        
        proxy_url = f"{endpoint}?{urlencode(params)}"
        return proxy_url


    async def start(self):
        proxy_url = self.get_proxy_url(self.target_url)
        yield scrapy.Request(proxy_url, callback=self.parse)


    def parse(self, response):
        self.page_no += 1
        if self.page_no == 1:
            try: 
                self.last_page_no = int(response.xpath(self.selectors['last_page'])[-1].xpath('./a/text()').get(default="1").strip())
            except:
                self.last_page_no = 1        
        
        products = response.xpath(self.selectors['products'])
        
        for product in products:
            daraz_scraper_item = DarazscraperItem()
            
            daraz_scraper_item['title'] = product.xpath(self.selectors['title']).get(default="N/A")
            daraz_scraper_item['id'] = product.xpath(self.selectors['id']).get(default="N/A")
            
            try: daraz_scraper_item['price'] = product.xpath(self.selectors['price'])[0].xpath('./text()').get(default="N/A") 
            except: daraz_scraper_item['price'] = "N/A"
            
            try: daraz_scraper_item['sales'] = product.xpath(self.selectors['sales'])[0].xpath('./text()').get(default="N/A")
            except: daraz_scraper_item['sales'] = "N/A"
            
            try: daraz_scraper_item['region'] = product.xpath(self.selectors['region'])[-1].xpath('./@title').get(default="N/A")
            except: daraz_scraper_item['region'] = "N/A"

            daraz_scraper_item['url'] = 'https:' + product.xpath(self.selectors['url']).get(default="N/A")
            yield daraz_scraper_item
        
        if self.page_no < self.last_page_no:
            next_page_url = f'https://www.daraz.pk/catalog/?page={self.page_no+1}&q={self.modified_search}'
            logger.info(f"Following next page link: {next_page_url}")
            yield scrapy.Request(self.get_proxy_url(next_page_url), callback=self.parse)
        else:
            logger.error(f"I suppose all pages have been scraped. for instance, {self.page_no} pages were scraped.")
