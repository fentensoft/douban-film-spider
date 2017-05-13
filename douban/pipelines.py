# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from sqlalchemy import create_engine, MetaData, Table


class DoubanPipeline(object):
    conn = None
    film_table = None

    def open_spider(self, spider):
        engine = create_engine('postgresql+psycopg2://postgres:orchid@127.0.0.1:5432/postgres', echo=False)
        self.conn = engine.connect()
        metadata = MetaData(engine)
        self.film_table = Table('film', metadata, autoload=True)

    def process_item(self, item, spider):
        ins = self.film_table.insert().values(item)
        try:
            self.conn.execute(ins)
        except Exception, e:
            pass

        return item

    def close_spider(self, spider):
        self.conn.close()
