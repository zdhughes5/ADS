#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 24 16:15:33 2018

@author: zdhughes
"""

import scipy.stats as st
import scipy.interpolate as si
import numpy as np
from herc.io_functions import colors
import matplotlib.pyplot as plt
import scipy.integrate as ini
import random as rn
import sys
import scipy.signal as ss

class array_crv(st.rv_continuous):
	
	'''Continous random variable with pdf defined by array. This is slow.'''
	
	def __init__(self, f, lower = None, upper = None, c = None):
		
		self.c = c if c is not None else colors()
		
		try:
			f.shape
			model = f
		except:
			try:
				model = np.load(f)
			except:
				print('Model is neither a npy file or npy array.')
		
		if len(model.shape) == 2:
			self.baseX = model[:, 0]
			self.baseY = model[:, 1]
			self.xLower = self.baseX[0]
			self.xUpper = self.baseX[-1]
		elif len(model.shape) == 1 and (upper and lower) is not None:
			self.baseY = model
			self.xLower = lower if lower is not None else print('Lower not set.')
			self.xUpper = upper if upper is not None else print('Upper not set.')
			self.baseX = np.linspace(self.xLower, self.xUpper, len(self.baseY))
		else:
			print('You mixed parameters or something went wrong.')

		try:
			self.baseY = self.baseY/(ini.quad(self.contPDF, self.xLower, self.xUpper)[0])
			print('Setting bounds to ' + str(self.xLower) + ' and ' + str(self.xUpper))
			st.rv_continuous.__init__(self, a = self.xLower, b = self.xUpper)
		except:
			print(self.c.red('Warning: Bounds were passed but not set.'))
			st.rv_continuous.__init__(self)
			self.baseX = np.linspace(0, 1, len(self.baseY))
			
		self.contPDF = si.interp1d(self.baseX, self.baseY, kind='linear')

	def _pdf(self, x):
		return np.interp(x, self.baseX, self.baseY)
	
class array_drv():
	
	'''Discrete random variable with pdf defined by array.
		Bug in scipy, can't call base class __init__ . . . . . . . .'''
	
	def __init__(self, f, lower = None, upper = None, c = None):
		
		self.c = c if c is not None else colors()
		
		try:
			f.shape
			model = f
		except:
			try:
				model = np.load(f)
			except:
				print('Model is neither a npy file or npy array.')
		
		if len(model.shape) == 2:
			self.baseX = model[:, 0]
			self.baseY = model[:, 1]
			self.xLower = self.baseX[0]
			self.xUpper = self.baseX[-1]
		elif len(model.shape) == 1 and (upper and lower) is not None:
			self.baseY = model
			self.xLower = lower if lower is not None else print('Lower not set.')
			self.xUpper = upper if upper is not None else print('Upper not set.')
			self.baseX = np.linspace(self.xLower, self.xUpper, len(self.baseY))
		else:
			print('You mixed parameters or something went wrong.')

		self.support = np.arange(len(self.baseX))
		self.baseY = self.baseY/np.sum(self.baseY)
		self.drv = st.rv_discrete(a=self.xLower, b=self.xUpper, values=(self.support, self.baseY))

			
	def rvs(self, **kwargs):
		return self.baseX[self.drv.rvs(**kwargs)]
	
	def rvs_raw(self, **kwargs):
		return self.drv.rvs(**kwargs)
	
class physical_gaussian():
	
	def __init__(self, samplesPerTime, pulseWidthPhysical):
		self.samplesPerTime = samplesPerTime
		self.pulseWidthPhysical = pulseWidthPhysical
		self.pulseWidthData = int((samplesPerTime*pulseWidthPhysical))
		self.pulseProfile = ss.gaussian(int(5.5*self.pulseWidthData), self.pulseWidthData/2.355)
		
	def pulse(self, amplitude):
		return amplitude * self.pulseProfile
		
def makeProfile(profile, samplePerTime, offset = 150):
	profile = np.load('CsIPDF.npy')
	baseX = profile[:, 0]
	baseY = profile[:, 1]
	returned = np.zeros(len(baseX))
	scale = np.random.random()
	returned[0:offset] = baseY[0:offset]*scale
	N0 = baseY[offset+1]*scale
	timeConstant = 1/(1.0*samplePerTime)
	for i, value in enumerate(baseY[offset+1::]):
		returned[i+offset] = N0*np.exp(-1*timeConstant*i)
	
	return returned

def simulate_CsI_discrete(CsI_rv, channel_rv, PE_rv, noiseStd, Nph):
	
	readout = np.random.normal(scale=noiseStd, size=len(CsI_rv.baseX))
	
	photonLoc = CsI_rv.rvs_raw(size=Nph)
	photonAmp = channel_rv.rvs(size=Nph)
	photonLoc = np.delete(photonLoc, np.where(photonLoc > len(readout) - len(PE_rv.pulseProfile) - 1)[0])
	photonAmp = np.delete(photonAmp, np.where(photonLoc > len(readout) - len(PE_rv.pulseProfile) - 1)[0])
	Nph = len(photonLoc)
	
	for i in range(Nph):
		photon = PE_rv.pulse(photonAmp[i])
		readout[photonLoc[i]:photonLoc[i]+len(PE_rv.pulseProfile)] += photon

	return readout
	



		
	
# =============================================================================
# things = [array_drv('ChannelPDF_'+str(x)+'.npy') for x in range(1,9)]
# for i in things:
# 	
# 	points = i.rvs(size=100000)
# 	weights = np.ones_like(points)/float(len(points))
# 	plt.hist(points, bins=2000, weights=weights)
# 	plt.plot(i.baseX, i.baseY)
# 	plt.show()
# =============================================================================
