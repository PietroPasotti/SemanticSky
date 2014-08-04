#!/usr/bin/python3

import tests
pickle = tests.pickle
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

def evaluate_online_accuracy_function(god,test = False,step = 1,store_subsequent_evaluations = True):
	
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
	
	equate_all_links(god,god.guardianangels)
	equate_all_links(god,[knower])
	
	god.sky.sky = [] # we empty the sky. We are then going to add back the clouds one by one.
	
	loops = 0
	while cloudlist:
		clouds = cloudlist[0:min(step,len(cloudlist))]
		
		if len(clouds) < step or len(cloudlist) == 0:
			break
			
		if test and loops > test:
			print('\n')
			print(loops, ' loops hit. Stopping. Total list of clouds already included follows: \n\n ', [cloud.item['id'] for cloud in god.sky.sky])
			break
		
		print('\nExtracted clouds [{}]. Now the sky contains {} clouds.'.format([acloud.item['id'] for acloud in clouds ],len(god.sky.sky) + len(clouds)))
		
		cloudlist = cloudlist[step:]
		add_to_sky_evaluate_feedback(god,clouds)
		
		# we store the beliefs in a more compressed form: from (ID,ID) pairs to god's beliefs.
		dump_to_file((god,god.trusts()))
		
		loops += 1
		
	return 

def dump_to_file(val):
	
	path = "./tests_output/"
	
	filename = path + str(len(val[0].sky.sky)) + '-clouds.log'
	
	god,trusts = val
	
	compressedbeliefs = {(tuple(pair)[0].item['id'],tuple(pair)[1].item['id']): god.beliefs[pair] for pair in  god.beliefs}
	compressedtrusts = {ga.name : trusts[ga] for ga in trusts}
	
	with open(filename,'wb+') as f:
		pickle.dump((compressedbeliefs,compressedtrusts),f)
		
	#print("Dumped to file {}.".format(filename))
	return True
		
def add_to_sky_evaluate_feedback(god,listofclouds):
	"""
	- Adds listofclouds to gods' sky;
	- Retrieves the iter_pairs of the sky and tells the guardianangels to evaluate
	the newly available pairs.
	- The knower gives feedback and updates the guardianangels' trustworthiness
	"""
	
	god.sky.sky.extend(listofclouds)
	
	iterpairs = tuple(god.sky.iter_pairs()) # will yield all 2-permutations of the clouds which are in the system
	
	print('Parsing [{}] pairs...'.format(len(iterpairs)**2 - len(iterpairs)))	
	i = 0
	for pair in iterpairs:
		i += 1
		bar(i/len(iterpairs))
		for cloud in listofclouds:
			if cloud in pair and pair not in god.beliefs:
				god.rebelieves(pair,weight = True,update = True,silent = False) 	# if nonzero, this will be stored in god.beliefs
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
	
	print('God has [{}] beliefs.'.format(len(god.beliefs)))
	
	knower = getknower(god)
	
	newclues = []
	for pair in god.logs:
		clouda,cloudb = pair
		if clouda in listofclouds or cloudb in listofclouds:
			newclues.extend(god.logs[pair])
			# a clue is 'new' iff either of its 'about' clouds is new
	
	knower.give_feedback(newclues)
			# this will prompt the knower to give feedback only on newly created clues.
	
	god.refresh()
	# this will ask god for a reevaluation, thus taking into account the feedback, old and new	
	return
	
