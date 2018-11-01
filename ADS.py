#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 12 13:56:50 2018

@author: zdhughes
"""

#TODO: Finishing porting traceAnalysis into the program.
#scp zdhughes@herc3:~/c_ether/server_FADC.c ./
#gcc server_FADC.c -lfadc -lvme -lm -o server


import sys
from PyQt5 import QtWidgets
from traceGUI import Ui_MainWindow
import numpy as np
import traceAnalysis
import Simulate
import Capture
import os
import bitmasks
import struct
import settings as g
import queue

class Window(QtWidgets.QMainWindow, Ui_MainWindow, traceAnalysis.Mixin, Simulate.Mixin, Capture.Mixin):
	
	'''This is the main application window.'''
	
	def __init__(self):
		


		#Execute the QMainWindow __init__. 
		#QMainWindow is a QWidget; a widget without a parent is a window.
		super().__init__()
		#Draw all the stuff from the UI file.
		self.setupUi(self)

		#Set-up some variables.
		#Simulate Tab
		self.stopSignal = False
		self.time = np.linspace(0,10,10000)
		self.samplesPerTime = 100
		self.gaussianWidth = 1
		self.Nph = 1
		self.factor = 1.
		self.std = 0.00033432*3
		self.place = -1
		
		#Event Caputre Tab
		self.ServerSet.setText('10.0.7.21:3491') #'10.0.7.11:3491' -> '10.0.7.21:3491'
		self.constraint = 1
		self.capture_type = self.checkInitialCaptureType()
		self.spillNum = None
		
		self.DirectorySet.setText('./data')
		self.directory = None
		self.FilenameSet.setText('run')
		self.filename = None
		self.spill = None
		self.saveData = self.SaveDataCB.isChecked()
		#self.verbose = True
		self.verbose = self.VerboseCB.isChecked()
		self.reread = self.RereadCB.isChecked()
		self.livePlot = self.LivePlotCB.isChecked()
		self.plot_selection = self.PlotReadRadio.isChecked()
		self.guiQueueIn = queue.Queue()
		self.guiQueueOut = queue.Queue()
		
		self.channelsSelected = 0
		self.channels = [
			self.Channel0CB,
			self.Channel1CB,
			self.Channel2CB,
			self.Channel3CB,
			self.Channel4CB,
			self.Channel5CB,
			self.Channel6CB,
			self.Channel7CB,
			self.Channel8CB,
			self.Channel9CB,
			self.Channel10CB,
			self.Channel11CB,
			self.Channel12CB,
			self.Channel13CB,
			self.Channel14CB,
			self.Channel15CB,
			self.Channel16CB,
			self.Channel17CB,
			self.Channel18CB,
			self.Channel19CB,
			self.Channel20CB,
			self.Channel21CB,
			self.Channel22CB,
			self.Channel23CB,
			self.Channel24CB,
			self.Channel25CB,
			self.Channel26CB,
			self.Channel27CB,
			self.Channel28CB,
			self.Channel29CB
			]
		
		self.boardsSelected = 0
		self.boards = [
			self.Board0CB,
			self.Board1CB,
			self.Board2CB
			]
		
		#Setup all the signals and slots.
		#TraceAnalysis tab
		self.BrowseButton.clicked.connect(self.pickAFile)
		self.LoadButton.clicked.connect(self.loadAfile)
		self.PreviousTraceButton.clicked.connect(self.plotPreviousTrace)
		self.NextTraceButton.clicked.connect(self.plotNextTrace)
		
		#Event Capture Tab
		self.ConnectServerButton.clicked.connect(self.connectServerAction)
		self.SingleEventButton.clicked.connect(self.singleEventAction)	
		self.DurationRadio.toggled.connect(self.selectDurationCapture)
		self.DurationButton.clicked.connect(self.setDuration)
		self.EventRadio.toggled.connect(self.selectEventCapture)
		self.EventButton.clicked.connect(self.setEvent)
		self.TimeoutRadio.toggled.connect(self.selectTimeoutCapture)
		self.TimeoutButton.clicked.connect(self.setTimeout)
		self.ContinuousRadio.toggled.connect(self.selectContinuousCapture)
		self.CloseServerButton.clicked.connect(self.closeServer)
		self.StartButton.clicked.connect(self.startAcquire)
		self.StopButton.clicked.connect(self.stopAcquire)

		self.ClearEventButton.clicked.connect(self.clearEventAction)
		#https://stackoverflow.com/questions/940555/pyqt-sending-parameter-to-slot-when-connecting-to-a-signal	
		self.DataWidthGetButton.clicked.connect(lambda: self.universalGet(g.GET_DATA_WIDTH))
		self.DataOffsetGetButton.clicked.connect(lambda: self.universalGet(g.GET_DATA_OFFSET))
		self.AreaWidthGetButton.clicked.connect(lambda: self.universalGet(g.GET_AREA_WIDTH))
		self.AreaOffsetGetButton.clicked.connect(lambda: self.universalGet(g.GET_AREA_OFFSET))
		self.RereadWidthGetButton.clicked.connect(lambda: self.universalGet(g.GET_REREAD_WIDTH))
		self.RereadOffsetGetButton.clicked.connect(lambda: self.universalGet(g.GET_REREAD_OFFSET))
		self.HILOWidthGetButton.clicked.connect(lambda: self.universalGet(g.GET_HILO_WIDTH))
		self.HILOOffsetGetButton.clicked.connect(lambda: self.universalGet(g.GET_HILO_OFFSET))
		self.CFDThreshGetButton.clicked.connect(lambda: self.universalGet(g.GET_CFD_THRESH))
		self.ZSLGetButton.clicked.connect(lambda: self.universalGet(g.GET_0_SUPRESS_LEVEL))
		
		self.DataWidthSetButton.clicked.connect(lambda: self.universalSet(g.SET_DATA_WIDTH))
		self.DataOffsetSetButton.clicked.connect(lambda: self.universalSet(g.SET_DATA_OFFSET))
		self.AreaWidthSetButton.clicked.connect(lambda: self.universalSet(g.SET_AREA_WIDTH))
		self.AreaOffsetSetButton.clicked.connect(lambda: self.universalSet(g.SET_AREA_OFFSET))
		self.RereadWidthSetButton.clicked.connect(lambda: self.universalSet(g.SET_REREAD_WIDTH))
		self.RereadOffsetSetButton.clicked.connect(lambda: self.universalSet(g.SET_REREAD_OFFSET))
		self.HILOWidthSetButton.clicked.connect(lambda: self.universalSet(g.SET_HILO_WIDTH))
		self.HILOOffsetSetButton.clicked.connect(lambda: self.universalSet(g.SET_HILO_OFFSET))
		self.CFDThreshSetButton.clicked.connect(lambda: self.universalSet(g.SET_CFD_THRESH))
		self.ZSLSetButton.clicked.connect(lambda: self.universalSet(g.SET_0_SUPRESS_LEVEL))

		
		self.DirectoryButton.clicked.connect(self.setCaptureDirectory)
		self.FilenameButton.clicked.connect(self.setCaptureFilename)
		self.SpillButton.clicked.connect(self.setCaptureSpillNum)
		self.SaveDataCB.stateChanged.connect(self.toggleSaveData)
		self.VerboseCB.stateChanged.connect(self.toggleVerbose)
		
		self.Board0CB.stateChanged.connect(self.getBoards)
		self.Board1CB.stateChanged.connect(self.getBoards)
		self.Board2CB.stateChanged.connect(self.getBoards)
		self.SelectAllBoardsCB.stateChanged.connect(self.selectAllBoards)
		
		self.Channel0CB.stateChanged.connect(self.getChannels)
		self.Channel1CB.stateChanged.connect(self.getChannels)
		self.Channel2CB.stateChanged.connect(self.getChannels)
		self.Channel3CB.stateChanged.connect(self.getChannels)
		self.Channel4CB.stateChanged.connect(self.getChannels)
		self.Channel5CB.stateChanged.connect(self.getChannels)
		self.Channel6CB.stateChanged.connect(self.getChannels)
		self.Channel7CB.stateChanged.connect(self.getChannels)
		self.Channel8CB.stateChanged.connect(self.getChannels)
		self.Channel9CB.stateChanged.connect(self.getChannels)
		self.Channel10CB.stateChanged.connect(self.getChannels)
		self.Channel11CB.stateChanged.connect(self.getChannels)
		self.Channel12CB.stateChanged.connect(self.getChannels)
		self.Channel13CB.stateChanged.connect(self.getChannels)
		self.Channel14CB.stateChanged.connect(self.getChannels)
		self.Channel15CB.stateChanged.connect(self.getChannels)
		self.Channel16CB.stateChanged.connect(self.getChannels)
		self.Channel17CB.stateChanged.connect(self.getChannels)
		self.Channel18CB.stateChanged.connect(self.getChannels)
		self.Channel19CB.stateChanged.connect(self.getChannels)
		self.Channel20CB.stateChanged.connect(self.getChannels)
		self.Channel21CB.stateChanged.connect(self.getChannels)
		self.Channel22CB.stateChanged.connect(self.getChannels)
		self.Channel23CB.stateChanged.connect(self.getChannels)
		self.Channel24CB.stateChanged.connect(self.getChannels)
		self.Channel25CB.stateChanged.connect(self.getChannels)
		self.Channel26CB.stateChanged.connect(self.getChannels)
		self.Channel27CB.stateChanged.connect(self.getChannels)
		self.Channel28CB.stateChanged.connect(self.getChannels)
		self.Channel29CB.stateChanged.connect(self.getChannels)
		self.SelectAllChannelsCB.stateChanged.connect(self.selectAllChannels)
		
		self.RereadCB.stateChanged.connect(self.toggleReread)
		
		self.LivePlotCB.stateChanged.connect(self.toggleLivePlot)
		self.PlotReadRadio.toggled.connect(self.setPlotSelection)
		self.PlotRereadRadio.toggled.connect(self.setPlotSelection)
		
		#Simulation tab.
		self.CsIPDFButton.clicked.connect(self.loadCsIPDF)
		self.ChannelPDFButton.clicked.connect(self.loadChannelPDF)	
		self.PEPDFButton.clicked.connect(self.loadPEPDF)
		self.GaussianPECB.stateChanged.connect(self.gaussianCBChange) #This blocks PEPDFButton and enables GaussianPEButton
		self.GaussianPEButton.clicked.connect(self.gaussianPDFSet)
		self.NPEButton.clicked.connect(self.setNph)
		self.FactorButton.clicked.connect(self.setFactor)
		self.SimulateButton.clicked.connect(self.simulatePulse)
		
	def setCaptureDirectory(self):
		 self.directory = str(self.DirectorySet.text())
		 self.DirectoryRO.setText(self.directory)
		 if self.directory is not None and self.filename is not None and self.spillNum is not None:
			 self.path = os.path.abspath(self.directory+'/'+self.filename+'_'+str(self.spillNum).zfill(6)+'.fits')
			 self.PathRO.setText(self.path)

	def setCaptureFilename(self):
		self.filename = str(self.FilenameSet.text())
		self.FilenameRO.setText(self.filename)
		if self.directory is not None and self.filename is not None and self.spillNum is not None:
 			self.path = os.path.abspath(self.directory+'/'+self.filename+'_'+str(self.spillNum).zfill(6)+'.fits')
 			self.PathRO.setText(self.path)
			 
	def setCaptureSpillNum(self):
		self.spillNum = int(self.SpillSet.text())
		self.SpillRO.setText(str(self.spillNum).zfill(6))
		if self.directory is not None and self.filename is not None and self.spillNum is not None:
 			self.path = os.path.abspath(self.directory+'/'+self.filename+'_'+str(self.spillNum).zfill(6)+'.fits')
 			self.PathRO.setText(self.path)	 
			 
	def updatePath(self):
		self.spillNum += 1
		self.SpillRO.setText(str(self.spillNum).zfill(6))
		self.path = os.path.abspath(self.directory+'/'+self.filename+'_'+str(self.spillNum).zfill(6)+'.fits')
		self.PathRO.setText(self.path)
		
	def toggleLivePlot(self):
		self.livePlot = not self.livePlot
 			
	def toggleSaveData(self):
		self.saveData = not self.saveData
		
	def selectAllChannels(self):
		
		status = self.Channel0CB.isEnabled()
		
		for channel in self.channels:
			channel.setEnabled(not status)
			
		if status:
			self.oldChannelState = self.channelsSelected
			self.channelsSelected = 0x3FFFFFFF
		else:
			self.channelsSelected = self.oldChannelState 

		print(format(self.channelsSelected, '#034b'))
			   
	def setPlotSelection(self):
		self.plot_selection = self.PlotReadRadio.isChecked()
		
	def getChannels(self):
		
		self.channelsSelected = 0
		
		for i, channel in enumerate(self.channels):
			if channel.isChecked():
				self.channelsSelected += 1 << i
		
		print(format(self.channelsSelected, '#034b'))
			   
	def selectAllBoards(self):
		
		status = self.Board0CB.isEnabled()
		
		for board in self.boards:
			board.setEnabled(not status)
			
		if status:
			self.oldBoardState = self.boardsSelected
			self.boardsSelected = 0x3FFFFFFF
		else:
			self.boardsSelected = self.oldBoardState 

		print(format(self.boardsSelected, '#034b'))		
		
	def getBoards(self):
		
		self.boardsSelected = 0
		
		for i, board in enumerate(self.boards):
			if board.isChecked():
				self.boardsSelected += 1 << i
		
		print(format(self.boardsSelected, '#034b'))
   
	def checkInitialCaptureType(self):
		   if self.DurationRadio.isChecked():
			   return g.TIMED_CBLT
		   elif self.EventRadio.isChecked():
			   return g.EVENT_CBLT
		   elif self.TimeoutRadio.isChecked():
			   return g.AUTOMATED_CBLT
		   elif self.ContinuousRadio.isChecked():
			   return g.CONTINUOUS_CBLT
		   else:
			   print('Something went wrong with initial capture determination!')
			   return -1
		

app = QtWidgets.QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec_())