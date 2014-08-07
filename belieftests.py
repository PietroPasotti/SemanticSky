#!/usr/bin/python3

import tests
import numpy as np
import matplotlib as plt
import pylab as lab

pickle = tests.pickle
center = tests.center
wrap = tests.wrap
table = tests.table
bmag = tests.bmag
stdout = tests.clues.ss.stdout
crop_at_nonzero = tests.crop_at_nonzero

def binput(msg):
	a = input(bmag('\t>> {}'.format(msg)))
	return a

def confirm(msg):
	if binput('Chosen "{}". Confirm? '.format(msg)) in 'yesYES':
		return True
	else:
		return False

def setup_new_god():
	
	tests.load_sky()
	sky = tests.sky
	
	God = tests.clues.God(sky)
	
	print(God,' has born.')
	
	return God

def express_all(god):
	
	for ga in god.guardianangels:
		ga.express()

def getknower(god):
	
	if hasattr(god,'knower'):
		if not god.knower.supervisor is god:
			god.knower.new_supervisor(god)
		return god.knower
		
	knower = tests.clues.knower if tests.clues.knower else tests.clues.Knower(god)
	if not knower.supervisor is god:
		knower.new_supervisor(god)
		
	return knower
	
def give_feedback(god,knower):
	
	knower.express()

def equate_all_links(god,angels):
	"""
	When unpickling evaluations, we often have that clouds made out of the same items
	are no longer properly indexed in dictionaries: they appear as different
	pairs altogether.

	This function only acts on evaluations of guardianangels of the given deity
	or of the default god, setting their evaluations to a common vocabulary
	of cloud pairs.
	"""
		
	pid = lambda x: (tuple(x)[0].item['id'], tuple(x)[1].item['id'])	

	print('\t\tParallelising beliefs... (May take a while)')
		
	for ga in angels:
		
		totln = len(ga.evaluation)
		i = 0
		for link,ev in ga.evaluation.items():
			del ga.evaluation[link]
			itlinks = pid(link)
			truelink = god.sky.pair_by_id(*itlinks)

			ga.evaluation[truelink] = ev
			
			bar(i/totln,title= 'Aliasing [{}]:'.format(ga))
			i+=1			
		print()
		
	return True
	
def interactive_setup(god,auto = False):
	"""
	Allows for semi-interactive picking of guardianangels for a given god.
	"""
	
	if god.guardianangels:
		pass
	else:
		god.spawn_servants()
		
	servs = []
	
	n = 0
	for ga in god.guardianangels:
		servs.append([n,ga])
		n += 1
		
	tdict = {number:serv for number,serv in servs}
	
	chosen = []
	
	print()
	table(servs)
	print()
	print('Enter the GuardianAngels you want to assign to {} '.format(god),'using the syntax "0,1,2,3...". "A" == All. Intervals accepted ("-").')
	while True:
		if auto:
			chosen = god.guardianangels
			break
			
		choice = input(bmag('\t>>: '))
					
		if not choice: # require an explicit choice
			continue
			
		if choice.strip() == 'A':
			chosen = god.guardianangels						
		else:			
			tolist = choice.split(',')
			for elem in tolist:
				tolist[tolist.index(elem)] = elem.strip()
					
			while '' in tolist:
				tolist.remove('')
			
			chosen = []
			
			for elem in tolist:
				if elem.isdigit() and '.' not in elem and int(elem) < len(tdict):
					n = int(elem)
					chosen.append(tdict[n])
				elif '-' in elem: # parsing for intervals
					ch = elem.split('-')
					
					ini = ch[0]
					end = ch[1]
					
					top = len(tdict)
			
					try:
						ini = int(ini)
						end = int(end)
						if not 0<=ini<end or not 0<end<top:
							continue
						
						for i in range(ini,end+1,1):
							chosen.append(tdict[i])
					except BaseException:
						continue
				else:
					print('Unrecognized input {}; skipping...'.format(elem))
					
		print("\t>> Selected:")
		for i in chosen:
			print('\t\t\t',repr(i))
		
		if input(bmag('\t>> Confirm? ')) in 'yesYES':
			break
			
	god.guardianangels = chosen
	
	tests.load_evaluations_to_gas(god.guardianangels)
	
	loadedweights = 0
	if input(bmag('\t>> Do you want to load weights as well? ')) in 'yesYES' or auto:
		tests.load_weights_to_gas(god.guardianangels)
		loadedweights += 1
		print('\t\t[Loaded.]')
	print()
	print('\t[All ready.]')
	
	print("\tNow the guardians' evaluations will be merged...")
	print('\t\t(aliasing links...)')
	equate_all_links(god,god.guardianangels)
	
	print()
	print('\t--EXPRESSING: the guardians spawn clues about the beliefs they have--')
	express_all(god)
	
	knower = getknower(god)
	if not loadedweights: # if weights weren't loaded automatically...
		if input(bmag('\t>> Summon the Knower and give feedback? ')) in 'yesYES':		
			knower.evaluate_all(express = False)	
			print()
			equate_all_links(god,[knower])	
			if knower not in god.whisperers:
				god.whisperer(knower)
			knower.express()
	else: # we do it another way
		if not knower.evaluation:
			knower.evaluate_all(express = False,verbose = False)	
		equate_all_links(god,[knower])
	
	print('\t\t[Done.]')
	
	if auto:
		pass	
	elif input(bmag('\t>> Display trusts? ')) in 'yesYES':
		god.trusts(god.guardianangels,local = False)
	
	print(wrap('...exiting interactive environment.','red'))
	return god
	
