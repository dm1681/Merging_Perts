import os
import numpy as np
import shelve
from astropy import units as u
from astropy import constants as const

ss = shelve.open('bss') # 'ss' stands for sim status
rootdir = "/gscratch/vsm/dm1681/runs"

t = 25000 #number of sims

uncomp = np.array([])
comp = np.array([])

co_b_semi_list = np.array([])
un_b_semi_list = np.array([])

co_b_ecc_list = np.array([])
un_b_ecc_list = np.array([])

co_b_inc_list = np.array([])
un_b_inc_list = np.array([])

co_c_inc_list = np.array([])
un_c_inc_list = np.array([])

co_b_longa_list = np.array([])
un_b_longa_list = np.array([])

co_c_longa_list = np.array([])
un_c_longa_list = np.array([])
	
#how to identify Runtime in system.log file:
n = 0
while n <= t-1:
	name_idx = '%05i'%n
	folder_name = name_idx
	wd = rootdir+'/'+folder_name+'/'
	
	b_in = wd+'b.in'
	b_file = open(b_in)
	b_content = b_file.read()
	b_content = b_content.split('\n')
	
	c_in = wd+'c.in'
	c_file = open(c_in)
	c_content = c_file.read()
	c_content = c_content.split('\n')
	
	log = wd+'system.log'
	log_file = open(log)
	log_content = log_file.read()
	log_content = log_content.split('\n') #separates by line
	runtime = log_content[-2] #takes the line corresponding to "Runtime"
	
	
	if runtime[0:7] == 'Runtime':
		comp = np.append(comp,folder_name)
		
		co_b_semi = b_content[10]
		co_b_semi = co_b_semi.split('\t')
		co_b_semi = co_b_semi[1]
		co_b_semi = float(co_b_semi)
		co_b_semi_list = np.append(co_b_semi_list, co_b_semi)
		
		co_b_ecc = b_content[9]
		co_b_ecc = co_b_ecc.split('\t')
		co_b_ecc = co_b_ecc[1]
		co_b_ecc = float(co_b_ecc)
		co_b_ecc_list = np.append(co_b_ecc_list, co_b_ecc)
		
		co_b_inc = b_content[12]
		co_b_inc = co_b_inc.split('\t')
		co_b_inc = co_b_inc[1]
		co_b_inc = float(co_b_inc)
		co_b_inc_list = np.append(co_b_inc_list, co_b_inc)
		
		co_c_inc = c_content[12]
		co_c_inc = co_c_inc.split('\t')
		co_c_inc = co_c_inc[1]
		co_c_inc = float(co_c_inc)
		co_c_inc_list = np.append(co_c_inc_list, co_c_inc)
		
		co_b_longa = b_content[13]
		co_b_longa = co_b_longa.split('\t')
		co_b_longa = co_b_longa[1]
		co_b_longa = float(co_b_longa)
		co_b_longa_list = np.append(co_b_longa_list, co_b_longa)
		
		co_c_longa = c_content[12]
		co_c_longa = co_c_longa.split('\t')
		co_c_longa = co_c_longa[1]
		co_c_longa = float(co_c_longa)
		co_c_longa_list = np.append(co_c_longa_list, co_c_longa)

	else:
		uncomp = np.append(uncomp,folder_name)
		
		un_b_semi = b_content[10]
		un_b_semi = un_b_semi.split('\t')
		un_b_semi = un_b_semi[1]
		un_b_semi = float(un_b_semi)
		un_b_semi_list = np.append(un_b_semi_list, un_b_semi)
		
		un_b_ecc = b_content[9]
		un_b_ecc = un_b_ecc.split('\t')
		un_b_ecc = un_b_ecc[1]
		un_b_ecc = float(un_b_ecc)
		un_b_ecc_list = np.append(un_b_ecc_list, un_b_ecc)
		
		un_b_inc = b_content[12]
		un_b_inc = un_b_inc.split('\t')
		un_b_inc = un_b_inc[1]
		un_b_inc = float(un_b_inc)
		un_b_inc_list = np.append(un_b_inc_list, un_b_inc)
		
		un_c_inc = c_content[12]
		un_c_inc = un_c_inc.split('\t')
		un_c_inc = un_c_inc[1]
		un_c_inc = float(un_c_inc)
		un_c_inc_list = np.append(un_c_inc_list, un_c_inc)
		
		un_b_longa = b_content[13]
		un_b_longa = un_b_longa.split('\t')
		un_b_longa = un_b_longa[1]
		un_b_longa = float(un_b_longa)
		un_b_longa_list = np.append(un_b_longa_list, un_b_longa)
		
		un_c_longa = c_content[12]
		un_c_longa = un_c_longa.split('\t')
		un_c_longa = un_c_longa[1]
		un_c_longa = float(un_c_longa)
		un_c_longa_list = np.append(un_c_longa_list, un_c_longa)


		#print ('Not Completed')
	
	n +=1

#comp first

dInc_b = co_b_inc_list
dInc_c = co_c_inc_list
dLongA_b = co_b_longa_list
dLongA_c = co_c_longa_list

dInc_b_deg = dInc_b * u.deg
dInc_b_rad = dInc_b_deg.to(u.rad)
dInc_c_deg = dInc_c * u.deg
dInc_c_rad = dInc_c_deg.to(u.rad)
dLongA_b_deg = dLongA_b * u.deg
dLongA_b_rad = dLongA_b_deg.to(u.rad)
dLongA_c_deg = dLongA_c * u.deg
dLongA_c_rad = dLongA_c_deg.to(u.rad)

mut_incl = np.arccos(np.cos(dInc_b_rad)*np.cos(dInc_c_rad)+
                     np.sin(dInc_b_rad)*np.sin(dInc_c_rad)*np.cos(dLongA_c_rad - dLongA_b_rad))
    
co_mut_incl = mut_incl

#uncomp last

dInc_b = un_b_inc_list
dInc_c = un_c_inc_list
dLongA_b = un_b_longa_list
dLongA_c = un_c_longa_list

dInc_b_deg = dInc_b * u.deg
dInc_b_rad = dInc_b_deg.to(u.rad)
dInc_c_deg = dInc_c * u.deg
dInc_c_rad = dInc_c_deg.to(u.rad)
dLongA_b_deg = dLongA_b * u.deg
dLongA_b_rad = dLongA_b_deg.to(u.rad)
dLongA_c_deg = dLongA_c * u.deg
dLongA_c_rad = dLongA_c_deg.to(u.rad)

mut_incl = np.arccos(np.cos(dInc_b_rad)*np.cos(dInc_c_rad)+
                     np.sin(dInc_b_rad)*np.sin(dInc_c_rad)*np.cos(dLongA_c_rad - dLongA_b_rad))
  

un_mut_incl = mut_incl


ss['uncomp'] = uncomp
ss['comp'] = comp

ss['co_b_semi'] = co_b_semi_list
ss['un_b_semi']=un_b_semi_list 

ss['co_b_ecc']=co_b_ecc_list 
ss['un_b_ecc']=un_b_ecc_list 

ss['co_b_inc']=co_b_inc_list 
ss['un_b_inc']=un_b_inc_list

ss['co_c_inc']=co_c_inc_list 
ss['un_c_inc']=un_c_inc_list 

ss['co_b_longa']=co_b_longa_list
ss['un_b_longa']=un_b_longa_list

ss['co_c_longa']=co_c_longa_list 
ss['un_c_longa']=un_c_longa_list

ss['co_mut_inc'] = co_mut_incl
ss['un_mut_inc'] = un_mut_incl

print (np.argmax(co_mut_incl))
