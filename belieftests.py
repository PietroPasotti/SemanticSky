#!/usr/bin/python3

import tests
import numpy as np
import matplotlib as plt
import pylab as lab
from copy import deepcopy
from tests import pickle,center,wrap,table,bmag,crop_at_nonzero
from semanticsky import stdout,regret

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

def evaluate_online_accuracy_function(	god = None, # a deity. Must be a fresh one!
										test = False, # if test is given (an integer), just up to *test* clouds will be added to god's sky before prematurely halting.
										step = 1, # how many clouds per loop we add back to gods'sky. Dramatically improves runtime and memory usage
										filename = "evaluation_output_FULL",
										updaterule = False, # default is step_by_step_ls: newvalue = (previousvalue + newvalue) / 2
										learningspeed = False, # default is 0.2 (or as defined at clues.learningspeed). Useful only if mergingrule takes learning speed into account!
										mergingrule = False, # default points to learningrate classical merging of previous/new value
										punish_false_negatives = False): 	# if this flag goes true, the knower will give negative feedback also for all the
																			# links that are NOT in his evaluation. This means TONS of (mostly useless) negative feedback.
	
	if learningspeed and isinstance(learningspeed,int):
		tests.clues.learningspeed = learningspeed
	
	if not god:
		god = setup_new_god()
	
	if updaterule:
		set_update_rule(updaterule)
	
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
		pout = add_to_sky_evaluate_feedback(god,clouds,punish_false_negatives = punish_false_negatives) # partial output, which will go to the total final output
		output["{} clues".format(len(god.sky.sky))] = pout
		
		loops += 1
		
		endtime = time.clock()
		
		totloops = test if test else int(len(cloudlist) / step)
		elapsed = round(endtime - initime)
		forecast = elapsed * (totloops - loops)
		
		print('\r'+center('--- [loop {} :: {} elapsed :: {} estimated to the end] ---'.format(loops,elapsed,forecast)))
	
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
		
def add_to_sky_evaluate_feedback(god,listofclouds,punish_false_negatives):
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
	
	# this will prompt the knower to give feedback only on newly created clues
	if punish_false_negatives:	
		knower.give_feedback(newclues) # we give feedback to ALL clues even those which knower has no clue upon:
		# this assumes that knower knows some right answers, but there might be more.
	else:
		knower.give_feedback([clue for clue in newclues if knower.evaluation.get(clue.about)])	
	
	god.refresh()
	# this will ask god for a reevaluation, thus taking into account the feedback, old and new

	return evaluate_status(god)

OUTPUT = {}


def evaluate_status(god):
	
	knower = getknower(god)
	
	out = {}
	
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
	out['god_regrets'] = god.regrets()
	
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
		out["average_precision_of_algorithms"][ga.name]['regrets'] = ga.regrets()
		
	out["BlackBox"] = BlackBox(god)

	return out
	
def setup_full_god(God = None):
	
	print('Setting up a God...')
	
	god = setup_new_god() if not God else God
	god.spawn_servants()
	tests.load_evaluations_to_gas(god.guardianangels)
	god.express_all()
	
	return god

def avg(itr):
	itr = tuple(itr)
	return sum(itr) / len(itr) if itr else 0

def feedback_only_test(	god = None,
						test = False, 
						filename = 'feedback_only_output',
						step = 300, # sampling ratio. We can't store all 21000 steps of the evaluation, so we record the status each *step* loops
						updaterule = False,
						learningspeed = False,
						mergingrule = False,
						punish_false_negatives = False):
		
	if updaterule:
		set_update_rule(updaterule)
	
	if not step:
		step = 1
		
	if learningspeed:
		tests.clues.learningspeed = learningspeed
		
	if mergingrule:
		set_merging_rule(mergingrule)
		
	god = setup_full_god(god)
	knower = getknower(god)
	
	out = {}
	
	i = 0
	
	def randomized(x):
		import random
		y = list(x)
		random.shuffle(y)
		for f in y:
			yield(f)
	
	ln = len(god.logs)
	print()
	
	for log in randomized(god.logs):
		
		i += 1
		u = 0
		lelog = len(god.logs[log])
		for clue in god.logs[log]:
			knower.give_feedback(clue,verbose = False)
			ur = test if test else ln
			u += 1
			print("\rKnower :: Feedback = [[{}/{}] of [{}/{}]]".format(u,lelog,i,ur),' '*30,end = '')
			print(' '*33,end = '')
		
		god.rebelieves(log)

		if i % step == 0: # we will sample each *step* loops the god's status
			print("\rLogging Status...                                                       ",end = '')
			pout = evaluate_status(god)
			out[i] = pout
		
		if test and i >= test:
			break
	
	if not out.get(i):
		finalpout = evaluate_status(god)
		out[i] = finalpout
	
	print()	
	return dump_to_file(out,filename)