def similarity_picker(god,auto = False):
	"""
	Generates a custom user and lets him spawn judgements about clouds.
	Provides further insights into semanticsky's way of working.
	"""

	tests.makeglobal(god)

	if not god.beliefs:
		print('God is pretty empty.')
	
	print(center(wrap(' similarity picker v0.4 ','brightred'),space='-'))
	
	exes = []
	
	while True: # AGENT CREATION
		
		if auto:
			uname = 'pietro'
			agent = tests.clues.Agent(uname,god) #name and supervisor
			print('\t\tNow you are {}.'.format(agent))
			break

		uname = binput('Choose your username: ')

		
		if not uname:
			print('\tCome on...')
			continue
		
		try:
			if confirm(uname):
				agent = tests.clues.Agent(uname,god) #name and supervisor
				print('\t\tNow you are {}.'.format(agent))
				break
		
		except BaseException as e:
			print('Something went wrong.')
			exes.append(e)
		
	doptions = lambda x: table([[y] for y in x])
	
	global curpair
	curpair = None
	def pick_random_link():
		link = tests.randomlink()
		global curpair
		curpair = link
	
	actualist = list(god.beliefs)
	tests.random.shuffle(actualist)
	actuiter = iter(actualist)
	del actualist
	
	def choose_a_link_yourself():
		global curpair
		while True:
			
			choice = binput('Give two cloudnames (IDs) separated by a space: ')
			
			ch = choice.split(' ')
			cch = []
			try:
				for c in ch:
					c = c.strip()
					if c.isdigit():
						cch.append(int(c))
					else:
						cch.append(c)
				print('\t\t Looking up cloud pair ({},{})...'.format(cch[0],cch[1]))
				
				try:
					cloud1 = god.sky.get_cloud(cch[0])
					try:
						cloud2 = god.sky.get_cloud(cch[1])
					except ValueError:
						print('Incorrect cloudID: {} not found.'.format(cch[1]))
						continue
				except ValueError:
					print('Incorrect cloudID: {} not found.'.format(cch[0]))
					continue
					
			except BaseException:
				print('Bad input.')
				
			curpair = tests.clues.ss.pair(cloud1,cloud2)
			print('\t Chosen {}'.format(set(curpair)))
			break
				
	def pick_random_actual_link():
		global curpair
		curpair = next(actuiter)

	def evaluate_similarity(): # lets agent evaluate the pair
		global curpair
		while True:
			rating = binput("Rate from 0 to 10 the similarity of the items. ('b' to go back) ")
			
			if rating.strip() == 'b':
				return None
				
			try:
				rating = float(rating)
			except BaseException:
				print('\t\tBad input.')
				continue
				
			if 0 <= rating <= 10:
				if confirm(rating):
					break

		agent.evaluate(curpair,rating/10)

	def more_info():
		global curpair
		print('\tThe currently selected link is about two clouds:')
		
		clouda,cloudb = curpair
		
		head1 = wrap(clouda.get_header(),'green')
		head2 = wrap(cloudb.get_header(),'green')
		
		print(center('-',space = '-'))
		print(wrap('\tITEM [1]','brightred'))
		print('\t\tItem 1 is identified by: ',head1)
		print('\t\tAnd is an item of type "{}".'.format(clouda.ctype()))
		print()
		
		
		
		print(center('-',space = '-'))
		print(wrap('\tITEM [2]','brightred'))
		print('\t\tItem 2 is identified by: ',head2)
		print('\t\tAnd is an item of type "{}".'.format(cloudb.ctype()))
		print()
		
		
		
		print()
		print(center(' GENERAL INFORMATION ',space = '-'))
		linked = wrap('are','brightblue') if tests.clues.algs.someonesuggested(clouda,cloudb) else "are " + wrap('not','brightred')
		print('\tIn starfish they currently {} linked.'.format(linked))
		
		if not god.logs.get(curpair):
			return
		
		godbels = god.believes(curpair)
		print('\tGod believes the link with {} confidence.'.format(godbels))
		
		ctype = tests.clues.ss.ctype(curpair)
		
		tbl = [['GuardianAngel','confidence','weight','--> weighted_confidence']]
		for ga in god.guardianangels:
			line = []
			conf = crop_at_nonzero(ga.evaluate(curpair,silent = True),4) # should return the confidence, and not spawn anything!
			
			weight = crop_at_nonzero(ga.reltrust(ctype),4)
			
			line += [conf,weight]
			if weight:
				weightedworth = crop_at_nonzero(weight * conf,4)
				line += [weightedworth]
					
			tbl.append(line)
			
		table(tbl) # prints the table
		
		allresps = [clue.agent for clue in god.logs[curpair]]
		nongas = [agent for agent in allresps if not isinstance(agent,tests.clues.GuardianAngel)]
		
		if nongas:
			print('\tOther responsibles for this belief are: ',nongas)
			print("\tThey clue'd as follows:")
			tbl = [['agent','value','weighted value']]
			for ag in nongas:
				line = [ag] + ag.believes(curpair) 
				tbl.append(line)
			print()
			table(tbl)	
			print()
		
	def make_me_whisper():
		print("\tCongratulations! Jou are now whispering.")
		return agent.makewhisperer()
		
	def fullcompare():	
		print()
		tests.fullcompare(god)
		print()
	
	def display_item_text(cloud,n):
		print()
		print(wrap(center(' displaying item [{}]: {}'.format(n,cloud.get_header()),space = '-'),'magenta'))
		print(cloud.item)
		print()
		
	def display_cloud(cloud,n):
		print()
		print(wrap(center(' layers of cloud [{}]: {}'.format(n,cloud.get_header()),space = '-'),'magenta'))
		print(cloud.layers)
		print()

	while True: # MAIN LOOP
		options = {	'r' : (pick_random_link,'random link'),
					'ra' : (pick_random_actual_link,	'pick a random actual link | god has some doubt about it'),
					'c' : (choose_a_link_yourself,	'choose a link by id'),
					'b' : ('exit','exit')}
						
		if curpair:
			print('\tCurrently focused: {}.'.format(wrap("[{}]".format(set(curpair)),'white')))
			global item1,item2
			item1,item2 = tuple(curpair)
			
			display_item1_text = lambda : display_item_text(item1,1)
			display_item2_text = lambda : display_item_text(item2,2)
			display_cloud1 = lambda : display_cloud(item1,1)
			display_cloud2 = lambda : display_cloud(item2,2)
			
			options.update({	'e'		: (evaluate_similarity,'give your rating'),
								'i'		: (more_info,'more info about the link'),
								'text1'	: (display_item1_text,"display item 1's content"),
								'text2'	: (display_item2_text,"display item 2's content"),
								'cloud1': (display_cloud1,"display the cloud 1"),
								'cloud2': (display_cloud2,"display the cloud 2"),
								'I'  	: (fullcompare,'a lot more info -- fullcompare')})
		lopts = []
		for option in options:	
			lopts.append([ option, options[option][1] ])
			
		choice = binput('')
		
		choice = choice.strip()
		if not choice:
			print(center(wrap('enter "h" for available commands','lightgrey')))
			continue
		
		if choice in 'Hh':
			print('Available commands:')
			table(lopts)
		elif choice in 'bB':
			print(wrap('exiting...','brightred'))
			break
		elif choice in options.keys():
			options[choice][0]()
		else:
			print(center(wrap('unknown command','lightgrey')))
	
	return god,curpair
	
