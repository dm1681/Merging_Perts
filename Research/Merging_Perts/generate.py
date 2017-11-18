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
import vplot

# just making sure they know I'm downloading files to their machine
verif_string =  'The purpose of this script is to generate "n" initial conditions\n'
verif_string += 'for two planets and one star for use in McDonald(2017).\n'
verif_string += 'It will download any missing data files\n'
verif_string += 'to your current working directory automatically.\n'
verif_string += 'You can then choose which modules to apply.\n'
verif_string += 'Proceed? [y/n] '
verification = input(verif_string)
if verification != 'y':
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
			bLoad = input("Load found file?: [idx/n] ")
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
	print ('Ecc Distribution saved in IC_figs')

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
	# check again to make sure it downloaded
	for item in dirlist:
		if item == 'probecc_comma.dat':
			found = True
			return found
	if found == False:
		print('probecc_comma.dat could not be found or downloaded! Are you connected to the internet?')
		sys.exit()

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

def write_ICs(runs_dir, n, modules):
#	global mass_b, rad_b, semi_b, ecc_b, incl_b, longasci_b, argperi_b, Qp_b, mass_star, rad_star, Qstar
	modules_star = modules[0]
	modules_b = modules[1]
	modules_c = modules[2]

	bWriteEqtide_star = False
	bWriteEqtide_b = False
	bWriteEqtide_c = False
	bWriteDistorb_star = False
	bWriteDistorb_b = False
	bWriteDistorb_c = False
	bWriteAtmesc_star = False
	bWriteAtmesc_b = False
	bWriteAtmesc_c = False

	# b.in
	name_b = 'b'
	modules_b = modules_b
	dMass_b = mass_b * -1# sets to earth masses;
	dEnvMass_b = env_mass_b * -1
	dRadius_b = rad_b * -1 # sets to earth radii
	dSemi_b = semi_b
	dEcc_b = ecc_b
	dObliquity_b = 45
	dRadGyra_b = 0.5


	#c.in
	name_c = 'c'
	modules_c = modules_c
	dMass_c = mass_c * -1 # sets to earth masses;
	dEnvMass_c = env_mass_c * -1
	dRadius_c = rad_c * -1 # sets to earth radii
	dSemi_c = semi_c # semi_c defined above
	dEcc_c = ecc_c # ecc_c defined above
	dObliquity_c = 45
	dRadGyra_c = 0.5


	#star.in
	name_star = 'star'
	modules_star = modules_star
	dMass_star = mass_star #solar masses;
	dRadius_star = rad_star # * ratio of solar radii to au
	dObliquity_star = 0
	dRotPeriod_star = -30
	dRadGyra_star = 0.5
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

	# now lets determine which modules to write
	#b.in
	if modules_b.find('distorb') > -1:
		bWriteDistorb_b = True
	if modules_b.find('atmesc') > -1:
		bWriteAtmesc_b = True
	if modules_b.find('eqtide') > -1:
		bWriteEqtide_b = True

	#c.in
	if modules_c.find('distorb') > -1:
		bWriteDistorb_c = True
	if modules_c.find('atmesc') > -1:
		bWriteAtmesc_c = True
	if modules_c.find('eqtide') > -1:
		bWriteEqtide_c = True

	# star.in
	if modules_star.find('distorb') > -1:
		bWriteDistorb_star = True
	if modules_star.find('atmesc') > -1:
		bWriteAtmesc_star = True
	if modules_star.find('eqtide') > -1:
		bWriteEqtide_star = True

	i = 0
	while i <= n-1:
		# make strings of values; b.in
		name_idx = '%05i'%i
		print ('Writing...\n')
		if os.path.isdir(runs_dir+name_idx) == True: #sim folders exist
			shutil.rmtree(runs_dir) #removes previous folders; THIS LINE DELETES THE ENTIRE RUNS DIRECTORY
			os.makedirs(runs_dir+name_idx)
		else: #sims folder does not exist
			os.makedirs(runs_dir+name_idx)

		# b.in
		mass_str = str(dMass_b[i])
		radius_str = str(dRadius_b[i])
		obl_str = str(dObliquity_b)
		radgy_str = str(dRadGyra_b)
		ecc_str = str(dEcc_b[i])
		semi_str = str(dSemi_b[i])

		b = open(runs_dir+name_idx+'/b.in','w')
		b_content = ('sName\t\t\t'+ name_b +
					 '\nsaModules\t\t'+modules_b+

					 '\n\n#Physical Properties'+
					 '\ndMass\t\t\t'+mass_str+
					 '\ndRadius\t\t\t'+radius_str+
					 '\ndObliquity\t\t'+obl_str+
					 '\ndRadGyra\t\t'+radgy_str+

					 '\n\n#Orbital Properties'+
					 '\ndEcc\t\t\t'+ecc_str+
					 '\ndSemi\t\t\t'+semi_str)

		b_output = '\nsaOutputOrder\t\tTime'
		if bWriteEqtide_b:
			b_content, b_output = write_eqtide(b_content, b_output,'b', i)
		if bWriteDistorb_b:
			b_content, b_output = write_distorb(b_content, b_output,'b', i)
		if bWriteAtmesc_b:
			b_content, b_output = write_atmesc(b_content, b_output,'b', i)

		b_content += (b_output+'\n')
		b.write(b_content)
		b.close()

		#c.in
		if modules_c != 'null':
			saBodyFiles = 'star.in b.in c.in'
			mass_str = str(dMass_c[i])
			radius_str = str(dRadius_c[i])
			obl_str = str(dObliquity_c)
			radgy_str = str(dRadGyra_c)
			ecc_str = str(dEcc_c[i])
			semi_str = str(dSemi_c[i])

			c = open(runs_dir+name_idx+'/c.in','w')
			c_content = ('sName\t\t\t'+ name_c +
						 '\nsaModules\t\t'+modules_c+

						 '\n\n#Physical Properties'+
						 '\ndMass\t\t\t'+mass_str+
						 '\ndRadius\t\t\t'+radius_str+
						 '\ndObliquity\t\t'+obl_str+
						 '\ndRadGyra\t\t'+radgy_str+

						 '\n\n#Orbital Properties'+
						 '\ndEcc\t\t\t'+ecc_str+
						 '\ndSemi\t\t\t'+semi_str)

			c_output = '\nsaOutputOrder\t\tTime'
			if bWriteEqtide_c:
				c_content, c_output = write_eqtide(c_content, c_output,'c',i)
			if bWriteDistorb_c:
				c_content, c_output = write_distorb(c_content, c_output,'c',i)
			if bWriteAtmesc_c:
				c_content, c_output = write_atmesc(c_content, c_output,'c',i)

			c_content += (c_output+'\n')

			c.write(c_content)
			c.close()
		else:
			saBodyFiles = 'star.in b.in'

		#star.in
		name_star = name_star
		modules_star = modules_star
		strMass_str = str(dMass_star[i])
		strRad_str = str(dRadius_star[i])
		strObl_str = str(dObliquity_star)
		strRotPer_str = str(dRotPeriod_star)
		strRadGyr_str = str(dRadGyra_star)
		dSatXUVtime_str = str(satxuvtime[i])
		strsaOutputOrder = saOutputOrder_s

		star = open(runs_dir+name_idx+'/star.in','w')
		star_content = ('sName\t\t\t'+name_star+
						'\nsaModules\t\t'+modules_star+
						'\n\ndMass\t\t\t'+strMass_str+
						'\ndRadius\t\t\t'+strRad_str+
						'\ndObliquity\t\t'+strObl_str+
						'\ndRotPeriod\t\t'+strRotPer_str+
						'\ndRadGyra\t\t'+strRadGyr_str)

		star_output = '\nsaOutputOrder\t\tTime'
		if bWriteEqtide_star:
			star_content, star_output = write_eqtide(star_content, star_output,'star',i)
		if bWriteDistorb_star:
			star_content, star_output = write_distorb(star_content, star_output,'star',i)
		if bWriteAtmesc_star:
			star_content, star_output = write_atmesc(star_content, star_output,'star',i)

		star_content += (star_output+'\n')

		star.write(star_content)
		star.close()

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

		# now lets move those hill files
		if bLoad == False: # ICs not loaded from file, therefore Hill stab has been calculated
			cmd = 'cp ./hill_runs/'+name_idx+'/hill* ' +runs_dir+'/'+name_idx+'/'
			p = subprocess.call([cmd],shell=True, cwd='./')
			p_rm = subprocess.call(['rm -rf ./hill_runs/'+name_idx], shell=True, cwd='./')

		i += 1
	p_rm = subprocess.call('rm -rf ./hill_runs', shell=True, cwd='./')
	return 0

