'''
Diego McDonald - University of Washington
dm1681@uw.edu or dm1681@gmail.com

Written for Python3.6

execute using "python generate.py n", 
defaults to n = 25000 if n not specified

The purpose of this script is to generate "n" initial conditions
for the eqtide, distorb, and atmesc models in vplanet. 

eqtide - how tides influence orbits
distorb - planet-planet interactions
atmesc - atmospheric escape due to XUV flux

coupling all of these modules should provide two pieces of information:
1) how adding a perturbing planet can influence the orbit of the inner planet
	(i.e., does it cause the inner to merge with its host star?)
2) the critical radius between rocky and gaseous planets (mostly using atmesc)

todo:
-----
- generate input files
--- generate input files for loaded IC files

'''

# imports

from astropy.table import QTable
import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
import astropy.constants as const
import os
import shutil
import subprocess
import datetime
import sys
import pdb


# just making sure they know I'm downloading files to their machine
verif_string =  'The purpose of this script is to generate "n" initial conditions\n'
verif_string += 'for use in McDonald(2017). It will download any missing data files\n'
verif_string += 'to your current working directory automatically.\n' 
verif_string += 'Proceed? [y/n] '
verification = input(verif_string)
if verification == 'n':
	sys.exit()

### some helper functions and overhead ###

# lets add a check in IC_figs for IC_table.csv so that we don't have to generate new ICs every time
def check_prev_ICs():
	'''
	This function checks the current directory of previous files
	starting with 'ICs_', a prefix in how the generated ICs are saved
	to file. 
	'''

	try:
		dirlist = os.listdir('./')
		ic_files = {}
		i = 0
		for item in dirlist:
			if item[:4] == "ICs_":
				ic_files[i] = item
				print('Found file: %s [%i]'%(item,i))
				i+=1

		if len(ic_files.keys()) > 0:
			bLoad = input("Load found file?: [idx] ")
		elif len(ic_files) == 0:
			print ('No previous IC_files found in current directory.\nGenerating new ICs')
			bLoad = False
			ICs = -99999
		if ((bLoad != 'n') & (len(ic_files.keys())>0)):
			for key in ic_files:
				if (int(key) == int(bLoad)):
					bLoad = True
					ICs = QTable.read('./'+ic_files[key],format='ascii.csv')
					return ICs, bLoad
		else:
			bLoad = False
			ICs = -99999
			return ICs, bLoad
			print('Generating new ICs')
	except FileNotFoundError:
		print ('ICs_ file not found!')
		bLoad = False
		ICs = -99999
		return ICs, bLoad

IC, bLoad = check_prev_ICs()

def plot_ecc_dist(ecc_b, ecc_c, prob_ecc_data):

	fig, ax = plt.subplots(1,1)
	fig.set_size_inches(11,8.5)

	binwidth = 0.05
	x = np.arange(0,1,binwidth)
	y = prob_ecc_data['cum%']

	ax.set(xlabel='Eccentricity', ylabel='P(Eccentricity)')

	ax.bar(prob_ecc_data['ecc']+0.025,prob_ecc_data['%inbin'],width=binwidth,
		   color='r',label='Source')
	

	ecc_hist_b = ax.hist(ecc_b, 
						 bins=x, 
						 weights=np.zeros_like(ecc_b)+1./ecc_b.size, 
						 histtype='step', color='blue', label='b')
	ecc_hist_c = ax.hist(ecc_c, 
						 bins=x, 
						 weights=np.zeros_like(ecc_c)+1./ecc_c.size, 
						 histtype='step', color='green', label='c')
	ax.legend(loc=0)



	fig.savefig('./IC_figs/ecc_dist.png')
	print ('Ecc Distribution Figure saved in IC_figs')

def plot_rad_dist(rad_b, rad_c, ref_rad_data):
	fig,ax = plt.subplots(1,1)
	fig.set_size_inches(11,8.5)

	x = np.arange(0,4,0.25)
	rad_dist = ax.hist(ref_rad_data, bins=x, 
					   weights=np.zeros_like(rad_data)+1./rad_data.size, 
					   color='red', label='source')
	y = rad_dist[0].cumsum()	

	rad_b_hist = ax.hist(rad_b, bins=x,
						 weights = np.zeros_like(rad_b)+1/rad_b.size,
						 histtype='step', color='blue', label='b')

	rad_c_hist = ax.hist(rad_c, bins=x,
						 weights = np.zeros_like(rad_c)+1/rad_c.size,
						 histtype='step', color='green', label='c')
	ax.set(xlabel='Radius(EarthRads)')
	ax.legend(loc=0)

	fig.savefig('./IC_figs/rad_dist.png')
	print ('Radius Distribution saved in IC_figs')

