#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 20 17:28:37 2018

@author: zdhughes
"""

import Capture
import bitmasks
import struct
import os
import matplotlib.pyplot as plt
import numpy as np


os.chdir('./data/')

file1 = 'run_0'
file2 = 'run_1'
file3 = 'run_2'

nwords1 = 675
nwords2 = 1275
nwords3 = 1275


format1 = '<'+'B'*nwords1*4
format2 = '<'+'B'*nwords2*4
format3 = '<'+'B'*nwords3*4

with open(file1, 'rb') as f:
	data1 = f.read()
	
with open(file2, 'rb') as f:
	data2 = f.read()
	
with open(file3, 'rb') as f:
	data3 = f.read()

bytes1 = np.array(struct.unpack(format1, data1))
bytes2 = np.array(struct.unpack(format2, data2))
bytes3 = np.array(struct.unpack(format3, data2))

	
holder1 = Capture.CBLT_data(data1)
holder2 = Capture.CBLT_data(data2)
holder3 = Capture.CBLT_data(data3)


words1 = holder1.wordifyBinaryData(holder1.binary_data, nwords1, endian='<')
words2 = holder2.wordifyBinaryData(holder2.binary_data, nwords2, endian='<')
words3 = holder2.wordifyBinaryData(holder2.binary_data, nwords3, endian='<')


holder1.addWords(words1)
holder2.addWords(words2)
holder2.addWords(words3)


holder1.extractCLKHeader(words1)
holder2.extractCLKHeader(words2)
holder2.extractCLKHeader(words3)


#plt.plot(bytes1)
#plt.show()

#plt.plot(bytes2)
#plt.show()

cblt1 = Capture.CBLTData(data2)
cblt2 = Capture.CBLTData(data3)
spill = Capture.SpillHolder()
spill.addCBLT(cblt1)
spill.addCBLT(cblt2)
spill.parseCBLTs()
spill.constructTable()




