def write_distorb(body_content, body_outputorder, body, idx):
	global IC, modules
	sOrbitModel = 'rd4'
	bOutputLapl_str = '0'
	InvPlane_str = '1'
	planet_outputorder = ' LongP Inc LongA ArgP'
	star_outputorder = ''
	if body == 'star':
		outputorder = star_outputorder
	elif body == 'b':
		outputorder = planet_outputorder
		body_content += ('\n\n#DISTORB Properties'+
						 '\ndInc\t\t\t'+str(IC['Incl_'+body+'_0'][idx])+
						 '\ndLongA\t\t\t'+str(IC['LongA_'+body+'_0'][idx])+
						 '\ndArgP\t\t\t'+str(IC['ArgP_'+body+'_0'][idx])+
						 '\nsOrbitModel\t\t'+sOrbitModel+  #for Distorb
						 '\nbOutputLapl\t\t'+bOutputLapl_str+ #for Distorb
						 '\nbInvPlane\t\t'+InvPlane_str)
	elif body == 'c':
		outputorder = planet_outputorder
		body_content += ('\n\n#DISTORB Properties'+
						 '\ndInc\t\t\t'+str(IC['Incl_'+body+'_0'][idx])+
						 '\ndLongA\t\t\t'+str(IC['LongA_'+body+'_0'][idx])+
						 '\ndArgP\t\t\t'+str(IC['ArgP_'+body+'_0'][idx]))
	body_outputorder += outputorder
	return body_content, body_outputorder

