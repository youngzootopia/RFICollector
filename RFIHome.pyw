# -*- coding: utf-8 -*-
# Qt UI 사용하기 위해
import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import uic
# Scrapy 사용하기 위해
import scrapy
from scrapy.crawler import CrawlerProcess
from RFICollector.spiders.RFICollectorSpider import RFICollectorSpider
# RFI 리스트목록을 출력할 윈도우
from RFIListView import RFIListWindow
# Date 객체를 사용하기 위해
import datetime
from datetime import date

form_class = uic.loadUiType("RFIProject.ui")[0]

class RFIWindow(QMainWindow, form_class):
    startDay = date.today() - datetime.timedelta(1)
    endDay = date.today() - datetime.timedelta(1)
    
    def __init__(self):
        super(RFIWindow, self).__init__() 
        self.setupUi(self) # layout 클래스에 대한 객체 생성. 즉, UI를 생성.
        self.listWindow = None
        self.connect(self.collectButton, SIGNAL("clicked()"), self.collectButton_clicked)
        self.connect(self.listViewButton, SIGNAL("clicked()"), self.listViewButton_clicked)
        self.startCalendar.clicked[QDate].connect(self.setStartDay)
        self.endCalendar.clicked[QDate].connect(self.setEndDay)
        self.startCalendar.setSelectedDate(self.startDay)
        self.endCalendar.setSelectedDate(self.endDay)

    def setStartDay(self, selectedDate):
        self.startDay = selectedDate.toPyDate()

    def setEndDay(self, selectedDate):
        self.endDay = selectedDate.toPyDate()
        
    def collectButton_clicked(self):
        # crawl 수행
        process = CrawlerProcess({
            'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
        })
        process.crawl(RFICollectorSpider, self.startDay, self.endDay)
        process.start() # the script will block here until the crawling is finished

    def listViewButton_clicked(self):
        self.hide()
        self.listWindow = RFIListWindow(self.startDay, self.endDay)
        self.listWindow.move(0, 0)
        self.listWindow.show()
        self.connect(self.listWindow.homeButton, SIGNAL("clicked()"), self.restart)
        self.connect(self.listWindow, SIGNAL('triggered()'), self.restart)

    def restart(self):
        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    startWindow = RFIWindow()
    startWindow.move(0, 0)
    startWindow.show()
    app.exec_()
