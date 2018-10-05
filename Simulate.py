#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 29 14:15:59 2018

@author: zdhughes
"""

import array_rv
from PyQt5 import QtWidgets
import numpy as np

########## SIMULATION TAB ##########

class Mixin:
	
	""" This is just a Mixin class to hold all the signal actions for the Simulation tab. """
	
	def loadCsIPDF(self):
		
		""" This creates and plots the CsI PDF from a 2d numpy array file. Array.array_drv
			is what takes the file and creates the PDF. SamplesPerTime is set here to be used
			in the PE gaussian profile."""
		
		fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', '.')
		
		if fname[0]:
			self.CsIPDFPlotWidget.canvas.ax.clear()
			self.CsIPDFRO.setText(fname[0])
			self.CsIPDF = array_rv.array_drv(fname[0])
			self.CsIPDFPlotWidget.canvas.ax.plot(self.CsIPDF.baseX, self.CsIPDF.baseY, color='black')
			self.samplesPerTime = (len(self.CsIPDF.baseX))/np.ptp(self.CsIPDF.baseX)
			self.CsIPDFPlotWidget.canvas.ax.set_title('CsI PDF')
			#self.CsIPDFPlotWidget.canvas.ax.set_xlim(np.min(self.CsIPDF.baseX), np.max(self.CsIPDF.baseX))
			self.CsIPDFPlotWidget.canvas.ax.set_xlabel('time $\mu s$')
			self.CsIPDFPlotWidget.canvas.ax.set_ylabel('p')
			self.CsIPDFPlotWidget.canvas.draw()
			self.PDFTabs.setCurrentIndex(0)
			
	def loadChannelPDF(self):
		
		"""  Does the same thing as loadCsIPDF with no other variable setting. """
		
		fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', '.')
		
		if fname[0]:
			self.ChannelPDFPlotWidget.canvas.ax.clear()
			self.ChannelPDFRO.setText(fname[0])
			self.ChannelPDF = array_rv.array_drv(fname[0])
			self.ChannelPDFPlotWidget.canvas.ax.plot(self.ChannelPDF.baseX, self.ChannelPDF.baseY, color='black')
			self.ChannelPDFPlotWidget.canvas.ax.set_title('Channel PDF')
			self.ChannelPDFPlotWidget.canvas.ax.set_xlabel('Peak Voltage')
			self.ChannelPDFPlotWidget.canvas.ax.set_ylabel('p')
			self.ChannelPDFPlotWidget.canvas.draw()
			self.PDFTabs.setCurrentIndex(1)
			
	def loadPEPDF(self):
		
		""" Does the same thing as loadCsIPDF with no other variable setting.  """
		
		fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', '.')
		
		if fname[0]:
			self.PEPDFPlotWidget.canvas.ax.clear()
			self.PEPDFRO.setText(fname[0])
			self.PEPDF = array_rv.array_drv(fname[0])
			self.PEPDFPlotWidget.canvas.ax.plot(self.PEPDF.baseX, self.PEPDF.baseY, color='black')
			self.PEPDFPlotWidget.canvas.ax.set_title('Channel PDF')
			self.PEPDFPlotWidget.canvas.ax.set_xlabel('time $\mu s$')
			self.PEPDFPlotWidget.canvas.ax.set_ylabel('p')
			self.PEPDFPlotWidget.canvas.draw()
			self.PDFTabs.setCurrentIndex(1)
			
	def gaussianCBChange(self):
		
		""" This greys out the PE PDF and enables the gaussian PDF when checked. """
		
		if self.GaussianPECB.isChecked() == True:
			self.PEPDFRO.setEnabled(False)
			self.PEPDFButton.setEnabled(False)
			self.GaussianPEButton.setEnabled(True)
			self.GaussianPESet.setEnabled(True)
		else:
			self.PEPDFRO.setEnabled(True)
			self.PEPDFButton.setEnabled(True)
			self.GaussianPEButton.setEnabled(False)
			self.GaussianPESet.setEnabled(False)
			
	def gaussianPDFSet(self):
		
		""" This sets the gaussian PE PDF based on user input and using the CsI PDF scale. 
			The PDF is set by the samplesPerTime from the CSI PDF and the user Gaussian width."""
		
		self.PEPDFPlotWidget.canvas.ax.clear()
		self.gaussianWidth = float(self.GaussianPESet.text())
		self.GaussianPERO.setText(str(self.gaussianWidth))
		self.PEPDF = array_rv.physical_gaussian(self.samplesPerTime, self.gaussianWidth)
		CsITimeDomain = len(self.CsIPDF.baseX[0:len(self.PEPDF.pulseProfile)])
		self.PEPDFPlotWidget.canvas.ax.plot(self.CsIPDF.baseX[0:len(self.PEPDF.pulseProfile)], self.PEPDF.pulseProfile[0:CsITimeDomain], color='black') 
		self.PEPDFPlotWidget.canvas.ax.set_title('PE PDF')
		self.PEPDFPlotWidget.canvas.ax.set_xlabel('time $\mu s$')
		self.PEPDFPlotWidget.canvas.ax.set_ylabel('$V_{0}$')
		self.PEPDFPlotWidget.canvas.draw()
		self.PDFTabs.setCurrentIndex(2)
		
	def setNph(self):
		
		""" Sets how many photons will be simulated. """
		
		self.Nph = int(eval(self.NPESet.text()))
		self.NPERO.setText(str(self.Nph))
		
	def setFactor(self):
		
		""" Changes the PE pulse height by this factor. """
		
		self.factor = float(eval(self.FactorSet.text()))
		self.FactorRO.setText(str(self.factor))


	def simulatePulse(self):
		
		""" Uses array_rv.simulate_CsI_discrete to simulate CsI pulse and plots it. """
		
		self.previousAxes = self.SimulationPlotWidget.canvas.ax.get_ylim()
		self.SimulationPlotWidget.canvas.ax.clear()
		if self.FixAxesCB.isChecked() == True:
			self.SimulationPlotWidget.canvas.ax.set_ylim(self.previousAxes)
		self.simulationOutput = array_rv.simulate_CsI_discrete(self.CsIPDF, self.ChannelPDF, self.PEPDF, self.std, int(self.Nph*self.factor))
		self.SimulationPlotWidget.canvas.ax.plot(self.CsIPDF.baseX, self.simulationOutput, color='blue')
		self.SimulationPlotWidget.canvas.ax.set_title('Simulated WLS Events')
		self.SimulationPlotWidget.canvas.ax.set_xlabel('time $\mu s$')
		self.SimulationPlotWidget.canvas.ax.set_ylabel('Voltage [V]')
		self.SimulationPlotWidget.canvas.draw()
		self.SimulationPlotWidget.ntb.update()

######### /SIMULATION TAB ##########