def write_eqtide(body_content, body_outputorder, body, idx):
	global IC, modules
	bForceEqSpin_str = '1'
	dK2_str = '0.3'
	sTideModel = 'p2'
	planet_outputorder = ' Semim Ecce Obliquity SurfEnFluxEqtide'
	star_outputorder = ''
	if body == 'star':
		if modules[2].find('eqtide') != -1:
			perts_str = 'b c'
		else:
			perts_str = 'b'

		Q = str(IC['Q_star'][idx])
		outputorder = star_outputorder
		eqtide_content = ('\n\n#EQTIDE Properties'+
						 '\ndTidalQ\t\t\t'+Q+
						 '\ndK2\t\t\t'+dK2_str+
						 '\nsaTidePerts\t\t'+perts_str)
	elif body == 'b':
		perts_str = 'star'
		Q = str(IC['Qp_'+body][idx])
		outputorder = planet_outputorder
		eqtide_content = ('\n\n#EQTIDE Properties'+
						 '\nsTideModel\t\t' + sTideModel +
						 '\nbForceEqSpin\t\t'+bForceEqSpin_str+
						 '\ndTidalQ\t\t\t'+Q+
						 '\ndK2\t\t\t'+dK2_str+
						 '\nsaTidePerts\t\t'+perts_str)
	elif body == 'c':
		perts_str = 'star'
		Q = str(IC['Qp_'+body][idx])
		outputorder = planet_outputorder
		eqtide_content = ('\n\n#EQTIDE Properties'+
						 '\nbForceEqSpin\t\t'+bForceEqSpin_str+
						 '\ndTidalQ\t\t\t'+Q+
						 '\ndK2\t\t\t'+dK2_str+
						 '\nsaTidePerts\t\t'+perts_str)

	body_content += eqtide_content
	body_outputorder += outputorder
	return body_content, body_outputorder