def plot_b_c_mass_rad(mass_b, rad_b, mass_c, rad_c,):
	#graphs of b.in parameters        
	fig,ax = plt.subplots(2,2)
	fig.set_size_inches(11,8.5)
	ran = max(mass_b)-min(mass_b)
	x = np.arange(0,4,0.25)

	ax[0,0].hist(mass_b, bins=18, weights=np.zeros_like(mass_b)+1./mass_b.size) # 18 bins --> binwidth ~10 earthMass
	ax[0,1].hist(rad_b, bins=x, weights=np.zeros_like(rad_b)+1./rad_b.size)

	ax[0,0].set_xlabel('Mass_b (EarthMass)')
	ax[0,1].set_xlabel('Radius_b (EarthRad)')

	# distributions for c.in of mass, Radius. 
	ran = max(mass_c)-min(mass_c)
	ax[1,0].hist(mass_c, bins=18, weights=np.zeros_like(mass_c)+1./mass_c.size, color = 'green') # 18 bins --> binwidth ~10 earthMass
	ax[1,1].hist(rad_c, bins = x, weights=np.zeros_like(rad_c)+1./rad_c.size, color = 'green') 


	ax[1,0].set_xlabel('Mass_c (EarthMass)')
	ax[1,1].set_xlabel('Radius_c (EarthRad)')

	fig.savefig('IC_figs/mass_rad_dist.png')
	print ('Mass and Radius Distribution Figures saved in IC_figs')

def get_probecc_data():
	dirlist = os.listdir('./')
	found = False
	for item in dirlist:
		if item == 'probecc_comma.dat':
			found = True
			return found
	if found == False:
		print('Unable to find probecc_comma.dat in current directory.\n'
			  'Downloading via wget')
		subprocess.call('wget https://raw.githubusercontent.com/dm1681/Merging_Perts/master/Research/Merging_Perts/probecc_comma.dat',
				shell=True, cwd='./')
		found = True
		return found

def get_planetrad_data():
	dirlist = os.listdir('./')
	found = False
	for item in dirlist:
		if item == 'planets.csv':
			found = True
			return found
	if found == False:
		print('Unable to find planets.csv in current directory.\n'
			  'Downloading via wget')
		subprocess.call('wget https://raw.githubusercontent.com/dm1681/Merging_Perts/master/Research/Merging_Perts/planets.csv',
				shell=True, cwd='./')
		found = True
		return found

