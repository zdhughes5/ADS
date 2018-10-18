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

		self.ConnectServerButton.setEnabled(False)
		self.RereadCB.setEnabled(True)
		
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
		
		self.StartButton.setEnabled(not self.StartButton.isEnabled())
		self.StopButton.setEnabled(not self.StartButton.isEnabled())
		self.SingleEventButton.setEnabled(not self.SingleEventButton.isEnabled())
		self.CloseServerButton.setEnabled(not self.CloseServerButton.isEnabled())
		self.DurationRadio.setEnabled(not self.DurationRadio.isEnabled())
		self.EventRadio.setEnabled(not self.EventRadio.isEnabled())
		self.TimeoutRadio.setEnabled(not self.TimeoutRadio.isEnabled())
		self.ContinuousRadio.setEnabled(not self.ContinuousRadio.isEnabled())
		self.DirectoryButton.setEnabled(not self.DirectoryButton.isEnabled())
		self.FilenameButton.setEnabled(not self.FilenameButton.isEnabled())
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
		self.stop_event = threading.Event()
		self.workerThread = QThread()
		self.worker = captureWorker(self.ADS_socket, self.spill, self.stop_event, self.capture_type, self.constraint, self.verbose, self.reread)
		self.worker.flipStateSignal.connect(self.flipButtonStates)
		self.workerThread.finished.connect(self.notifyFinished)
		self.worker.moveToThread(self.workerThread)
		self.workerThread.started.connect(self.worker.universalCapture)
		self.workerThread.start()
		self.workerThread.quit() #Be careful with this, will it prematurely end the thread? Without it
		#we get 'QThread: Destroyed while thread is still running'. Memory Leak?

	@pyqtSlot()		
	def stopAcquire(self):
		
		""" Sets the capture thread stop_event to True. """
		
		self.stop_event.set()

	@pyqtSlot()		
	def notifyFinished(self):
		
		""" Just something to do when a thread emits a finsihed signal. """

		print('Worker is finished. Here is the spill data.')
		self.spill.parseCBLTs()
# =============================================================================
# 		for cblt in self.spill.cblts:
# 			bitmasks.printWordBlocks(cblt.words)
# =============================================================================
		if self.saveData == True:
			self.spill.constructTable()
		print('There were %d cblts.' % len(self.spill.cblts))
		

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


