#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 19 14:30:10 2018

@author: zdhughes
"""

import struct
import numpy as np
from herc.io_functions import colors

# Using 32-bit words
# I don't like counting 1's and 0's and I can't to dec->bin conversions
# in my head so I use strings to define the masks. They are easy to
# verify at a glance.

# Start header

first2ByteMask = eval('0b' + '1'*16 + '0'*16)
first2ByteShift = 16

third1ByteMask = eval('0b' + '0'*16 + '1'*8 + '0'*8)
third1ByteShift = 8

fourth1ByteMask = eval('0b' + '0'*24 + '1'*8)
fourth1ByteShift = 0

# Event Header

first6bMask = eval('0b' + '1'*6 + '0'*26)
first6bShift = 26

last26bMask = eval('0b' + '0'*26 + '1'*6)
last26bShift = 0

# Hit header

first2bMask = eval('0b' + '1'*2 + '0'*30)
first2bShift = 30

first10bMask = eval('0b' + '0'*2 + '1'*10 + '0'*20)
first10bShift = 20

second10bMask = eval('0b' + '0'*12 + '1'*10 + '0'*10)
second10bShift = 10

third10bMask = eval('0b' + '0'*22 + '1'*10)
third10bShift = 0

# Area header

first4bMask = eval('0b' + '1'*4 + '0'*28)
first4bShift = 28

next12bMask = eval('0b' + '0'*4 + '1'*12 + '0'*16)
next12bShift = 16

last16bMask = eval('0b' + '0'*16 + '1'*16)
last16bShift = 0

# Last BD Status

first15bMask = eval('0b' + '1'*15 + '0'*17)
first15bShift = 17

last17bMask = eval('0b' + '0'*15 + '1'*17)
last17bShift = 0

# Trigger Header

last2ByteMask = eval('0b' + '0'*16 + '1'*16)
last2ByteShift = 0

first1ByteMask = eval('0b' + '1'*8 + '0'*24)
first1ByteShift = 24

second1ByteMask = eval('0b' + '0'*8 + '1'*8 + '0'*16)
second1ByteShift = 16


def maskAndRShifter(word, mask, shift):
	return (word&mask) >> shift



def wordify(binary_data, nwords):
	
	formatCode = '<'+'I'*nwords
	
	words = struct.unpack(formatCode, binary_data)
	
	return words


def extractHeader(words):

	startHeader = {
		'0xCAFE': maskAndRShifter(words[0], first2ByteMask, first2ByteShift),
		'Board Number': maskAndRShifter(words[0], third1ByteMask, third1ByteShift),
		'Serial Number' : maskAndRShifter(words[0], fourth1ByteMask, fourth1ByteShift)
			}
	eventHeader = {
			'EVT' : words[1]
			}
	trigHeader = {
			'Trig EVT' : maskAndRShifter(words[2], first2ByteMask, first2ByteShift),
			'Trig Code' : maskAndRShifter(words[2], last2ByteMask, last2ByteShift)
			}
	GPSHeader = {
			'GPS Second' : words[3]
			}
	elapsedTimeHeader = {
			'Elapsed Time Scalar' : words[4]
			}
	livetimeHeader = {
			'Livetime Scalar' : words[5]
			}
	dummyHeader = {
			'Dummy Register' : words[6]
			}
	junkHeader = {
			'Junk Word' : words[7]
			}	
	CLKHeader = {
			'Start Header' : startHeader,
			'Event Header' : eventHeader,
			'Trig Header' : trigHeader,
			'GPS Header' : GPSHeader,
			'Elapsed Header' : elapsedTimeHeader,
			'Livetime Header' : livetimeHeader,
			'Dummy Header' : dummyHeader,
			'Junk Header' : junkHeader,
			}

	return CLKHeader

def extractCBLTData(words):
	
	pass


def extractWordsPerChannel(words):
	
	numbers = []
	
	for i, word in enumerate(words):
		hexed = '0x%08x' % word
		if hexed[0:6].lower() == '0xfadc':
			numbers += [maskAndRShifter(word, fourth1ByteMask, fourth1ByteShift)]
	
	numbers = np.array(numbers)
	if (numbers == numbers[0]).all():
		return numbers[0]
	else:
		print('Warning got different number of words for each board:')
		print(numbers)
		print('Dumping words:')
		for i, word in enumerate(words):
			hexed = '0x%08x' % word
			print(hexed, end=' ')
			if (i+1) % 8 == 0:
				print('')	
		
def extractADC(word):
	
	counts = []
	#counts.append(maskAndRShifter(word, first1ByteMask, first1ByteShift))
	#counts.append(maskAndRShifter(word, second1ByteMask, second1ByteShift))
	#counts.append(maskAndRShifter(word, third1ByteMask, third1ByteShift))
	#counts.append(maskAndRShifter(word, fourth1ByteMask, fourth1ByteShift))
	
	counts.append(maskAndRShifter(word, fourth1ByteMask, fourth1ByteShift))
	counts.append(maskAndRShifter(word, third1ByteMask, third1ByteShift))
	counts.append(maskAndRShifter(word, second1ByteMask, second1ByteShift))
	counts.append(maskAndRShifter(word, first1ByteMask, first1ByteShift))
	
	

	return counts

def wordsToADC(words):
	
	counts = np.array([])
	for word in words:
		counts = np.append(counts, extractADC(word))
		
	return counts

def getWordIndicies(words, wordsPerChannel = None):
	
	''' This function catagorizes the words based on location and returns the indicies of those catagories. '''

	indexArray = [x for x in range(len(words))] # Total set to compare against subsets.
	clkLocations = [x for x in range(8)] # CLK trigger board locations. First 8 words.
	fadcLocations = [] # Start of FADC board.
	otherLocations = [] # The two words following 0xFADC.
	dataLocations = [] # The ADC data.
	areaLocations = [] # The area words.
	lastBoardLocation = [] # Last Board status.
	
	if wordsPerChannel is None:
		wordsPerChannel = extractWordsPerChannel(words) # Data words
		wordsPerChannel += 1 #The area word
	
	# Find 0xFADC words.
	for i, word in enumerate(words):
		hexed = '0x%08x' % word
		if hexed[0:6].lower() == '0xfadc':
			fadcLocations += [i]

	# Get data and area words relative to 0xFADC words.
	for i, start in enumerate(fadcLocations):
		otherLocations += [start + 1, start + 2]
		areaLocations += [start + 2 + wordsPerChannel * (x+1) for x in range(10)]
		for j in range(10):
			dataLocations += list(range(start + 3 + wordsPerChannel*j, start + 3 + wordsPerChannel*(j+1) - 1))
			
	foundLocations = clkLocations + fadcLocations + otherLocations + dataLocations + areaLocations

	lastBoardLocation = [x for x in indexArray if x not in foundLocations]
#	if len(lastBoardLocation) != 1:
#		print('Error: Number of last board status location not 1.')
#		print(lastBoardLocation)

	totalLocations = foundLocations + lastBoardLocation
	duplicates = set([x for x in totalLocations if totalLocations.count(x) > 1])
	if len(duplicates) != 0:
		print('Error: Got duplicates:')
		print(duplicates)
		
	return (clkLocations, fadcLocations, otherLocations, dataLocations, areaLocations, lastBoardLocation, duplicates)

def printWordBlocks(words, colorText = True, wordsPerChannel = None):
	
	''' Hex prints and colors words based on location. '''
	
	c = colors()
	if colorText == True:
		c.enableColors()
	
	clkLocations, fadcLocations, otherLocations, dataLocations, areaLocations, lastBoardLocation, duplicates = getWordIndicies(words, wordsPerChannel = wordsPerChannel)

	for i, word in enumerate(words):
		hexed = '0x%08x' % word
		if i in clkLocations:
			print(c.pink(hexed), end=' ')
		elif i in fadcLocations:
			print(c.yellow(hexed), end=' ')
		elif i in otherLocations:
			print(c.blue(hexed), end=' ')
		elif i in dataLocations:
			 print(c.cyan(hexed), end=' ')
		elif i in areaLocations:
			print(c.green(hexed), end=' ')
		elif i in lastBoardLocation:
			print(c.red(hexed), end=' ')
		else:
			 print(hexed, end = ' ')
		if (i+1) % 8 == 0:
			print('')
	print('')




def parseFADCs(words, wordsPerChannel = None):
	
	boards = []
	
	c = colors()
	c.enableColors()
	
	if wordsPerChannel is None:
		wordsPerChannel = extractWordsPerChannel(words)
		wordsPerChannel += 1
		
	for i, word in enumerate(words):
		hexed = '0x%08x' % word
		if hexed[0:6].lower() == '0xfadc':
			startHeader = {
					'0xFADC' : maskAndRShifter(words[i], first2ByteMask, first2ByteShift),
					'Board Number' : maskAndRShifter(words[i], third1ByteMask, third1ByteShift),
					'Words Per Channel' : maskAndRShifter(words[i], fourth1ByteMask, fourth1ByteShift) 
					}
			eventHeader = {
					'Misc. 6 bits' : maskAndRShifter(words[i+1], first6bMask, first6bShift),
					'Event Count' : maskAndRShifter(words[i+1], last26bMask, last26bShift)
					}
			hitHeader = {
					'Mode' : maskAndRShifter(words[i+2], first2bMask, first2bShift),
					'HILO' : maskAndRShifter(words[i+2], first10bMask, first10bShift),
					'Trigger Flags' : maskAndRShifter(words[i+2], second10bMask, second10bShift),
					'Channel Hits' : maskAndRShifter(words[i+2], third10bMask, third10bShift)
					}

			#print('\n')			
			#print('0x%08x' % words[i], end= ' ')
			#print('0x%08x' % words[i+1], end= ' ')
			#print('0x%08x' % words[i+2])
			
			channel_words = [words[i+3+wordsPerChannel*x:i+3+wordsPerChannel*(x+1)] for x in range(10)]
			#for things in channel_words:
			#	for box, beep in enumerate(things):
			#		printThis = '0x%08x' % beep
			#		print(printThis, end = ' ')
			#		if (box+1) % 8 == 0:
			#			print('')
			#	print('')
				
			
			channel_data = [wordsToADC(words[:-1]) for words in channel_words]
			area_words = [words[-1] for words in channel_words]
			area_data = [{
					'Channel Number' : maskAndRShifter(area_words[x], first4bMask, first4bShift),
					'Unused' : maskAndRShifter(area_words[x], next12bMask, next12bShift),
					'Pulse Area' : maskAndRShifter(area_words[x], last16bMask, last16bShift),
					'ADC' : channel_data[x]
					} for x in range(10)]
			
			board = {
					'Start Header' : startHeader,
					'Event Header' : eventHeader,
					'Hit Header' : hitHeader,
					}
			for y in area_data:
				board['Channel '+str(y['Channel Number'])] = y
			
			
			boards.append(board)
			
	lastBoardStatus = {
			'Sync Pattern' : maskAndRShifter(words[-1], first15bMask, first15bShift),
			'CBLT Buf Size' : maskAndRShifter(words[-1], last17bMask, last17bShift)
			}

			
	return boards	
	


def parseFADCsNew(words, wordsPerChannel = None):
	
	boards = []
	
	if wordsPerChannel is None:
		wordsPerChannel = extractWordsPerChannel(words) # Channel data words.
		wordsPerChannel += 1 #For the area header word.
		
	clkLocations, fadcLocations, otherLocations, dataLocations, areaLocations, lastBoardLocation, duplicates = getWordIndicies(words, wordsPerChannel = wordsPerChannel)
		
	startHeader = {
		'0xCAFE': maskAndRShifter(words[0], first2ByteMask, first2ByteShift),
		'Board Number': maskAndRShifter(words[0], third1ByteMask, third1ByteShift),
		'Serial Number' : maskAndRShifter(words[0], fourth1ByteMask, fourth1ByteShift)
			}
	eventHeader = {
			'EVT' : words[1]
			}
	trigHeader = {
			'Trig EVT' : maskAndRShifter(words[2], first2ByteMask, first2ByteShift),
			'Trig Code' : maskAndRShifter(words[2], last2ByteMask, last2ByteShift)
			}
	GPSHeader = {
			'GPS Second' : words[3]
			}
	elapsedTimeHeader = {
			'Elapsed Time Scalar' : words[4]
			}
	livetimeHeader = {
			'Livetime Scalar' : words[5]
			}
	dummyHeader = {
			'Dummy Register' : words[6]
			}
	junkHeader = {
			'Junk Word' : words[7]
			}	
	clkEntry = {
			'Start Header' : startHeader,
			'Event Header' : eventHeader,
			'Trig Header' : trigHeader,
			'GPS Header' : GPSHeader,
			'Elapsed Header' : elapsedTimeHeader,
			'Livetime Header' : livetimeHeader,
			'Dummy Header' : dummyHeader,
			'Junk Header' : junkHeader,
			}		
	
	boards.append(clkEntry)	

	for i, word in enumerate(words):
		hexed = '0x%08x' % word
		if hexed[0:6].lower() == '0xfadc':
			startHeader = {
					'0xFADC' : maskAndRShifter(words[i], first2ByteMask, first2ByteShift),
					'Board Number' : maskAndRShifter(words[i], third1ByteMask, third1ByteShift),
					'Words Per Channel' : maskAndRShifter(words[i], fourth1ByteMask, fourth1ByteShift) 
					}
			eventHeader = {
					'Misc. 6 bits' : maskAndRShifter(words[i+1], first6bMask, first6bShift),
					'Event Count' : maskAndRShifter(words[i+1], last26bMask, last26bShift)
					}
			hitHeader = {
					'Mode' : maskAndRShifter(words[i+2], first2bMask, first2bShift),
					'HILO' : maskAndRShifter(words[i+2], first10bMask, first10bShift),
					'Trigger Flags' : maskAndRShifter(words[i+2], second10bMask, second10bShift),
					'Channel Hits' : maskAndRShifter(words[i+2], third10bMask, third10bShift)
					}

			channel_words = [words[i+3+wordsPerChannel*x:i+3+wordsPerChannel*(x+1)] for x in range(10)]
			channel_data = [wordsToADC(words[:-1]) for words in channel_words]
			
			area_words = [words[-1] for words in channel_words]
			channel_entries = [{
					'Channel Number' : maskAndRShifter(area_words[x], first4bMask, first4bShift),
					'Unused' : maskAndRShifter(area_words[x], next12bMask, next12bShift),
					'Pulse Area' : maskAndRShifter(area_words[x], last16bMask, last16bShift),
					'ADC' : channel_data[x]
					} for x in range(10)]
			
			board = {
					'Start Header' : startHeader,
					'Event Header' : eventHeader,
					'Hit Header' : hitHeader,
					}
			
			for channel_entry in channel_entries:
				board['Channel '+str(channel_entry['Channel Number'])] = channel_entry
			
			
			boards.append(board)
			
	lastBoardStatus = {
			'Sync Pattern' : maskAndRShifter(words[lastBoardLocation[0]], first15bMask, first15bShift),
			'CBLT Buf Size' : maskAndRShifter(words[lastBoardLocation[0]], last17bMask, last17bShift)
			}
	
	boards.append(lastBoardStatus)

			
	return boards	
	
	

































	