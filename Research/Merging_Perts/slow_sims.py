#imports
import numpy as np
import shelve
from astropy.table import QTable
import matplotlib.pyplot as plt
from astropy import units as u
from astropy import constants as const
import os
import math
import shutil
from IPython.core.debugger import Tracer
import subprocess
import re
#%matplotlib inline

stable_ICs = shelve.open('stable_ICs')
ecc_b = stable_ICs['ecc_b']
ecc_c = stable_ICs['ecc_c']
semi_b = stable_ICs['semi_b']
semi_c = stable_ICs['semi_c']
dInc_b = stable_ICs['dInc_b']
dInc_c = stable_ICs['dInc_c']
dLongA_b = stable_ICs['dLongA_b']
dLongA_c = stable_ICs['dLongA_c']
dArgP_b = stable_ICs['dArgP_b']
dArgP_c = stable_ICs['dArgP_c']
mean_an_b = stable_ICs['mean_an_b']
mean_an_c = stable_ICs['mean_an_c']
good_hill = stable_ICs['good_hill']
bad_hill = stable_ICs['bad_hill']
dPrecA_b = stable_ICs['dPrecA_b']
dMass_star = stable_ICs['dMass_star']
dRadius_star = stable_ICs['dRadius_star']
dMass_b = stable_ICs['dMass_b']
dMass_c = stable_ICs['dMass_c']
dRadius_b = stable_ICs['dRadius_b']
dRadius_c = stable_ICs['dRadius_c']
dTidalQ_b = stable_ICs['dTidalQ_b']
dTidalQ_c = stable_ICs['dTidalQ_c']
dTidalQ_star = stable_ICs['dTidalQ_star']
dStopTime = stable_ICs['dStopTime']
stable_ICs.close()

#opening completed list
comp = open('compd.txt','r')
comp_list = np.array([])

sim_list = np.array([])
mut_incl_list = np.array([])
b_semi_list = np.array([])
c_semi_list = np.array([])


for line in comp.readlines():
	line = line.split('/')
	sim_num = line[-1]
	sim_num = sim_num.rsplit('\n')
	sim_num = sim_num[0]
	comp_list = np.append(comp_list,sim_num)	

for num in comp_list:
	sh_file = open('./sh/'+num,'r')
	sh_cont = sh_file.read()
	sh_cont = sh_cont.split()
	sim = sh_cont[2]
	sim = sim.split('/')
	sim = sim[-1]
	sim_list = np.append(sim_list,sim)

for n in sim_list:
	n = int(n)
	dInc_b_deg = dInc_b[n] * u.deg
	dInc_b_rad = dInc_b_deg.to(u.rad)
	dInc_c_deg = dInc_c[n] * u.deg
	dInc_c_rad = dInc_c_deg.to(u.rad)
	dLongA_b_deg = dLongA_b[n] * u.deg
	dLongA_b_rad = dLongA_b_deg.to(u.rad)
	dLongA_c_deg = dLongA_c[n] * u.deg
	dLongA_c_rad = dLongA_c_deg.to(u.rad)
	mut_incl = np.arccos(np.cos(dInc_b_rad)*np.cos(dInc_c_rad)+
						 np.sin(dInc_b_rad)*np.sin(dInc_c_rad)*np.cos(dLongA_c_rad-
						 dLongA_b_rad))
	mut_incl_list = np.append(mut_incl_list,mut_incl)
	b_semi_list = np.append(b_semi_list,semi_b[n])
	c_semi_list = np.append(c_semi_list,semi_c[n])
	
	
	

	

all_data = np.vstack((sim_list,mut_incl_list,b_semi_list,c_semi_list))
all_data = np.transpose(all_data)

x = np.arange(all_data.shape[0])
y = all_data[:,1:2]
#y = float(y)

fig,ax = plt.subplots(1,1)
ax.plot(x,y)
plt.show()	

print (all_data,all_data.shape)
#print (comp_list.shape,comp_list)

'''
make list of what didnt run
system.log with no time,
run on desktop, with deltaT in output 

compare slow sims with fast running sim 
look at high e, low a of b, mutual incl. 

eqtide only:
pick age b/w 2gy and 8gyrs (verify), get ecc, orbital, plot avg ecc for each bin of orbit per
'''