def set_update_rule(name):
	
	ur = getattr(tests.clues.updaterules.TWUpdateRule.builtin_update_rules,name)
	tests.clues.default_updaterule = ur
	
	print('\nclues.default_updaterule now points to ' + wrap(name,'brightred'))
	
def set_merging_rule(name):
	
	mr = getattr(tests.clues.updaterules.TWUpdateRule.builtin_mergers,name)
	tests.clues.updaterules.TWUpdateRule.set_merger(mr)

	print('\ntwupdate_rules.MERGER default now points to ' + wrap(name,'brightred'))

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
		Link = tests.clues.ss.Link
		for bel,val in god.beliefs.items():
			if not val > 0: # we only store > 0 values
				continue
			link = Link(bel)
			self.beliefs[Link(link.ids)] = val
		
		# in self.beliefs, stores a ID,ID -> value
		
		for ga in god.guardianangels:
			self.stats[ga.name] = deepcopy(ga.stats)
			
		# in self.stats, stores a ga.name -> ga.stats copy

		for bel,logs in god.logs.items():
			link = tests.clues.ss.Link(bel)
			self.logs[Link(link.ids)] = tuple(tuple((log.agent.name,log.value,log.weightedvalue())) for log in logs)
		
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
	
	def regrets(self):
		return regret(self.beliefs,self.truths)
			
