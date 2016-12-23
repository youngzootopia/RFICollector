# -*- coding: utf-8 -*-
import scrapy
import sys
import os
import datetime
from datetime import date
from scrapy.spiders  import Spider
from scrapy.selector import HtmlXPathSelector
from scrapy.selector import Selector
from RFICollector.items import RFICollectorItem
from RFICollector.items import RFIDetailGoodsItem
from RFICollector.items import RFIFileLinkItem
from scrapy.http import FormRequest
# Qt UI 사용하기 위해
import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import uic
# 작업이 완료되었음을 알려주기위해 잠시 멈춤
import time
# 스레드 사용하기 위해
from threading import Thread

reload(sys)
sys.setdefaultencoding('utf-8')

class RFICollectorSpider(Spider):
    name = "RFICollector" # spider 이름
    # spider setting
    custom_settings = {
        'BOT_NAME': 'RFICollector',
        'SPIDER_MODULES': 'RFICollector.spiders',
        'RFICollector.spiders': 'RFICollector.spiders',
        'LOG_LEVEL': 'ERROR',
        'CELERYD_MAX_TASKS_PER_CHILD': 1,
        'CELERYD_CONCURRENCY': 10,
        'ITEM_PIPELINES': {
            'RFICollector.pipelines.RFICollectorPipeline': 100
        }
    }
    
    allowed_domains = ["g2b.go.kr"] # 크롤링할 도메인
    detail = 0 # 상세페이지를 크롤링 할것인지 결정하는 변수
    item = 0 # item 객체 선언
    pageCount = 1 # RFI 리스트 페이지를 증가시키면서 크롤링
    lastPageNum = 0 # 마지막 RFI 리스트 페이지
    items = [] #데이터를 Item별로 구별해서 담을 리스트
    endDay = None
    startDay = None
    startDayStr = None
    endDayStr = None


    def __init__(self, startDay, endDay):
        self.startDay = startDay
        self.endDay = endDay
        self.endDayStr = "{0}/{1}/{2}".format(str(endDay.year), str(endDay.month), str(endDay.day)) # form 속성 지정하기 위한 문자열 만들기
        self.startDayStr = "{0}/{1}/{2}".format(str(startDay.year), str(startDay.month), str(startDay.day)) # form 속성 지정하기 위한 문자열 만들기
        self.detailProgressBar = None
        self.title = ""
        self.total = 0
        self.progress = 0

    def progressBarThread(self):
        self.progressBar = progressBarWindow(self.title, self.total)
        self.progressBar.move(710, 465)
        self.progressBar.show()

        while True:
            self.progressBar.updateValue(self.progress)

            if self.total <= self.progress:
                break

    def start_requests(self):        
        if self.detail == 0: #목록 페이지를 가져올 거라면
            return [FormRequest("http://www.g2b.go.kr:8081/ep/preparation/prestd/preStdPublishList.do",
                     formdata={'fromRcptDt': self.startDayStr, 'toRcptDt': self.endDayStr, 'currentPageNo': str(self.pageCount)},
                     callback=self.parse)]
        else: # 상세 페이지를 가져올 거라면
            return [FormRequest("http://www.g2b.go.kr:8081/ep/preparation/prestd/preStdPublishList.do",
                     formdata={'preStdRegNo': self.items[self.detail]['registrationNum']},
                     callback=self.parse)]
        
    def parse(self, response):
        hxs = Selector(response) #지정된 주소에서 전체 소스코드를 가져옴
        if self.lastPageNum == 0: # 끝 페이지를 가져오지 않았다면
            lastPageLink = str(hxs.xpath('//a[@class="next_end"]/@href').extract()) # 끝 페이지 링크를 가져옴
            index = lastPageLink.rfind('currentPageNo=') # 링크에서 끝 페이지 정보를 가져옴
            if index != 0:
                lastPageLink = lastPageLink[index + 14:]
                lastPageLink = lastPageLink.replace("'", "")
                lastPageLink = lastPageLink.replace("]", "") # 끝 페이지 숫자만 추출
                self.lastPageNum = int(lastPageLink)

                # 스레드 실행
                self.title = u'RFI 리스트 크롤링 중'
                self.total = self.lastPageNum
                Thread(target = self.progressBarThread).start()
                                
        if self.pageCount <= self.lastPageNum and self.detail == 0:
            selects = [] #전체 소스코드 중에서 필요한 영역만 잘라내서 담을 리스트
            selects = hxs.xpath('//tbody/tr') #필요한 영역을 잘라서 리스트에 저장
            self.parseList(selects) # 목록 페이지 파싱
            
        if self.pageCount < self.lastPageNum:
            self.pageCount = self.pageCount + 1
            self.progress = self.pageCount
            return [FormRequest("http://www.g2b.go.kr:8081/ep/preparation/prestd/preStdPublishList.do",
                    formdata={'fromRcptDt': self.startDayStr, 'toRcptDt': self.endDayStr, 'currentPageNo': str(self.pageCount)},
                    callback=self.parse)]
        
        elif self.lastPageNum == self.pageCount and self.detail < len(self.items) - 1: # 끝 페이지까지 크롤링을 했다면

            if self.detailProgressBar == None:
                # 스레드 실행
                self.title = u'RFI 상세정보 크롤링 중'
                self.total = len(self.items) - 2
                self.progress = 0
                Thread(target = self.progressBarThread).start()
                self.detailProgressBar = True
            else:
                self.progress = self.detail
                
            selects = [] #전체 소스코드 중에서 필요한 영역만 잘라내서 담을 리스트
            selects = hxs.xpath('//body/div') #필요한 영역을 잘라서 리스트에 저장
            self.parseDetail(selects)
            return [FormRequest("https://www.g2b.go.kr:8143/ep/preparation/prestd/preStdDtl.do",
                     formdata={'preStdRegNo': self.items[self.detail]['registrationNum']},
                     callback=self.parse)]
        else:
            return self.items
        
    def parseList(self, selects):        
        for sel in selects:
            self.item = RFICollectorItem()
            temp = sel.xpath('td/div/a/text()').extract() # 등록번호와 품명(사업명), 태그가 같기 때문에 temp로 저장하고 나눔.
            self.item['registrationNum'] = temp[0] # 등록번호
            if len(temp) > 1:
                self.item['goodsName'] = temp[1] # 품명(사업명)
            else:
                self.item['goodsName'] = ''
            temp = sel.xpath('td[@class="tl"]/div/text()').extract() # 참조번호와 수요기관의 태그가 같기 때문에 temp로 저장하고 나눔.
            self.item['referenceNum'] = temp[0]
            temp[3] = temp[3].replace('\t', '')
            temp[3] = temp[3].replace('\r', '')
            self.item['demandOrgan'] = temp[3].replace('\n', '')
            temp = sel.xpath('td/div/text()').extract() # 등록 날짜
            temp = temp[5].split()
            self.item['publicDate'] = temp[0]
            self.item['link'] = "https://www.g2b.go.kr:8143/ep/preparation/prestd/preStdDtl.do?preStdRegNo={0}\&fromRcptDt={1}%2F{2}%2F{3}&toRcptDt={4}%2F{5}%2F{6}".format(str(self.item['registrationNum']), \
                str(self.startDay.year), str(self.startDay.month), str(self.startDay.day), str(self.endDay.year), \
                str(self.endDay.month), str(self.endDay.day)) # 링크 만들기
            # default
            self.item['budget'] = ""
            self.item['publicOrgan'] = ""
            self.item['manager'] = ""
            self.item['managerPhoneNum'] = ""
            self.item['deadline'] = "{0}/{1}/{2}".format(str(self.endDay.year), str(self.endDay.month), str(self.endDay.day))
            self.item['detailGoodsItems'] = [] # 세부품목을 담을 리스트
            self.item['fileLinkItems'] = [] # 규격서 파일 링크를 담을 리스트
                     
            self.items.append(self.item) #Item 1개 세트를 리스트에 담음
        pass
    def parseDetail(self, selects):
        # 물품과 공사 상세 페이지 소스코드가 다르기 때문에 검사 하기 위함
        isConstruction = str(selects.xpath('//div[@id="content_header"]/h2/text()').extract()[0])
        temp = [] # 데이터를 뽑아올 리스트
        temp = selects.xpath('//tr/td/div[@class="tb_inner"]/text()').extract()
        for i in range(len(temp)):
            temp[i] = temp[i].replace('\t', '')
            temp[i] = temp[i].replace('\r', '')
            temp[i] = temp[i].replace('\n', '')
            
        if isConstruction.find(u'공사') != -1: # 공사일 경우
            if temp:
                self.items[self.detail]['budget'] = temp[3] # 배정예산
                self.items[self.detail]['deadline'] = temp[6] # 의견등록 마감일시
                self.items[self.detail]['publicOrgan'] = temp[7] # 공고기관
                
                temp[8] = temp[8].split('(')
                self.items[self.detail]['manager'] = temp[8][0] # 담당자
                if len(temp[8]) > 1: # 전화번호가 있다면
                    self.items[self.detail]['managerPhoneNum'] = temp[8][1].replace(')', '')
                detailTemp = selects.xpath('//div[@id="container"]/div[@class="results"]/table[@class="table_list_prestdDtl table_list"] \
                    /tbody/tr') # 세부 품목 테이블 가져옴
                if detailTemp:
                    for detail in detailTemp:
                        detailItem = RFIDetailGoodsItem()
                        detailStr = detail.xpath('td/div/text()').extract()
                        detailItem['registrationNum'] = self.items[self.detail]['registrationNum']
                        detailItem['detailGoodsNum'] = detailStr[1]
                        detailItem['detailGoodsName'] = detailStr[2]
                        self.items[self.detail]['detailGoodsItems'].append(detailItem)
                fileTemp = selects.xpath('//div[@class="tb_inner"]/a[@href="#"]/text()').extract() # 규격서 파일 테이블 가져옴
                if fileTemp:
                    fileIndex = 1
                    for fileName in fileTemp:
                        fileItem = RFIFileLinkItem()
                        fileItem['registrationNum'] = self.items[self.detail]['registrationNum']
                        fileItem['link'] = "https://www.g2b.go.kr:8143/ep/co/fileDownload.do?fileTask=PS&fileSeq={0}::{1}".format(str(fileItem['registrationNum']), str(fileIndex))
                        fileItem['fileName'] = fileName
                        self.items[self.detail]['fileLinkItems'].append(fileItem)
                        fileIndex = fileIndex + 1
                    
        else: # 물품과 용역
            if temp:
                self.items[self.detail]['budget'] = temp[3] # 배정예산
                self.items[self.detail]['deadline'] = temp[5] # 의견등록 마감일시
                self.items[self.detail]['publicOrgan'] = temp[6] # 공고기관
                
                temp[7] = temp[7].split('(')
                self.items[self.detail]['manager'] = temp[7][0] # 담당자
                if len(temp[7]) > 1: # 전화번호가 있다면
                    self.items[self.detail]['managerPhoneNum'] = temp[7][1].replace(')', '')
                detailTemp = selects.xpath('//div[@id="container"]/div[@class="results"]/table[@class="table_list_prestdDtl table_list"] \
                    /tbody/tr') # 세부 품목 테이블 가져옴
                if detailTemp:
                    for detail in detailTemp:
                        detailStr = detail.xpath('td/div/text()').extract()
                        if detailStr:
                            detailItem = RFIDetailGoodsItem()
                            detailItem['registrationNum'] = self.items[self.detail]['registrationNum']
                            detailItem['detailGoodsNum'] = detailStr[1]
                            detailItem['detailGoodsName'] = detailStr[2]
                            self.items[self.detail]['detailGoodsItems'].append(detailItem)
                fileTemp = selects.xpath('//div[@class="tb_inner"]/a[@href="#"]/text()').extract() # 규격서 파일 테이블 가져옴
                if fileTemp:
                    fileIndex = 1
                    for fileName in fileTemp:
                        fileItem = RFIFileLinkItem()
                        fileItem['registrationNum'] = self.items[self.detail]['registrationNum']
                        fileItem['link'] = "https://www.g2b.go.kr:8143/ep/co/fileDownload.do?fileTask=PS&fileSeq={0}::{1}".format(str(fileItem['registrationNum']), str(fileIndex))
                        fileItem['fileName'] = fileName
                        self.items[self.detail]['fileLinkItems'].append(fileItem)
                        fileIndex = fileIndex + 1
     
        self.detail = self.detail + 1
        pass


form_class = uic.loadUiType("progressBar.ui")[0]

class progressBarWindow(QMainWindow, form_class):
    def __init__(self, title, total):
        self.total = total
        super(QMainWindow, self).__init__()
        self.setupUi(self)
        self.titleLabel.setText(title)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(total)
        
    def updateValue(self, value):
        self.progressBar.setValue(value)
        if value >= self.total:
            time.sleep(1) # 1초 멈춤
            self.close()
            self = None