def gen_eqtide(runs_dir_eqonly, n):
    global mass_b, rad_b, semi_b, ecc_b, incl_b, longasci_b, argperi_b, Qp_b, mass_star, rad_star, Qstar
    runs_dir = runs_dir_eqonly

    # b.in
    name_b = 'b'
    modules_b = 'eqtide'
    sTideModel_b = 'p2'
    dMass_b = mass_b * -1# sets to earth masses;
    dRadius_b = rad_b * -1 # sets to earth radii
    dSemi_b = semi_b #semi_b defined above
    dEcc_b = ecc_b #ecc_b defined above
    bForceEqSpin_b = 1
    #dRotPeriod = -1 
    dObliquity_b = 45 
    dRadGyra_b = 0.5
    bInvPlane = 1 #distorb
    dInc_b = incl_b #distorb
    dLongA_b = longasc_b #distorb
    dArgP_b = argperi_b #distorb
    sOrbitModel_b = 'rd4' #distorb
    bOutputLapl_b = 0 #distorb
    #dPrecA_b = dPrecA_b #distrot
    #bCalcDynEllip_b = 1 #distrot
    dTidalQ_b = Qp_b 
    dK2_b = 0.3
    #dMaxLockDiff = 0.1 
    saTidePerts_b = 'star'
    saOutputOrder_b = 'Time Semim Ecce Obliquity SurfEnFluxEqtide' #precA only for distrot, Incl and LongA for Distorb

    #star.in
    name_star = 'star'
    modules_star = 'eqtide'
    dMass_star = mass_star #solar masses;
    dRadius_star = rad_star # * ratio of solar radii to au
    dObliquity_star = 0  
    bForceEqSpin_star = 1
    dRotPeriod_star = -30 
    dRadGyra_star = 0.5 
    dTidalQ_star = Qstar
    dK2_star = 0.3 
    saTidePerts_star = 'b'
    saOutputOrder_s = 'Time'

    #vpl.in
    Sys_name = 'system'
    iVerbose = 5
    bOverwrite = 1
    saBodyFiles = 'star.in b.in'  #c.in for distorb
    UnitMass = 'solar' 
    UnitLength = 'aU'  
    UnitTime = 'YEARS'
    UnitAngle = 'd'
    UnitTemp = 'K'
    bDoLog = 1
    iDigits = 6
    dMinValue = 10**(-10)
    bDoForward = 1
    bVarDt = 1
    dEta = 0.01
    dStopTime = 10**10
    dOutputTime = 10**9
    
    i = 0
    while i <= n-1: # will make n <= x amount of folders; (25000);
        # make strings of values; b.in
        name_idx = '%05i'%i

        if os.path.isdir(runs_dir+name_idx) == True: #sim folders exist
            shutil.rmtree(runs_dir) #removes previous folders; THIS LINE DELETES THE ENTIRE RUNS DIRECTORY
            os.makedirs(runs_dir+name_idx)
        else: #sims folder does not exist
            os.makedirs(runs_dir+name_idx)

        mass_str_b = str(dMass_b[i]) 
        radius_str_b = str(dRadius_b[i])
        eqspin_str_b = str(bForceEqSpin_b)
        obl_str_b = str(dObliquity_b)
        radgy_str_b = str(dRadGyra_b)
        ecc_str_b = str(dEcc_b[i])
        semi_str_b = str(dSemi_b[i])
        dInc_str_b = str(dInc_b[i]) # new
        dLongA_str_b = str(dLongA_b[i]) # new
        dArgP_str_b = str(dArgP_b[i]) # new
        bOutputLapl_str_b = str(bOutputLapl_b) # new
        #dPrecA_str_b = str(dPrecA_b[n]) # distrot
        #bCalcDynEllip_str_b = str(bCalcDynEllip_b) #distrot
        q_str_b = str(dTidalQ_b[i])
        dK2_str_b = str(dK2_b)
        InvPlane_str = str(bInvPlane)
        perts_str_b = str(saTidePerts_b)
        outorder_str_b = str(saOutputOrder_b)

        #star.in
        name_star = name_star
        modules_star = modules_star
        strMass_str = str(dMass_star[i])
        strRad_str = str(dRadius_star[i])
        strObl_str = str(dObliquity_star)
        #strEqSpin_str = str(bForceEqSpin_star)
        strRotPer_str = str(dRotPeriod_star)
        strRadGyr_str = str(dRadGyra_star)
        strTidalQ_str = str(dTidalQ_star[i])
        strdK2_str = str(dK2_star)
        saTidePerts_star = saTidePerts_star
        strsaOutputOrder = saOutputOrder_s

        #vpl.in
        sys_name = Sys_name
        iVerbose_str = str(iVerbose)
        bOverwrite_str = str(bOverwrite)
        saBodyFiles = saBodyFiles
        UnitMass = UnitMass
        UnitLength = UnitLength
        UnitTime = UnitTime
        UnitAngle = UnitAngle
        UnitTemp = UnitTemp
        bDoLog_str = str(bDoLog)
        iDigits_str = str(iDigits)
        dMinValue_str = str(dMinValue)
        bDoForward_str = str(bDoForward)
        bVarDt_str = str(bVarDt)
        dEta_str = str(dEta)
        dStopTime_str = str(int(dStopTime))
        dOutputTime_str = str(dOutputTime)


        b = open(runs_dir+name_idx+'/b.in','w')
        b_content = ('sName\t\t'+ name_b + 
                     '\nsaModules\t'+modules_b+
                     '\nsTideModel\t'+sTideModel_b+
                     '\n\ndMass\t\t'+mass_str_b+
                     '\ndRadius\t\t'+radius_str_b+
                     '\ndObliquity\t'+obl_str_b+
                     '\ndRadGyra\t'+radgy_str_b+
                     '\n\ndEcc\t\t'+ecc_str_b+
                     '\ndSemi\t\t'+semi_str_b+
                     '\n\ndInc\t\t'+dInc_str_b+
                     '\ndLongA\t\t'+dLongA_str_b+
                     '\ndArgP\t\t'+dArgP_str_b+
                     #'\nsOrbitModel\t'+sOrbitModel_b+  #for Distorb
                     #'\nbOutputLapl\t'+bOutputLapl_str_b+ #for Distorb
                     #'\n\ndPrecA\t'+dPrecA_str_b+     #distrot? 
                     #'\nbCalcDynEllip\t'+bCalcDynEllip_str_b+ #distrot?
                     '\n\nbForceEqSpin\t'+eqspin_str_b+
                     '\ndTidalQ\t\t'+q_str_b+
                     '\ndK2\t\t'+dK2_str_b+
                     '\nsaTidePerts\t'+perts_str_b+
                     #'\n\nbInvPlane\t'+InvPlane_str+ #for Distorb
                     '\n\nsaOutputOrder\t'+outorder_str_b+'\n')
        b.write(b_content)
        b.close()
        
        star = open(runs_dir+name_idx+'/star.in','w')
        star_content = ('sName\t\t'+name_star+
                        '\nsaModules\t'+modules_star+
                        '\n\ndMass\t\t'+strMass_str+
                        '\ndRadius\t\t'+strRad_str+
                        '\ndObliquity\t'+strObl_str+
                        '\ndRotPeriod\t'+strRotPer_str+
                        '\ndRadGyra\t'+strRadGyr_str+
                        '\n\ndTidalQ\t\t'+strTidalQ_str+
                        '\ndK2\t\t'+strdK2_str+
                        '\n\nsaTidePerts\t'+saTidePerts_star+
                        '\n\nsaOutputOrder\t'+strsaOutputOrder+'\n')
        star.write(star_content)
        star.close()

        vpl = open(runs_dir+name_idx+'/vpl.in','w')
        vpl_content = ('sSystemName\t'+sys_name+
                       '\niVerbose\t'+iVerbose_str+
                       '\nbOverwrite\t'+bOverwrite_str+
                       '\n\nsaBodyFiles\t'+saBodyFiles+
                       '\n\nsUnitMass\t'+UnitMass+
                       '\nsUnitLength\t'+UnitLength+
                       '\nsUnitTime\t'+UnitTime+
                       '\nsUnitAngle\t'+UnitAngle+
                       '\nsUnitTemp\t'+UnitTemp+
                       '\n\nbDoLog\t\t'+bDoLog_str+
                       '\niDigits\t\t'+iDigits_str+
                       '\ndMinValue\t'+dMinValue_str+
                       '\n\nbDoForward\t'+bDoForward_str+
                       '\nbVarDt\t\t'+bVarDt_str+
                       '\ndEta\t\t'+dEta_str+
                       '\ndStopTime\t'+dStopTime_str+
                       '\ndOutputTime\t'+ dOutputTime_str+'\n')
        vpl.write(vpl_content)
        vpl.close()

        i += 1
    return 0