def interactive(god = None,auto = False):
	print()	
	if not god:
		print('Setting up a fresh god...')
		god = setup_new_god()
		print()
	print()
	print('Initializing interactive setupper...')
	print()
	interactive_setup(god,auto)
	print()
	print('Initializing interactive similarity_picker...')
	print()
	out = similarity_picker(god,auto)
	print()
	
	exec("global GOD{0}\nGOD{0} = god".format(god.godid))

	print('exiting... (god stored in the global GOD{})'.format(god.godid))
	
	return out

# matplotlib tests

def evaluate_online_accuracy_function(god,test = False,step = 1,store_subsequent_evaluations = True,filename = "evaluation_output" ):
	
	tests.random.shuffle(god.sky.sky)
	cloudlist = god.sky.sky
	
	if not god.guardianangels:
		god.spawn_servants()
		
	knower = getknower(god)
	if not knower.evaluation:
		knower.evaluate_all(express = False)
	
	print()
	print('removing tag-similarity angels...')
	god.guardianangels = [ga for ga in god.guardianangels if ga.name not in ['tag_similarity_naive','tag_similarity_extended']]
		
	tests.load_evaluations_to_gas(god.guardianangels)
	
	god.sky.sky = [] # we empty the sky. We are then going to add back the clouds one by one.
	god.cleanbuffer() # EMPTY THE BUFFER
	
	loops = 0
	
	output = {}
	
	import time
	
	while cloudlist:
		
		initime = time.clock()
		
		clouds = cloudlist[0:min(step,len(cloudlist))]
		
		if len(clouds) < step or len(cloudlist) == 0:
			break
			
		if test and loops > test:
			print('\n')
			print(loops, ' loops hit. Stopping. Total list of clouds already included now stored to cluecount.log: \n\n ', [cloud.item['id'] for cloud in god.sky.sky])
			pickle.dump( [cloud.item['id'] for cloud in god.sky.sky] , open('./tests_output/cluecount.log','wb+'))
			break
		
		print('\nExtracted clouds [{}]. Now the sky contains {} clouds.'.format([acloud.item['id'] for acloud in clouds ],len(god.sky.sky) + len(clouds)))
		
		cloudlist = cloudlist[step:]
		pout = add_to_sky_evaluate_feedback(god,clouds) # partial output, which will go to the total final output
		output["{} clues".format(len(god.sky.sky))] = pout
		
		loops += 1
		
		endtime = time.clock()
		
		totloops = test if test else int(len(cloudlist) / step)
		elapsed = round(endtime - initime)
		forecast = elapsed * (totloops - loops)
		
		print(center('--- [loop {} :: {} elapsed :: {} estimated to the end] ---'.format(loops,elapsed,forecast)))
	
	dump_to_file(output,filename)
	return 

