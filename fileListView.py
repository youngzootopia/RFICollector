# -*- coding: utf-8 -*-
# Qt UI 사용하기 위해
import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import uic
# pymySQL 사용하기 위해
import pymysql.cursors
# 파일 다운로드 하기 위해
import urllib2
# 다운로드 받은 파일 실행 및 폴더 생성하기 위해
import os
# 진행바 윈도우
from progressWindow import progressBarWindow
# 임시폴더 파일들 지우기 위해
import shutil

form_class = uic.loadUiType("fileList.ui")[0]

class fileListWindow(QMainWindow, form_class):
    registrationNum = ""
    
    def __init__(self, registrationNum):
        self.registrationNum = registrationNum
        super(QMainWindow, self).__init__()
        self.setupUi(self)
        self.fileListTable.horizontalHeader().resizeSection(0, 50)
        self.fileListTable.horizontalHeader().resizeSection(1, 509)
        self.fileListTable.horizontalHeader().resizeSection(2, 170)
        self.fileListTable.horizontalHeader().resizeSection(3, 50)
        self.connect(self.deleteButton, SIGNAL("clicked()"), self.deleteButton_clicked)
        self.fileListTable.cellDoubleClicked.connect(self.fileDownload)
        self.dataToTable(True)
        self.connect(self, SIGNAL('triggered()'), self.closeEvent)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        # 임시 폴더가 있으면 삭제
        if os.path.isdir("C:/temporary") == True:
            # 폴더 및 파일 삭제
            shutil.rmtree('C:/temporary')
        
    # 셀을 더블클릭하면 URL실행시켜서 파일 다운로드
    def fileDownload(self, row, col):
        url = str(self.fileListTable.item(row, 2).text())
        fileName = str(self.fileListTable.item(row, 1).text()).encode('cp949')
        
        if col == 3:
            self.saveFile(url, fileName)

        else: # C:\temporary에 저장 후 자동으로 열기
            self.openFile(url, fileName)

    # C:\temporary으로 파일 다운로드 및 파일 실행
    def openFile(self, url, fileName):
        url = url
        urlLib = urllib2.urlopen(url)

        # 임시 폴더가 없으면 생성
        if os.path.isdir("C:/temporary") != True:
            os.mkdir("C:/temporary")

        # 파일 입출력을 이용하여 임시폴더에 저장
        file = open("C:/temporary/" + fileName, 'wb')
        meta = urlLib.info()
        fileSize = int(meta.getheaders("Content-Length")[0])
        downloadedFileSize = 0
        blockSize = 16384
        
        progressWindow = progressBarWindow(u'"%s" 다운로드 중\n'%(fileName.decode('cp949')), fileSize)
        progressWindow.move(710, 465)
        progressWindow.show()

        while True:
            buffer = urlLib.read(blockSize)
            if not buffer:
                break

            # 파일 출력 및 다운로드 진행 상황 출력
            downloadedFileSize += len(buffer)
            progressWindow.updateValue(downloadedFileSize)
            file.write(buffer)
            
        file.close()

        # 파일 실행
        os.system('"C:/temporary/%s"'%(fileName))

    # 다른 이름으로 파일 저장
    def saveFile(self, url, fileName):
        url = url
        urlLib = urllib2.urlopen(url)

        path = QFileDialog.getSaveFileName(self, u"다른 이름으로 저장", fileName.decode('cp949'));
        path = str(path).decode('utf-8')

        # 파일 입출력을 이용하여 사용자가 지정한 폴더에 저장
        file = open(path, 'wb')
        meta = urlLib.info()
        fileSize = int(meta.getheaders("Content-Length")[0])
        downloadedFileSize = 0
        blockSize = 16384
        
        progressWindow = progressBarWindow(u'"%s" 다운로드 중\n'%(fileName.decode('cp949')), fileSize)
        progressWindow.move(710, 465)
        progressWindow.show()

        while True:
            buffer = urlLib.read(blockSize)
            if not buffer:
                break

            # 파일 출력 및 다운로드 진행 상황 출력
            downloadedFileSize += len(buffer)
            progressWindow.updateValue(downloadedFileSize)
            file.write(buffer)
        file.close()

    # 삭제 버튼을 누르면 튜플 삭제
    def deleteButton_clicked(self):
        # MySQL에서 데이터 셀렉트
        database = fileListManagement()
        database.delete(self.registrationNum)
        self.close()

    # 파일 확장자에따라 아이콘 출력
    def iconToCell(self, row, extender):
        if extender == 'hwp':
            imageLabel = QLabel()
            imageLabel.setPixmap(QPixmap("icon/hwp.png"))
            self.fileListTable.setCellWidget(row, 0, imageLabel)
        elif extender == 'doc':
            imageLabel = QLabel()
            imageLabel.setPixmap(QPixmap("icon/doc.png"))
            self.fileListTable.setCellWidget(row, 0, imageLabel)
        elif extender == 'pdf':
            imageLabel = QLabel()
            imageLabel.setPixmap(QPixmap("icon/pdf.png"))
            self.fileListTable.setCellWidget(row, 0, imageLabel)
        elif extender == 'xlsx':
            imageLabel = QLabel()
            imageLabel.setPixmap(QPixmap("icon/xlsx.png"))
            self.fileListTable.setCellWidget(row, 0, imageLabel)
        elif extender == 'unknown':
            imageLabel = QLabel()
            imageLabel.setPixmap(QPixmap("icon/unknown.png"))
            self.fileListTable.setCellWidget(row, 0, imageLabel)

    def dataToTable(self, isMore):
        # MySQL에서 데이터 셀렉트
        database = fileListManagement()
        result = database.selectFileList(self.registrationNum)
        self.fileListTable.setRowCount(len(result))
        self.fileListTable.setColumnCount(4)
        for row in range(0, len(result)):
            for col in range(1, len(result[row]) + 1):
                    self.fileListTable.setItem(row, col, QTableWidgetItem(result[row][col - 1]))

            if result[row][0].find('hwp') != -1:
                self.iconToCell(row, 'hwp')
            elif result[row][0].find('doc') != -1:
                self.iconToCell(row, 'doc')
            elif result[row][0].find('pdf') != -1:
                self.iconToCell(row, 'pdf')
            elif result[row][0].find('xlsx') != -1:
                self.iconToCell(row, 'xlsx')
            else:
                self.iconToCell(row, 'unknown')

            imageLabel = QLabel()
            imageLabel.setPixmap(QPixmap("icon/downloadIcon.png"))
            self.fileListTable.setCellWidget(row, 3, imageLabel)

        
        
