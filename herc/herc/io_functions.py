#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 29 15:58:13 2018

@author: zdhughes
"""

import sys

class tee():
	
	"tee implemented in python"
	
	def __init__(self, fd1, fd2):
		self.fd1 = fd1
		self.fd2 = fd2
		
	def __del__(self):
		
		stdStreams = [0, 1, 2]
		fd1_no = self.fd1.fileno()
		fd2_no = self.fd2.fileno()
		
		if fd1_no not in stdStreams:
			self.fd1.close()
		if fd2_no not in stdStreams:
			self.fd2.close()
	
	def write(self, text):
		self.fd1.write(text)
		self.fd2.write(text)

	def flush(self):
		self.fd1.flush()
		self.fd2.flush()

class colors():
	
	"""This class will color console text output using ANSI codes."""

	RED = ''
	ORANGE = ''
	YELLOW = ''
	GREEN = ''
	BLUE = ''
	INDIGO = ''
	VIOLET = ''
	PINK = ''                                                                        
	BLACK = ''
	CYAN = ''
	PURPLE = ''
	BROWN = ''
	GRAY = ''
	DARKGRAY = ''
	LIGHTBLUE = ''
	LIGHTGREEN = ''
	LIGHTCYAN = ''
	LIGHTRED = ''
	LIGHTPURPLE = ''
	WHITE = ''
	BOLD = ''
	UNDERLINE = ''
	ENDC = ''
    
	def enableColors(self):

		self.RED = '\033[0;31m'
		self.ORANGE = '\033[38;5;166m'
		self.YELLOW = '\033[1;33m'
		self.GREEN = '\033[0;32m'
		self.BLUE = '\033[0;34m'
		self.INDIGO = '\033[38;5;53m'
		self.VIOLET = '\033[38;5;163m'
		self.PINK =  '\033[38;5;205m'
		self.BLACK = '\033[0;30m'
		self.CYAN = '\033[0;36m'
		self.PURPLE = '\033[0;35m'
		self.BROWN = '\033[0;33m'
		self.GRAY = '\033[0;37m'
		self.DARKGRAY = '\033[1;30m'
		self.LIGHTBLUE = '\033[1;34m'
		self.LIGHTGREEN = '\033[1;32m'
		self.LIGHTCYAN = '\033[1;36m'
		self.LIGHTRED = '\033[1;31m'
		self.LIGHTPURPLE = '\033[1;35m'
		self.WHITE = '\033[1;37m'
		self.BOLD = '\033[1m'
		self.UNDERLINE = '\033[4m'
		self.ENDC = '\033[0m'

        
	def disableColors(self):
        
		self.RED = ''        
		self.ORANGE = ''
		self.YELLOW = ''
		self.GREEN = ''
		self.BLUE = ''
		self.INDIGO = ''
		self.VIOLET = ''
		self.PINK = ''
		self.BLACK = ''
		self.CYAN = ''
		self.PURPLE = ''
		self.BROWN = ''
		self.GRAY = ''
		self.DARKGRAY = ''
		self.LIGHTBLUE = ''
		self.LIGHTGREEN = ''
		self.LIGHTCYAN = ''
		self.LIGHTRED = ''
		self.LIGHTPURPLE = ''
		self.WHITE = ''
		self.BOLD = ''
		self.UNDERLINE = ''
		self.ENDC = ''

	def getState(self):
		if self.ENDC:
			return True
		elif not self.ENDC:
			return False
		else:
			return -1

	def flipState(self):
		if self.getState():
			self.disableColors()
		elif not self.getState():
			self.enableColors()
		else:
			sys.exit("Can't flip ANSI state, exiting.")

	def confirmColors(self):
		if self.getState() == True:
			print('Colors are '+self.red('e')+self.orange('n')+self.yellow('a')+self.green('b')+self.blue('l')+self.indigo('e')+self.violet('d'))
		elif self.getState() == False:
			print('Colors are off!')
		elif self.getState() == -1:
			print('Error: Can\'t get color state.')

	def confirmColorsDonger(self):
		if self.getState() == True:
			print('Colors are '+self.pink('(ﾉ')+self.lightblue('◕')+self.pink('ヮ')+self.lightblue('◕')+self.pink('ﾉ')+self.red('☆')+self.orange('.')+self.yellow('*')+self.green(':')+self.blue('･ﾟ')+self.indigo('✧')+self.violet(' enabled!'))    
		elif self.getState() == False:
			print('Colors are off!')
		elif self.getState() == -1:
			print('Error: Can\'t get color state.')

	def orange(self, inString):
		inString = str(self.ORANGE+str(inString)+self.ENDC)
		return inString
	def indigo(self, inString):
		inString = str(self.INDIGO+str(inString)+self.ENDC)
		return inString
	def violet(self, inString):
		inString = str(self.VIOLET+str(inString)+self.ENDC)
		return inString
	def pink(self, inString):
		inString = str(self.PINK+str(inString)+self.ENDC)
		return inString
	def black(self, inString):
		inString = str(self.BLACK+str(inString)+self.ENDC)
		return inString
	def blue(self, inString):
		inString = str(self.BLUE+str(inString)+self.ENDC)
		return inString
	def green(self, inString):
		inString = str(self.GREEN+str(inString)+self.ENDC)
		return inString
	def cyan(self, inString):
		inString = str(self.CYAN+str(inString)+self.ENDC)
		return inString
	def red(self, inString):
		inString = str(self.RED+str(inString)+self.ENDC)
		return inString
	def purple(self, inString):
		inString = str(self.PURPLE+str(inString)+self.ENDC)
		return inString
	def brown(self, inString):
		inString = str(self.BROWN+str(inString)+self.ENDC)
		return inString
	def gray(self, inString):
		inString = str(self.GRAY+str(inString)+self.ENDC)
		return inString
	def darkgray(self, inString):
		inString = str(self.DARKGRAY+str(inString)+self.ENDC)
		return inString
	def lightblue(self, inString):
		inString = str(self.LIGHTBLUE+str(inString)+self.ENDC)
		return inString
	def lightgreen(self, inString):
		inString = str(self.LIGHTGREEN+str(inString)+self.ENDC)
		return inString
	def lightcyan(self, inString):
		inString = str(self.LIGHTCYAN+str(inString)+self.ENDC)
		return inString
	def lightred(self, inString):
		inString = str(self.LIGHTRED+str(inString)+self.ENDC)
		return inString
	def yellow(self, inString):
		inString = str(self.YELLOW+str(inString)+self.ENDC)
		return inString
	def white(self, inString):
		inString = str(self.WHITE+str(inString)+self.ENDC)
		return inString
	def bold(self, inString):
		inString = str(self.BOLD+str(inString)+self.ENDC)
		return inString
	def underline(self, inString):
		inString = str(self.UNDERLINE+str(inString)+self.ENDC)
		return inString
