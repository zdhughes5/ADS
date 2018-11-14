#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 12 13:57:22 2018

@author: zdhughes
"""

import ADS_socket
import threading
from PyQt5.QtCore import pyqtSignal, QThread, QObject, pyqtSlot
import settings as g
import struct
import sys
import bitmasks
import subprocess
import numpy as np
from herc.io_functions import colors
import matplotlib.pyplot as plt
from astropy.io import fits
import multiprocessing as mp
import queue
from time import sleep
from traceGUI import Ui_MainWindow
import pickle

########## CAPTURE TAB ##########

class Mixin:
	
	""" This is just a Mixin class to hold all the capture actions for the Event Capture tab. """
	
	@pyqtSlot()
	def connectServerAction(self):
		
		""" Reads in and connects to the HOST:PORT string entered
		into the textbox using ADS_socket class. """
		
		self.currentHost = self.ServerSet.text()
		self.ServerRO.setText(self.currentHost)
		
		self.ADS_socket = ADS_socket.ADS_socket(self.currentHost)
		
		self.enableOnConnect()


	
	@pyqtSlot()
	def enableOnConnect(self):
		
		self.ConnectServerButton.setEnabled(False)
		self.RereadCB.setEnabled(True)
		self.VerboseCB.setEnabled(True)
		self.LivePlotCB.setEnabled(True)
		self.PlotReadRadio.setEnabled(True)
		self.PlotRereadRadio.setEnabled(True)
		self.StartButton.setEnabled(True)
		self.SingleEventButton.setEnabled(True)
		self.ClearEventButton.setEnabled(True)
		self.CloseServerButton.setEnabled(True)
		self.TimeInButton.setEnabled(True)
			
		
	@pyqtSlot()
	def singleEventAction(self):
		
		""" This asks the server for a single event. """
		
		self.ADS_socket.sendCommandToServer(g.SINGLE_CBLT, 1, '1U-S Sent Value: %d with length %d (Command Request).')
		server_rendevous = self.ADS_socket.receiveCommandFromServer(1, '1S-R Received Value: %d with length %d (CBLT Status Rendevous).')
		if server_rendevous != g.RENDEVOUS_PROCEED:
			print('Got bad rendevous from server. Breaking.')
			return
		self.ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, '2S-S Received Value: %d with length %d (Send nwords Rendevous).')
		nwords = self.ADS_socket.receiveCommandFromServer(4, '3S-R Received Value: %d with length %d (nwords value).')
		self.ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, '4S-S Sent Value: %d with length %d (Send CBLT Rendevous).')	
		self.raw_data = self.ADS_socket.recv_all(nwords, '5S-R Received Value: %d with length %d (CBLT data).') #raw is the bytearray, cblt the numpy array.
		self.ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, '6S-S Sent Value: %d with length %d (CBLT complete Rendevous).')
		self.this_capture = CBLTData(self.raw_data)
		self.this_capture.wordifyBinaryData()
		if self.verbose:
			bitmasks.printWordBlocks(self.this_capture.words)
			
		
		if self.reread:
			server_rendevous = self.ADS_socket.receiveCommandFromServer(1, '7S-R Sent Value: %d with length %d (CBLT reread Status Rendevous).')
			if server_rendevous != g.RENDEVOUS_PROCEED:
				print('Got bad rendevous from server. Breaking.')
				return			
			self.ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, '8S-S Received Value: %d with length %d (Send reread nwords Rendevous).')		
			reread_nwords = self.ADS_socket.receiveCommandFromServer(4, '9S-R Sent Value: %d with length %d (reread nwords value).')
			self.ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, '10S-R Received Value: %d with length %d (Send reread CBLT Rendevous).')	
			self.raw_reread_data = self.ADS_socket.recv_all(reread_nwords, '11S-R Sent Value: %d with length %d (reread CBLT data).') #raw is the bytearray, cblt the numpy array.
			self.ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, '12S-R Received Value: %d with length %d (reread CBLT compelete Rendevous).')			
			self.this_capture_reread = CBLTData(self.raw_reread_data)
			self.this_capture_reread.wordifyBinaryData()
			if self.verbose:
				bitmasks.printWordBlocks(self.this_capture_reread.words)
				
				
			sys.stdout.flush()
		if self.saveData:
			with open(self.path, 'wb') as f:
				f.write(self.this_capture.binary_data)
			self.fileNum += 1
			self.updatePath()
		print('Command Complete.')
	
	@pyqtSlot()	
	def clearEventAction(self):
		self.ADS_socket.sendCommandToServer(g.CLEAR_EVENT, 1, '1U-S Sent Value: %d with length %d (Command Request).')
		return
	
	@pyqtSlot()
	def toggleReread(self):

		
		self.reread = self.RereadCB.isChecked()
		self.ADS_socket.sendCommandToServer(g.SET_REREAD_MODE, 1, '1U-S Sent Value: %d with length %d (Command Request).')
		server_rendevous = self.ADS_socket.receiveCommandFromServer(1, '1S-R Sent Value: %d with length %d (Send status Rendevous).')

		if server_rendevous == g.RENDEVOUS_PROCEED:
			if self.RereadCB.isChecked():
				self.ADS_socket.sendCommandToServer(g.REREAD_ON, 1, '2S-S Received Value: %d with length %d (Reread status).')
			else:
				self.ADS_socket.sendCommandToServer(g.REREAD_OFF, 1, '2S-S Received Value: %d with length %d (Reread status).')
		else:
			print('Got bad rendevous from server. Breaking.')

		return
	
	@pyqtSlot()
	def toggleVerbose(self):

		
		self.verbose = self.VerboseCB.isChecked()
		self.ADS_socket.sendCommandToServer(g.SET_VERBOSITY, 1, '1U-S Sent Value: %d with length %d (Command Request).')
		server_rendevous = self.ADS_socket.receiveCommandFromServer(1, '1S-R Sent Value: %d with length %d (Send status Rendevous).')

		if server_rendevous == g.RENDEVOUS_PROCEED:
			if self.VerboseCB.isChecked():
				self.ADS_socket.sendCommandToServer(g.VERBOSE_ON, 1, '2S-S Received Value: %d with length %d (Verbose status).')
			else:
				self.ADS_socket.sendCommandToServer(g.VERBOSE_OFF, 1, '2S-S Received Value: %d with length %d (Verbose status).')
		else:
			print('Got bad rendevous from server. Breaking.')

		return	
		
	@pyqtSlot()
	def universalGet(self, get_request):
		
		valuesGot = []
		server_rendevous = 1

		self.ADS_socket.sendCommandToServer(get_request, 1, '1C-S Sent Value: %d with length %d (Command Request).')

		
		while server_rendevous == 1:
			server_rendevous = 255
			server_rendevous = self.ADS_socket.receiveCommandFromServer(1, '1G-R Received Value: %d with %d bytes (Getter OK Rendevous).')
			if server_rendevous != 1:
				print('Got bad rendevous from server. Breaking.')
				break
			server_rendevous = 255
			self.ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, '2G-S Sent Value: %d with %d bytes (Send Value Rendevous).')
			valuesGot += [self.ADS_socket.receiveCommandFromServer(4, '3G-R Received Value: %d with %d bytes (Parameter Send).')]
			self.ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, '4G-S Sent Value: %d with %d bytes (Got Parameter Rendevous).')
			server_rendevous = self.ADS_socket.receiveCommandFromServer(1, '5G-R Received Value: %d with %d bytes (Continue Rendevous).')


		
		print('Got these Values for get:')
		for i, value in enumerate(valuesGot):
			print(str(i)+': '+str(value))
		#index = [x for x in range(len(valuesGot))]
		#pairs = [[str(index[x]),str(valuesGot[x])] for x in range(len(valuesGot))]
		#pairedUp = [':'.join(x) for x in pairs]
		#output = ', '.join(pairedUp)
		#print(output)

	@pyqtSlot()			
	def universalSet(self, set_request):

		selection = self.channelsSelected
		
		if set_request == g.SET_DATA_WIDTH:
			set_value = int(self.DataWidthSet.text())	
			self.DataWidthRO.setText(str(set_value))
			selection = self.boardsSelected
		elif set_request == g.SET_DATA_OFFSET:
			set_value = int(self.DataOffsetSet.text())
			self.DataOffsetRO.setText(str(set_value))
		elif set_request == g.SET_AREA_WIDTH:
			set_value = int(self.AreaWidthSet.text())
			self.AreaWidthRO.setText(str(set_value))
		elif set_request == g.SET_AREA_OFFSET:
			set_value = int(self.AreaOffsetSet.text())
			self.AreaOffsetRO.setText(str(set_value))
		elif set_request == g.SET_REREAD_WIDTH:
			set_value = int(self.RereadWidthSet.text())
			self.RereadWidthRO.setText(str(set_value))
			selection = self.boardsSelected
		elif set_request == g.SET_REREAD_OFFSET:
			set_value = int(self.RereadOffsetSet.text())
			self.RereadOffsetRO.setText(str(set_value))
		elif set_request == g.SET_HILO_WIDTH:
			set_value = int(self.HILOWidthSet.text())
			self.HILOWidthRO.setText(str(set_value))
			selection = self.boardsSelected
		elif set_request == g.SET_HILO_OFFSET:
			set_value = int(self.HILOOffsetSet.text())
			self.HILOOffsetRO.setText(str(set_value))
		elif set_request == g.SET_CFD_THRESH:
			set_value = int(self.CFDThreshSet.text())
			self.CFDThreshRO.setText(str(set_value))
		elif set_request == g.SET_0_SUPRESS_LEVEL:
			set_value = int(self.ZSLSet.text())
			self.ZSLRO.setText(str(set_value))
		else:
			print('Bad set command. Returning.')
			return
		
		
		self.ADS_socket.sendCommandToServer(set_request, 1, '1C-S Sent Value: %d with length %d (Command Request).')	
		server_rendevous = self.ADS_socket.receiveCommandFromServer(1, '1S-R Received Value: %d with %d bytes (Setter OK Rendevous).')
		if server_rendevous == 1:
			server_rendevous = 255
			self.ADS_socket.sendCommandToServer(selection, 4, '2S-S Sent Value: %d with %d bytes (Send channels).')
		else:
			print('Got bad rendevous from server. Breaking.')
		server_rendevous = self.ADS_socket.receiveCommandFromServer(1, '3S-R Received Value: %d with %d bytes (Channels OK Rendevous).')
		if server_rendevous == 1:
			server_rendevous = 255
			self.ADS_socket.sendCommandToServer(set_value, 4, '4S-S Sent Value: %d with %d bytes (Send Value).')
		else:
			print('Got bad rendevous from server. Breaking.')
		server_rendevous = self.ADS_socket.receiveCommandFromServer(1, '5S-R Received Value: %d with %d bytes (Setter Complete Rendevous).')
				

	@pyqtSlot(int)		
	def flipButtonStates(self, capture_type):
		
		""" Flips the button states when starting and stopping the event capture.
			Should only be called from the main thread. """
		
		self.RereadCB.setEnabled(not self.RereadCB.isEnabled())
		self.VerboseCB.setEnabled(not self.VerboseCB.isEnabled())
		self.DurationRadio.setEnabled(not self.DurationRadio.isEnabled())
		self.EventRadio.setEnabled(not self.EventRadio.isEnabled())
		self.TimeoutRadio.setEnabled(not self.TimeoutRadio.isEnabled())
		self.ContinuousRadio.setEnabled(not self.ContinuousRadio.isEnabled())
		self.LivePlotCB.setEnabled(not self.LivePlotCB.isEnabled())
		self.PlotReadRadio.setEnabled(not self.PlotReadRadio.isEnabled())
		self.PlotRereadRadio.setEnabled(not self.PlotRereadRadio.isEnabled())
		self.StartButton.setEnabled(not self.StartButton.isEnabled())
		self.StopButton.setEnabled(not self.StartButton.isEnabled())
		self.SingleEventButton.setEnabled(not self.SingleEventButton.isEnabled())
		self.ClearEventButton.setEnabled(not self.ClearEventButton.isEnabled())
		self.CloseServerButton.setEnabled(not self.CloseServerButton.isEnabled())
		self.DirectoryButton.setEnabled(not self.DirectoryButton.isEnabled())
		self.FilenameButton.setEnabled(not self.FilenameButton.isEnabled())
		self.SpillButton.setEnabled(not self.SpillButton.isEnabled())
		self.SaveDataCB.setEnabled(not self.SaveDataCB.isEnabled())
		if capture_type == g.TIMED_CBLT:
			self.DurationButton.setEnabled(not self.DurationButton.isEnabled())
		elif capture_type == g.EVENT_CBLT:
			self.EventButton.setEnabled(not self.EventButton.isEnabled())
		elif capture_type == g.AUTOMATED_CBLT:
			self.TimeoutButton.setEnabled(not self.TimeoutButton.isEnabled())
		
	@pyqtSlot()
	def startAcquire(self):
		
		if self.constraint == None:
			print("Constraint is NoneType. Did you forget to press 'Set'?")
			return
	
		self.spill = SpillHolder()
		self.stop_event = mp.Event()
		self.cont_event = mp.Event()
		self.workerThread = QThread()
		self.worker = captureWorker(self.ADS_socket, self.spill, self.stop_event, self.guiQueueIn, self.guiQueueOut, self.livePlot, self.plot_selection, self.capture_type, self.constraint, self.verbose, self.reread)
		self.worker.flipStateSignal.connect(self.flipButtonStates)
		self.worker.updateGUISignal.connect(self.updateLivePlot)
		self.workerThread.finished.connect(self.notifyFinished)
		self.worker.moveToThread(self.workerThread)
		self.workerThread.started.connect(self.worker.beginCapture)
		self.workerThread.start()
		if self.livePlot == True:
			self.guiQueueIn.put(('plotReady', True))
		self.workerThread.quit()
		
	@pyqtSlot()
	def updateLivePlot(self):
		
		try:
			guiQueueItem = self.guiQueueOut.get(False)
			if guiQueueItem[0] == 'plotData':
				#self.LivePlotWidget.clearAll() #This deletes the plotItem object, I think. Don't need it to update plot.
				for i, board in enumerate(guiQueueItem[1].boards[1:]):
					#self.LivePlotWidget.isThisRight[10*i+0].setData(data)
					print(board)
					print('+++++++++++++++++++++++++++++++++++++++')
					self.LivePlotWidget.dataChannel[10*i+0].setData(board['Channel 0']['ADC'])
					self.LivePlotWidget.dataChannel[10*i+1].setData(board['Channel 1']['ADC'])
					self.LivePlotWidget.dataChannel[10*i+2].setData(board['Channel 2']['ADC'])
					self.LivePlotWidget.dataChannel[10*i+3].setData(board['Channel 3']['ADC'])
					self.LivePlotWidget.dataChannel[10*i+4].setData(board['Channel 4']['ADC'])
					self.LivePlotWidget.dataChannel[10*i+5].setData(board['Channel 5']['ADC'])
					self.LivePlotWidget.dataChannel[10*i+6].setData(board['Channel 6']['ADC'])
					self.LivePlotWidget.dataChannel[10*i+7].setData(board['Channel 7']['ADC'])
					self.LivePlotWidget.dataChannel[10*i+8].setData(board['Channel 8']['ADC'])
					try:
						self.LivePlotWidget.dataChannel[10*i+9].setData(board['Channel 9']['ADC'])
					except:
						print(bitmasks.printWordBlocks(guiQueueItem[1].words))
						print(guiQueueItem[1])
						print(guiQueueItem[1].binary_data)
# =============================================================================
# 					self.LivePlotWidget.plotChannel[10*i+0].plot(board['Channel 0']['ADC'])
# 					self.LivePlotWidget.plotChannel[10*i+1].plot(board['Channel 1']['ADC'])
# 					self.LivePlotWidget.plotChannel[10*i+2].plot(board['Channel 2']['ADC'])
# 					self.LivePlotWidget.plotChannel[10*i+3].plot(board['Channel 3']['ADC'])
# 					self.LivePlotWidget.plotChannel[10*i+4].plot(board['Channel 4']['ADC'])
# 					self.LivePlotWidget.plotChannel[10*i+5].plot(board['Channel 5']['ADC'])
# 					self.LivePlotWidget.plotChannel[10*i+6].plot(board['Channel 6']['ADC'])
# 					self.LivePlotWidget.plotChannel[10*i+7].plot(board['Channel 7']['ADC'])
# 					self.LivePlotWidget.plotChannel[10*i+8].plot(board['Channel 8']['ADC'])
# 					self.LivePlotWidget.plotChannel[10*i+9].plot(board['Channel 9']['ADC'])
# =============================================================================
					
				#self.LivePlotWidget.p0.plot(guiQueueItem[1].boards[1]['Channel 0']['ADC'])
				#self.LivePlotWidget.p1.plot(guiQueueItem[1].boards[1]['Channel 1']['ADC'])
				#self.LivePlotWidget.plot(guiQueueItem[1].boards[1]['Channel 0']['ADC'])
				self.guiQueueIn.put(('plotReady', True))
			elif guiQueueItem[0] == 'spill':
				print('Got the spill on the update signal. Woah!')
				self.spill = guiQueueItem[1]
			else:
				print('Got something in the gui queue in the update:')
				print(guiQueueItem)
			
		except queue.Empty:
			print('Got GUI update signal but queue is empty.')
	

	@pyqtSlot()		
	def stopAcquire(self):
		
		""" Sets the capture thread stop_event to True. """
		
		self.stop_event.set()
		self.cont_event.set()

	@pyqtSlot()		
	def notifyFinished(self):
		
		""" Just something to do when a thread emits a finsihed signal. """

		print('Worker is finished. Here is the spill data.')
		#print('The guiqueue is empty:')
		#print(self.guiQueueOut.empty())
		while not self.guiQueueOut.empty():
			try:
				guiQueueItem = self.guiQueueOut.get()
				if guiQueueItem[0] == 'spill':
					print('Found the spill')
					self.spill = guiQueueItem[1]
					if self.saveData == True:
						if len(self.spill.cblts) > 0:
							print('CBLT Number: '+str(len(self.spill.cblts)))
							print('Rereads Number: '+str(len(self.spill.rereads)))
							print('Saving Data...')
							p = mp.Process(target=spillDumpProcess, args=(self.spill, self.directory, self.path))
							p.start()	
							pf = mp.Process(target=spillParseProcess, args=(self.spill, self.directory, self.path))
							pf.start()
							self.updatePath()
							print('Done')
						else:
							print('There seems to be no CBLTs in the spill. Updating path to next spill.')
							self.updatePath()
				else:
					print('Something weird when gui thread looks in gui queue!')
					print(guiQueueItem)
			except queue.Empty:
				pass
			
		print('There were %d cblts.' % len(self.spill.cblts))
		self.flipButtonStates(self.capture_type)
		
		#print(self.cont_event.is_set())
		#print(self.capture_type)
		#print(g.EVENT_CBLT )
		
		if self.capture_type == g.AUTOMATED_CBLT and self.cont_event.is_set() == False:
			print('Rerunning')
			self.startAcquire()

	@pyqtSlot()		
	def selectDurationCapture(self):
		
		""" Used to select the duration capture option. 
			Clears whatever the constraint was before. """
		
		self.DurationSet.setEnabled(True)
		self.DurationButton.setEnabled(True)
		self.EventSet.setEnabled(False)
		self.EventButton.setEnabled(False)
		self.TimeoutSet.setEnabled(False)
		self.TimeoutButton.setEnabled(False)
		self.EventRO.clear()
		self.constraint = None
		self.capture_type = g.TIMED_CBLT

	@pyqtSlot()		
	def selectEventCapture(self):
		
		""" Used to select the event capture option. 
			Clears whatever the constraint was before. """
		
		self.DurationSet.setEnabled(False)
		self.DurationButton.setEnabled(False)
		self.EventSet.setEnabled(True)
		self.EventButton.setEnabled(True)
		self.TimeoutSet.setEnabled(False)
		self.TimeoutButton.setEnabled(False)
		self.DurationRO.clear()
		self.constraint = None
		self.capture_type = g.EVENT_CBLT
		
	@pyqtSlot()		
	def selectTimeoutCapture(self):
		
		""" Used to select the timeout capture option. 
			Clears whatever the constraint was before. """
		
		self.DurationSet.setEnabled(False)
		self.DurationButton.setEnabled(False)
		self.EventSet.setEnabled(False)
		self.EventButton.setEnabled(False)
		self.TimeoutSet.setEnabled(True)
		self.TimeoutButton.setEnabled(True)
		self.TimeoutRO.clear()
		self.constraint = None
		self.capture_type = g.AUTOMATED_CBLT
	
	@pyqtSlot()		
	def selectContinuousCapture(self):
		
		""" Used to select the continuous capture option. 
			Clears whatever the constraint was before (and sets it to 1). """		
		
		self.DurationSet.setEnabled(False)
		self.DurationButton.setEnabled(False)
		self.EventSet.setEnabled(False)
		self.EventButton.setEnabled(False)
		self.TimeoutSet.setEnabled(False)
		self.TimeoutButton.setEnabled(False)
		self.DurationRO.clear()
		self.EventRO.clear()
		self.TimeoutRO.clear()		
		self.constraint = 1
		self.capture_type = g.CONTINUOUS_CBLT

	@pyqtSlot()
	def setDuration(self):
		
		""" Sets the constraint variable from the what is in the duration set box. """
		
		self.constraint = int(self.DurationSet.text())
		self.DurationRO.setText(str(self.constraint))

	@pyqtSlot()
	def setEvent(self):
		
		""" Sets the constraint variable from the what is in the event set box. """
		
		self.constraint = int(self.EventSet.text())
		self.EventRO.setText(str(self.constraint))
		
	@pyqtSlot()
	def setTimeout(self):
		
		""" Sets the constraint variable from the what is in the timeout set box. """
		
		self.constraint = int(self.TimeoutSet.text())
		self.TimeoutRO.setText(str(self.constraint))

	@pyqtSlot()		
	def closeServer(self):
		
		""" Sends the server command '255' which ends the server program. """
		
		self.ADS_socket.sendCommandToServer(g.CLOSE_SERVER, 1, '1CL-S Sent Value: %d with length %d (close request).')
		
		server_status = self.ADS_socket.receiveCommandFromServer(16, '2CL-R Received Value: %d of length %d (close status).')
		
		if server_status == g.SERVER_CLOSED:
			print('It closed.')
		else:
			print('Something went wrong with closing the server.')
		self.ConnectServerButton.setEnabled(True)
		
		
class HaltCapture(Exception):
	
	""" An exception to be used to break while loops from a function. """
	
	pass

class CBLTData:
	
	def __init__(self, binary_data, endianness = '<', wordSize = 4):
		self.binary_data = binary_data
		self.endianness = endianness
		self.wordSize = wordSize
		self.words = None

	def __getitem__(self, key):
		return self.boards[key]

	def wordifyBinaryData(self):
		
		self.nwords = int(len(self.binary_data)/self.wordSize)
		self.formatCode = self.endianness+'I'*self.nwords
		
		self.words = np.array(struct.unpack(self.formatCode, self.binary_data))
		
	def parseWords(self):
		
		if self.words is None:
			self.wordifyBinaryData()
		
		self.boards = bitmasks.parseFADCsNew(self.words)
		

class SpillHolder:
	
	def __init__(self):
		self.cblts = []
		self.rereads = []
		self.boardNum = None
		
	def __getitem__(self, key):
		return self.cblts[key]
	
	def addCBLT(self, CBLT, reread = False):
		
		if reread:
			self.rereads.append(CBLT)
		else:
			self.cblts.append(CBLT)
		
	def addBinary(self, binary_data, reread = False):
		
		if reread:
			CBLT = CBLTData(binary_data)
			self.rereads.append(CBLT)
		else:
			CBLT = CBLTData(binary_data)
			self.cblts.append(CBLT)
		
		
	def parseCBLTs(self):
		
		for cblt in self.cblts:
			cblt.parseWords()
		for cblt in self.rereads:
			cblt.parseWords()
			
		self.boardNum = len(self.cblts[0].boards)
			
	def dumpBinary(self, directory, path):
		folder = path.split('/')[-1].split('.')[0]
		dumpDir = directory+'/'+folder+'/'
		subprocess.call('mkdir -p '+dumpDir, shell=True)
		for i, cblt in enumerate(self.cblts):
			with open(dumpDir+'read_'+str(i), 'wb') as f:
				f.write(cblt.binary_data)
		for i, reread in enumerate(self.rereads):
			with open(dumpDir+'reread_'+str(i), 'wb') as f:
				f.write(reread.binary_data)
				
	def clockHeader(self, data, reread = False):
		
		prefix = ''
		if reread == True:
			prefix = 'RR_'
		
		# CLK board
		# Start Header
		a1 = np.array([x[0]['Start Header']['0xCAFE'] for x in data])
		c1 = fits.Column(name=prefix+'0xCAFE', array=a1, format='I') #Unsigned

		a2 = np.array([x[0]['Start Header']['Board Number'] for x in data])
		c2 = fits.Column(name=prefix+'CLK_Board_Number', array=a2, format='B')

		a3 = np.array([x[0]['Start Header']['Serial Number'] for x in data])
		c3 = fits.Column(name=prefix+'Serial_Number', array=a3, format='B')
		
		# Event Header
		a4 = np.array([x[0]['Event Header']['EVT'] for x in data])
		c4 = fits.Column(name=prefix+'CLK_Event', array=a4, format='J')

		# Trigger Header		
		a5 = np.array([x[0]['Trig Header']['Trig EVT'] for x in data])
		c5 = fits.Column(name=prefix+'CLK_Trigger_Event', array=a5, format='I')

		a6 = np.array([x[0]['Trig Header']['Trig Code'] for x in data])
		c6 = fits.Column(name=prefix+'CLK_Trigger_Code', array=a6, format='I')	

		# GPS Header
		a7 = np.array([x[0]['GPS Header']['GPS Second'] for x in data])
		c7 = fits.Column(name=prefix+'GPS_Second', array=a7, format='J')	
		
		# Elapsed Header
		a8 = np.array([x[0]['Elapsed Header']['Elapsed Time Scalar'] for x in data])
		c8 = fits.Column(name=prefix+'Elapsed_Time_Scalar', array=a8, format='J')	

		# Livetime Header
		a9 = np.array([x[0]['Livetime Header']['Livetime Scalar'] for x in data])
		c9 = fits.Column(name=prefix+'Livetime_Scalar', array=a9, format='J')	

		# Elapsed Header
		a10 = np.array([x[0]['Dummy Header']['Dummy Register'] for x in data])
		c10 = fits.Column(name=prefix+'Dummy_Register', array=a10, format='J')	

		# Elapsed Header
		a11 = np.array([x[0]['Junk Header']['Junk Word'] for x in data])
		c11 = fits.Column(name=prefix+'Junk_Word', array=a11, format='J')	

		return (c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11)
			
	def fadcHeader(self, data, board_num, reread = False):
		
		prefix = ''
		if reread == True:
			prefix = 'RR_'
			
		ax1 = np.array([x[board_num]['Start Header']['0xFADC'] for x in data])
		cx1 = fits.Column(name=prefix+'Board_'+str(board_num)+'_0xFADC', array=ax1, format='I') #Unsigned
		ax2 = np.array([x[board_num]['Start Header']['Board Number'] for x in data])
		cx2 = fits.Column(name=prefix+'Board_'+str(board_num)+'_Board_Number', array=ax2, format='B')
		ax3 = np.array([x[board_num]['Start Header']['Words Per Channel'] for x in data])
		cx3 = fits.Column(name=prefix+'Board_'+str(board_num)+'_Words_Per_Channel', array=ax3, format='B')

		# Event Header
		ax4 = np.array([x[board_num]['Event Header']['Event Count'] for x in data])
		cx4 = fits.Column(name=prefix+'Board_'+str(board_num)+'_Event_Count', array=ax4, format='J') #Unsigned
		ax5 = np.array([x[board_num]['Event Header']['Misc. 6 bits'] for x in data])
		cx5 = fits.Column(name=prefix+'Board_'+str(board_num)+'_misc_bits', array=ax5, format='B')

		# Hit Header
		ax6 = np.array([x[board_num]['Hit Header']['Mode'] for x in data])
		cx6 = fits.Column(name=prefix+'Board_'+str(board_num)+'_Mode', array=ax6, format='B') #Unsigned
		ax7 = np.array([x[board_num]['Hit Header']['HILO'] for x in data])
		cx7 = fits.Column(name=prefix+'Board_'+str(board_num)+'_HILO', array=ax7, format='I')
		ax8 = np.array([x[board_num]['Hit Header']['Trigger Flags'] for x in data])
		cx8 = fits.Column(name=prefix+'Board_'+str(board_num)+'_Trigger_Flags', array=ax8, format='I')
		ax9 = np.array([x[board_num]['Hit Header']['Channel Hits'] for x in data])
		cx9 = fits.Column(name=prefix+'Board_'+str(board_num)+'_Channel_Hits', array=ax9, format='I')
	
		return (cx1, cx2, cx3, cx4, cx5, cx6, cx7, cx8, cx9)
	
	def fadcPayload(self, data, board_num, channel, reread = False):
		
		prefix = ''
		if reread == True:
			prefix = 'RR_'
		
		adcFormat = str(len(data[0][1]['Channel 1']['ADC']))+'B' #The first channel (['Channel 1']) of the first fadc board (1) of the first cblt (0)
		ax1 = np.array([x[board_num]['Channel '+str(channel)]['ADC'] for x in data])
		print(prefix+' '+str(len(ax1)))
		print(board_num)
		print(channel)
		
		for i in ax1:
			print(i)
			print('')
		cx1 = fits.Column(name=prefix+'Board_'+str(board_num)+'_Channel_'+str(channel)+'_ADC', array=ax1, format=adcFormat)
		
		ax2 = np.array([x[board_num]['Channel '+str(channel)]['Channel Number'] for x in data])
		cx2 = fits.Column(name=prefix+'Board_'+str(board_num)+'_Channel_'+str(channel), array=ax2, format='B')
		
		ax3 = np.array([x[board_num]['Channel '+str(channel)]['Unused'] for x in data])
		cx3 = fits.Column(name=prefix+'Board_'+str(board_num)+'_Channel_'+str(channel)+'_Unused', array=ax3, format='I')
		
		ax4 = np.array([x[board_num]['Channel '+str(channel)]['Pulse Area'] for x in data])
		cx4 = fits.Column(name=prefix+'Board_'+str(board_num)+'_Channel_'+str(channel)+'_Area', array=ax4, format='I')

		return (cx1, cx2, cx3, cx4)	
			
	def constructTable(self, directory, path):
		columns = []
		
		clkHeaders = self.clockHeader(self.cblts)
		for item in clkHeaders:
			columns.append(item)
			
		for i in range(1, self.boardNum):
			
			fadcHeaders = self.fadcHeader(self.cblts, i)
			for item in fadcHeaders:
				columns.append(item)

			for j in range(10):
				fadcPayload = self.fadcPayload(self.cblts, i, j)
				for item in fadcPayload:
					columns.append(item)
				
		if self.rereads:
			rr_clkHeaders = self.clockHeader(self.rereads, reread = True)
			for item in rr_clkHeaders:
				columns.append(item)
				
			for i in range(1, self.boardNum):
				
				rr_fadcHeaders = self.fadcHeader(self.rereads, i, reread = True)
				for item in rr_fadcHeaders:
					columns.append(item)
	
				for j in range(10):
					rr_fadcPayload = self.fadcPayload(self.rereads, i, j, reread = True)
					for item in rr_fadcPayload:
						columns.append(item)


		t = fits.BinTableHDU.from_columns(columns)
		subprocess.call('mkdir -p ' + directory, shell=True)
		t.writeto(path, overwrite=True)
		
def spillDumpProcess(spill, directory, path):
	print('Dumping binary...', end='')
	spill.dumpBinary(directory, path)
	
def spillParseProcess(spill, directory, path):
	print('Parsing...')
	spill.parseCBLTs()
	print('Saving Spill...', end='')
	spill.constructTable(directory, path)
	print('Done')		
		
		
class captureWorker(QObject):
	
	""" This object does the actual non-single-event capture. It is run in a seperate QThread. """
	
	flipStateSignal = pyqtSignal(int)
	updateGUISignal = pyqtSignal()
	
	def __init__(self, ADS_socket, spill, stop_event, guiQueueIn, guiQueueOut, livePlot, plot_selection, capture_type, constraint, verbose, reread, parent = None):
		super().__init__(parent)
		super(self.__class__, self).__init__(parent)
		self.ADS_socket = ADS_socket
		self.spill = spill
		self.stop_event = stop_event
		self.guiQueueIn = guiQueueIn
		self.guiQueueOut = guiQueueOut
		self.livePlot = livePlot
		self.plot_selection = plot_selection
		self.capture_type = capture_type
		self.constraint = constraint
		self.verbose = verbose
		self.reread = reread
		
		
	def beginCapture(self):
		
		self.intoQueue = mp.Queue()
		self.outofQueue = mp.Queue()
		#pool = mp.Pool()
		self.tester = 'tester!'
		self.lester = ' lester! '
		#universalCapture(self.ADS_socket, self.stop_event, self.livePlot, self.plot_selection, self.capture_type, self.constraint, self.verbose, self.reread, self.intoQueue, self.outofQueue)
		#pool_result = pool.apply_async(universalCapture, args=(self.ADS_socket, self.stop_event, self.livePlot, self.plot_selection, self.capture_type, self.constraint, self.verbose, self.reread, self.intoQueue, self.outofQueue))
		p = mp.Process(target=universalCapture, args=(self.ADS_socket, self.stop_event, self.livePlot, self.plot_selection, self.capture_type, self.constraint, self.verbose, self.reread, self.intoQueue, self.outofQueue))
		p.start()	
		
		while p.is_alive():
			try:
				queueItem = self.outofQueue.get(False)
				if queueItem[0] == 'flipStateSignal':
					self.flipStateSignal.emit(self.capture_type) #It's possible that the process ends after this line and the queus is not empty. Check at end of thread for stuff in the queue. Is the queue destroyed when the subprocess exits?
				elif queueItem[0] == 'plotData':
					self.guiQueueOut.put(queueItem)
					self.updateGUISignal.emit()
				elif queueItem[0] == 'spill':
					self.guiQueueOut.put(queueItem)
				else:
					print('Have a queue item but do not know what to do with it.')
					print(queueItem)
			except queue.Empty:
				pass

			try:
				guiQueueItem = self.guiQueueIn.get(False)
				if guiQueueItem[0] == 'plotReady':
					self.intoQueue.put(guiQueueItem)
				else:
					print('Have a GUI queue item but do not know what to do with it.')
					print(guiQueueItem)
			except queue.Empty:
				pass
			
		else:
			while not self.outofQueue.empty():
				queueItem = self.outofQueue.get(False)
				if queueItem[0] == 'flipStateSignal':
					self.flipStateSignal.emit(self.capture_type)
				elif queueItem[0] == 'plotData':
					pass
				elif queueItem[0] == 'spill':
					self.guiQueueOut.put(queueItem)
				else:
					print('Have a queue item but do not know what to do with it.')
		
		
	
		
def checkForStopEvent(ADS_socket, stop_event, **kwargs):
	
	""" Checks whether the stop_event has been set by the user.
		Based on the result it tells the server whether to halt or proceed. """
	
	if not stop_event.is_set():
		ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, **kwargs)
	else:
		ADS_socket.sendCommandToServer(g.RENDEVOUS_HALT, 1, **kwargs)
		print('Sent halt, breaking.')
		raise HaltCapture
		
def echo(thing, bing):
	print(thing+bing)
		
def universalCapture(ADS_socket, stop_event, livePlot, plot_selection, capture_type, constraint, verbose, reread, intoQueue, outofQueue):
	
	""" Starts the event capture. Capture_type is for the server cblt capture mode. 
		Constraint is the corresponding parameter that tells the server when to stop
		the capture. """
		
	statement1CS = None
	statement1UR = None
	statement2US = None
	statement3UR = None
	statement4US = None
	statement5UR = None
	statement6US = None
	statement7UR = None
	statement8US = None
	statement1RR = None
	statement2RS = None
	statement3RR = None
	statement4RS = None
	statement5RR = None
	statement6RS = None
	statement9UR = None
	statement10US = None
	
	if verbose:
		statement1CS = '1C-S Sent Value: %d with length %d (CBLT command request).'
		statement1UR = '1U-R Received Value: %d of length %d (Server Begin Rendevous.)'
		statement2US = '2U-S Sent Value: %d with length %d (Constraint Send).'
		statement3UR = '3U-R Received Value: %d with length %d (CBLT Status Rendevous).'
		statement4US = '4U-S Sent Value: %d with length %d (Send nwords Rendevous).'
		statement5UR = '5U-R Received Value: %d of length %d (nwords)'
		statement6US = '6U-S Sent Value: %d with length %d (nwords Rendevous).'
		statement7UR = '7U-R Received Value: %d and length %d (CBLT bytes)'
		statement8US = '8U-S Sent Value: %d with length %d (CBLT complete Rendevous).'
		statement1RR = '1R-R Received Value: %d with length %d (CBLT reread Status Rendevous).'
		statement2RS = '2R-S Sent Value: %d with length %d (Send reread nwords Rendevous).'
		statement3RR = '3R-R Received Value: %d with length %d (reread nwords value).'
		statement4RS = '4R-S Sent Value: %d with length %d (Send reread CBLT Rendevous).'
		statement5RR = '5R-R Received Value: %d with length %d (reread CBLT data).'
		statement6RS = '6R-S Sent Value: %d with length %d (reread CBLT complete Rendevous).'
		statement9UR = '9U-R Received Value: %d of length %d (Continue Rendevous)\n'
		statement10US = '10U-S Sent Value: %d with length %d (OK continue Rendevous).'
		
	spill = SpillHolder()
		
	if capture_type == g.TIMED_CBLT or capture_type == g.EVENT_CBLT or capture_type == g.AUTOMATED_CBLT:
		constraint_size = 4 #For time and event constrait mode, the constraint is sent as an int
	elif capture_type == g.CONTINUOUS_CBLT:
		constraint_size = 1 #For continuous, it is just a rendevous check. Thus, a char.
	else:
		print('Bad capture_type: '+str(capture_type))
		sleep(0.2) #We give outselves a time cushion for the queue to clear out.
		return
	
	outofQueue.put(('flipStateSignal', capture_type))
	
	ADS_socket.sendCommandToServer(capture_type, 1, statement1CS)
	
	server_rendevous = ADS_socket.receiveCommandFromServer(1, statement1UR)

	if server_rendevous == g.RENDEVOUS_PROCEED:
		ADS_socket.sendCommandToServer(constraint, constraint_size, statement2US)
	else:
		print('Got %d for server constraint rendevous. Returning.' % server_rendevous)
		outofQueue.put(('spill', spill))
		#outofQueue.put(('flipStateSignal', capture_type))
		sleep(0.2)
		return

	server_rendevous = g.SERVER_RENDEVOUS_DEFAULT #Could use different variable, resetting it instead.
	
	#Functions can not break while loops. So, to use a function (reduce code redundacy/neatness) 
	#and have it break the while loop it instead throws an exception (which travels up the calling 
	#chain until it is handled). The stop_event 1. triggers the exception (for mid-loop breaks) and 2. 
	#ends the while loop normally for server initiated stops (i.e. reaching the constraint).
	try:
		while not stop_event.is_set():
			
				
			server_rendevous = ADS_socket.receiveCommandFromServer(1, statement3UR)
			if server_rendevous != g.RENDEVOUS_PROCEED:
				print('Got bad rendevous from server at 3U-R. Breaking.')
				outofQueue.put(('spill', spill))
				#outofQueue.put(('flipStateSignal', capture_type))
				sleep(0.2)
				return
			ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, statement4US)				
			
			nwords = ADS_socket.receiveCommandFromServer(4, statement5UR)

			checkForStopEvent(ADS_socket, stop_event, statement = statement6US)
			
			raw_data = ADS_socket.recv_all(nwords, statement7UR) #raw is the bytearray
			spill.addBinary(raw_data)

			if verbose:
				this_capture = CBLTData(raw_data)
				this_capture.wordifyBinaryData()
				bitmasks.printWordBlocks(this_capture.words)

			checkForStopEvent(ADS_socket, stop_event, statement = statement8US)				

			if reread:
				print('REREAD IS SET!')
				server_rendevous = ADS_socket.receiveCommandFromServer(1, statement1RR)
				if server_rendevous != g.RENDEVOUS_PROCEED:
					print('Got bad rendevous from server at 1R-R. Breaking.')
					outofQueue.put(('spill', spill))
					sleep(0.2)
					return			
				ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, statement2RS)		
				reread_nwords = ADS_socket.receiveCommandFromServer(4, statement3RR)
				ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, statement4RS)	
				raw_reread_data = ADS_socket.recv_all(reread_nwords, statement5RR) #raw is the bytearray, cblt the numpy array.
				spill.addBinary(raw_reread_data, reread=True)
				ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, statement6RS)
				
				if verbose:
					this_capture_reread = CBLTData(raw_reread_data)
					this_capture_reread.wordifyBinaryData()
					bitmasks.printWordBlocks(this_capture_reread.words)
				
			server_rendevous = ADS_socket.receiveCommandFromServer(1, statement9UR) #This was 4, why? Changed to 1 10/5
			
			if server_rendevous == g.RENDEVOUS_HALT:
				print('Server indicates halt. Stopping.')
				stop_event.set()
			elif server_rendevous != g.RENDEVOUS_PROCEED:
				print('Got %d for server continue rendevous. Returning.' % server_rendevous)
				outofQueue.put(('spill', spill))
				#outofQueue.put(('flipStateSignal', capture_type))
				sleep(0.2)
				return #Added as after thought, test this if there is a bug.
			
			server_rendevous = g.SERVER_RENDEVOUS_DEFAULT
			if livePlot == True:
				try:
					queueItem = intoQueue.get(False)
					if queueItem[0] == 'plotReady' and queueItem[1] == True and verbose == True:
						this_capture.parseWords()
						outofQueue.put(('plotData', this_capture))
					elif queueItem[0] == 'plotReady' and queueItem[1] == True and verbose == False:
						this_capture = CBLTData(raw_data)
						this_capture.parseWords()
						outofQueue.put(('plotData', this_capture))
					elif queueItem[0] == 'plotReady' and queueItem[1] == False and verbose == True:
						this_capture_reread.parseWords()
						outofQueue.put(('plotData', this_capture_reread))
					elif queueItem[0] == 'plotReady' and queueItem[1] == False and verbose == False:
						this_capture_reread = CBLTData(raw_reread_data)
						this_capture_reread.parseWords()
						outofQueue.put(('plotData', this_capture_reread))
					else:
						print('Failed to send requested plot data.')
				except queue.Empty:
					pass
			checkForStopEvent(ADS_socket, stop_event, statement = statement10US)
				 
	except HaltCapture:
		pass
			
	print('Exited while loop.')
	#outofQueue.put(('flipStateSignal', capture_type))
	outofQueue.put(('spill', spill))
	sleep(0.2)
	return
		
		
		
		
		
		
		
		
		
		
		
		
