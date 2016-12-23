# -*- coding: utf-8 -*-
# Qt UI 사용하기 위해
import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import uic
# 작업이 완료되었음을 알려주기위해 잠시 멈춤
import time

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