def gen_eqorb(runs_dir_eqorb, n):
    global mass_b, rad_b, semi_b, ecc_b, incl_b, longasc_b, argperi_b, Qp_b, mass_c, rad_c, semi_c, ecc_c, incl_c, longasc_c, argperi_c, Qp_c, mass_star, rad_star, Qstar
    runs_dir = runs_dir_eqorb
    
    # b.in
    name_b = 'b'
    modules_b = 'eqtide distorb'
    sTideModel_b = 'p2'
    dMass_b = mass_b * -1# sets to earth masses;
    dRadius_b = rad_b * -1 # sets to earth radii
    dSemi_b = semi_b #semi_b defined above
    dEcc_b = ecc_b #ecc_b defined above
    bForceEqSpin_b = 1
    #dRotPeriod = -1 
    dObliquity_b = 45 
    dRadGyra_b = 0.5
    bInvPlane = 1 #distorb
    dInc_b = incl_b #distorb
    dLongA_b = longasc_b #distorb
    dArgP_b = argperi_b #distorb
    sOrbitModel_b = 'rd4' #distorb
    bOutputLapl_b = 0 #distorb
    #dPrecA_b = dPrecA_b #distrot
    #bCalcDynEllip_b = 1 #distrot
    dTidalQ_b = Qp_b 
    dK2_b = 0.3
    #dMaxLockDiff = 0.1 
    saTidePerts_b = 'star'
    saOutputOrder_b = 'Time Semim Ecce Obliquity SurfEnFluxEqtide LongP Inc LongA' #precA only for distrot, Incl and LongA for Distorb

    # c.in
    name_c = 'c'
    modules_c = 'eqtide distorb'
    sTideModel_c = 'p2'
    dMass_c = mass_c * -1 # sets to earth masses; this isnt working!!
    dRadius_c = rad_c * -1 # sets to earth radii
    dSemi_c = semi_c # semi_c defined above
    dEcc_c = ecc_c # ecc_c defined above
    bForceEqSpin_c = 1
    #dRotPeriod = -1 
    dObliquity_c = 45 
    dRadGyra_c = 0.5
    dInc_c = incl_c
    dLongA_c = longasc_c
    dArgP_c = argperi_c
    sOrbitModel_c = 'rd4'
    bOutputLapl_c = 0
    dTidalQ_c = Qp_c 
    dK2_c = 0.3
    #dMaxLockDiff = 0.1 
    saTidePerts_c = 'star'
    saOutputOrder_c = 'Time Semim Ecce LongP Inc LongA' #change to include Incl and LongA for Distorb runs

    #star.in
    name_star = 'star'
    modules_star = 'eqtide'
    dMass_star = mass_star #solar masses;
    dRadius_star = rad_star # * ratio of solar radii to au
    dObliquity_star = 0  
    bForceEqSpin_star = 1
    dRotPeriod_star = -30 
    dRadGyra_star = 0.5 
    dTidalQ_star = Qstar
    dK2_star = 0.3 
    saTidePerts_star = 'b c'
    saOutputOrder_s = 'Time'

    #vpl.in
    Sys_name = 'system'
    iVerbose = 5
    bOverwrite = 1
    saBodyFiles = 'star.in b.in c.in'  #c.in for distorb
    UnitMass = 'solar' 
    UnitLength = 'aU'  
    UnitTime = 'YEARS'
    UnitAngle = 'd'
    UnitTemp = 'K'
    bDoLog = 1
    iDigits = 6
    dMinValue = 10**(-10)
    bDoForward = 1
    bVarDt = 1
    dEta = 0.01
    dStopTime = 10**10
    dOutputTime = 10**9
    
    i = 0
    while i <= n-1: # will make n <= x amount of folders; (25000);
        # make strings of values; b.in
        name_idx = '%05i'%i

        if os.path.isdir(runs_dir+name_idx) == True: #sim folders exist
            shutil.rmtree(runs_dir) #removes previous folders; THIS LINE DELETES THE ENTIRE RUNS DIRECTORY
            os.makedirs(runs_dir+name_idx)
        else: #sims folder does not exist
            os.makedirs(runs_dir+name_idx)

        mass_str_b = str(dMass_b[i]) 
        radius_str_b = str(dRadius_b[i])
        eqspin_str_b = str(bForceEqSpin_b)
        obl_str_b = str(dObliquity_b)
        radgy_str_b = str(dRadGyra_b)
        ecc_str_b = str(dEcc_b[i])
        semi_str_b = str(dSemi_b[i])
        dInc_str_b = str(dInc_b[i]) # new
        dLongA_str_b = str(dLongA_b[i]) # new
        dArgP_str_b = str(dArgP_b[i]) # new
        bOutputLapl_str_b = str(bOutputLapl_b) # new
        #dPrecA_str_b = str(dPrecA_b[n]) # distrot
        #bCalcDynEllip_str_b = str(bCalcDynEllip_b) #distrot
        q_str_b = str(dTidalQ_b[i])
        dK2_str_b = str(dK2_b)
        InvPlane_str = str(bInvPlane)
        perts_str_b = str(saTidePerts_b)
        outorder_str_b = str(saOutputOrder_b)

        #c.in
        mass_str_c = str(dMass_c[i]) 
        radius_str_c = str(dRadius_c[i])
        eqspin_str_c = str(bForceEqSpin_c)
        obl_str_c = str(dObliquity_c)
        radgy_str_c = str(dRadGyra_c)
        ecc_str_c = str(ecc_c[i])
        semi_str_c = str(semi_c[i])
        dInc_str_c = str(dInc_c[i])
        dLongA_str_c = str(dLongA_c[i])
        dArgP_str_c = str(dArgP_c[i])
        q_str_c = str(dTidalQ_c[i])
        dK2_str_c = str(dK2_c)
        perts_str_c = str(saTidePerts_c)
        outorder_str_c = str(saOutputOrder_c)


        #star.in
        name_star = name_star
        modules_star = modules_star
        strMass_str = str(dMass_star[i])
        strRad_str = str(dRadius_star[i])
        strObl_str = str(dObliquity_star)
        #strEqSpin_str = str(bForceEqSpin_star)
        strRotPer_str = str(dRotPeriod_star)
        strRadGyr_str = str(dRadGyra_star)
        strTidalQ_str = str(dTidalQ_star[i])
        strdK2_str = str(dK2_star)
        saTidePerts_star = saTidePerts_star
        strsaOutputOrder = saOutputOrder_s

        #vpl.in
        sys_name = Sys_name
        iVerbose_str = str(iVerbose)
        bOverwrite_str = str(bOverwrite)
        saBodyFiles = saBodyFiles
        UnitMass = UnitMass
        UnitLength = UnitLength
        UnitTime = UnitTime
        UnitAngle = UnitAngle
        UnitTemp = UnitTemp
        bDoLog_str = str(bDoLog)
        iDigits_str = str(iDigits)
        dMinValue_str = str(dMinValue)
        bDoForward_str = str(bDoForward)
        bVarDt_str = str(bVarDt)
        dEta_str = str(dEta)
        dStopTime_str = str(int(dStopTime))
        dOutputTime_str = str(dOutputTime)


        b = open(runs_dir+name_idx+'/b.in','w')
        b_content = ('sName\t\t'+ name_b + 
                     '\nsaModules\t'+modules_b+
                     '\nsTideModel\t'+sTideModel_b+
                     '\n\ndMass\t\t'+mass_str_b+
                     '\ndRadius\t\t'+radius_str_b+
                     '\ndObliquity\t'+obl_str_b+
                     '\ndRadGyra\t'+radgy_str_b+
                     '\n\ndEcc\t\t'+ecc_str_b+
                     '\ndSemi\t\t'+semi_str_b+
                     '\n\ndInc\t\t'+dInc_str_b+
                     '\ndLongA\t\t'+dLongA_str_b+
                     '\ndArgP\t\t'+dArgP_str_b+
                     '\nsOrbitModel\t'+sOrbitModel_b+  #for Distorb
                     '\nbOutputLapl\t'+bOutputLapl_str_b+ #for Distorb
                     #'\n\ndPrecA\t'+dPrecA_str_b+     #distrot? 
                     #'\nbCalcDynEllip\t'+bCalcDynEllip_str_b+ #distrot?
                     '\n\nbForceEqSpin\t'+eqspin_str_b+
                     '\ndTidalQ\t\t'+q_str_b+
                     '\ndK2\t\t'+dK2_str_b+
                     '\nsaTidePerts\t'+perts_str_b+
                     '\n\nbInvPlane\t'+InvPlane_str+ #for Distorb
                     '\n\nsaOutputOrder\t'+outorder_str_b+'\n')
        b.write(b_content)
        b.close()

        c = open(runs_dir+name_idx+'/c.in','w')
        c_content = ('sName\t\t'+ name_c + 
                     '\nsaModules\t'+modules_c+
                     '\n\n\ndMass\t\t'+mass_str_c+
                     '\ndRadius\t\t'+radius_str_c+
                     '\ndObliquity\t'+obl_str_c+
                     '\ndRadGyra\t'+radgy_str_c+
                     '\n\ndEcc\t\t'+ecc_str_c+
                     '\ndSemi\t\t'+semi_str_c+
                     '\n\ndInc\t\t'+dInc_str_c+
                     '\ndLongA\t\t'+dLongA_str_c+
                     '\ndArgP\t\t'+dArgP_str_c+
                     '\n\nbForceEqSpin\t'+eqspin_str_c+
                     '\ndTidalQ\t\t'+q_str_c+
                     '\ndK2\t\t'+dK2_str_c+
                     '\nsaTidePerts\t'+perts_str_c+
                     '\n\nsaOutputOrder\t'+outorder_str_c+'\n')
        c.write(c_content)
        c.close()

        star = open(runs_dir+name_idx+'/star.in','w')
        star_content = ('sName\t\t'+name_star+
                        '\nsaModules\t'+modules_star+
                        '\n\ndMass\t\t'+strMass_str+
                        '\ndRadius\t\t'+strRad_str+
                        '\ndObliquity\t'+strObl_str+
                        '\ndRotPeriod\t'+strRotPer_str+
                        '\ndRadGyra\t'+strRadGyr_str+
                        '\n\ndTidalQ\t\t'+strTidalQ_str+
                        '\ndK2\t\t'+strdK2_str+
                        '\n\nsaTidePerts\t'+saTidePerts_star+
                        '\n\nsaOutputOrder\t'+strsaOutputOrder+'\n')
        star.write(star_content)
        star.close()

        vpl = open(runs_dir+name_idx+'/vpl.in','w')
        vpl_content = ('sSystemName\t'+sys_name+
                       '\niVerbose\t'+iVerbose_str+
                       '\nbOverwrite\t'+bOverwrite_str+
                       '\n\nsaBodyFiles\t'+saBodyFiles+
                       '\n\nsUnitMass\t'+UnitMass+
                       '\nsUnitLength\t'+UnitLength+
                       '\nsUnitTime\t'+UnitTime+
                       '\nsUnitAngle\t'+UnitAngle+
                       '\nsUnitTemp\t'+UnitTemp+
                       '\n\nbDoLog\t\t'+bDoLog_str+
                       '\niDigits\t\t'+iDigits_str+
                       '\ndMinValue\t'+dMinValue_str+
                       '\n\nbDoForward\t'+bDoForward_str+
                       '\nbVarDt\t\t'+bVarDt_str+
                       '\ndEta\t\t'+dEta_str+
                       '\ndStopTime\t'+dStopTime_str+
                       '\ndOutputTime\t'+ dOutputTime_str+'\n')
        vpl.write(vpl_content)
        vpl.close()

        i += 1

    return 1
