#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 30 14:02:50 2018

@author: zdhughes
"""

from test import Ui_MainWindow
from PyQt5 import QtWidgets
import sys

class Window(QtWidgets.QMainWindow, Ui_MainWindow):
	
	'''This is the main application window.'''
	
	def __init__(self):

		#Execute the QMainWindow __init__. 
		#QMainWindow is a QWidget; a widget without a parent is a window.
		super().__init__()
		#Draw all the stuff from the UI file.
		self.setupUi(self)
		
		
		
		

		
app = QtWidgets.QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec_())