def write_atmesc(body_content, body_outputorder, body, idx):
	global IC, modules
	sPlanetRadiusModel = 'lehmer'
	bHaltEnvelopeGone_str = '1'
	planet_outputorder = ' -Mass -EnvelopeMass -DEnvMassDt -Radius -RadSolid -RadXUV -PresSurf -FXUV'
	star_outputorder = ''
	if body == 'star':
		outputorder = star_outputorder

	elif body == 'b':
		body_content += ('\n\n#ATMESC Properties'
						 + '\nsPlanetRadiusModel\t' + sPlanetRadiusModel
						 + '\nbHaltEnvelopeGone\t' + bHaltEnvelopeGone_str
						 + '\ndEnvelopeMass\t\t' + str(IC['EnvMass_'+body][idx] * -1)
						 + '\ndAtmXAbsEffH\t\t' + str(IC['AtmXAbsEffH_'+body][idx])
						 + '\ndThermTemp\t\t' + str(IC['ThermTemp_'+body][idx])
						 + '\ndPresXUV\t\t' + str(IC['PresXUV_'+body][idx])
						 + '\ndAtmGasConst\t\t' + str(IC['AtmGasConst_'+body][idx])
#					 	 + '\ndFXUV\t\t\t' + str(IC['FXUV_'+body][idx])
						 )
		outputorder = planet_outputorder

	body_outputorder += outputorder
	return body_content, body_outputorder

### Time to do things ###

if bLoad == False:
	# number of simulations to generate
	if len(sys.argv) == 1:
		n = 25000
		print ('Defaulting to n = 25000 simulations')
	elif len(sys.argv) > 1:
		n = int(sys.argv[1])
		print ('Generatiing n = %i simulations '%n)

	IC = QTable()

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

	# def linear interp for Q and atmmassfrac;
	min_q = 10**6
	max_q = 10**7
	min_atmmassfrac = 0.01
	max_atmmassfrac = 0.1
	slope = (max_atmmassfrac - min_atmmassfrac)/(max_q - min_q)
	# y = atmmassfrac, x = q
	def linear_interp(x):
		y = min_atmmassfrac + slope * (x - min_q)
		return y

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
			if toggle == 'atm':
				return 0.0
		else:
			r = r.to(u.cm)
			volume = (4.0 * np.pi * r**3.0) / 3.0
			density = (1 * u.g)/(1 * u.cm)**3
			mass = volume * density
			mass = mass.to(u.earthMass)
			Qplanet = np.random.uniform(10**6, (10**7)+1)
			atmmassfrac = linear_interp(Qplanet)
			if toggle == 'atm':
				return atmmassfrac
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

	##### EQTIDE #####

	rad_b = rad_b * u.earthRad
	rad_c = rad_c * u.earthRad

	mass_b = np.array([])
	atmmassfrac_b = np.array([])
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
		AtmMassFrac_b = calc_mass_Qp(r,'atm')
		atmmassfrac_b = np.append(atmmassfrac_b, AtmMassFrac_b)

	mass_c = np.array([])
	atmmassfrac_c = np.array([])
	Qp_c= np.array([])

	print ('Generating Mass Distribution for: %s'%name_outer)
	print ('Generating Q Distribution for: %s'%name_outer)
	for r in rad_c:
		m = calc_mass_Qp(r,'m')
		mass_c = np.append(mass_c, m)
		q = calc_mass_Qp(r,'Q')
		Qp_c = np.append(Qp_c, q)
		AtmMassFrac_c = calc_mass_Qp(r,'atm')
		atmmassfrac_c = np.append(atmmassfrac_c, AtmMassFrac_c)

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



	##### DISTORB #####

	# making semi_c hill stable
	runs_dir = './hill_runs/'

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
					semi_c[i] = semi_c[i] + 0.1 # change to 0.1 to make faster... 0.01 for slower
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


	##### ATMESC #####
	# Replicating Lehmer 2017 ranges: #

	presxuv_b = np.random.uniform(0.1, 10, n)
	presxuv_c = np.random.uniform(0.1, 10, n)
	atmgasconst_b = np.random.uniform(3600, 4157, n)
	atmgasconst_c = np.random.uniform(3600, 4157, n)
	thermtemp_b = np.random.uniform(880, 3000, n)
	thermtemp_c = np.random.uniform(880, 3000, n)
	fxuv_b = np.random.uniform(43, 172, n)
	fxuv_c = np.random.uniform(43, 172, n)
	#atmmassfrac_b = np.random.uniform(0.01, 0.1, n)
	#atmmassfrac_c = np.random.uniform(0.01, 0.1, n)
	atmxabseffH_b = np.random.uniform(0.1, 0.6, n)
	atmxabseffH_c = np.random.uniform(0.1, 0.6, n)
	planetradiusmodel = 'lehmer'
	satxuvtime = np.random.uniform(80e6, 120e6, n)
	env_mass_b = mass_b * atmmassfrac_b
	env_mass_c = mass_c * atmmassfrac_c


	# now lets save everything to an IC table using astropy
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
	IC['PresXUV_b'] = presxuv_b
	IC['PresXUV_c'] = presxuv_c
	IC['AtmGasConst_b'] = atmgasconst_b
	IC['AtmGasConst_c'] = atmgasconst_c
	IC['ThermTemp_b'] = thermtemp_b
	IC['ThermTemp_c'] = thermtemp_c
	IC['FXUV_b'] = fxuv_b
	IC['FXUV_c'] = fxuv_c
	IC['AtmMassFrac_b'] = atmmassfrac_b
	IC['AtmMassFrac_c'] = atmmassfrac_c
	IC['AtmXAbsEffH_b'] = atmxabseffH_b
	IC['AtmXAbsEffH_c'] = atmxabseffH_c
	IC['SatXUVTime'] = satxuvtime
	IC['EnvMass_b'] = env_mass_b
	IC['EnvMass_c'] = env_mass_c

	# saving above generated ICs to csv file
	now = datetime.datetime.now().strftime("%Y_%m_%d_%H%M%S")
	path = './ICs_'+now+'.csv'
	IC.write(path, format='ascii.csv')
	print('ICs saved @ %s'%path)