def gen_eqorbmesc(runs_dir_eqorbmesc, n):
	print ('Will be coming!!')
	return 2 



### Time to do things ### 

# number of simulations to generate
if len(sys.argv) == 1:
	n = 25000
	print ('Defaulting to n = 25000 simulations')
elif len(sys.argv) > 1:
	n = int(sys.argv[1])
	print ('Generatiing n = %i simulations '%n)

if bLoad == False:

	np.random.seed(42)
	# create directory to store figures:
	if os.path.isdir('./IC_figs'):
		print ('Removing previous IC_figs directory')
		shutil.rmtree('./IC_figs')
		os.makedirs('./IC_figs')
	else:
		os.makedirs('./IC_figs')

	# first we are basing our eccentricity distribution on kepler data? (i think)
	# this is stored in a file named "probecc_comma.dat", if not found, email me
	found_probecc = get_probecc_data()
	found_planetrad = get_planetrad_data()

	if found_probecc == True:
		prob_ecc_data = QTable.read('probecc_comma.dat',format='ascii.no_header', names=['ecc','%inbin','cum%'])
	else:
		print ('ProbEcc data not found! E-mail dm1681@gmail.com for help!')


	# generates a discribution of "n" eccentricities fit observed
	def ecc_gen(n,name):
		print('Generating Ecc Distribution for:',name)
		i = 0
		x = np.arange(0,1,0.05)
		ecc_list = np.array([])
		while i <= n-1:
			r = np.random.sample(1) # some y value (percentage)
			if r <= prob_ecc_data['%inbin'][0]:
				bin_lower = 0.0
				bin_upper = 0.05
			else:
				r_mask = np.where(prob_ecc_data['cum%']<=r)
				x_below = x[r_mask]
				x_below = np.append(x_below,x_below[-1]+0.05)
				bin_upper = x_below[-1] + 0.05
				bin_lower = x_below[-2] + 0.05
			rand = np.random.uniform(0,0.05,1)
			ecc = bin_lower + rand
			ecc_list = np.append(ecc_list, ecc)
			i+=1
			continue
		return ecc_list

	# function to calc mass and tidal Q based on radius
	def calc_mass_Qp(radius,toggle):
		r = radius
		R_crit = 2.0 * u.earthRad
		if r < R_crit:
			mass = ((r/const.R_earth)**(3.68))*const.M_earth
			mass = mass.to(u.earthMass)
			Qplanet = np.random.uniform(30,301)
		else:
			r = r.to(u.cm)
			volume = (4.0 * np.pi * r**3.0) / 3.0
			density = (1 * u.g)/(1 * u.cm)**3
			mass = volume * density
			mass = mass.to(u.earthMass)
			Qplanet = np.random.uniform(10**6, (10**7)+1)
		if toggle == 'm':
			return mass
		elif toggle == 'Q':
			return Qplanet

	# now to generate ecc based on above, b = inner planet, c = outer planet
	name_inner = 'b'
	name_outer = 'c'
	ecc_b = ecc_gen(n, name_inner)
	ecc_c = ecc_gen(n, name_outer)

	plot_ecc_dist(ecc_b, ecc_c, prob_ecc_data)

	# now to generate radii from the kepler radius distrubtion:
	if found_planetrad == True:
		exo_data = QTable.read('planets.csv',format='ascii')
	else:
		print ('ExoPlanet Rad data not found! E-mail dm1681@gmail.com for help.')


	exo_data['pl_radj'] = exo_data['pl_radj'] * (const.R_jup/const.R_earth) #converts from jupiter radii to earth radii
	rad_data = exo_data['pl_radj']

	x = np.arange(0,4,0.25)
	

	fig,ax = plt.subplots(1,1)
	rad_dist = ax.hist(rad_data, bins=x, 
					   weights=np.zeros_like(rad_data)+1./rad_data.size, 
					   color='red', label='source')	
	y = rad_dist[0].cumsum()

	# function similar to the one above(ecc_gen()), except different distribution
	def rad_gen(n,name):
		print ('Generating Rad Distribution for:',name)
		i = 0
		rad_list = np.array([])
		while i <= n-1:
			r = (np.random.sample()) # some y value (percentage)
			if r <= rad_dist[0][0]:
				bin_lower = 0.0
				bin_upper = 0.25
			else:
				r_mask = np.where(y<=r)
				x_below = x[r_mask]
				x_below = np.append(x_below, x_below[-1] + 0.25)
				bin_upper = x_below[-1] + 0.25
				bin_lower = x_below[-2] + 0.25
			rand = np.random.uniform(0,0.25,1)
			rad = bin_lower+rand
			rad_list = np.append(rad_list, rad)
			i+=1
			continue
		return rad_list


	rad_b = rad_gen(n,name_inner)
	rad_c = rad_gen(n,name_outer)

	plot_rad_dist(rad_b, rad_c, rad_data)

	# now to generate other params for b and then c
	# Q, semi, mass

	rad_b = rad_b * u.earthRad
	rad_c = rad_c * u.earthRad

	mass_b = np.array([])
	Qp_b = np.array([])
	semi_b = np.random.uniform(0.01,0.15,n)

	print ('Generating Mass Distribution for: %s'%name_inner)
	print ('Generating Q Distribution for: %s'%name_inner)
	print ('Generating Semi Distribution for: %s'%name_inner)
	for r in rad_b:
		m = calc_mass_Qp(r,'m')
		mass_b = np.append(mass_b,m)
		q = calc_mass_Qp(r,'Q')
		Qp_b = np.append(Qp_b, q)

	mass_c = np.array([])
	Qp_c= np.array([])

	print ('Generating Mass Distribution for: %s'%name_outer)
	print ('Generating Q Distribution for: %s'%name_outer)
	for r in rad_c:
		m = calc_mass_Qp(r,'m')
		mass_c = np.append(mass_c, m)
		q = calc_mass_Qp(r,'Q')
		Qp_c = np.append(Qp_c, q)
	# star.in parameters
	mass_star = np.random.uniform(0.7,1.4,n)
	rad_star = mass_star * 0.0048 # R_sun
	Qstar = np.random.uniform(10**6,10**7,n)
	#print ('Star.in parameters generated')

	# vpl.in 
	Ages = 10e09

	# convert to values to its easier to write to file
	rad_b = rad_b.value
	rad_c = rad_c.value
	mass_b = mass_b.value
	mass_c = mass_c.value

	plot_b_c_mass_rad(mass_b, rad_b, mass_c, rad_c)

	# making semi_c hill stable
	runs_dir = './runs/'

	semi_c = np.copy(semi_b) # start with c at same distance, then move outwards

	# fills the following arrays:
	hill_list = np.array([])
	mean_an_b_list = np.array([])
	mean_an_c_list = np.array([])
	incl_b = np.array([])
	incl_c = np.array([])
	longa_b = np.array([])
	longa_c = np.array([])
	argp_b = np.array([])
	argp_c = np.array([])

	good_hill_list = np.array([])
	bad_hill_list = np.array([])
	bad_count = 0

	i = 0
	print('Making Semi_c hill stable (this may take a while...)')

	# the following loop uses hillstab.c, written by Rory Barnes,
	# available at github.com/RoryBarnes/HillStability, 
	# make sure to compile, and put in your PATH (.bshrc/.cshrc)
	try:
		while i <= n-1:
			name_idx = '%05i'%i
			if os.path.isdir(runs_dir) == True: # runs folder exists
				if os.path.isdir(runs_dir+name_idx) == True: # sim folder exists
					shutil.rmtree(runs_dir) #removes previous folders
			os.makedirs(runs_dir + name_idx)
			percentage = ((i+1)/n)*100
			print ('Sim#: ',name_idx,' %0.3f'%percentage,'%',end='\r')
			while True:
				# hill.in
				inc_b = 0
				inc_c = np.random.uniform(0,20)
				longasc_b = np.random.uniform(0,360)
				longasc_c = np.random.uniform(0,360)
				argperi_b = np.random.uniform(0,360)
				argperi_c = np.random.uniform(0,360)
				mean_an_b = np.random.uniform(0,360)
				mean_an_c = np.random.uniform(0,360)

				innermass_str = str(mass_b[i])
				outermass_str = str(mass_c[i])
				strMass_str = str(mass_star[i])
				semi_str_b = str(semi_b[i])
				semi_str_c = str(semi_c[i])
				ecc_str_b = str(ecc_b[i])
				ecc_str_c = str(ecc_c[i])

				incl_str_b = str(inc_b)
				incl_str_c = str(inc_c)
				longasc_str_b = str(longasc_b)
				longasc_str_c = str(longasc_c)
				argperi_str_b = str(argperi_b)
				argperi_str_c = str(argperi_c)
				mean_an_str_b = str(mean_an_b)
				mean_an_str_c = str(mean_an_c)

				hill = open(runs_dir+name_idx+'/hill.in','w')
				hill_content = (strMass_str + '\n'
		                        +innermass_str+' '+semi_str_b+' '+ecc_str_b+' '+incl_str_b+' '+argperi_str_b+' '+longasc_str_b+' '+mean_an_str_b+'\n'
		                        +outermass_str+' '+semi_str_c+' '+ecc_str_c+' '+incl_str_c+' '+argperi_str_c+' '+longasc_str_c+' '+mean_an_str_c+'\n'
		                        +'body\n')
				hill.write(hill_content)
				hill.close()

				wd = runs_dir + name_idx
				hill = subprocess.call(['hillstab hill.in > hill_log'],
										shell=True,
										cwd=wd)
				hill_log = open(wd+'/hill_log','r')
				hill_content = hill_log.read()
				hill_content = hill_content.split()
				hill_exact = hill_content[1]
				hill_exact = float(hill_exact)
				if hill_exact < 1: # push out semi so that hill stab > 1
					semi_c[i] = semi_c[i] + 0.01
					continue
				elif hill_exact >= 1:
					hill_list = np.append(hill_list, hill_exact)
					incl_b = np.append(incl_b, inc_b)
					incl_c = np.append(incl_c, inc_c)
					longa_b = np.append(longa_b, longasc_b)
					longa_c = np.append(longa_c, longasc_c)
					argp_b = np.append(argp_b, argperi_b)
					argp_c = np.append(argp_c, argperi_c)
					mean_an_b_list = np.append(mean_an_b_list, mean_an_b)
					mean_an_c_list = np.append(mean_an_c_list, mean_an_c)
					good_hill_list = np.append(good_hill_list, name_idx)
					break
			i+=1
		print('Semi_c made hill stable')
	except IndexError:
		print ('ERROR: hill_log is empty! Is hillstab in your path? See comments in code.')
	# now lets plot that distribution and save it
	fig,ax = plt.subplots(1,1)
	fig.set_size_inches(10,10)

	less_than_1 = np.where(semi_c <=1.0)

	semi_c_hist = ax.hist(semi_c[less_than_1],bins=20,
						 weights=np.zeros_like(semi_c[less_than_1])+1./semi_c[less_than_1].size)
	ax.set(xlabel='semi_c (AU)', ylabel='Percentage')
	ax.text(0.6,0.1,'N = ' + str(semi_c[less_than_1].size))

	fig.savefig('./IC_figs/semi_c.png')

	def write_ics(path):
		# table of initial conditions for easy reference:
		global IC
		IC = QTable()
		IC['Sim #'] = good_hill_list
		IC['Mass_b'] = mass_b
		IC['Mass_c'] = mass_c
		IC['Radius_b'] = rad_b
		IC['Radius_c'] = rad_c
		IC['Semi_b_0'] = semi_b
		IC['Semi_c_0'] = semi_c
		IC['Ecc_b_0'] = ecc_b
		IC['Ecc_c_0'] = ecc_c
		IC['Incl_b_0'] = incl_b
		IC['Incl_c_0'] = incl_c
		IC['LongA_b_0'] = longasc_b
		IC['LongA_c_0'] = longasc_c
		IC['ArgP_b_0'] = argperi_b
		IC['ArgP_c_0'] = argperi_c
		IC['Qp_b'] = Qp_b
		IC['Qp_c'] = Qp_c
		IC['Q_star'] = Qstar
		IC['Mass_star'] = mass_star
		IC['Radius_star'] = rad_star
		IC.write(path, format='ascii.csv')

	# should we save the above generated ICs to file so we dont have to generate new ones?
	save_option = input('Save the generated ICs to csv file? [y/n] ')

	if save_option == 'y':
		now = datetime.datetime.now().strftime("%Y_%m_%d_%H%M%S")
		path = './ICs_'+now+'.csv'
		write_ics(path)
		print('ICs saved @ %s'%path)

