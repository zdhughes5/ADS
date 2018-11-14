#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 09:35:23 2018

@author: zdhughes
"""

import numpy as np
import math as m
import matplotlib.pyplot as plt


pi = np.pi
Na = 6.022140857e23 # #
r_e = 2.817e-13 # cm
m_e = 9.10938356e-28 # g
m_p = 1.6726219e-24
Z_CsI = 53+55 # #
A_CsI = 259.80992 # #
p_CsI = 4.51 # g/cm^3
#I_CsI = 6.260018845027454e-06 #MeV
I_CsI = 553.100000e-6
Z_water = 10
A_water = 18
p_water = 1
I_water = 74.6e-6

c = 2.998e10
erg_to_MeV = 624150.91 #MeV
m_e_MeV = m_e * c**2 * erg_to_MeV # MeV/c^2
m_p_MeV = m_p * c**2 * erg_to_MeV 


prefactor = 0.1535 # MeV cm^2/g   2pi N R^2 M_e c^2


def gammaToBeta(y):
	return np.sqrt( 1-(1/(y**2)) )
	
def betaToGamma(b):
	return 1/np.sqrt(1-b**2)

def W_max(B, M): #in grams
	
	y = betaToGamma(B)
	N2 = B**2 * y**2
	s = m_e / M
	
	numer = 2 * m_e * c**2 * N2
	numer = numer * erg_to_MeV # ergs to MeV
	denom = 1 + 2*s * np.sqrt(1+N2)+s**2
	
	return numer/denom

def betaFromE(E, z): # MeV, #
	
		if z == 0:
			y = E/(m_e_MeV)+1
		else:
			y = E/(z*m_p_MeV)+1
		B = gammaToBeta(y)
		print('Got '+str(B)+' for beta.')
		return B
  
def bethBlochIon(p, Z, A, z, E, M, I): #g/cm**2, #, #, #, MeV, g, MeV
	 
	B = betaFromE(E, z)
	B2 = B**2
	y2 = betaToGamma(B)**2
	N2 = y2 * B2
	W = W_max(B, M) #MeV
	 
	outsideParentheses = prefactor * p * (Z/A) * (z**2/B2)
	lnTerm = np.log( (2*m_e_MeV*N2*W)/(I**2) )
	betaTerm = 2*B2
	 
	dE_dX = outsideParentheses * ( lnTerm - betaTerm )
	 
	return dE_dX




if __name__ == "__main__":
	z_ion = 1 # #
	KE_start = 1 # MeV
	
	
	KEs = np.array([KE_start])
	KE_current = KE_start
	dE_dXs = np.array([])
	
	x_0 = 0.00 #cm
	x_f = 30 #cm
	dx = 0.001 #cm
	
	depth = np.arange(x_0, x_f, dx)
	
	for x in depth:
		if KE_current > 0:
			this_dE_dX = bethBlochIon(p_water, Z_water, A_water, z_ion, KE_current, z_ion*m_p, I_water)
			dE_dXs = np.append(dE_dXs, this_dE_dX)
			E_loss = this_dE_dX*dx
			KE_current = KE_current - E_loss
			KEs = np.append(KEs, KE_current)
	
	if len(dE_dXs) > len(depth):
		dE_dXs = dE_dXs[:-1]
	if len(KEs) > len(depth):
		KEs = KEs[:-1]	
		
	#plt.plot(depth[0:len(dE_dXs)], dE_dXs)
	#plt.show()
	
	fig = plt.figure()
	ax = fig.add_subplot(111) 
	ax.plot(depth[0:len(KEs)], KEs)
	#ax.set_xscale('log')
	ax.set_yscale('log')
	plt.show()
	
	fig = plt.figure()
	ax = fig.add_subplot(111) 
	ax.plot(depth[0:len(dE_dXs)], dE_dXs)
	#ax.set_xscale('log')
	#ax.set_yscale('log')
	plt.show()
	  
	
	rE_0 = 0.01 #MeV
	rE_f = 100000 #MeV
	dE = 0.01 #MeV
	
	sE_0 = -3 #MeV
	sE_f = 10 #MeV
	NE = 10000
	
	E_range = np.arange(rE_0, rE_f, dE)
	E_space = np.logspace(sE_0, sE_f, NE)
	dE_dXs = np.array([])
	
	for this_E in E_space:
		this_dE_dX = bethBlochIon(p_CsI, Z_CsI, A_CsI, z_ion, this_E, z_ion*m_p, I_CsI)
		dE_dXs = np.append(dE_dXs, this_dE_dX)
	
	fig = plt.figure()
	ax = fig.add_subplot(111) 
	ax.plot(E_space[0:len(dE_dXs)], dE_dXs/p_CsI)
	ax.set_xscale('log')
	ax.set_yscale('log')
	plt.show()
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  