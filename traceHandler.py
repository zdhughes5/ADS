"""
Created on Thu Jan 26 17:45:11 2017

@author: zdhughes
"""

import sys
import numpy as np
from pathlib import Path
import code
import pandas as pd
from configparser import ConfigParser, ExtendedInterpolation
import subprocess

#TODO: Recomment since refactor. Get rid of colors and use the general purpose modules I've made.

#This class does the data extraction, crunching, and plotting. Data crunching is done functionally. 
#That is, even though the class functions are not static, they are called like they are.
#Why? I'm self-taught and experimenting.
class traceHandler:
	
	'''This class handles all the metadata related to the oscilliscope traces. Basically, it reads in the master config file and stores the information
		and anything directly created from the master config file, i.e. plotting window parameters.'''
	
	def __init__(self, config = None, c = None):
		self.config = config if config is not None else sys.exit('No config found for traceExtractor. Aborting.')
		self.c = c if c is not None else colors()
		
	#Reads in values from config and meta files and creates all forseeable *static* variables.
	#meta file = file that describes oscilliscope settings	
	def setupClassVariables(self):
		
		'''This class method is what does the parameterization. Invoke it after instantiating. Could have just of been part of __init__ . '''
		
		def getDefaultColor(self):
			self.currentColor += 1
			if self.currentColor == len(self.defaultColors):
				self.currentColor = -1
			return self.defaultColors[self.currentColor]

		def _absoluteParsX(self):
			
			xRange = ( float(0), self.xWidthPhysical )
			xRangeImage = ( int(0),  int(self.sample))
			xTicks = np.linspace(xRange[0], xRange[1], self.xDivs+1)
			iSIL = int(round(self.SIL*self.xConversionPtoI))
			iSIU = int(round(self.SIU*self.xConversionPtoI))
			iPIL = int(round(self.PIL*self.xConversionPtoI))
			iPIU = int(round(self.PIU*self.xConversionPtoI))
			x = np.linspace(xRange[0], xRange[1], self.sample)
			xWidthUnit = self.xWidthUnit
			selection = 'absolute'
		
			return (xRange, xRangeImage, x, xTicks, iSIL, iSIU, iPIL, iPIU, xWidthUnit, selection)
			
			
		def _relativeParsX(self):
			
			xRange = ( -1*(self.xWidthPhysical/2+self.xLocation), self.xWidthPhysical/2-self.xLocation )
			xRangeImage = ( int(0),  int(self.sample))
			if self.xRelativeGrid == True:
				leftTick = -1*self.xWidthPhysical/self.xDivs
				rightTick =  self.xWidthPhysical/self.xDivs
				xTicks = np.array([0])
				while rightTick <= xRange[1]:
					xTicks = np.append(xTicks, rightTick)
					rightTick += self.xWidthPhysical/self.xDivs	
				while leftTick >= xRange[0]:
					xTicks = np.insert(xTicks, 0, leftTick)
					leftTick += -1*self.xWidthPhysical/self.xDivs				
			elif self.xRelativeGrid == False:	
				xTicks = np.linspace(xRange[0], xRange[1], self.xDivs+1)			
			iSIL = int(round((self.SIL+self.xWidthPhysical/2+self.xLocation)*self.xConversionPtoI))
			iSIU = int(round((self.SIU+self.xWidthPhysical/2+self.xLocation)*self.xConversionPtoI))
			iPIL = int(round((self.PIL+self.xWidthPhysical/2+self.xLocation)*self.xConversionPtoI))
			iPIU = int(round((self.PIU+self.xWidthPhysical/2+self.xLocation)*self.xConversionPtoI))
			x = np.linspace(xRange[0], xRange[1], self.sample)
			xWidthUnit = self.xWidthUnit
			selection = 'relative'
		
			return (xRange, xRangeImage, x, xTicks, iSIL, iSIU, iPIL, iPIU, xWidthUnit, selection)
			
		def _symmetricParsX(self):
			
			xRange = ( -1*self.xWidthPhysical/2, self.xWidthPhysical/2 )
			xRangeImage = ( int(0),  int(self.sample))
			xTicks = np.linspace(xRange[0], xRange[1], self.xDivs+1)
			iSIL = int(round((self.SIL+self.xWidthPhysical/2)*self.xConversionPtoI))
			iSIU = int(round((self.SIU+self.xWidthPhysical/2)*self.xConversionPtoI))
			iPIL = int(round((self.PIL+self.xWidthPhysical/2)*self.xConversionPtoI))
			iPIU = int(round((self.PIU+self.xWidthPhysical/2)*self.xConversionPtoI))
			x = np.linspace(xRange[0], xRange[1], self.sample)
			xWidthUnit = self.xWidthUnit
			selection = 'symmetric'
		
			return (xRange, xRangeImage, x, xTicks, iSIL, iSIU, iPIL, iPIU, xWidthUnit, selection)

		def _relativeParsY(self, scale, yLocation):
			yRange = (-1*scale*self.yDivs/2-yLocation*scale, scale*self.yDivs/2-yLocation*scale )
			yTicks = np.linspace(yRange[0], yRange[1], self.yDivs+1)
			
			return (yRange, yTicks)
			
		def _symmetricParsY(self, scale, yLocation):
			yRange = ( -1*scale*self.yDivs/2, scale*self.yDivs/2 )
			yTicks = np.linspace(yRange[0], yRange[1], self.yDivs+1)
			
			return (yRange, yTicks)
			
		def _getParsX(self, f):
			
			def wrapper():
				
				xRange, xRangeImage, x, xTicks, iSIL, iSIU, iPIL, iPIU, xWidthUnit, selection = f(self)
				
				signalLimitsPhys = (self.SIL, self.SIU)
				signalLimitsImag = (iSIL, iSIU)
				pedestalLimitsPhys = (self.PIL, self.PIU)
				pedestalLimitsImag = (iPIL, iPIU)

				signalIntervalPhys = self.SIU - self.SIL
				signalIntervalImag = iSIU - iSIL
				pedestalIntervalPhys = self.PIU - self.PIL
				pedestalIntervalImag = iPIU - iPIL
				
				windowPars = {
					'xRange' : xRange,
					'xTicks' : xTicks,
					'x' : x,
					'SIL' : self.SIL,
					'SIU' : self.SIU,
					'PIL' : self.PIL,
					'PIU' : self.PIU,
					'signalLimits' : signalLimitsPhys,
					'pedestalLimits' : pedestalLimitsPhys,
					'signalInterval' : signalIntervalPhys,
					'pedestalInterval' : pedestalIntervalPhys,
					'xWidthUnit' : xWidthUnit,
					'selection' : selection
					}
				dataPars = {
					'xRange' : xRangeImage,
					'SIL' : iSIL,
					'SIU' : iSIU,
					'PIL' : iPIL,
					'PIU' : iPIU,
					'signalLimits' : signalLimitsImag,
					'pedestalLimits' : pedestalLimitsImag,
					'signalInterval' : signalIntervalImag,
					'pedestalInterval' : pedestalIntervalImag
					}	
					
				return windowPars, dataPars
				
			return wrapper
			
		def _getParsY(self, f, scale, yLocation, objectName):
			
			def wrapper():
				
				yRange, yTicks = f(self, scale, yLocation)
				windowPars = {
					'yLocation' : yLocation,
					'yRange' : yRange,
					'yTicks' : yTicks,
					'scale' : scale,
					'object' : objectName,
					'color' : getDefaultColor(self)
					}
				dataPars = {
					}
					
				return windowPars, dataPars
				
			return wrapper
		

		##############################			
		#Set-up variables
		##############################
			
		#Parse master file
		#[General]
		self.workingDir = Path(self.config['General']['workingDir'])
		self.dataDir = Path(self.config['General']['dataDir'])
		self.plotsDir = Path(self.config['General']['plotsDir'])
		self.traceDir = Path(self.config['General']['traceDir'])
		self.ansiColors = self.config['General'].getboolean('ansiColors')
		self.doPlots = self.config['General'].getboolean('doPlots')
		
		#[IO]
		self.saveData = self.config['IO'].getboolean('saveData')
		self.saveTo = Path(self.config['IO']['saveTo'])
		self.load = self.config['IO'].getboolean('load')
		self.loadFrom = Path(self.config['IO']['loadFrom'])
		self.showPlots = self.config['IO'].getboolean('showPlots')
		self.savePlots = self.config['IO'].getboolean('savePlots')
		self.allPlots = self.config['IO'].getboolean('allPlots')	
		
		#[Channels]
		self.doubleChannel = self.config['Channels'].getboolean('doubleChannel')
		self.BGSubtraction = self.config['Channels'].getboolean('BGSubtraction')
		self.channel1 = Path(self.config['Channels']['channel1'])
		self.channel2 = Path(self.config['Channels']['channel2'])
		self.meta = Path(self.config['Channels']['meta'])
		self.channel1BG = Path(self.config['Channels']['channel1BG'])
		self.channel2BG = Path(self.config['Channels']['channel2BG'])
		self.metaBG = Path(self.config['Channels']['metaBG'])
		
		#[Window]
		self.xPlotType = self.config['Window']['xPlotType']
		self.yPlotType = self.config['Window']['yPlotType']
		self.xRelativeGrid = self.config['Window'].getboolean('xRelativeGrid')

		#[Integration]
		self.SIL = float(self.config['Integration']['signalIntegrationLower'])
		self.SIU = float(self.config['Integration']['signalIntegrationUpper'])
		self.PIL = float(self.config['Integration']['pedestalIntegrationLower'])
		self.PIU = float(self.config['Integration']['pedestalIntegrationUpper'])
		
		#[SpikeRejection]
		self.doSpikeRejection = self.config['SpikeRejection'].getboolean('doSpikeRejection')
		self.voltageThreshold = float(self.config['SpikeRejection']['voltageThreshold'])
		self.timeThreshold = int(self.config['SpikeRejection']['timeThreshold'])
		
		#[SmoothedDoubleRejection]
		self.doDoubleRejection = self.config['SmoothedDoubleRejection'].getboolean('doDoubleRejection')
		self.SGWindow = int(self.config['SmoothedDoubleRejection']['SGWindow'])
		self.SGOrder = int(self.config['SmoothedDoubleRejection']['SGOrder'])
		self.minimaWindowDR = int(self.config['SmoothedDoubleRejection']['minimaWindowDR'])
		self.medianFactorDR = float(self.config['SmoothedDoubleRejection']['medianFactorDR'])
		self.fitWindow = int(self.config['SmoothedDoubleRejection']['fitWindow'])
		self.alphaThreshold = float(self.config['SmoothedDoubleRejection']['alphaThreshold'])
		
		#[PeakFinder]
		try:
			self.plotRaw = [int(x) for x in self.config['PeakFinder']['plotRaw'].split(',')]
		except:
			print('No plotRaw dfined. Passing...')
			self.plotRaw = []
		self.photonFilename = self.config['PeakFinder']['photonFilename']
		self.doPeakFinder = self.config['PeakFinder'].getboolean('doPeakFinder')
		self.savePhotons = self.config['PeakFinder'].getboolean('savePhotons')
		self.medianFactorPF = float(self.config['PeakFinder']['medianFactorPF'])
		self.stdFactor = float(self.config['PeakFinder']['stdFactor'])
		self.convWindow = int(self.config['PeakFinder']['convWindow'])
		self.convPower = float(self.config['PeakFinder']['convPower'])
		self.convSig = float(self.config['PeakFinder']['convSig'])
		self.minimaWindowPF = int(self.config['PeakFinder']['minimaWindowPF'])
		
		#[PhotonCounting]
		self.doPhotonCounting = self.config['PhotonCounting'].getboolean('doPhotonCounting')
		self.photonFiles = self.config['PhotonCounting']['photonFiles'].split(',')
		self.photonLabels = self.config['PhotonCounting']['photonLabels'].split(',')
		self.photonTitle = self.config['PhotonCounting']['photonTitle']
		
		#Parse meta file		
		#[General]
		self.metaConfig = ConfigParser(interpolation=ExtendedInterpolation(),inline_comment_prefixes=('#'))
		self.metaConfig.read(str(self.meta))
		self.xWidthPhysical = float(self.metaConfig['General']['xWidthPhysical'])
		self.xWidthUnit = self.metaConfig['General']['xWidthUnit']
		self.xLocation = -1*float(self.metaConfig['General']['xLocation'])
		self.yHeightUnits = self.metaConfig['General']['yHeightUnits']
		self.trigger = float(self.metaConfig['General']['trigger'])
		self.triggerSource = self.metaConfig['General']['triggerSource']
		self.triggerType = self.metaConfig['General']['triggerType']
		self.sample = float(self.metaConfig['General']['sample'])
		self.xDivs = float(self.metaConfig['General']['xDivs'])
		self.yDivs = float(self.metaConfig['General']['yDivs'])
		
		#[channel1]
		self.object1 = self.metaConfig['Channel1']['object']
		self.inputImpedence1 = self.metaConfig['Channel1']['inputImpedence']
		self.coupling1 = self.metaConfig['Channel1']['coupling']
		self.offset1 = self.metaConfig['Channel1']['offset']
		self.bandwidth1 = self.metaConfig['Channel1']['bandwidth']
		self.VoltsPerDiv1 = float(self.metaConfig['Channel1']['VoltsPerDiv'])
		self.yLocation1 = float(self.metaConfig['Channel1']['yLocation'])
		
		#[channel2]
		if self.doubleChannel == True:
			self.object2 = self.metaConfig['Channel2']['object']
			self.inputImpedence2 = self.metaConfig['Channel2']['inputImpedence']
			self.coupling2 = self.metaConfig['Channel2']['coupling']
			self.offset2 = self.metaConfig['Channel2']['offset']
			self.bandwidth2 = self.metaConfig['Channel2']['bandwidth']
			self.VoltsPerDiv2 = float(self.metaConfig['Channel2']['VoltsPerDiv'])
			self.yLocation2 = float(self.metaConfig['Channel2']['yLocation'])
		
		#Repeat above for BG file
		if self.BGSubtraction == True:
			self.metaConfigBG = ConfigParser(interpolation=ExtendedInterpolation(),inline_comment_prefixes=('#'))
			self.metaConfigBG.read(str(self.metaBG))
			
			self.xWidthPhysicalBG = float(self.metaConfigBG['General']['xWidthPhysical'])
			self.xWidthUnitBG = self.metaConfigBG['General']['xWidthUnit']
			self.xLocationBG = float(self.metaConfigBG['General']['xLocation'])
			self.yHeightUnitsBG = self.metaConfigBG['General']['yHeightUnits']
			self.triggerBG = float(self.metaConfigBG['General']['trigger'])
			self.triggerSourceBG = self.metaConfigBG['General']['triggerSource']
			self.triggerTypeBG = self.metaConfigBG['General']['triggerType']
			self.sampleBG = float(self.metaConfigBG['General']['sample'])
			self.xDivsBG = float(self.metaConfigBG['General']['xDivs'])
			self.yDivsBG = float(self.metaConfigBG['General']['yDivs'])
			
			self.objectBG1 = self.metaConfigBG['Channel1']['object']
			self.inputImpedenceBG1 = self.metaConfigBG['Channel1']['inputImpedence']
			self.couplingBG1 = self.metaConfigBG['Channel1']['coupling']
			self.offsetBG1 = self.metaConfigBG['Channel1']['offset']
			self.bandwidth1 = self.metaConfigBG['Channel1']['bandwidth']
			self.VoltsPerDivBG1 = float(self.metaConfigBG['Channel1']['VoltsPerDiv'])
			self.yLocationBG1 = float(self.metaConfigBG['Channel1']['yLocation'])
			
			if self.doubleChannel == True:
				self.objectBG2 = self.metaConfigBG['Channel2']['object']
				self.inputImpedenceBG2 = self.metaConfigBG['Channel2']['inputImpedence']
				self.couplingBG2 = self.metaConfigBG['Channel2']['coupling']
				self.offsetBG2 = self.metaConfigBG['Channel2']['offset']
				self.bandwidth2 = self.metaConfigBG['Channel2']['bandwidth']
				self.VoltsPerDivBG2 = float(self.metaConfigBG['Channel2']['VoltsPerDiv'])
				self.yLocationBG2 = float(self.metaConfigBG['Channel2']['yLocation'])	
		
		##############################
		#Calculate some values
		##############################
		
		#Get Axis styles
		self.xPlotSelection = {'absolute' : False, 'relative' : False, 'symmetric' : False}
		self.xPlotSelection[self.xPlotType.lower()] = True
		self.yPlotSelection = {'relative' : False, 'symmetric' : False}
		self.yPlotSelection[self.yPlotType.lower()] = True
		self.defaultColors = ['blue', 'red', 'green', 'cyan', 'magenta', 'yellow', 'black', '#42f48c', '#5909ed', '#e59409', '#492500']
		self.currentColor = -1 
		self.photonColors = [getDefaultColor(self) for x in self.photonFiles]
		self.currentColor = -1

		#parse unit for plot axis
		if self.xWidthUnit == 's':
			self.xWidthUnit = '$Seconds$'			
		elif self.xWidthUnit == 'm':
			self.xWidthUnit = '$milliseconds$'		
		elif self.xWidthUnit == 'u':
			self.xWidthUnit = '$\mu s$'
		elif self.xWidthUnit == 'n':
			self.xWidthUnit = '$ns$'			
		
		#Conversion factors
		self.xConversionDtoP = self.xWidthPhysical/self.xDivs #Turns division points/ticks into physicsal marks
		self.xConversionPtoI = self.sample/self.xWidthPhysical #Turns physical units into array index

		#Window, data specific parameters
		if self.xPlotSelection['absolute'] == True:
			self.windowParametersX, self.dataParametersX = _getParsX(self, _absoluteParsX)()
		elif self.xPlotSelection['relative'] == True:
			self.windowParametersX, self.dataParametersX = _getParsX(self, _relativeParsX)()
		elif self.xPlotSelection['symmetric'] == True:
			self.windowParametersX, self.dataParametersX = _getParsX(self, _symmetricParsX)()
		else:
			sys.exit('Something wrong in getting the x-axis window parameters!')
				
		if self.yPlotSelection['relative'] == True:
			self.windowParametersY1, self.dataParametersY1 = _getParsY(self, _relativeParsY, self.VoltsPerDiv1, self.yLocation1, self.object1)()
			self.windowParametersY2, self.dataParametersY2 = _getParsY(self, _relativeParsY, self.VoltsPerDiv2, self.yLocation2, self.object2)()
		elif self.yPlotSelection['symmetric'] == True:
			self.windowParametersY1, self.dataParametersY1 = _getParsY(self, _symmetricParsY, self.VoltsPerDiv1, self.yLocation1, self.object1)()
			self.windowParametersY2, self.dataParametersY2 = _getParsY(self, _symmetricParsY, self.VoltsPerDiv2, self.yLocation2, self.object2)()
		else:
			sys.exit('Something wrong in getting the y-axis window parameters!')	
		
		##############################			
		#Print sanity check
		##############################
		print('\n#################################################################')
		print('################## '+self.c.lightgreen('Time for a sanity check...!')+' ##################')
		print('#################################################################\n')
		print('Physical-to-image signal integration window map: '+self.c.cyan('[ '+str(self.windowParametersX['SIL'])+','+str(self.windowParametersX['SIU'])+' ] -->')+self.c.yellow(' [ '+str(self.dataParametersX['SIL'])+','+str(self.dataParametersX['SIU'])+' ]'))
		print('Physical-to-image pedestal integration window map: '+self.c.cyan('[ '+str(self.windowParametersX['PIL'])+','+str(self.windowParametersX['PIU'])+' ] -->')+self.c.yellow(' [ '+str(self.dataParametersX['PIL'])+','+str(self.dataParametersX['PIU'])+' ]'))
		print('                             --and--                             ')
		print('The x-axis range will be: '+self.c.blue('( '+str(self.windowParametersX['xRange'][0])+', '+str(self.windowParametersX['xRange'][1])+' )')+', with ticks at: ')
		print(self.windowParametersX['xTicks'])
		print('\n#################################################################\n')
		
	##########	

	#Takes in a path to oscilliscope file and returns the lines.	
	def openRawTraceFile(self, channel1File):
		with open(str(channel1File),'r') as f:
			lines = [line.strip('\n') for line in f]
													
		return lines
		
	#Convenience function that opens two oscilliscope files.
	def openDualRawTraceFile(self, channel1File, channel2File):
		
		lines1 = self.openRawTraceFile(channel1File)
		lines2 = self.openRawTraceFile(channel2File)
													
		return (lines1, lines2)
		
	def initializeData(self, channels=2, saveInternal=False):
		import traceMethods as tm
		
		try:
			print('Making working directory: '+self.c.yellow(str(self.workingDir))+'...')
			subprocess.call('mkdir -p '+str(self.workingDir), shell=True)
		except NameError:
			sys.exit(self.c.red('WorkingDir variable not found. Did you setupClassVariables?'))
		
		if self.load == True:
			print('Loading in trace list...')
			traceList = pd.read_hdf(str(self.loadFrom), 'table')
		else:
			print('Reading in lines... (this takes a lot of memory!)')
			if channels == 2:
				lines = self.openDualRawTraceFile(self.channel1, self.channel2)
				traceList = tm.dualTraceToPandas(tm.extractDualRawTraces(lines), self.windowParametersX['x'])
				del lines
			elif channels == 1:
				lines = self.openRawTraceFile(self.channel1)
				traceList = tm.tracetoPandas(tm.extractRawTraces(lines), self.windowParametersX['x'])
				del lines
			if self.saveData == True:
				traceList.to_hdf(str(self.saveTo), 'table')
				
		if saveInternal:
			self.traceList = traceList
				
		return traceList
	
		
	##########			
		
class colors:

	BLACK = ''
	BLUE = ''
	GREEN = ''
	CYAN = ''
	RED = ''
	PURPLE = ''
	BROWN = ''
	GRAY = ''
	DARKGRAY = ''
	LIGHTBLUE = ''
	LIGHTGREEN = ''
	LIGHTCYAN = ''
	LIGHTRED = ''
	LIGHTPURPLE = ''
	YELLOW = ''
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
		if self.getState() ==  True:		
			print('Colors are '+self.red('e')+self.orange('n')+self.yellow('a')+self.green('b')+self.blue('l')+self.indigo('e')+self.violet('d'))
		elif self.getState() == False:
			print('Colors are off!')
		elif self.getState() == -1:
			print('Error: Can\'t get color state.')
			
	def confirmColorsDonger(self):
		if self.getState() ==  True:
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
