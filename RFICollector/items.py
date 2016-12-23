# -*- coding: utf-8 -*-
import scrapy
from scrapy.item import Item, Field

class RFICollectorItem(scrapy.Item):
    registrationNum = scrapy.Field() # 등록번호
    link = scrapy.Field() # URL
    referenceNum = scrapy.Field() # 참조번호
    goodsName = scrapy.Field() # 품명(사업명)
    demandOrgan = scrapy.Field() # 수요기관
    publicDate = scrapy.Field() # 사전규격공개일
    publicOrgan = scrapy.Field() # 공개기관
    deadline = scrapy.Field() # 의견등록마감일
    budget = scrapy.Field() # 배정예산
    manager = scrapy.Field() # 담당자이름
    managerPhoneNum = scrapy.Field() # 담당자전화번호
    detailGoodsItems = scrapy.Field() # 세부품목 리스트
    fileLinkItems = scrapy.Field() # 파일 링크 리스트
    pass

class RFIDetailGoodsItem(scrapy.Item):
    registrationNum = scrapy.Field() # 등록번호
    detailGoodsNum = scrapy.Field() # 세부품명번호
    detailGoodsName = scrapy.Field() # 세부품명이름
    pass

class RFIFileLinkItem(scrapy.Item):
    registrationNum = scrapy.Field() # 등록번호
    link = scrapy.Field() # URL
    fileName = scrapy.Field() # 파일 이름
    pass
