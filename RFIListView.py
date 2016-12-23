# -*- coding: utf-8 -*-
# Qt UI 사용하기 위해
import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import uic
# pymySQL 사용하기 위해
import pymysql.cursors
# data 객체를 사용하기 위해
import datetime
from datetime import date
# 클립보드에 복사하기 위해
import pyperclip
# 파일 리스트목록을 출력할 윈도우
from fileListView import fileListWindow
# 엑셀파일을 읽기위해
from xlrd import open_workbook

form_class = uic.loadUiType("RFIList.ui")[0]

class RFIListWindow(QMainWindow, form_class):
    startDay = None
    endDay = None
    def __init__(self, startDay, endDay):
        self.startDay = startDay
        self.endDay = endDay
                      
        super(QMainWindow, self).__init__()
        self.setupUi(self)
        self.listTable.horizontalHeader().resizeSection(4, 400)
        self.listTable.horizontalHeader().resizeSection(7, 130)
        self.listTable.horizontalHeader().resizeSection(8, 130)
        self.listTable.horizontalHeader().resizeSection(14, 50)
        self.listTable.horizontalHeader().resizeSection(15, 50)
        self.connect(self.homeButton, SIGNAL("clicked()"), self.homeButton_clicked)
        self.moreLessTab.currentChanged.connect(self.tabChange)
        self.listTable.cellDoubleClicked.connect(self.cellCopyToClipboard)
        self.connect(self, SIGNAL('triggered()'), self.homeButton_clicked)

        wb = open_workbook('organ classify/organ classify.xls')
        sheet = wb.sheet_by_index(0)

        self.organDict = {}
        for i in range(1, sheet.nrows):
            self.organDict[sheet.cell_value(i, 1).replace(' ', '').decode('utf-8')] = sheet.cell_value(i, 0).decode('utf-8')
            
        self.dataToTable(True)
        
    def homeButton_clicked(self):
        self.close()
        self = None

    # 1억원 이상과 1억원 미만 및 달러 탭을 변경하면 데이터를 변경
    def tabChange(self, i):
        if i == 0:
            for row in range(self.listTable.rowCount()):
                for col in range(self.listTable.columnCount()):
                    self.listTable.setItem(row, col, QTableWidgetItem(""))
            
            self.dataToTable(True)
        elif i == 1:
            for row in range(self.listTable.rowCount()):
                for col in range(self.listTable.columnCount()):
                    self.listTable.setItem(row, col, QTableWidgetItem(""))
                    
            self.dataToTable(False)

    def tupleDelete(self):
        isNext = True
        while isNext:
            for col in range(0, 14):
                self.listTable.setItem(self.row, col, QTableWidgetItem(""))

            self.listTable.setCellWidget(self.row, 13, QLabel())
            self.listTable.setCellWidget(self.row, 14, QLabel())
            if self.listTable.item(self.row + 1, 2) is None:
                self.row = self.row + 1
            else:
                isNext = False
        

    # 셀을 더블클릭하면 파일리스트 출력 혹은 튜플 삭제, 클립보드에 복사
    def cellCopyToClipboard(self, row, column):
        # 파일 리스트 출력
        if column == 14:
            self.fileWindow = fileListWindow(self.listTable.item(row, 2).text())
            self.fileWindow.move(560, 415)
            self.fileWindow.show()
            self.connect(self.fileWindow.deleteButton, SIGNAL("clicked()"), self.tupleDelete)
            self.row = row
            for col in range(0, 14):
                self.listTable.item(row, col).setBackground(QColor(255, 255, 0))
            database = RFIListManagement()
            database.update(self.listTable.item(row, 2).text())

        # 튜플 삭제
        elif column == 15:
            database = RFIListManagement()
            database.delete(self.listTable.item(row, 2).text())
            isNext = True
            while isNext:
                for col in range(0, 13):
                    self.listTable.setItem(row, col, QTableWidgetItem(""))

                self.listTable.setCellWidget(row, 13, QLabel())
                self.listTable.setCellWidget(row, 14, QLabel())
                if self.listTable.item(row + 1, 2) is None:
                    row = row + 1
                else:
                    isNext = False

        # 클립보드에 복사
        elif column == 0:
            for col in range(0, 14):
                if col == 0:
                    copyStr = self.listTable.item(row, col).text() + '\t'
                elif col == 13:
                    copyStr = copyStr + '\t' + self.listTable.item(row, col).text()
                else:
                    copyStr = copyStr + self.listTable.item(row, col).text() + '\t'

            pyperclip.copy(str(copyStr).encode('cp949')) # 클립보드에 복사

        else:
            pyperclip.copy(str(self.listTable.item(row, column).text()).encode('cp949')) # 클립보드에 복사

    # 파일 보기 및 삭제 버튼 아이콘을 출력
    def iconToCell(self, row, isFile):
        # 파일 아이콘
        if isFile:
            imageLabel = QLabel()
            imageLabel.setPixmap(QPixmap("icon/downloadIcon.png"))
            self.listTable.setCellWidget(row, 14, imageLabel)
        # 삭제 아이콘
        else:
            imageLabel = QLabel()
            imageLabel.setPixmap(QPixmap("icon/removeICon.png"))
            self.listTable.setCellWidget(row, 15, imageLabel)
        
    def dataToTable(self, isMore):
        # MySQL에서 데이터 셀렉트
        database = RFIListManagement()
        result = database.selectSQL(isMore, self.startDay, self.endDay)
        self.listTable.setRowCount(len(result))
        self.listTable.setColumnCount(16)
        for row in range(0, len(result)):
            for col in range(0, len(result[row]) + 1):
                if row > 0 and result[row][2] == result[row - 1][2]: # 세부 품목이 여러개인 경우
                    if col == 10 or col == 11:
                        self.listTable.setItem(row, col, QTableWidgetItem(result[row][col - 1]))
                    else:
                        pass
                else: # 그렇지 않은 경우
                    if col == 6:
                        organName = str(result[row][col - 1]).decode('utf-8').replace(' ', '')
                        try:
                            self.listTable.setItem(row, col, QTableWidgetItem(self.organDict[organName]))
                        except:
                            self.listTable.setItem(row, col, QTableWidgetItem(""))
                    elif col < 6:
                        if result[row][col] is None:
                           self.listTable.setItem(row, col, QTableWidgetItem(""))
                        else:
                            self.listTable.setItem(row, col, QTableWidgetItem(result[row][col]))
                    elif col > 6:
                        if result[row][col - 1] is None:
                           self.listTable.setItem(row, col, QTableWidgetItem(""))
                        elif type(result[row][col - 1]) == date:
                            self.listTable.setItem(row, col, QTableWidgetItem(str(result[row][col - 1])))
                        elif col == len(result[row]) and result[row][col - 1] != 0:
                            for c in range(0, 14):
                                self.listTable.item(row, c).setBackground(QColor(255, 100, 100))    
                        else:
                            self.listTable.setItem(row, col, QTableWidgetItem(result[row][col - 1]))
            if row > 0 and result[row][2] == result[row - 1][2]: # 세부 품목이 여러개인 경우
                pass
            else:
                self.iconToCell(row, True)
                self.iconToCell(row, False)
        
        