class Evaluator(object):
	
	def __init__(self,filename = "./tests_output/evaluation_output.log"):
		"""
		Can init from pickled or from dict.
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
		
		if isinstance(filename,dict):
			self.raw_data = self.normalize(filename)
			
			bbs = tuple(self.blackboxes())
			if not hasattr(bbs[0],'truths'):
				self.gettruths()
			
			return
		
		import pickle
		with open (filename, 'rb') as f:
			self.raw_data = self.normalize(pickle.load(f))
			
		bbs = tuple(self.blackboxes())
		if not hasattr(bbs[0],'truths'):
			self.gettruths()
		
		return
			
	def gettruths(self):
		
		if tests.clues.knower:
			knower = tests.clues.knower
		else:
			knower = getknower(setup_new_god())
			if not knower.evaluation:
				knower.evaluate_all(express = False)
		
		self.knower = knower
		
		for bb in self.blackboxes():
			truths = tuple( tests.clues.ss.Link((clouda.item['id'],cloudb.item['id'])) for clouda,cloudb in knower.evaluation)
			
			bb.truths = tuple(truth for truth in truths if truth in bb.beliefs)
			
		return
		
	def normalize(self,data):
		"""
		From {'1 cloud': value} to { 1 : value}.
		"""
		
		def tonumber(string):
			
			if isinstance(string,int):
				return string
			
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
	
	def blackboxes(self):
		
		for out in self.iter_values():
			yield out['BlackBox']
	
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
		
		if len(names )> 5:
			names = '{} angels'.format(len(names))
		
		lab.title('display_guardians({},{})'.format(names,params))
		
		self.show()

	def guardian_names(self):
		
		from algorithms import algsbyname
		
		return [name for name in algsbyname if name not in ['someonesuggested','tag_similarity_naive','tag_similarity_extended']]
	
	def plot_ga_regrets(self,show = True,use_stored_values = True):	
		
		if use_stored_values: # we use values filled in at runtime, instead of computing them again
			progressions = {}
			godprog = []
			bar = tests.clues.ss.ProgressBar(len(self.raw_data),title = 'Reading BlackBoxes')
			for out in self.iter_values():
				bar()
				greg = out.get('god_regrets')
				if not greg:
					greg = out['BlackBox'].regrets()
					out['god_regrets'] = greg
					
				godprog.append(greg)
				
				for angel in out["average_precision_of_algorithms"]:
					
					if not angel in progressions:
						progressions[angel] = []
					
					progressions[angel].append( out["average_precision_of_algorithms"][angel]['regrets'] ) # which was filled in at test runtime
			print()
			print("Plotting...                   ",end = '')
			
			for angel,prog in progressions.items():
				lab.plot(prog,label = "{}'s regrets".format(angel))
			
			lab.title('Regrets of GuardianAngels (as logged)')
			lab.plot(godprog,'bD',label = 'God')
			return self.show() if show else None

		# ----------------------------------------------------------------------- #

		progressions = {aname : [] for aname in self.guardian_names()}
		godprog = [] # god's progression
		
		bar = tests.clues.ss.ProgressBar(len(self.raw_data),title = 'Reading BlackBoxes')

		for bb in self.blackboxes():
			
			godprog.append(bb.regrets())
			
			bar()
			
			BELIEFS = {aname : {} for aname in self.guardian_names()}
			
			for belief,loglist in bb.logs.items():
				for log in loglist:
					BELIEFS[log[0]][belief] = log[2] # we set the belief to the WEIGHTED BELIEF!
			
			for angel in BELIEFS:
				progressions[angel].append( regret(BELIEFS[angel],bb.truths) )
		
		for name,progression in progressions.items():
			self.addtoplot(progression,name)
		
		lab.plot(godprog,'b.',label = "god",linewidth = 2)
		lab.title('Regrets of GuardianAngels (computed all over)')
		if show:
			self.show()
		
		return
		
	def plot_relative_tw(self,gas = False,ctypes = False,show = True,legend = False,averaging = True):
		
		progressions = {angel : {} for angel in self.guardian_names()}
		
		bar = tests.clues.ss.ProgressBar(len(self.raw_data),title = 'Reading BlackBoxes')
		for bb in self.blackboxes():
			
			bar()
			
			stats = bb.stats
			
			angels = tuple(stats.keys())
			
			if gas: # if a special list of angels is given, we restrict our results to these.
				angels = [ga for ga in angels if ga in gas]
			
			for angel in angels:
				
				if angel not in progressions:
					progressions[angel] = {}
				
				avvals = avg(stats[angel]['relative_tw'].values())
				
				for ctype,value in stats[angel]['relative_tw'].items():
					
					if ctypes:
						if ctypes == 'expertises': # we only plot the angel's expertises
							if value < avvals: # avvals is average value
								continue
						
						elif ctype not in ctypes: # we only take selected ctypes
							continue
					
					if not	progressions[angel].get(ctype):
						progressions[angel][ctype] = []
						
					progressions[angel][ctype].append(value)
					
			# progressions is now
			# angel.name : { 'PP' : [0.1,0.12], 'PO' : [0.22,0.232] ...}		
					
		bar = tests.clues.ss.ProgressBar(len(progressions),title = 'Normalizing Values')
		try:
			toplen = max( max(len(x) for x in progressions[angel].values() ) for angel in progressions if progressions[angel] )
		except ValueError:
			print("AN ERROR OCCURRED: progressions == ",progressions)
			return
		
		for angel in progressions:
			
			bar()
			
			for ctype in progressions[angel]:
				progressions[angel][ctype] = [0]*(toplen - len(progressions[angel][ctype])) + progressions[angel][ctype]
		
		
		for angel in progressions:

			for ctype in progressions[angel]:
				
				array = np.array(progressions[angel][ctype])
			
				self.addtoplot(array, text = "{}'s {}".format(angel,ctype) if legend else None)
		
		#for angel in progressions:
		#		[lab.plot( p ) for p in progressions[angel].values()]
		#		angelsaverage = [avg(progressions[angel][pprog][i] for pprog in progressions[angel]) for i in range(len( tuple(progressions[angel].values())[0] ))]
		#		lab.plot(angelsaverage,'--',label = "{}'s average tw".format(angel))
		
		if averaging:
			paverages = []
			for angel in progressions:
				paverage = [avg(     pro[i] for pro in progressions[angel].values()  ) for i in range(len( tuple(progressions[angel].values())[0] ))   ]
				paverages.append(paverage)
			
			average = [ avg(paverage[i] for paverage in paverages) for i in range(len(paverages[0]))]
			
			lab.plot(average,'rD',label = 'total average')
			
		lab.title('Progression of Relative trustworthiness')
		if show:
			self.show()

	def plot_ga_average_belief_in_links(self,linktype = True,gas = False,includegod = True, show = True,legend = True):
		
		beliefs = {}
		
		bar = tests.clues.ss.ProgressBar(len(self.raw_data),title = 'Reading BlackBoxes')
		for box in self.blackboxes():
				
			bar()
			
			allbeliefs = {}
			
			for log,cluelist in box.logs.items():
				
				if linktype is True: # we take only true links
					if log not in box.truths: # i.e. those which are in truths
						continue
				elif linktype is False: # we consider only false links
					if log in box.truths: # that is: those which are not in truths
						continue
				elif linktype is None: # go on: take all of them (for linktype == None or any other value)
					pass
				else:
					raise BaseException('Something wrong here.')
				
				# here cluelist is a list of guesses by some algs about something of the desired category
					
				for clue in cluelist:
					name,unweighted,weighted = clue # unpack stored values
					
					if not allbeliefs.get(name):
						allbeliefs[name] = []
						
					allbeliefs[name].append(weighted)
				
				if includegod:
					if not allbeliefs.get('God'):
						allbeliefs['God'] = []
					
					allbeliefs['God'].append(box.beliefs.get(log,avg(clue[2] for clue in cluelist))) # average of weighted ga's
					
			# now allbeliefs stores, by name, a list of belief-values about sthg of the desired category
			
			for name,believeds in allbeliefs.items():
				averaged = avg(believeds)
			
				if not beliefs.get(name):
					beliefs[name] = []
				beliefs[name].append(averaged)
					

				
		bar = tests.clues.ss.ProgressBar(len(beliefs),title = 'Normalizing')
		toplen = max(len(x) for x in beliefs.values())
		for name,values in beliefs.items():
			
			if gas: # if gas is given
				if name not in gas and not (name == 'God' and includegod is True): # and name is not there
					continue # we don't plot it
			
			bar()
			
			prog = [0]*(toplen - len(values)) + values
			array = np.array(prog)
			
			if name == 'God':
			
				lab.plot(array,'ro',label = 'god',)
				continue
				
			self.addtoplot(array,text = name if legend else '')
		
		lab.title('Average belief in {} links'.format(linktype))
		
		if show:
			self.show()
			
		return

	def stats_at_stage(self,stage):
		
		if not stage in self.raw_data:
			
			print('Wrong step. Try with [{}]'.format([d for d in self.raw_data if d in tuple(range(stage -10, stage +10))]))

		return self.raw_data[stage].stats

class MonoEvaluator(Evaluator,object):
	
	def __init__(self,god):
		
		self.god = god
		self.knower = getknower(god)
		self.truths = tuple(self.knower.evaluation)
		
	def belief_in_links(self,truthvalue = True):
		
		for belief in self.god.beliefs:
			value = self.god.beliefs[belief]
			if truthvalue is True:
				if belief in self.truths:
					yield value
			elif truthvalue is False:
				if belief not in self.truths:
					yield value
			else:
				yield value
	
	def plot(self,*args,**kwargs):
		
		return lab.plot(*args,**kwargs)
			
	def plot_average_belief_in_links(self,truthvalue = True,show = False,linestyle = 'bD'):
		
		beliefs = tuple(self.belief_in_links(truthvalue))
		
		avgbelief = avg(beliefs)
		
		self.plot(avgbelief,linestyle)
		
		if show:
			self.show()
		
	def plot_all_beliefs(self,truthvalue = True,show = False,**kwargs):
		
		for belief in self.belief_in_links(truthvalue):
			self.plot(belief,**kwargs)
			
		if show:
			self.show()
		
	def plot_true_against_false(self,truestyle = None,falsestyle = None,show = True):
		
		if truestyle is None:
			truestyle = 'ro'
			
		if falsestyle is None:
			truestyle = 'bD'
			
		self.plot_all_beliefs(True,truestyle)
		self.plot_all_beliefs(False,falsestyle)
		
		if show:
			self.show()	

class RegretsPlotter(object):
	
	def __init__(self,god,evaluator,samplingstep = 5):

		self.evaluator = evaluator
		self.god = god
		self.god.remove_tag_similarity_angels()
		self.samplingstep = samplingstep
		
	def plot_regrets(self,showangels = True,showgod = True,onall = False):
		# if onall goes True, the regrets will also include the (always negative) feedback for what is not in the knower's evaluation
		
		i = 0
		god = self.god
		
		if not hasattr(god,'knower'):
			god.knower = getknower(god)
		
		progressions = {}
		
		bar = tests.clues.ss.ProgressBar(len(self.evaluator.raw_data)/self.samplingstep ,title = 'Reading Plots')
		for bb in self.evaluator.blackboxes():
			
			if i % self.samplingstep != 0:
				i += 1
				continue
			
			bar()
			
			stats = bb.stats
			
			for ga in god.guardianangels: # we load the stats for that instant
				ga.stats = stats[ga.name]
			
			god.refresh(verbose = False)
			print('\r(REFRESHING...)',end = '')
			
			angelsregrets = god.guardians_regrets()
			for ganame,value in angelsregrets.items():
				if not ganame in progressions:
					progressions[ganame] = []
				progressions[ganame].append(value)
				
			godregrets = god.regrets()
			if not 'god' in progressions:
				progressions['god'] = []
				
			progressions['god'].append(godregrets)
			
			i += 1
		
		for name,progression in progressions.items():
			
			if name != 'god' and showangels:
				lab.plot(progression,label = "{}'s regrets".format(name))
			elif name == 'god' and showgod:
				lab.plot(progression,'b--',label = "{}'s regrets".format(name))
		
		lab.title('Regrets for series of weights'.format(linktype))
		lab.legend()
		lab.show()
			
class FeedbackEvaluator(object):
	
	def __init__(self,filename):

		self.data = pickle.load(open(filename,'rb'))
		
	def ordered_keys(self):
		
		keys = list(self.data)
		ordered = sorted(keys)
		for key in ordered:
			yield key
			
		raise StopIteration()
		
	def ordered_data(self):
		
		for num in self.ordered_keys():
			yield self.data[num]
		
		raise StopIteration()
		
	def blackboxes(self):
		
		for pdata in self.ordered_data():
			yield pdata['BlackBox']

		raise StopIteration()

	def plot_trustworthinesses(self):
		
		progressions = {}
		
		for bb in self.blackboxes():
			
			stats = bb.stats
			
			for ga in stats:
				if ga not in progressions:
					progressions[ga] = []
					
				progressions[ga].append(stats[ga]['trustworthiness']) # that is: their 'trustworthiness' value.
		
		average = [avg((pro[x] for pro in progressions.values())) for x in range(len(tuple(progressions.values())[0]))]
		lab.plot(average,'r--',label = 'average')
		
		for ga,progression in progressions.items():
			lab.plot(progression,label = ga)
			
		lab.legend()
		lab.show()
		
	def plot_regrets(self,onall = False):
		
		progressions = {}
		
		god = setup_new_god()
		truths = tuple(getknower(god).evaluation)
		
		for data in self.ordered_data():
			god_regret = data['god_regrets']['onall'] if onall else data['god_regrets']['on_true']
			
			if not progressions.get('god'):
				progressions['god'] = []
			progressions['god'].append(onall_god)
			
			for angel in data['average_precision_of_algorithms']:
				if not progressions.get(angel):
					progressions[angel] = []
					
				progressions[angel].append( data['average_precision_of_algorithms'][angel]['regret_onall'] if onall else data['average_precision_of_algorithms'][angel]['distance_from_perfection==regret?'])
		
		
		
		
		
		
		
		
		