def dump_to_file(val,filename = "evaluation_output"):
	print('Dumping output...')
	path = "./tests_output/"
	
	filename = path + filename + '.log'
	
	with open(filename,'wb+') as f:
		pickle.dump(val,f)
		
	print("\tDumped to file {}.".format(filename))
	return True
		
def add_to_sky_evaluate_feedback(god,listofclouds):
	"""
	- Adds listofclouds to gods' sky;
	- Retrieves the iter_pairs of the sky and tells the guardianangels to evaluate
	the newly available pairs.
	- The knower gives feedback and updates the guardianangels' trustworthiness
	"""
	
	god.sky.sky.extend(listofclouds)
	
	iterpairs = tuple(god.sky.iter_pairs()) # all 2-permutations of the clouds which are in the system
	
	bar = tests.clues.ss.ProgressBar(len(iterpairs),title = 'Parsing [{}] pairs...'.format(len(iterpairs)))
	for pair in iterpairs:
		
		bar()
		
		for cloud in listofclouds:
			if cloud in pair and pair not in god.beliefs:
				god.rebelieves(pair,weight = True,silent = False) 	# if nonzero, this will be stored in god.beliefs
																					# and a clue will be spawned and logged				
				break 
								# this part makes sure that god's rebelief is called just on pairs such that at least one of its clouds is part of listofclouds;
								# that is: of the clouds we are adding now to the system.
								# we only ask to clue for pairs which arent' already there.
								# otherwise we'll just do more work.
								# the refresh() which we will run afterwards will retrieve the new value of the agents' trustworthiness
								# from the logged clue, in case it has changed. All we need to know is that THERE IS A CLUE THERE.
		
				
		
	# at this point we have a fresh belief set, made out of the feedbacks of the previous iterations
	# and the clues we already had + the ones we have now

	god.clean_trivial_beliefs()
	
	print('\nGod has [{}] beliefs.'.format(len(god.beliefs)))
	
	knower = getknower(god)
	
	newclues = god.getbuffer()
	
	knower.give_feedback(newclues)
	# this will prompt the knower to give feedback only on newly created clues.
	
	god.refresh()
	# this will ask god for a reevaluation, thus taking into account the feedback, old and new

	return evaluate_status(god)

