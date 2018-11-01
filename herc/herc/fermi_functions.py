#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 29 16:11:36 2018

@author: zdhughes
"""

import os
import subprocess
from herc.io_functions import colors
import json


def dataServerDownload(inputFile, dataDir = None, dirStem = None, c = None, SCFilename = None, runlistFilename = None):
	
	'''This file downloads fermi data from a server query. The input file consists of the query details followed by the wget commands.
	This makes downloading from the website slightly less tedious.'''

	if not c:
		c = colors()
		c.enableColors()
		
	print('Working on file: ', c.yellow(inputFile))
	
	if not dirStem:
		dirStem = '.'
	if not SCFilename:
		SCFilename = 'spacecraft.fits'
	if not runlistFilename:
		runlistFilename = 'runlist.lst'

	with open(inputFile) as f:
		lines = [line.rstrip() for line in f]
	wgets = lines[5:]

	if dataDir is None:
		latLongPart = '_'.join(lines[0].split()[-1][1:-1].split(','))
		metPart = '_'.join(lines[1].split()[-1][1:-1].split(',')+['MET'])
		mevPart = '_'.join(lines[3].split()[-1][1:-1].split(',')+['MeV'])
		radPart = '_'.join([lines[4].split()[-1],'rad'])
		dataDir = '_'.join([latLongPart, metPart, mevPart, radPart])
		
	path = dirStem + '/' + dataDir
	subprocess.call('mkdir -p ' + path,shell=True)
	cwd = os.getcwd()
	os.chdir(path)

	for wget in wgets:
		if wget.split('_')[-1][:2] == 'SC':
			print('Calling ' + c.purple(wget))
			print(os.getcwd())
			subprocess.call(wget, shell=True)
			print('Calling ' + c.purple('mv '+wget.split('/')[-1]+' '+SCFilename))
			subprocess.call('mv '+wget.split('/')[-1]+' '+SCFilename, shell=True)
		elif wget.split('_')[-1][:2] == 'PH':
			print('Calling ' + c.purple(wget))
			subprocess.call(wget, shell=True)
		else:
			print(c.red('Something went wrong.'))
			
	print('Calling ' + c.purple('ls -d -1 $PWD/*.* > ' + runlistFilename))
	subprocess.call('ls -d -1 $PWD/*_PH* > ' + runlistFilename, shell=True)			
	
	os.chdir(cwd)
	
def callFermiFunction(tool, parameters, usePython, color = None, prepend = None):
	
	'''Call either the CLI fermi tools or their python wrappers from a non-fermi tools python install.'''
	
	if not prepend:
		prepend = '. /nfs/programs/fermi/v10r0p5/x86_64-unknown-linux-gnu-libc2.17/fermi-init.sh && python /nfs/optimus/home/zdhughes/Desktop/projects/herc/herc/anaconda2fermi.py '
	if not color:
		color = 'False'
	if type(parameters) is str:
		pass
	elif type(parameters) is dict:
		parameters = json.dumps(parameters)
		parameters = """'""" + parameters + """'""" 
	else:
		print('Something went wrong.')
		
	callargs = ' '.join([tool, parameters, usePython, color])
	subprocess.call(prepend + callargs, shell = True)
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	