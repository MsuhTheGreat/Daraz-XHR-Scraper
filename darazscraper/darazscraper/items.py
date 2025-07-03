# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DarazscraperItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    id = scrapy.Field()
    price = scrapy.Field()
    region = scrapy.Field()
    sales = scrapy.Field()
    url = scrapy.Field()