OUTPUT = {}

def evaluate_status(god):
	
	knower = getknower(god)
	
	out = {}
	
	avg = lambda iterable: sum(iterable) / len(iterable) if iterable else 0
	
	beltrue = tuple(god.believes(x) for x in knower.evaluation)
	avgbeltrue = sum(beltrue) / len(beltrue) if beltrue else 0
	
	belfalse = tuple(god.believes(x) for x in god.beliefs if x not in knower.evaluation)
	avgbelfalse = sum(belfalse) / len(belfalse) if belfalse else 0
	
	belall = tuple(god.beliefs.values())
	avgbelall = sum(belall) / len(belall) if belall else 0
	
	out['average_strength_of_god_beliefs'] = {}
	out['average_strength_of_god_beliefs']['in true beliefs'] = avgbeltrue
	out['average_strength_of_god_beliefs']['in false beliefs'] = avgbelfalse
	out['average_strength_of_god_beliefs']['in all beliefs'] = avgbelall

	out["average_precision_of_algorithms"] = {}
	
	for ga in god.guardianangels:
		truebels = tuple(set(knower.evaluation).intersection(ga.evaluation))
		trueconfs = tuple(ga.evaluation[x] for x in truebels) # unweighted confidences in true beliefs
		
		falsebels = tuple(set(ga.evaluation).difference(truebels))
		falseconfs = tuple(ga.evaluation[x] for x in falsebels) 
		avgallbels = avg(ga.evaluation.values())
	
		avgtruebels = avg(trueconfs)
		avgfalsebels = avg(falseconfs)
		
		out["average_precision_of_algorithms"][ga.name] = {}
		out["average_precision_of_algorithms"][ga.name]['unweighted'] = {}
		
		out["average_precision_of_algorithms"][ga.name]['unweighted']['average belief in true links'] = avgtruebels
		out["average_precision_of_algorithms"][ga.name]['unweighted']['average belief in false links'] = avgfalsebels
		out["average_precision_of_algorithms"][ga.name]['unweighted']['average belief in all links'] = avgallbels
		
		wevaluation = {belief: ga.belief_with_feedback(belief) for belief in ga.evaluation}
		
		wtruebels = tuple(set(knower.evaluation).intersection(wevaluation))
		wtrueconfs = tuple(wevaluation[x] for x in wtruebels)	# weighted confidences in true beliefs
		
		wfalsebels = tuple(set(wevaluation).difference(truebels))
		wfalseconfs = tuple(wevaluation[x] for x in wfalsebels) # weighted confidences in false beliefs
		
		wavgallbels = avg(wevaluation.values())
	
		wavgtruebels = avg(wtrueconfs)
		wavgfalsebels = avg(wfalseconfs)		
		
		
		out["average_precision_of_algorithms"][ga.name]['weighted'] = {}
	
		out["average_precision_of_algorithms"][ga.name]['weighted']['average belief in true links'] = wavgtruebels
		out["average_precision_of_algorithms"][ga.name]['weighted']['average belief in false links'] = wavgfalsebels
		out["average_precision_of_algorithms"][ga.name]['weighted']['average belief in all links'] = wavgallbels	
		
		regret = 0
		diff = lambda x,y: max(x,y) - min(x,y)

		for belief in ga.evaluation:
			regret += diff(ga.evaluation[belief],knower.evaluation.get(belief,0))
			
		out["average_precision_of_algorithms"][ga.name]['distance_from_perfection==regret?'] = regret
		out["BlackBox"] = BlackBox(god)

	return out
	
