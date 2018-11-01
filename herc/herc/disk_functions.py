#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 29 15:49:02 2018

@author: zdhughes
"""

import sys
import subprocess
import numpy as np
import random

def getBestDisk(inputFile=None, Abort=False):
	
	if inputFile == None:
		inputFile = '/nfs/programs/VWrap/available_data_disks_replacement.txt'

	with open(inputFile,'r') as f:
		dirs, disks = zip(*[(line.rstrip(),line.rstrip().split('/')[-1]) for line in f])
	dirs = list(dirs)
	disks = list(disks)

	freeDiskSpace = []
	freeDiskPercent = []
			
	for i, elements in enumerate(dirs):

		dfCall = subprocess.check_output('df -m '+elements,shell=True)

		freeSpace = str(dfCall).split()[9]
		freeSpace = round(float(freeSpace)/1024,1)
		freeDiskSpace.append(freeSpace)

		freePercent = str(dfCall).split()[10]
		freePercent = 100 - float(freePercent.split('%')[0])
		freeDiskPercent.append(freePercent)

	freeDiskSpace = np.array(freeDiskSpace)
	freeDiskPercent = np.array(freeDiskPercent)
	disks = np.array(disks)
	print(disks, 'considered with corresponding free space',freeDiskSpace,'GB')

	disksCut = disks[np.where(freeDiskSpace > 20.0)]
	print(disksCut,' survive 20 GB minimum cut.')

	if (disksCut.size == 0 and Abort == True):
		sys.exit('Did not find any disks with more than 20GB free. Aborting.')
	elif (disksCut.size == 0 and Abort == False):
		print('Warning: did not find an acceptable disk with > 20 GB free and Abort set to False. Returning with the almost full disk. Practice good housekeeping!')
		return (disks[np.argmax(freeDiskSpace)],dirs[np.argmax(freeDiskSpace)])
	else:
		print(disksCut[np.argmax(freeDiskSpace)],' has ',freeDiskSpace[np.argmax(freeDiskSpace)],' GB free space left ( ',freeDiskPercent[np.argmax(freeDiskSpace)],'% )')
		return (disksCut[np.argmax(freeDiskSpace)],dirs[np.argmax(freeDiskSpace)])
	
def createCacheDir(specificDir = None, availableDisks = None):
	
	if availableDisks == None:
		availableDisks = '/nfs/programs/VWrap/available_cache_disks.txt'	

	if not specificDir:
		print('\n+++++ Creating Cache Dir +++++')
		scratchDir = ''.join(random.SystemRandom().choice('0123456789abcdef') for i in range(32))
		chosenDisk = getBestDisk(availableDisks, Abort=True)
		subprocess.call('mkdir -p /nfs/data_disks/'+chosenDisk+'/'+scratchDir,shell=True)
		print('Created directory ',scratchDir,' at ','/nfs/data_disks/',chosenDisk,'/',scratchDir,sep='')
		print('++++++++++++++++++++++++++++++\n')
		return (chosenDisk,scratchDir,'/nfs/data_disks/'+chosenDisk+'/'+scratchDir)
	if specificDir:
		print('\n+++++ Creating Cache Dir +++++')
		scratchDir = ''.join(random.SystemRandom().choice('0123456789abcdef') for i in range(32))
		subprocess.call('mkdir -p '+str(specificDir)+'/'+scratchDir,shell=True)
		print('Created directory '+str(specificDir)+'/'+scratchDir)
		print('++++++++++++++++++++++++++++++\n')
		return (scratchDir,str(specificDir)+'/'+scratchDir)
	
def preallocateFile(orginalLTLocations, scratchDir):
	
	filename = orginalLTLocations.split('/')[-1]
	print('\n~~~~~~~ Pre-allocation ~~~~~~~')
	print('Pre-allocating the file '+orginalLTLocations+' --> '+str(scratchDir)+'/'+filename,sep='')
	subprocess.call('rsync -rptgoD --copy-links '+orginalLTLocations+' '+str(scratchDir)+'/'+filename,shell=True)
	print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n')

def deleteCacheDir(location):
	print('Deleting cache directory at ',location,'...',sep='')
	subprocess.call('/bin/rm -r '+location,shell=True)
	print('done.',sep='')
	
def makeLink(source, link):
	print('Making softlink from ',source,' to ',link,sep='')
	subprocess.call('ln -s '+source+' '+link,shell=True)
	
def alreadyDLed(pre, post, inputFile, c):
		
	print('Checking to see if ',inputFile,' is already downloaded...',sep='')
	directories = [str(x) for x in list(pre.glob('*/'+str(post)+'/*/'+inputFile))]
	downloaded = None 
	if len(directories) == 1:
		print('It is. File found to be located at: ',c.YELLOW+directories[0]+c.ENDC,sep='' )
		downloaded = True		
	elif len(directories) == 0:
		print('File not found on cluster.')
		downloaded = False
	elif len(directories) > 1:
		sys.exit('Warning: Found more than one download of file',inputFile,':\n\n',directories,'\n\n','You should fix this. Exiting.')
	elif downloaded == None:
		sys.exit('Error: Could not resolve whether file ',inputFile,' was downloaded or not. Something went wrong. Exiting.', sep='')
	return (downloaded, directories)

def alreadyLinked(link,inputDate, inputFile, c):
		
	print('Checking to see if', inputFile, 'is linked anywhere...')
	isLinked = None
	finalLink = link/inputDate/inputFile
	isLinked = finalLink.is_file()
	if isLinked == True:
		dataPath = finalLink.resolve()
		print('It is. Link is: ',c.LIGHTCYAN+str(finalLink)+c.ENDC,' ---> ', c.LIGHTGREEN+str(dataPath)+c.ENDC,sep='')
	elif isLinked == False:
		print('No link found.')
		
	return isLinked
	
	