if bLoad == True:
	print ('Generating IC_figs for loaded ICs')
	prob_ecc_data = QTable.read('probecc_comma.dat',format='ascii.no_header', names=['ecc','%inbin','cum%'])

	exo_data = QTable.read('planets.csv',format='ascii')
	exo_data['pl_radj'] = exo_data['pl_radj'] * (const.R_jup/const.R_earth) #converts from jupiter radii to earth radii
	rad_data = exo_data['pl_radj']

	plot_ecc_dist(IC['Ecc_b_0'], IC['Ecc_c_0'], prob_ecc_data)
	plot_rad_dist(IC['Radius_b'], IC['Radius_c'], rad_data)
	plot_b_c_mass_rad(IC['Mass_b'], IC['Radius_b'], IC['Mass_c'], IC['Radius_c'])	
print("Initial Conditions Generated.")

bWrite = input('Write input files? [y/n] ')

if bWrite == 'y':

	sim_idx = IC['Sim #']
	mass_b = IC['Mass_b']
	mass_c = IC['Mass_c']
	rad_b= IC['Radius_b'] * -1
	rad_c = IC['Radius_c'] * -1
	semi_b = IC['Semi_b_0'] 
	semi_c = IC['Semi_c_0']
	ecc_b = IC['Ecc_b_0']
	ecc_c = IC['Ecc_c_0']
	incl_b = IC['Incl_b_0']
	incl_c = IC['Incl_c_0']
	longasc_b = IC['LongA_b_0']
	longasc_c = IC['LongA_c_0']
	argperi_b = IC['ArgP_b_0']
	argperi_c = IC['ArgP_c_0']
	Qp_b = IC['Qp_b']
	Qp_c = IC['Qp_c']
	Qstar = IC['Q_star']
	mass_star = IC['Mass_star']
	rad_star = IC['Radius_star']

	write_which = input('Which options: [eq_only(0), eqorb(1), eqorbmesc(2)]\n (for help, add \'-h\') ')
	if ((write_which == 'eq_only') or (write_which == '0')):
		print ('Writing input files for %s %s sims'%(str(n),'eqtide'))
		gen_eqtide('./runs_eq_only/',n)
	elif ((write_which == 'eqorb') or (write_which == '1')):
		print ('Writing input files for %s %s sims'%(str(n),'eqorb'))
		gen_eqorb('./runs_eqorb/',n)
	elif ((write_which == 'eqorbmesc') or (write_which == '2')):
		print ('do eqorbmesc stuff')
		gen_eqorbmesc()
	else:
		print ('Error: option not recognized.')

elif bWrite == 'n':
	print ('do NOT do stuff')
else:
	print('Error: answer not recognized. Options are: y or n')
print (IC)
print ('Time to fire up your favorite super computer!')