def setup_full_god():
	
	print('Setting up a God...')
	
	god = setup_new_god()
	god.spawn_servants()
	tests.load_evaluations_to_gas(god.guardianangels)
	god.express_all()
	
	return god

def avg(itr):
	return sum(itr) / len(itr) if itr else 0

def feedback_only_test(god = None,test = False, filename = 'feedback_only_output'):
	
	if not god:
		god = setup_full_god()
	
	knower = getknower(god)
	
	out = {}
	
	bar = tests.clues.ss.ProgressBar(len(god.logs),title = 'Feedbacking',displaynumbers = True)
	i = 0
	
	def randomized(x):
		import random
		y = list(x)
		random.shuffle(y)
		return y
	
	for log in randomized(god.logs):
		
		bar()
		
		knower.give_feedback(god.logs[log],verbose = False)
		
		pout = evaluate_status(god)
		
		out[i] = pout

		i += 1
		
		if test and test >= i:
			break
			
	return dump_to_file(out,filename)
	
class BlackBox(object):
	"""
	Wrapper for a god's belief set.
	"""
	
	def __init__(self,god):
		
		self.wrap(god)		
		self.godname = str(god)
		knower = getknower(god)
		if not knower.evaluation:
			knower.evaluate_all(express = False)
			
		self.truths = tuple( tests.clues.ss.Link((clouda.item['id'],cloudb.item['id'])) for clouda,cloudb in knower.evaluation)

	def istrue(self,link):
		
		if link in self.truths:
			return True
		
		return False
					
	def __str__(self):
		print( "< BlackBox of {}. >".format(self.godname))
	
	def wrap(self,god):
		
		self.beliefs = {}
		self.stats = {}
		self.logs = {}
		
		for bel,val in god.beliefs.items():
			if not val > 0: # we only store > 0 values
				continue
			link = tests.clues.ss.Link(bel)
			self.beliefs[link.ids] = val
		
		# in self.beliefs, stores a ID,ID -> value
		
		for ga in god.guardianangels:
			self.stats[ga.name] = {item:val for item,val in ga.stats.items()}
			
		# in self.stats, stores a ga.name -> ga.stats copy

		for bel,logs in god.logs.items():
			link = tests.clues.ss.Link(bel)
			self.logs[link.ids] = tuple(tuple((log.agent.name,log.value,log.weightedvalue())) for log in logs)
		
		# in self.logs, stores an ID,ID -> agent, value, weightedvalue for each clue logged
		return
		
	def believes(self,sthg,returnvalue = 0):
		
		return self.beliefs.get(sthg,returnvalue)
	
	def falsebeliefs(self):
		
		for i in self.beliefs:
			if i not in self.truths:
				yield i
				
	def truebeliefs(self):
		
		for i in self.truths:
			if i in self.beliefs:
				yield i
	
	def allbeliefs(self):
		
		for i in self.beliefs:
			yield i
			