class captureWorker(QObject):
	
	""" This object does the actual non-single-event capture. It is run in a seperate QThread. """
	
	flipStateSignal = pyqtSignal(int)
	
	def __init__(self, ADS_socket, spill, stop_event, capture_type = None, constraint = None, verbose = False, reread = False, parent = None):
		super().__init__(parent)
		super(self.__class__, self).__init__(parent)
		self.ADS_socket = ADS_socket
		self.stop_event = stop_event
		self.capture_type = capture_type
		self.constraint = constraint
		self.verbose = verbose
		self.reread = reread
		self.spill = spill
		
		self.statement1CS = None
		self.statement1UR = None
		self.statement2US = None
		self.statement3UR = None
		self.statement4US = None
		self.statement5UR = None
		self.statement6US = None
		self.statement7UR = None
		self.statement8US = None
		self.statement9UR = None
		
		if self.verbose:
			self.statement1CS = '1C-S Sent Value: %d with length %d (CBLT command request).'
			self.statement1UR = '1U-R Received Value: %d of length %d (First Rendevous.)'
			self.statement2US = '2U-S Sent Value: %d with length %d (Constraint Send).'
			self.statement3UR = '3U-R Received Value: %d with length %d (CBLT Status Rendevous).'
			self.statement4US = '4U-S Received Value: %d with length %d (Send nwords Rendevous).'
			self.statement5UR = '5U-R Received Value: %d of length %d (nwords)'
			self.statement6US = '6U-S Sent Value: %d with length %d (nwords Rendevous).'
			self.statement7UR = '7U-R Received Value: %d and length %d (CBLT bytes)'
			self.statement8US = '8U-S Sent Value: %d with length %d (CBLT complete Rendevous).'
			self.statement9UR = '9U-R Received Value: %d of length %d (Continue Rendevous)\n'
		
	def checkForStopEvent(self, **kwargs):
		
		""" Checks whether the stop_event has been set by the user.
			Based on the result it tells the server whether to halt or proceed. """
		
		if not self.stop_event.isSet():
			self.ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, **kwargs)
		else:
			self.ADS_socket.sendCommandToServer(g.RENDEVOUS_HALT, 1, **kwargs)
			print('Sent halt, breaking.')
			raise HaltCapture

	def universalCapture(self):
		
		""" Starts the event capture. Capture_type is for the server cblt capture mode. 
			Constraint is the corresponding parameter that tells the server when to stop
			the capture. """
			
		if self.capture_type == g.TIMED_CBLT or self.capture_type == g.EVENT_CBLT or self.capture_type == g.AUTOMATED_CBLT:
			self.constraint_size = 4 #For time and event constrait mode, the constraint is sent as an int
		elif self.capture_type == g.CONTINUOUS_CBLT:
			self.constraint_size = 1 #For continuous, it is just a rendevous check. Thus, a char.
		else:
			print('Bad capture_type: '+str(self.capture_type))
			return
		
		self.flipStateSignal.emit(self.capture_type)

		self.ADS_socket.sendCommandToServer(self.capture_type, 1, self.statement1CS)
		
		server_rendevous = self.ADS_socket.receiveCommandFromServer(1, self.statement1UR)

			
		if server_rendevous == g.RENDEVOUS_PROCEED:
			self.ADS_socket.sendCommandToServer(self.constraint, self.constraint_size, self.statement2US)
		else:
			print('Got %d for server constraint rendevous. Returning.' % server_rendevous)
			self.flipStateSignal.emit(self.capture_type) #Turn the buttons back on on a premature ending.
			return
	
		server_rendevous = g.SERVER_RENDEVOUS_DEFAULT #Could use different variable, resetting it instead.
		
		#Functions can not break while loops. So, to use a function (reduce code redundacy/neatness) 
		#and have it break the while loop it instead throws an exception (which travels up the calling 
		#chain until it is handled). The stop_event 1. triggers the exception (for mid-loop breaks) and 2. 
		#ends the while loop normally for server initiated stops (i.e. reaching the constraint).
		try:
			while not self.stop_event.isSet():
				server_rendevous = self.ADS_socket.receiveCommandFromServer(1, self.statement3UR)
				if server_rendevous != g.RENDEVOUS_PROCEED:
					print('Got bad rendevous from server. Breaking.')
					self.flipStateSignal.emit(self.capture_type)
					return
				self.ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, self.statement4US)				
				
				
				nwords = self.ADS_socket.receiveCommandFromServer(4, self.statement5UR)
	
				self.checkForStopEvent(statement = self.statement6US)
				
				raw_data = self.ADS_socket.recv_all(nwords, self.statement7UR) #raw is the bytearray, cblt the numpy array.
				self.spill.addBinary(raw_data)


				if self.verbose:
					this_capture = CBLTData(raw_data)
					this_capture.wordifyBinaryData()
					bitmasks.printWordBlocks(this_capture.words)

				self.checkForStopEvent(statement = self.statement8US)				

				if self.reread:
					server_rendevous = self.ADS_socket.receiveCommandFromServer(1, '1R-R Received Value: %d with length %d (CBLT reread Status Rendevous).')
					if server_rendevous != g.RENDEVOUS_PROCEED:
						print('Got bad rendevous from server. Breaking.')
						return			
					self.ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, '2R-S Sent Value: %d with length %d (Send reread nwords Rendevous).')		
					reread_nwords = self.ADS_socket.receiveCommandFromServer(4, '3R-R Received Value: %d with length %d (reread nwords value).')
					self.ADS_socket.sendCommandToServer(g.RENDEVOUS_PROCEED, 1, '4R-S Sent Value: %d with length %d (Send reread CBLT Rendevous).')	
					raw_reread_data = self.ADS_socket.recv_all(reread_nwords, '5R-R Received Value: %d with length %d (reread CBLT data).') #raw is the bytearray, cblt the numpy array.
					if self.verbose:
						this_capture_reread = CBLTData(raw_reread_data)
						this_capture_reread.wordifyBinaryData()
						bitmasks.printWordBlocks(this_capture_reread.words)

				
				server_rendevous = self.ADS_socket.receiveCommandFromServer(1, self.statement9UR) #This was 4, why? Changed to 1 10/5
				
				if server_rendevous == g.RENDEVOUS_HALT:
					print('Server indicates halt. Stopping.')
					self.stop_event.set()
				elif server_rendevous != g.RENDEVOUS_PROCEED:
					print('Got %d for server continue rendevous. Returning.' % server_rendevous)
					self.flipStateSignal.emit(self.capture_type)
					return #Added as after thought, test this if there is a bug.
				server_rendevous = g.SERVER_RENDEVOUS_DEFAULT
		except HaltCapture:
			pass
				
		print('Exited while loop.')
		self.flipStateSignal.emit(self.capture_type) #Turn the buttons back on.
		
		


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
			
	def fadcHeader(self, board_num):
		ax1 = np.array([x[board_num]['Start Header']['0xFADC'] for x in self.cblts])
		cx1 = fits.Column(name='B'+str(board_num)+'_0xFADC', array=ax1, format='I') #Unsigned
		ax2 = np.array([x[board_num]['Start Header']['Board Number'] for x in self.cblts])
		cx2 = fits.Column(name='B'+str(board_num)+'_Board_Number', array=ax2, format='B')
		ax3 = np.array([x[board_num]['Start Header']['Words Per Channel'] for x in self.cblts])
		cx3 = fits.Column(name='B'+str(board_num)+'_Words_Per_Channel', array=ax3, format='B')

		# Event Header
		ax4 = np.array([x[board_num]['Event Header']['Event Count'] for x in self.cblts])
		cx4 = fits.Column(name='B'+str(board_num)+'_Event_Count', array=ax4, format='J') #Unsigned
		ax5 = np.array([x[board_num]['Event Header']['Misc. 6 bits'] for x in self.cblts])
		cx5 = fits.Column(name='B'+str(board_num)+'_misc_bits', array=ax5, format='B')

		# Hit Header
		ax6 = np.array([x[board_num]['Hit Header']['Mode'] for x in self.cblts])
		cx6 = fits.Column(name='B'+str(board_num)+'_Mode', array=ax6, format='B') #Unsigned
		ax7 = np.array([x[board_num]['Hit Header']['HILO'] for x in self.cblts])
		cx7 = fits.Column(name='B'+str(board_num)+'_HILO', array=ax7, format='I')
		ax8 = np.array([x[board_num]['Hit Header']['Trigger Flags'] for x in self.cblts])
		cx8 = fits.Column(name='B'+str(board_num)+'_Trigger_Flags', array=ax8, format='I')
		ax9 = np.array([x[board_num]['Hit Header']['Channel Hits'] for x in self.cblts])
		cx9 = fits.Column(name='B'+str(board_num)+'_Channel_Hits', array=ax9, format='I')
	
		return (cx1, cx2, cx3, cx4, cx5, cx6, cx7, cx8, cx9)
	
	def fadcPayload(self, board_num, channel):
		
		adcFormat = str(len(self.cblts[0][1]['Channel 1']['ADC']))+'B' #The first channel (['Channel 1']) of the first fadc board (1) of the first cblt (0)
		ax1 = np.array([x[board_num]['Channel '+str(channel)]['ADC'] for x in self.cblts])
		cx1 = fits.Column(name='B'+str(board_num)+'_Channel_'+str(channel)+'_ADC', array=ax1, format=adcFormat)
		ax2 = np.array([x[board_num]['Channel '+str(channel)]['Channel Number'] for x in self.cblts])
		cx2 = fits.Column(name='B'+str(board_num)+'_Channel_'+str(channel), array=ax2, format='B')
		ax3 = np.array([x[board_num]['Channel '+str(channel)]['Unused'] for x in self.cblts])
		cx3 = fits.Column(name='B'+str(board_num)+'_Channel_'+str(channel)+'_Unused', array=ax3, format='I')
		ax4 = np.array([x[board_num]['Channel '+str(channel)]['Pulse Area'] for x in self.cblts])
		cx4 = fits.Column(name='B'+str(board_num)+'_Channel_'+str(channel)+'_Area', array=ax4, format='I')

		return (cx1, cx2, cx3, cx4)	
			
	def constructTable(self):
		columns = []
		
		# CLK board
		# Start Header
		a1 = np.array([x[0]['Start Header']['0xCAFE'] for x in self.cblts])
		c1 = fits.Column(name='0xCAFE', array=a1, format='I') #Unsigned
		columns.append(c1)
		a2 = np.array([x[0]['Start Header']['Board Number'] for x in self.cblts])
		c2 = fits.Column(name='CLK Board Number', array=a2, format='B')
		columns.append(c2)
		a3 = np.array([x[0]['Start Header']['Serial Number'] for x in self.cblts])
		c3 = fits.Column(name='Serial Number', array=a3, format='B')
		columns.append(c3)
		
		# Event Header
		a4 = np.array([x[0]['Event Header']['EVT'] for x in self.cblts])
		c4 = fits.Column(name='CLK Event', array=a4, format='J')
		columns.append(c4)

		# Trigger Header		
		a5 = np.array([x[0]['Trig Header']['Trig EVT'] for x in self.cblts])
		c5 = fits.Column(name='CLK Trigger Event', array=a5, format='I')
		columns.append(c5)
		a6 = np.array([x[0]['Trig Header']['Trig Code'] for x in self.cblts])
		c6 = fits.Column(name='CLK Trigger Code', array=a6, format='I')	
		columns.append(c6)

		# GPS Header
		a7 = np.array([x[0]['GPS Header']['GPS Second'] for x in self.cblts])
		c7 = fits.Column(name='GPS Second', array=a7, format='J')	
		columns.append(c7)
		
		# Elapsed Header
		a8 = np.array([x[0]['Elapsed Header']['Elapsed Time Scalar'] for x in self.cblts])
		c8 = fits.Column(name='Elapsed Time Scalar', array=a8, format='J')	
		columns.append(c8)

		# Livetime Header
		a9 = np.array([x[0]['Livetime Header']['Livetime Scalar'] for x in self.cblts])
		c9 = fits.Column(name='Livetime Scalar', array=a9, format='J')	
		columns.append(c9)

		# Elapsed Header
		a10 = np.array([x[0]['Dummy Header']['Dummy Register'] for x in self.cblts])
		c10 = fits.Column(name='Dummy Register', array=a10, format='J')	
		columns.append(c10)

		# Elapsed Header
		a11 = np.array([x[0]['Junk Header']['Junk Word'] for x in self.cblts])
		c11 = fits.Column(name='Junk Word', array=a11, format='J')	
		columns.append(c11)		
			
		for i in range(1, len(self.cblts[1].boards)-1):
			
			print(i)
			(cx1, cx2, cx3, cx4, cx5, cx6, cx7, cx8, cx9) = self.fadcHeader(i)
			columns.append(cx1)
			columns.append(cx2)
			columns.append(cx3)
			columns.append(cx4)
			columns.append(cx5)
			columns.append(cx6)
			columns.append(cx7)
			columns.append(cx8)
			columns.append(cx9)

			for j in range(10):
				cx1, cx2, cx3, cx4 = self.fadcPayload(i, j)
				columns.append(cx1)
				columns.append(cx2)
				columns.append(cx3)
				columns.append(cx4)

		t = fits.BinTableHDU.from_columns(columns)
		subprocess.call('mkdir -p /nfs/optimus/home/zdhughes/Desktop/projects/ADS/data/', shell=True)
		t.writeto('/nfs/optimus/home/zdhughes/Desktop/projects/ADS/data/test.fits', overwrite=True)
		
		
		
	

			
		

		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