class RFIListManagement():
    def __init__(self): # MySQL 접속 및 커서 열기
        try:
            self.conn = pymysql.connect(user='root', passwd='kcia', db='rficollector', host='localhost', charset="utf8", use_unicode=True)

            self.cursor = self.conn.cursor()

        except pymysql.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)

    # 데이터 Select
    def selectSQL(self, isMore, startDay, endDay):
        if isMore:
            self.cursor.execute("SELECT RFIInfo.publicOrgan, RFIInfo.link, RFIInfo.registrationNum, RFIInfo.referenceNum, RFIInfo.goodsName, \
                    RFIInfo.demandOrgan, RFIInfo.publicDate, RFIInfo.deadline, RFIInfo.budget, detailgoods.detailGoodsNum, \
                    detailgoods.detailGoodsName, RFIInfo.manager, RFIInfo.managerPhoneNum, RFIInfo.isCheck \
                    FROM \
                    (SELECT rfimore.publicOrgan, rfimore.link, rfimore.registrationNum, rfimore.referenceNum, rfimore.goodsName, \
                    rfimore.demandOrgan, rfimore.publicDate, rfimore.deadline, rfimore.budget, rfimore.manager, rfimore.managerPhoneNum,\
                    rfiregistrationnum.isCheck \
                    FROM rfimore, rfiregistrationnum \
                    WHERE rfimore.registrationNum = rfiregistrationnum.registrationNum)RFIInfo \
                    LEFT OUTER JOIN detailgoods \
                    ON RFIInfo.registrationNum = detailgoods.registrationNum \
                    WHERE RFIInfo.publicDate >= '%s' and RFIInfo.publicDate <= '%s' \
                    order by RFIInfo.registrationNum DESC"%(startDay.strftime('%Y/%m/%d'), endDay.strftime('%Y/%m/%d')))
            result = self.cursor.fetchall()

        else:
            self.cursor.execute("SELECT RFIInfo.publicOrgan, RFIInfo.link, RFIInfo.registrationNum, RFIInfo.referenceNum, RFIInfo.goodsName, \
                    RFIInfo.demandOrgan, RFIInfo.publicDate, RFIInfo.deadline, RFIInfo.budget, detailgoods.detailGoodsNum, \
                    detailgoods.detailGoodsName, RFIInfo.manager, RFIInfo.managerPhoneNum, RFIInfo.isCheck \
                    FROM \
                    (SELECT rfiless.publicOrgan, rfiless.link, rfiless.registrationNum, rfiless.referenceNum, rfiless.goodsName, \
                    rfiless.demandOrgan, rfiless.publicDate, rfiless.deadline, rfiless.budget, rfiless.manager, rfiless.managerPhoneNum,\
                    rfiregistrationnum.isCheck \
                    FROM rfiless, rfiregistrationnum \
                    WHERE rfiless.registrationNum = rfiregistrationnum.registrationNum)RFIInfo \
                    LEFT OUTER JOIN detailgoods \
                    ON RFIInfo.registrationNum = detailgoods.registrationNum \
                    WHERE RFIInfo.publicDate >= '%s' and RFIInfo.publicDate <= '%s' \
                    order by RFIInfo.registrationNum DESC"%(startDay.strftime('%Y/%m/%d'), endDay.strftime('%Y/%m/%d')))
            result = self.cursor.fetchall()
            
        return result

    # 파일 리스트 Select
    def selectFileList(self, registrationNum):
        self.cursor.execute("SELECT fileName, link FROM filelink")
        result = self.cursor.fetchall()

        return result

    # 데이터 Delete
    def delete(self, registrationNum):
        try:
            self.cursor.execute("delete from rfiregistrationnum where registrationNum = '%s'" %(registrationNum))
            self.conn.commit()

        except pymysql.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            return

    # 파일 리스트 확인시 rfiregistrationnum 테이블의 isCheck 항목 업데이트
    def update(self, registrationNum):
        try:
            self.cursor.execute("update rfiregistrationnum set isCheck = isCheck + 1 where registrationNum = '%s'" %(registrationNum))
            self.conn.commit()

        except pymysql.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            return
    