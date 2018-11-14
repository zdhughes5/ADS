#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 11 23:28:46 2018

@author: zdhughes
"""

import math as m
import numpy as np
import matplotlib.pyplot as plt

#m_nucleon = 938.27 #MeV/c^2
#m_electron = 0.511 #MeV/c^2
#e_charge = 1.6022*10**-19 #C
#k = (8.99*10**9) * (5.61*10**29) * (1/(100**3))
#I_CsI = 4.895*10**(-4) #MeV
#n_CsI = 1.048*10**22 #2.53*10**27 #MeV/cm^3c^2 4.51 g/cm^3
#A_CsI = (55+53) #atomic number

k0_mks = 8.988*10**9 #N*m**2 C**-2
e_mks = 1.6021766*10**(-19) #C
m_e_mks = 9.109383*10**(-31) #kg
c_mks = 2.998*10**8 #m**1 s**-1

k0_ev = 5.609*10**24 # MeV cm/C**2
e_ev = 1.6021766*10**(-19) #C
m_e_ev = 0.511 #MeV/c^2
m_p_ev = 938.27 #MeV/c^2
c_ev = 2.998*10**10 #cm**1 s**-1

MeV_to_J = 1.6021766e-13
J_to_MeV = 1/MeV_to_J

n_CsI = 1.129*10**24


def getI(mks = False):
	I_ev = (55/108)*m.log(52.8 + 8.71 * 55) + (53/108)*m.log(52.8 + 8.71 * 53)
	I_MeV = I_ev*1e-6
	print(I_MeV)
	if not mks:
		return I_MeV
	else:
		return I_MeV * MeV_to_J
	#return 553.1e-6

def gammaToBeta(y):
	return m.sqrt( 1-(1/(y**2)) )
	
def betaToGamma(b):
	return 1/m.sqrt(1-b**2)

# =============================================================================
# def betaFromE(E, m):
# 	y = E/m + 1
# 	return gammaToBeta(y)
# =============================================================================
	
def EfromBeta(B, m):
	E = (betaToGamma(B)-1)*m
	return E

def betaFromE(E, z):
	if z == 0:
		y = E/(m_e_ev)+1
	else:
		y = E/(z*m_p_ev)+1
	B = gammaToBeta(y)
	print('Got '+str(B)+' for beta.')
	return B	
		

def heavyBethe(E, z, n, I):
	B = betaFromE(E, z, mks=True)
	B2 = B**2
	
	prefactor = (4 * np.pi * k0_mks**2 * e_mks**4 * z**2 * n) / (m_e_mks * c_mks**2 * B2)
	lnConst = m.log(2 * m_e_mks * c_mks**2)
	betaTerm = m.log(B2/(1-B2)) - B2
	lnI = -m.log(I)
	
	dE_dX = prefactor*(lnConst + betaTerm + lnI)
	
	return dE_dX*J_to_MeV
	


def ionBethe(E, I, n, z): #This uses eV and cm.
	B = betaFromE(E, z)
	
	prefixConstant = ( 4 * np.pi * k0_ev**2 * e_ev**4 ) / ( m_e_ev ) # GOOD
	prefixVariable = ( z**2 * n ) / (B**2)
	prefix = prefixConstant * prefixVariable
	
	suffixConstant = 2 * m_e_ev
	f_B = m.log( (suffixConstant * B**2)/(1-B**2) ) - B**2
	logI = m.log(I)
	suffix = f_B - logI


	dE_dX = prefix*suffix

	return dE_dX

def electronBethe(E, I, n, z):
	
	B = betaFromE(E, z)
	
	prefixConstant = ( 4 * np.pi * k0_ev**2 * e_ev**4 ) / ( m_e_ev )
	prefixVariable = ( n ) / (B**2)
	prefix = prefixConstant * prefixVariable
	
	suffix1 = m.log( (m_e_ev * B**2 * E) / (2*I**2 * (1 - B**2)) )
	suffix2 = m.log(2) * (2*m.sqrt(1-B**2) - 1 + B**2)
	suffix3 = 1 - B**2
	suffix4 = (1/8) * (1 - m.sqrt(1-B**2))**2
	suffix = suffix1 - suffix2 + suffix3 + suffix4
	
	dE_dX = prefix*suffix
		
	return dE_dX

def ionBethe2(E, I, n, z):
	B = betaFromE(E, z)
	
	const1 = 5.08*10**(-31)
	const2 = 1.02*10**6
	
	prefactorNum = ( const1 * z**2 * n )
	prefix = prefactorNum / B**2
	lnTerm = m.log((const2* B**2)/(1 - B**2)) - B**2
	lnI = m.log(I)
	suffix = lnTerm - lnI
	
	dE_dX = prefix * suffix
	
	print('prefactorNum: '+str(prefactorNum))
	print('prefix: '+str(prefix))	
	print('F(B): '+str(lnTerm))
	print('ln(I): '+str(lnI))
	
	print('B: '+str(B))
	print('B^2: '+str(B**2))
	print('const1 '+str(const1))
	print('const2 '+str(const2))
	print('I: '+str(I))
	
	
	return dE_dX	

if __name__ == "__main__":
	T_electron = 1 #MeV
	z_electron = 0
	
	T_ion = 200 #MeV
	z_ion = 1
	KE_now = T_ion
	
	
	
	
	
	
	
	dE_dXs = np.array([])
	
	x_0 = 0.00 #cm
	x_f = 30 #cm
	dx = 0.01 #cm
	
	depth = np.arange(x_0, x_f, dx)
	
	for x in depth:
		if KE_now > 0:
			this_dE_dX = ionBethe2(KE_now, 74.6, 3.34e29, 1)
			dE_dXs = np.append(dE_dXs, this_dE_dX)
			E_loss = this_dE_dX * dx
			KE_now = KE_now - E_loss
		
	fig = plt.figure()
	ax = fig.add_subplot(111) 
	ax.plot(depth[0:len(dE_dXs)], dE_dXs)
	ax.set_xscale('log')
	ax.set_yscale('log')
	plt.show()





# =============================================================================
# #stoppingPower_ion = ionBethe(T_ion, 74.6*10**(-6), 3.34*10**23, 1)
# 
# ionStop = ionBethe(T_ion, getI(), n_CsI, z_ion)
# ionStop2 = heavyBethe(T_ion*MeV_to_J, getI(True), n_CsI, z_ion)
# electronStop = electronBethe(T_electron, getI(), n_CsI, z_electron)
# 
# print('++++++++++++++++++++')
# print('dE/dX for ion with z=' + str(z_ion) + ': '+str(ionStop) )
# print('dE/dX for ion with z=' + str(z_ion) + ': '+str(ionStop2) )
# print('dE/dX for electron ' + str(z_electron) + ': '+str(electronStop) )
# print('++++++++++++++++++++')
# 
# 
# 
# KE_ion = [T_ion]
# dE_dXs = []
# x_0 = 0.00 #cm
# x_f = 10 #cm
# dx = 0.0001 #cm
# 
# depth = np.arange(x_0, x_f, dx)
# E_start = T_ion
# 
# for x in depth:
# 	if T_ion > 0:
# 		this_dE_dX = ionBethe(T_ion, getI(), n_CsI, z_ion)
# 		dE_dXs.append(this_dE_dX)
# 		E_loss = this_dE_dX*dx
# 		T_ion = T_ion - E_loss
# 		KE_ion.append(T_ion)
# 		#print(this_dE_dX)
# 
# #print(KE_ion[-1]-E_start)
# if len(dE_dXs) > len(depth):
# 	dE_dXs = dE_dXs[:-1]
# plt.plot(depth[0:len(dE_dXs)], dE_dXs)
# 
# # =============================================================================
# # if len(KE_ion) > len(depth):
# # 	KE_ion = KE_ion[:-1]
# # plt.plot(depth[0:len(KE_ion)], KE_ion[0:len(KE_ion)])
# # =============================================================================
# 
# plt.show()
# 
# 
# #for i in points:
# #	ratios.append(ionBethe(i, I_CsI, n_CsI, A_CsI, 1))
# 
# #plt.plot(ratios)
# #plt.show()
# =============================================================================
