#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 27 17:18:50 2018

@author: zdhughes
"""

from PyQt5 import QtWidgets
from configparser import ConfigParser, ExtendedInterpolation
import traceHandler
import numpy as np
import matplotlib.patches as mpatches
import matplotlib as mpl



########## TRACE ANALYSIS TAB ##########

class Mixin:
	
	""" Just a  mixin class for ADS that holds all the first tab functions. """
 		
	def pickAFile(self):
		
		""" Opens a file browser to pick a traceAnalysis master.conf file. """
		
		fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', '.')
		
		if fname[0]:
			self.FilePathText.setText(fname[0])
			self.LoadButton.setEnabled(True)
			
	def loadAfile(self):
		
		""" Runs the first part of traceAnalysis to load the master and config file. """
		
		configFile = self.FilePathText.text()
		config = ConfigParser(interpolation=ExtendedInterpolation(),inline_comment_prefixes=('#'))
		config.read(configFile)
		c = traceHandler.colors()
		if config['General'].getboolean('ansiColors') == True:
			c.enableColors()
		c.confirmColorsDonger()
		self.te = traceHandler.traceHandler(config, c)
		self.te.setupClassVariables()
		self.traceList = self.te.initializeData()
		self.PreviousTraceButton.setEnabled(True)
		self.NextTraceButton.setEnabled(True)
	
		
		#[General]
		self.workingDirRO.setText(str(self.te.workingDir))
		self.dataDirRO.setText(str(self.te.dataDir))
		self.plotsDirRO.setText(str(self.te.plotsDir))
		self.traceDirRO.setText(str(self.te.traceDir))
		self.ansiColorsRO.setText(str(self.te.ansiColors))
		self.doPlotsRO.setText(str(self.te.doPlots))
		
		#[IO]
		self.saveDataRO.setText(str(self.te.workingDir))
		self.saveToRO.setText(str(self.te.saveTo))
		self.loadRO.setText(str(self.te.load))
		self.loadFromRO.setText(str(self.te.loadFrom))
		self.showPlotsRO.setText(str(self.te.showPlots))
		self.savePlotsRO.setText(str(self.te.savePlots))
		self.allPlotsRO.setText(str(self.te.allPlots))
		
		#[Channels]
		self.doubleChannelRO.setText(str(self.te.doubleChannel))
		self.BGSubtractionRO.setText(str(self.te.BGSubtraction))
		self.channel1RO.setText(str(self.te.channel1))
		self.channel2RO.setText(str(self.te.channel2))
		self.metaRO.setText(str(self.te.meta))
		self.channel1BGRO.setText(str(self.te.channel1BG))
		self.channel2BGRO.setText(str(self.te.channel2BG))
		self.metaBGRO.setText(str(self.te.metaBG))
		
		#[Window]
		self.xPlotTypeRO.setText(str(self.te.xPlotType))
		self.yPlotTypeRO.setText(str(self.te.yPlotType))
		self.xRelativeGridRO.setText(str(self.te.xRelativeGrid))
		
		#[Integration]
		self.SILRO.setText(str(self.te.SIL))
		self.SIURO.setText(str(self.te.SIU))
		self.PILRO.setText(str(self.te.PIL))
		self.PIURO.setText(str(self.te.PIU))
		
		#[SpikeRejection]
		self.doSpikeRejectionRO.setText(str(self.te.doSpikeRejection))
		self.voltageThresholdRO.setText(str(self.te.voltageThreshold))
		self.timeThresholdRO.setText(str(self.te.timeThreshold))
		
		#[SmoothedDoubleRejection]
		self.doDoubleRejectionRO.setText(str(self.te.doDoubleRejection))
		self.SGWindowRO.setText(str(self.te.SGWindow))
		self.SGOrderRO.setText(str(self.te.SGOrder))
		self.minimaWindowDRRO.setText(str(self.te.minimaWindowDR))
		self.medianFactorDRRO.setText(str(self.te.medianFactorDR))
		self.fitWindowRO.setText(str(self.te.fitWindow))
		self.alphaThresholdRO.setText(str(self.te.alphaThreshold))
		
		#[PeakFinder]
		self.plotRawRO.setText(str(self.te.plotRaw))
		self.photonFilenameRO.setText(str(self.te.photonFilename))
		self.doPeakFinderRO.setText(str(self.te.doPeakFinder))
		self.savePhotonsRO.setText(str(self.te.savePhotons))
		self.medianFactorPFRO.setText(str(self.te.medianFactorPF))
		self.stdFactorRO.setText(str(self.te.stdFactor))
		self.convWindowRO.setText(str(self.te.convWindow))
		self.convPowerRO.setText(str(self.te.convPower))
		self.convSigRO.setText(str(self.te.convSig))
		self.minimaWindowPFRO.setText(str(self.te.minimaWindowPF))
		
		#[PhotonCounting]
		self.doPhotonCountingRO.setText(str(self.te.doPhotonCounting))
		self.photonFilesRO.setText(str(self.te.photonFiles))
		self.photonLabelsRO.setText(str(self.te.photonLabels))
		self.photonTitleRO.setText(str(self.te.photonTitle))
		
		#Parse meta file		
		#[General]
		self.xWidthPhysicalRO.setText(str(self.te.xWidthPhysical))
		self.xWidthUnitRO.setText(str(self.te.xWidthUnit))
		self.xLocationRO.setText(str(self.te.xLocation))
		self.yHeightUnitsRO.setText(str(self.te.yHeightUnits))
		self.triggerRO.setText(str(self.te.trigger))
		self.triggerSourceRO.setText(str(self.te.triggerSource))
		self.triggerTypeRO.setText(str(self.te.triggerType))
		self.sampleRO.setText(str(self.te.sample))
		self.xDivsRO.setText(str(self.te.xDivs))
		self.yDivsRO.setText(str(self.te.yDivs))
		
		#[channel1]
		self.object1RO.setText(str(self.te.object1))
		self.inputImpedence1RO.setText(str(self.te.inputImpedence1))
		self.coupling1RO.setText(str(self.te.coupling1))
		self.offset1RO.setText(str(self.te.offset1))
		self.bandwidth1RO.setText(str(self.te.bandwidth1))
		self.VoltsPerDiv1RO.setText(str(self.te.VoltsPerDiv1))
		self.yLocation1RO.setText(str(self.te.yLocation1))
		
		#[channel2]
		self.object2RO.setText(str(self.te.object2))
		self.inputImpedence2RO.setText(str(self.te.inputImpedence2))
		self.coupling2RO.setText(str(self.te.coupling2))
		self.offset2RO.setText(str(self.te.offset2))
		self.bandwidth2RO.setText(str(self.te.bandwidth2))
		self.VoltsPerDiv2RO.setText(str(self.te.VoltsPerDiv2))
		self.yLocation2RO.setText(str(self.te.yLocation2))		
		
		
	def plotDualTrace(self):
		
		""" Plots the traces from the trace File. """
		
		self.TracePlotWidget.canvas.ax1.clear()
		self.TracePlotWidget.canvas.ax2.clear()
		legend1 = self.te.windowParametersY1['object']
		legend2 = self.te.windowParametersY2['object']
		color1 = self.te.windowParametersY1['color']
		color2 = self.te.windowParametersY2['color']
		if self.te.windowParametersX['selection'] == 'relative':
			xLabel = 'Time Relative to Trigger ['+self.te.windowParametersX['xWidthUnit']+']'
		else:
			xLabel = 'Time ['+self.te.windowParametersX['xWidthUnit']+']'
		yLabel1 = self.te.windowParametersY1['object']+' Voltage [V]'
		yLabel2 = self.te.windowParametersY2['object']+' Voltage [V]'
		title = ('APT Raw Detector Trace')
		myFont = {'fontname':'Liberation Serif'}
	 		
		SIL = self.te.windowParametersX['SIL']
		SIU = self.te.windowParametersX['SIU']
		PIL = self.te.windowParametersX['PIL']
		PIU = self.te.windowParametersX['PIU']
		VS = np.min([self.te.windowParametersY1['yRange'][0], self.te.windowParametersY2['yRange'][0]])
		VE = np.max([self.te.windowParametersY1['yRange'][1], self.te.windowParametersY2['yRange'][1]])
				
		self.TracePlotWidget.canvas.ax1.set_title(title,**myFont)		
		self.TracePlotWidget.canvas.ax1.grid(b=True, linestyle=':')
		self.TracePlotWidget.canvas.ax1.plot(self.te.windowParametersX['x'], self.traceList.iloc[:, 0::2].iloc[:, self.place], color=color1, linewidth=0.5, linestyle="-")
		self.TracePlotWidget.canvas.ax1.set_xlabel(xLabel, **myFont)
		self.TracePlotWidget.canvas.ax1.set_xlim(self.te.windowParametersX['xRange'][0], self.te.windowParametersX['xRange'][1])
		self.TracePlotWidget.canvas.ax1.set_xticks(self.te.windowParametersX['xTicks'])
		self.TracePlotWidget.canvas.ax1.set_ylim(self.te.windowParametersY1['yRange'][0], self.te.windowParametersY1['yRange'][1])
		self.TracePlotWidget.canvas.ax1.set_ylabel(yLabel1,**myFont)
		self.TracePlotWidget.canvas.ax1.set_yticks(self.te.windowParametersY1['yTicks'])
		self.TracePlotWidget.canvas.ax1.tick_params('y',colors=color1)
		
		self.TracePlotWidget.canvas.ax2.plot(self.te.windowParametersX['x'], self.traceList.iloc[:, 1::2].iloc[:, self.place], color=color2, linewidth=0.5, linestyle="-")
		self.TracePlotWidget.canvas.ax2.set_ylim(self.te.windowParametersY2['yRange'][0], self.te.windowParametersY2['yRange'][1])
		self.TracePlotWidget.canvas.ax2.set_ylabel(yLabel2,**myFont)
		self.TracePlotWidget.canvas.ax2.set_yticks(self.te.windowParametersY2['yTicks'])
		self.TracePlotWidget.canvas.ax2.tick_params('y',colors=color2)
		#fig.tight_layout()
		
		self.TracePlotWidget.canvas.ax1.plot([SIL,SIL],[VS,VE],color='cyan',linestyle="--",alpha=0.65)
		self.TracePlotWidget.canvas.ax1.plot([SIU,SIU],[VS,VE],color='cyan',linestyle="--",alpha=0.65)
		self.TracePlotWidget.canvas.ax1.plot([PIL,PIL],[VS,VE],color='purple',linestyle="--",alpha=0.65)
		self.TracePlotWidget.canvas.ax1.plot([PIU,PIU],[VS,VE],color='purple',linestyle="--",alpha=0.65)
		
		blue_patch = mpatches.Patch(color=color1, label=legend1)
		red_patch = mpatches.Patch(color=color2, label=legend2)
		mpl.rc('font',family='Liberation Serif')		
		self.TracePlotWidget.canvas.ax1.legend(loc='lower right',handles=[red_patch,blue_patch])
		self.TracePlotWidget.ntb.update()
		self.TracePlotWidget.canvas.draw()
		
	def plotNextTrace(self):
		
		""" Plots the next trace. """
		
		if self.place <= len(self.traceList.iloc[:, 0::2].columns)-1:
			self.place += 1
		self.plotDualTrace()
	
	def plotPreviousTrace(self):
		
		""" Plots the previous trace. """
		
		if self.place >= 1:
			self.place -= 1
		self.plotDualTrace()
		
######### /TRACE ANALYSIS TAB ##########