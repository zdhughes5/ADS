#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 13 12:28:48 2018

@author: zdhughes
"""

import numpy as np
from PyQt5.QtCore import QObject
import socket



class ADS_socket(QObject):
	
	
	def __init__(self, host):
		
		self.HOST = host
		self.IP, self.PORT = self.HOST.split(':')
		self.PORT = int(self.PORT)

		print('Connecting to %s on port %d' % (self.IP, self.PORT))
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		self.s.connect((self.IP, self.PORT))
		
	
	#REMEMBER TO CHANGE THIS FOR A 32 BIT SYSTEM!
	def recv_all(self, nwords, statement = None):
		
		""" Python recv should be able to capture over multiple packets. It apparently can't.
			This does it. """
		
		bytes_received = 0
		dt = np.dtype('i4') #8->4
		dt = dt.newbyteorder('=')
		message = b''
		
		while bytes_received < nwords*4: #8->4
		
			raw = self.s.recv(nwords*4) #8->4
			bytes_received += len(raw)
			message += raw
	
		translated_data = np.frombuffer(message, dtype=dt)	
		
		if statement is not None:
			print(statement % (len(message), len(message))) # The server side prints expected and actual sent bytes. The Client only has received. Repeat for parity of printouts.
		
		return translated_data, message
	
	def sendCommandToServer(self, outgoing_command, byte_length=1, statement=None):
		
		"""Sends a command to the socket and has the option of printing out a confirmation statement."""
		
		wire_command = bytearray()
		wire_command += (outgoing_command).to_bytes(byte_length, byteorder='little')
		self.s.send(wire_command)
		if statement is not None:
			print(statement % (outgoing_command, byte_length))
			
	def receiveCommandFromServer(self, byte_length=1, statement=None):
		
		incoming_message = int.from_bytes(self.s.recv(byte_length), byteorder='little')
		if statement is not None:
			print(statement % (incoming_message, byte_length))
		
		return incoming_message
		
		
		
		
		
		
		