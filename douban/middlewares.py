# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import os
import time
import netifaces
import json
import urllib2


class ChangeProxyMiddleware(object):
    last_change = 0

    def changeip(self, spider):
        start = 0
        if spider.lock:
            spider.logger.info("Waiting for new IP.")
            start = time.time()
            while spider.lock:
                if time.time() - start > 100:
                    break
        else:
            spider.lock = True
            try:
                spider.logger.info("Shutting down last connection.")
                os.system("poff tmp")
                start = time.time()
                while "ppp0" in netifaces.interfaces():
                    if time.time() - start > 100:
                        start = time.time()
                        os.system("poff tmp")
                spider.logger.info("Starting new connection.")
                os.system("pon tmp")
                start = time.time()
                while "ppp0" not in netifaces.interfaces():
                    if time.time() - start > 100:
                        os.system("pon tmp")
                        start = time.time()
                start = time.time()
                while 2 not in netifaces.ifaddresses("ppp0"):
                    if time.time() - start > 100:
                        os.system("pon tmp")
                        start = time.time()
                time.sleep(1)
                ip = json.loads(urllib2.urlopen("http://httpbin.org/ip", timeout=10).read())["origin"]
                spider.logger.info("New IP: " + ip)
                if ip == spider.local:
                    os.system("ip route add default dev ppp0")
                    time.sleep(1)
            except:
                pass
            spider.p += 1
            spider.lock = False

    def process_exception(self, request, exception, spider):
        if request.meta['p'] == spider.p:
            spider.logger.info("Changing ip: " + str(exception))
            self.changeip(spider)
            request.meta['p'] = spider.p
            spider.logger.info("Done.")
        else:
            request.meta['p'] = spider.p
        return request

    def process_response(self, request, response, spider):
        domain = response.url.split("//")[-1].split("/")[0]
        if (response.status != 200 and response.status != 404) or (response.body.startswith('<script>')) or (domain == 'sec.douban.com'):
            if request.meta['p'] == spider.p:
                spider.logger.info("Changing ip: " + str(response.status) + " " + str(response.body.startswith('<script>')) + " " + domain)
                self.changeip(spider)
                request.meta['p'] = spider.p
                request.headers['Uesr-Agent'] = ""
                spider.logger.info("Done.")
            else:
                request.meta['p'] = spider.p
            return request
        else:
            return response

class DoubanSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            print r.url
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