class fileListManagement():
    def __init__(self): # MySQL 접속 및 커서 열기
        try:
            self.conn = pymysql.connect(user='root', passwd='kcia', db='rficollector', host='localhost', charset="utf8", use_unicode=True)

            self.cursor = self.conn.cursor()

        except pymysql.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)

    # 파일 리스트 Select
    def selectFileList(self, registrationNum):
        self.cursor.execute("SELECT fileName, link FROM filelink WHERE registrationNum = '%s'"%(registrationNum))
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
    
class Downloader(QObject):
    def __init__(self, parentWidget, manager, fileName):
        super(Downloader, self).__init__(parentWidget)

        self.manager = manager
        self.reply = None
        self.downloads = {}
        self.path = ""
        self.parentWidget = parentWidget
        self.fileName = fileName

    def chooseSaveFile(self, url):
        if len(self.path) != 0:
            self.fileName = QDir(path).filePath(self.fileName)

        return QFileDialog.getSaveFileName(self.parentWidget, u"다른 이름으로 저장", self.fileName);
    
    def openFile(self, reply):
        if len(self.path) != 0:
            self.fileName = QDir(path).filePath(self.fileName)
        newPath = QString("c:/temporary/" + self.fileName)
        print newPath

        if len(newPath) != 0:
            file = QFile(newPath)
            if file.open(QIODevice.WriteOnly):
                file.write(reply.readAll())
                file.close()
                path = QDir(newPath).dirName()
                QMessageBox.information(self.parentWidget, u"다운로드 완료", u"'%s'." % newPath)
            else:
                QMessageBox.warning(self.parentWidget, u"다운로드 실패", u"다운로드에 실패하였습니다.")

    def saveFile(self, reply):
        newPath = self.downloads.get(reply.url().toString())

        if not newPath:
            newPath = self.chooseSaveFile(reply.url())
            print newPath

        if len(newPath) != 0:
            file = QFile(newPath)
            if file.open(QIODevice.WriteOnly):
                file.write(reply.readAll())
                file.close()
                path = QDir(newPath).dirName()
                QMessageBox.information(self.parentWidget, u"다운로드 완료", u"'%s'." % newPath)
            else:
                QMessageBox.warning(self.parentWidget, u"다운로드 실패", u"다운로드에 실패하였습니다.")