class Evaluator(object):
	
	def __init__(self,filename = "./tests_output/evaluation_output.log"):
		"""
		Expected data structure:
		
		dict({
		'1 clues': 	{	'average_precision_of_algorithms' : float(),
						'average_strength_of_god_beliefs': 	float(),
						'BlackBox' : BlackBox() }
		...
		...
		
		'n clues' : {...} })
		
		The BlackBox contains, in a slightly compressed form, god's belief
		state for [n] clues.
		"""
		
		
		import pickle
		with open (filename, 'rb') as f:
			self.raw_data = self.normalize(pickle.load(f))
		
		self.gettruths()
	
	def gettruths(self):
		
		if tests.clues.knower:
			knower = tests.clues.knower
		else:
			knower = getknower(setup_new_god())
			if not knower.evaluation:
				knower.evaluate_all(express = False)
		
		self.knower = knower
		
		for key in self.raw_data:                                                                                  
			bb = self.raw_data[key]['BlackBox']
			truths = tuple( tests.clues.ss.Link((clouda.item['id'],cloudb.item['id'])) for clouda,cloudb in knower.evaluation)
			
			bb.truths = tuple(truth for truth in truths if truth in bb.beliefs)
			
		return
		
	def normalize(self,data):
		"""
		From {'1 cloud': value} to { 1 : value}.
		"""
		
		def tonumber(string):
			
			lst = list(string)
			
			num = ''
			for i in lst:
				if i.isdigit():
					num += i
				elif i == ' ':
					break
					
			return int(num)
			
		normal = { tonumber(key):value for key,value in data.items() }
		return normal
		
	def iter_keys(self):
		"""
		Yields the keys from minimum to maximum number of clouds.
		"""
		
		
		keys = self.raw_data.keys()
		orderedkeys = sorted(keys) # from min to max
		
		for i in orderedkeys:
			yield i
	
	def iter_values(self):
		for key in self.iter_keys():
			yield self.raw_data[key]
	
	def evolution(self,param):
		"""
		Returns a np.array containing the evolution of [parameter] throughout
		the available dataset.
		"""
		
		if isinstance(param[0],str) and '_' in param[0]:
			progression = np.array([ self.raw_data[nclue][param[0]][param[1]] for nclue in self.iter_keys() ])
		
		else:
			progression = np.array( list(self.raw_data[key]['BlackBox'].believes(param) for key in self.iter_keys()) )
			# returns the evolution of the value throughout the god's belief evolution
			
		return progression

	def addtoplot(self,progression,text = None):
		
		lab.plot(progression,label = text)
	
	def multievolution(self,iterator):
		
		for i in iterator:
			evo = self.evolution(i)
			yield evo
	
	def multiplot(self,progressions):
		
		for progression in progressions:
			self.addtoplot(progression)
		
	def show(self):
		
		lab.legend()
		lab.show()
		
	def display(self,iterable):
		"""
		Calls multiplot(multievolution(iterator)):
		that is:
		- retrieves the progression of the values looked for in  the iterator,
		- adds them to the plot
		- calls show()
		"""
		evolutions = self.multievolution(iterable)
		self.multiplot(evolutions)
		self.show()
	
	def display_false(self,fbs = True):
		
		rdic = {}
		
		bar = tests.clues.ss.ProgressBar(len(self.raw_data),title = 'Reading BlackBoxes')
		for outdic in self.iter_values():
			bb = outdic['BlackBox']
			
			bar()
			
			todisplay = bb.falsebeliefs() if fbs else bb.truebeliefs()
			for belief in todisplay:
				if not rdic.get(belief,False):
					rdic[belief] = []
					
				rdic[belief].append(bb.beliefs[belief])
		
		toplen = max( len(x) for x in rdic.values() )
		
		bar = tests.clues.ss.ProgressBar(len(self.raw_data),title = 'Normalizing Results')
		for key in rdic: # normalize all lengths
			
			bar()
			
			if len(rdic[key]) < toplen:
				rdic[key] = [0]*(toplen - len(rdic[key])) + rdic[key]
		
		bar = tests.clues.ss.ProgressBar(len(rdic),title = 'Preparing Plot')
		for listofvalues in rdic.values():
			
			bar()
			
			self.addtoplot(np.array(listofvalues))
		
		print('Plotting...')
		self.show()
		
	def display_true(self):
		
		return self.display_false(fbs = False) # will yield evolutions of true beliefs.
	
	def display_all(self):
		mykeys = tuple(self.iter_keys())
		lastkey = sorted(mykeys,reverse = True)[0]
		bb = self.raw_data[lastkey]['BlackBox']
			
		# the last blackbox will contain all previous ones' beliefs as well!
		
		return self.display(bb.allbeliefs())
		
	def plot_guardian(self,name,param0,param1 = None):
		
		def citer(name,param0,param1):
			
			for key in self.iter_keys():
				if param1 is None:
					yield self.raw_data[key]['average_precision_of_algorithms'][name][param0]
				else:
					yield self.raw_data[key]['average_precision_of_algorithms'][name][param0][param1]
		
		evo = np.array(list(citer(name,param0,param1)))
			
		self.addtoplot(evo,text = name)
	
	def display_guardians(self,names = None,params = ('distance_from_perfection==regret?',)):
		
		if not names:
			key = tuple(self.raw_data.keys())[0]
			names = tuple(self.raw_data[key]['average_precision_of_algorithms'].keys())
		
		if isinstance(names,str):
			names = [names]
		
		for name in names:
			self.plot_guardian(name,*params)
			
		self.show()

	def plot_god_regrets(self,showangels = True):
		
		progression = []
		
		for out in self.iter_values():
			bb = out['BlackBox']
			progression.append(sum(( 1 - bb.believes(x) ) for x in bb.truths))
		
		lab.plot(progression,'b.',label = "God's regrets",linewidth = 2)
		
		if showangels:
			self.plot_ga_regrets(show = False)
			
		self.show()
	
	def plot_ga_regrets(self,show = True):	
		
		progressions = {}
		 
		bar = tests.clues.ss.ProgressBar(len(self.raw_data),title = 'Reading BlackBoxes')
		for out in self.iter_values():
			
			bar()
			
			bb = out['BlackBox']
			
			partial = {}
		
			for log in bb.logs:
				if log in bb.truths:
					# then the regret is relevant
					# the log form is list( (author.name,unweighted,weighted) )
					
					for logged in bb.logs[log]:
						if not partial.get(logged[0]):
							partial[logged[0]] = []
							
						partial[logged[0]] += [logged[2]]
						
			# now partial is a map from ga.names to their weighted evaluation of *true* clues.
			
			for name in partial:
				if not progressions.get(name):
					progressions[name] = []
				
				progressions[name].append(sum( (1-x) for x in partial[name] ))
			
			
		# normalize...
				
		maxlen = max(len(x) for x in progressions.values())
		
		bar = tests.clues.ss.ProgressBar(len(progressions),title = 'Normalizing Values',displaynumbers = True)
		for name in progressions:
			
			bar()
			
			if len(progressions[name]) < maxlen:
				progressions[name] = [0]*(maxlen - len(progressions[name])) + progressions[name]
		
		
		bar = tests.clues.ss.ProgressBar(len(progressions),title = 'Preparing Plots',displaynumbers = True)	
		for name,progression in progressions.items():
			
			bar()
			
			array = np.array(progression)
			self.addtoplot(progression,name)
		
		print('Plotting...')
		
		if show:
			self.show()
		
		return
		
	def plot_relative_tw(self,gas = False,ctypes = False,show = True):
		
		progressions = {}
		
		bar = tests.clues.ss.ProgressBar(len(self.raw_data),title = 'Reading BlackBoxes')
		for out in self.iter_values():
			
			bar()
			
			stats = out['BlackBox'].stats
			
			angels = tuple(stats.keys())
			
			if gas: # if a special list of angels is given, we restrict our results to these.
				angels = [ga for ga in angels if ga in gas]
			
			for angel in angels:
				
				if angel not in progressions:
					progressions[angel] = {}
				
				for ctype,value in stats[angel]['relative_tw'].items():
					
					if ctypes:
						if ctype not in ctypes: # we only take selected ctypes
							continue
					
					if not	progressions[angel].get(ctype):
						progressions[angel][ctype] = []
						
					progressions[angel][ctype].append(value)
					
			# progressions is now
			# angel.name : { 'PP' : [0.1,0.12], 'PO' : [0.22,0.232] ...}		
					
		bar = tests.clues.ss.ProgressBar(len(progressions),title = 'Normalizing Values')
		toplen = max( max(len(x) for x in progressions[angel].values() ) for angel in progressions )
		for angel in progressions:
			
			bar()
			
			for ctype in progressions[angel]:
				progressions[angel][ctype] = [0]*(toplen - len(progressions[angel][ctype])) + progressions[angel][ctype]
		
		
		for angel in progressions:
			
			
			for ctype in progressions[angel]:
				
				array = np.array(progressions[angel][ctype])
			
				self.addtoplot(array,"{}'s {}".format(angel,ctype))
		
		if show:
			self.show()
