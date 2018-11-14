#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 13 14:18:42 2018

@author: zdhughes
"""

import eqn2
import equations
import numpy as np
import matplotlib.pyplot as plt


z_ion = 1
A_ion = 1
KE_ion = 1000

x_0 = 0.00 #cm
x_f = 5 #cm
dx = 0.0001 #cm

rE_0 = 0.01 #MeV
rE_f = 100000 #MeV
dE = 0.01 #MeV

E_0 = -1 #MeV
E_f = 6 #MeV
NE = 10000

depth = np.arange(x_0, x_f, dx)
ERange = np.logspace(E_0, E_f, NE)

dE_dXs_water = np.array([])
dE_dXs_CsI = np.array([])

KEs_CsI = np.array([KE_ion])

for E in ERange:
	this_dE_dX_water = eqn2.bethBlochIon(eqn2.p_water, eqn2.Z_water, eqn2.A_water, z_ion, E, A_ion*eqn2.m_p, eqn2.I_water)
	this_dE_dX_CsI = eqn2.bethBlochIon(eqn2.p_CsI, eqn2.Z_CsI, eqn2.A_CsI, z_ion, E, A_ion*eqn2.m_p, eqn2.I_CsI)
	
	dE_dXs_water = np.append(dE_dXs_water, this_dE_dX_water)
	dE_dXs_CsI = np.append(dE_dXs_CsI, this_dE_dX_CsI)
	
for x in depth:
	if KEs_CsI[-1] > 0.1:
		this_dE_dX = eqn2.bethBlochIon(eqn2.p_CsI, eqn2.Z_CsI, eqn2.A_CsI, z_ion, KEs_CsI[-1], A_ion*eqn2.m_p, eqn2.I_CsI)
		E_now = KEs_CsI[-1] - this_dE_dX*dx
		KEs_CsI = np.append(KEs_CsI, E_now)
	

if len(KEs_CsI) > len(depth):
	KEs_CsI = KEs_CsI[:-1]
	
fig = plt.figure()
ax = fig.add_subplot(111) 
ax.plot(ERange[0:len(dE_dXs_CsI)], dE_dXs_water/eqn2.p_water, color='black', label='Water')
ax.plot(ERange[0:len(dE_dXs_CsI)], dE_dXs_CsI/eqn2.p_CsI, color='black', linestyle='-.', label='CsI')
ax.set_xscale('log')
ax.set_yscale('log')
ax.legend()
ax.set_ylabel(r"$\frac{dE}{dx}\rho^{-1}\ [MeV\ cm^{2} g^{-1}]$")
ax.set_xlabel(r'$E\ [MeV]$')
plt.grid(True,linestyle="--")
plt.show()


ion_labels = ['H', 'C', 'Si', 'Ge', 'Sn', 'Pb']
z_ion = [1, 6, 14, 32, 50, 82]
A_ion = [1, 12, 28, 72, 118, 207]
KE_ion = [100, 200, 300, 400]


for i, ion in enumerate(ion_labels):
	fig = plt.figure()
	ax = fig.add_subplot(111)
	#ax.set_xlim([0,1])
	ax.set_ylabel(r"$Energy\ [MeV]$")
	ax.set_xlabel(r'$Depth\ [cm]$')
	#ax.set_xscale('log')
	ax.set_yscale('log')
	plt.grid(True,linestyle="--")
	for E in KE_ion:
		KEs_CsI = np.array([E])
		for x in depth:
			if KEs_CsI[-1] > 2:
				this_dE_dX = eqn2.bethBlochIon(eqn2.p_CsI, eqn2.Z_CsI, eqn2.A_CsI, z_ion[i], KEs_CsI[-1], A_ion[i]*eqn2.m_p, eqn2.I_CsI)
				E_now = KEs_CsI[-1] - this_dE_dX*dx
				KEs_CsI = np.append(KEs_CsI, E_now)
		if len(KEs_CsI) > len(depth):
			KEs_CsI = KEs_CsI[:-1]
		ax.plot(depth[0:len(KEs_CsI)], KEs_CsI, color='black', linestyle='-.', label=ion)
	

	ax.legend()
	plt.show()






#fig = plt.figure()
#ax = fig.add_subplot(111) 
#ax.plot(depth[0:len(KEs_CsI)], KEs_CsI, color='black', linestyle='-.', label='CsI')
#ax.set_xscale('log')
#ax.set_yscale('log')
#ax.set_xlim([0,5])
#ax.legend()
#ax.set_ylabel(r"$Energy\ [MeV]$")
#ax.set_xlabel(r'$Depth\ [cm]$')
#plt.grid(True,linestyle="--")
#plt.show()
	


