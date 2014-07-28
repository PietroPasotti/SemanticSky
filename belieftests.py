#!/usr/bin/python3

import tests
center = tests.center
wrap = tests.wrap
table = tests.table
bmag = tests.bmag
bar = tests.clues.ss.bar
stdout = tests.clues.ss.stdout
crop_at_nonzero = tests.crop_at_nonzero


def binput(msg):
	a = input(bmag('\t>> {}'.format(msg)))
	return a

def confirm(msg):
	if binput('Chosen "{}". Confirm? ') in 'yesYES':
		return True
	else:
		return False

def setup_new_god():
	
	tests.load_sky()
	sky = tests.sky
	
	God = tests.clues.God(sky)
	return God
	
def interactive_setup(god):
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
						if not 0<ini<end or not 0<end<top:
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
	
	if input(bmag('\t>> Do you want to load weights as well? ')) in 'yesYES':
		tests.load_weights_to_gas(god.guardianangels)
		print('\t\t[Loaded.]')
	print()
	print('\t[All ready.]')
	
	print("\tNow the guardians' evaluations will be merged...")
	print('\t\t(aliasing links...)')
	equate_all_links(god,god.guardianangels)
	
	print('\t\tExpressing...')
	express_all(god)
	
	if input(bmag('\t>> Summon the Knower and give feedback? ')) in 'yesYES':
		knower = getknower(god)
		try:
			knower.evaluate_all(express = False)
		except BaseException:
			knower.new_supervisor(god)
			pass
			
		print()
		equate_all_links(god,[knower])	
		if knower not in god.whisperers:
			god.whisperer(knower)
		knower.express()

	print('\t\t[Done.]')
	
	if input(bmag('\t>> Display trusts? ')) in 'yesYES':
		god.trusts(god.guardianangels,local = False)
	
	print(wrap('...exiting interactive environment.','red'))
	return god
	
def express_all(god):
	
	for ga in god.guardianangels:
		ga.express()

def getknower(god):
	
	return tests.clues.knower if tests.clues.knower else tests.clues.Knower(god)

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
		print('\t\t\tAliasing links for ',ga)
		print()
		i = 0
		for link,ev in ga.evaluation.items():
			del ga.evaluation[link]
			itlinks = pid(link)
			truelink = god.sky.pair_by_id(*itlinks)

			ga.evaluation[truelink] = ev
			
			bar(i/totln)
			i+=1			
		print()
		
	return True

def similarity_picker(god):
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
		uname = binput('Choose your username: ')
		
		if not uname:
			print('\tCome on...')
			continue
		
		try:
			agent = tests.clues.Agent(uname,god) #name and supervisor
			if binput('Chosen "{}".'.format(uname)) in 'yesYES':
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

	def evaluate_similarity():
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
		
		godbels = god.believes(curpair)
		print('\tGod believes the link with {} confidence.'.format(godbels))
		
		ctype = tests.clues.ss.ctype(curpair)
		for ga in god.guardianangels:
			
			conf = ga.evaluate(curpair,silent = True) # should return the confidence, and not spawn anything!
			print('\t',ga,' believes the link with {} confidence.'.format(crop_at_nonzero(conf,4)))
			
			weight = crop_at_nonzero(ga.reltrust(ctype),4)
			
			if weight:
				weightedworth = crop_at_nonzero(weight * conf,4)
					
				print('\this weight for this type of links is {}; which makes his weighted decision worth {}.'.format(weight,weightedworth))
			
			print()
		
			
	def much_more_info():	
		global curpair
		print()
	
	while True:
		options = {	'n' : (pick_random_link,'random link'),
					'm' : (pick_random_actual_link,	'pick a random link | god has some doubt about it'),
					'c' : (choose_a_link_yourself,	'choose a link by id'),
					'b' : ('exit','exit')}
						
		if curpair:
			
			print('\tCurrently focused: {}.'.format(wrap("[{}]".format(set(curpair)),'white')))
			
			options.update({	'e'		: (evaluate_similarity,'give your rating'),
								'i'		: (more_info,'more info about the link'),
								'I'  	: (much_more_info,'a lot more info')})
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
	
	return god,curpair
	
def interactive(god = None):
	print()	
	if not god:
		print('Setting up a fresh god...')
		god = setup_new_god()
		print()
	print()
	print('Initializing interactive setupper...')
	print()
	interactive_setup(god)
	print()
	print('Initializing interactive similarity_picker...')
	print()
	out = similarity_picker(god)
	print()
	
	global GOD
	GOD = god
	print('exiting... (god stored in the global GOD)')
	
	return out