if bLoad == True:
	n = len(IC)
	print ('Assuming Semi_c is already Hill Stable')
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
	rad_b= IC['Radius_b']
	rad_c = IC['Radius_c']
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
	presxuv_b = IC['PresXUV_b']
	presxuv_c = IC['PresXUV_c']
	atmgasconst_b = IC['AtmGasConst_b']
	atmgasconst_c = IC['AtmGasConst_c']
	thermtemp_b = IC['ThermTemp_b']
	thermtemp_c = IC['ThermTemp_c']
	fxuv_b = IC['FXUV_b']
	fxuv_c = IC['FXUV_c']
	atmmassfrac_b = IC['AtmMassFrac_b']
	atmmassfrac_c = IC['AtmMassFrac_c']
	atmxabseffH_b = IC['AtmXAbsEffH_b']
	atmxabseffH_c = IC['AtmXAbsEffH_c']
	satxuvtime = IC['SatXUVTime']
	env_mass_b = IC['EnvMass_b']
	env_mass_c = IC['EnvMass_c']

	modules = {} # modules[0] = star; modules[1] = b, modules[2] = c, etc...
	which_modules = input('Write Options (eqtide(0) atmesc(1) eqorb(2)): ')
	if ((which_modules == '0') or (which_modules=='eqtide')):
		modules[0] = 'eqtide'
		modules[1] = 'eqtide'
		modules[2] = 'null'
		write_ICs('./runs_eqtide/',n,modules)
	elif ((which_modules == '1') or (which_modules == 'atmesc')):
		modules[0] = 'stellar'
		modules[1] = 'atmesc'
		modules[2] = 'null'
		write_ICs('./runs_atmesc/',n,modules)
	elif ((which_modules == '2') or (which_modules == 'eqorb')):
		modules[0] = 'eqtide'
		modules[1] = 'eqtide distorb'
		modules[2] = 'eqtide distorb'
		write_ICs('./runs_eqorb/',n,modules)
	else:
		print ('Error: Option not recognized.')


elif bWrite == 'n':
	print ('do NOT do stuff')
else:
	print('Error: answer not recognized. Options are: y or n')

print (IC)
print ('Time to fire up your favorite super computer!')
