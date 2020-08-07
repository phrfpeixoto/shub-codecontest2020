import re

import urllib.parse as urlparse

import scrapy

from codecontest2020.items import Codecontest2020Item


class ContestSpider(scrapy.Spider):
    name = 'contest'
    start_urls = ['http://ec2-34-235-144-255.compute-1.amazonaws.com:18881/clickhere']

    def parse(self, response, **kwargs):  # Parse a paged query

        parsed_url = urlparse.urlparse(response.url)
        url_query = urlparse.parse_qs(parsed_url.query)
        cur_page = url_query.setdefault('page', ['0'])
        cur_page = int(cur_page.pop())

        elements = response.xpath(
            '//section[@id="gtco-practice-areas"]'
            '//div[contains(concat(" ",normalize-space(@class)," ")," gtco-practice-area-item ")]'
            '//div[@class="gtco-copy"]//a/@href'
        )
        for elm in elements:
            yield response.follow(url=elm.get(), callback=self.parse_item)
        next_page_element = response.xpath(
            '//div[@class="row"][@align="center"]'
            '//a[last()]'
        )
        next_page_url = next_page_element.xpath("@href").get()

        parsed_url = urlparse.urlparse(next_page_url)
        url_query = urlparse.parse_qs(parsed_url.query)
        next_page = url_query.setdefault('page', ['0'])
        next_page = int(next_page.pop())

        if next_page > cur_page:
            yield response.follow(next_page_url)

    def parse_item(self, response, **kwargs):
        name_element = response.xpath(
            '//section[@id="gtco-about"]'
            '//h2[contains(concat(" ",normalize-space(@class)," ")," heading-colored ")]'
        )

        img_shadow = name_element.xpath('../..//div[@class="img-shadow"]')
        image_src = img_shadow.xpath("img/@src").get()
        image_uuid = None
        if image_src:
            image_uuid = image_src[5:-4]
        elif len(img_shadow.xpath('div[@id="mainimage"]')):
            match = re.search(r'i\.src = \'/gen/([a-z0-9\-]+).jpg\'', response.text)
            if match:
                (image_uuid,) = match.groups()

        name = name_element.xpath("text()").get()
        uuid = name_element.xpath('..//span[@id="uuid"]/text()').get()
        item = Codecontest2020Item(name=name, item_id=uuid, image_id=image_uuid)

        rating_element = name_element.xpath('..//p[2]//span')

        rating_url = rating_element.attrib.get('data-price-url')
        if rating_url:
            yield response.follow(
                rating_url, callback=self.parse_rating, meta=dict(item=item)
            )
        else:
            item['rating'] = rating_element.xpath('text()').get()

        yield item

    def parse_rating(self, response, **kwargs):
        item = response.meta['item']
        rating = response.json().get('value', '')
        item['rating'] = rating
        yield item
