# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from twisted.enterprise import adbapi
import datetime
import logging
import pymysql.cursors
import sys
from scrapy.exceptions import DropItem
from RFICollector.items import RFICollectorItem
from RFICollector.items import RFIDetailGoodsItem
from RFICollector.items import RFIFileLinkItem
reload(sys)
sys.setdefaultencoding('utf-8')

class RFICollectorPipeline(object):
    def __init__(self): # MySQL 접속 및 커서 열기
        try:
            self.conn = pymysql.connect(user='root', passwd='kcia', db='rficollector', host='localhost', charset="utf8", use_unicode=True)

            self.cursor = self.conn.cursor()
            
        except pymysql.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)                 
            
    def process_item(self, item, spider):
        isMore = self.decideMoreOrLess(item['budget'].encode('utf-8'), item)
        result = self.selectSQL(item['registrationNum'].encode('utf-8'))
        
        if result: # 데이터가 이미 있는 경우
            self.updateSQL(item, isMore)
            if result[1] != 0: # 확인했던 경우라면
                try:
                    self.cursor.execute("update rfiregistrationnum set isCheck = isCheck + 1 where registrationNum = '%s'" %(item['registrationNum'].encode('utf-8')))
                    self.conn.commit()
                except pymysql.Error, e:
                    print "Error %d: %s" % (e.args[0], e.args[1])
                    return

        else: # 데이터가 없는 경우
            self.insertSQL(item, isMore)

    # 데이터가 이미 존재할 경우 update
    def updateSQL(self, item, isMore):
        try:
            self.cursor.execute("delete from rfiregistrationnum where registrationNum = '%s'" %(item['registrationNum'].encode('utf-8'))) # 데이터를 삭제하고 다시 삽입
            self.insertSQL(item, isMore)
            self.conn.commit()

        except pymysql.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            return
        pass

    # 1억원 미만 및 달라인 경우 rfiLess에 insert, 1억원 이상인 경우 rfiMore에 insert
    def insertSQL(self, item, isMore):
        if isMore:
            try:
                # 1억원 이상일 경우 rfiMore 테이블에 삽입
                self.cursor.execute("insert into rfiregistrationnum(registrationNum, isCheck) \
                                        values('%s', 0)" %(item['registrationNum'].encode('utf-8')))             
                self.cursor.execute("insert into rfiMore(registrationNum, link, referenceNum, goodsName, demandOrgan, publicDate, publicOrgan, deadline, budget, manager, managerPhoneNum) \
                                        values('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" %(item['registrationNum'].encode('utf-8'), item['link'].encode('utf-8'), \
                                        item['referenceNum'].encode('utf-8'), item['goodsName'].encode('utf-8'), item['demandOrgan'].encode('utf-8'), \
                                        item['publicDate'].encode('utf-8'), item['publicOrgan'].encode('utf-8'), item['deadline'].encode('utf-8'), \
                                        item['budget'].encode('utf-8'), item['manager'].encode('utf-8'), item['managerPhoneNum'].encode('utf-8')))
                if item['detailGoodsItems']:
                    for detail in item['detailGoodsItems']:
                        self.cursor.execute("insert into detailgoods(registrationNum, detailGoodsNum, detailGoodsName) \
                                        values('%s', '%s', '%s')" %(detail['registrationNum'].encode('utf-8'), detail['detailGoodsNum'].encode('utf-8'), \
                                                                    detail['detailGoodsName'].encode('utf-8')))
                if item['fileLinkItems']:
                    for file in item['fileLinkItems']:
                        self.cursor.execute("insert into filelink(registrationNum, link, fileName) \
                                        values('%s', '%s', '%s')" %(file['registrationNum'].encode('utf-8'), file['link'].encode('utf-8'), \
                                                                    file['fileName'].encode('utf-8')))

                self.conn.commit()

            except pymysql.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                return item
            
        else:
            try:
                # 1억원 미만, 달라일 경우 rfiLess 테이블에 삽입
                self.cursor.execute("insert into rfiregistrationnum(registrationNum, isCheck) \
                                        values('%s', 0)" %(item['registrationNum'].encode('utf-8')))
                self.cursor.execute("insert into rfiLess(registrationNum, link, referenceNum, goodsName, demandOrgan, publicDate, publicOrgan, deadline, budget, manager, managerPhoneNum) \
                                        values('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" %(item['registrationNum'].encode('utf-8'), item['link'].encode('utf-8'), \
                                        item['referenceNum'].encode('utf-8'), item['goodsName'].encode('utf-8'), item['demandOrgan'].encode('utf-8'), \
                                        item['publicDate'].encode('utf-8'), item['publicOrgan'].encode('utf-8'), item['deadline'].encode('utf-8'), \
                                        item['budget'].encode('utf-8'), item['manager'].encode('utf-8'), item['managerPhoneNum'].encode('utf-8')))
                if item['detailGoodsItems']:
                    for detail in item['detailGoodsItems']:
                        self.cursor.execute("insert into detailgoods(registrationNum, detailGoodsNum, detailGoodsName) \
                                        values('%s', '%s', '%s')" %(detail['registrationNum'].encode('utf-8'), detail['detailGoodsNum'].encode('utf-8'), \
                                                                    detail['detailGoodsName'].encode('utf-8')))
                if item['fileLinkItems']:
                    for file in item['fileLinkItems']:
                        self.cursor.execute("insert into filelink(registrationNum, link, fileName) \
                                        values('%s', '%s', '%s')" %(file['registrationNum'].encode('utf-8'), file['link'].encode('utf-8'), \
                                                                    file['fileName'].encode('utf-8')))

                self.conn.commit()
                    
            except pymysql.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                return item
        pass
                    
            

    # 데이터가 이미 있는 지 확인
    def selectSQL(self, registrationNum):
        self.cursor.execute("select * from rfiregistrationnum where registrationNum = '%s'" %(registrationNum.encode('utf-8')))
        result = self.cursor.fetchone() 
        return result

    def decideMoreOrLess(self, budget, item):
        if budget.find(u'$') != -1:
            isMore = False # 달라
        
        else:
            if budget != []: # 예산이 비어 있지 않은 경우만
                budget = budget.replace(',', '')
                budget = budget.replace(budget[:2], '')
                if budget != '': # 원화 표시만 되어있고 돈은 입력이 안된 경우
                    budget = int(budget.encode('utf-8'))
                else:
                    budget = 0;
                    
                if budget < 100000000:
                    isMore = False # 원화이고, 1억원 미만
                else:
                    isMore = True # 원화이고, 1억원 이상
            else: # 예산이 비어있다면
                isMore = False # 원화이고, 1억원 미만

        item['budget'] = str(budget)

        return isMore
                
    
    def spider_closed(self, spider):
        self.cursor.close()   # 커서 닫기
        self.conn.close() # MySQL 연결 닫기
