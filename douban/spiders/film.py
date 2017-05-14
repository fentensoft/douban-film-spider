# -*- coding: utf-8 -*-
import scrapy
from pybloom import ScalableBloomFilter
import random
import string


class FilmSpider(scrapy.Spider):
    name = "film"
    allowed_domains = ["douban.com"]
    f = None
    lock = False
    p = 0
    start_urls = ['https://movie.douban.com/tag/2017?start=0&type=T']

    def start_requests(self):
        self.f = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH)
        yield scrapy.Request(url="https://movie.douban.com/tag/?view=cloud", meta={"p": self.p}, callback=self.parse_tags)

    def parse_tags(self, response):
        hrefs = response.xpath('//table[@class="tagCol"]//a/@href').extract()
        for i in hrefs:
            yield scrapy.Request(url="https://movie.douban.com" + i, meta={"p": self.p}, cookies={"bid": "".join(random.sample(string.ascii_letters + string.digits, 20))}, callback=self.parse_pages)

    def parse_pages(self, response):
        lists = response.xpath('//div[@class="paginator"]/a/text()').extract()
        if len(lists) > 0:
            last_page = int(lists[-1])
            baseurl = response.url + "?type=T&start="
            for i in range(last_page):
                yield scrapy.Request(url=baseurl + str(20 * i), meta={"p": self.p}, cookies={"bid": "".join(random.sample(string.ascii_letters + string.digits, 20))}, callback=self.parse_list)
        else:
            self.parse_list(response)

    def parse_list(self, response):
        hrefs = response.xpath('//a[@class="nbg"]/@href').extract()
        for i in hrefs:
            if i not in self.f:
                self.f.add(i)
                yield scrapy.Request(url=i, meta={"p": self.p}, cookies={"bid": "".join(random.sample(string.ascii_letters + string.digits, 20))}, callback=self.parse_film)

    def get_first(self, r, d = None):
        return r[0] if len(r) > 0 else d

    def parse_film(self, response):
        if len(response.xpath(u'//span[text()="集数:"]').extract()) == 0:
            item = dict()
            item['name'] = response.xpath('//div[@id="content"]/h1/span[1]/text()').extract()[0]
            item['img'] = response.xpath('//a[@class="nbgnbg"]/img/@src').extract()[0]
            item['year'] = self.get_first(response.xpath('//span[@class="year"]/text()').extract(), "").strip('()')
            item['director'] = "|".join(response.xpath('//a[@rel="v:directedBy"]/text()').extract())
            item['script'] = "|".join(response.xpath(u'//span[text()="编剧"]/parent::span/span[2]/a/text()').extract())
            item['acts'] = "|".join(response.xpath('//a[@rel="v:starring"]/text()').extract())
            item['country'] = self.get_first(response.xpath(u'//span[text()="制片国家/地区:"]/following::text()[1]').extract(), "").strip().replace(" / ", "|")
            item['language'] = self.get_first(response.xpath(u'//span[text()="语言:"]/following::text()[1]').extract(), "").strip().replace(" / ", "|")
            item['running_time'] = self.get_first(response.xpath('//span[@property="v:runtime"]/text()').extract(), "0")
            item['running_time'] = int(''.join(x for x in item['running_time'] if x.isdigit()))
            item['rate'] = self.get_first(response.xpath('//strong/text()').extract(), "0")
            item['votes'] = self.get_first(response.xpath('//span[@property="v:votes"]/text()').extract())
            item['type'] = "|".join(response.xpath('//span[@property="v:genre"]/text()').extract())
            item['tags'] = "|".join(response.xpath('//div[@class="tags-body"]/a/text()').extract())
            yield item

