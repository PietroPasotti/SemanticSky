
import clues
import random
from itertools import permutations
from collections import Counter


"""
Collection of tests to be run on the framework.
"""


# randoms

def randomlink():
	"""
	returns a random pair of clouds.
	"""
	import random
	
	clouda = random.choice(clues.sky.sky)
	cloudb = random.choice([cloud for cloud in clues.sky.sky if cloud is not clouda])
	
	return clues.ss.pair(clouda,cloudb)
	
def randomlinks(top = 1000):
	"""
	flow generator of random pairs of clouds.
	"""	
	
	i = 0
	
	while True:
		i += 1
		pair = randomlink()
		yield pair
		if i >= top:
			raise StopIteration()

def randomactuallink():
	"""
	returns a random pair of clouds such that the pair is in god's current
	belief set.
	"""
	
	return random.choice([ key for key in clues.god.beliefs.keys() if isinstance(key,frozenset) and len(key) == 2 ])

def randomtagcloud():
	"""
	returns a random pair of tag clouds.
	"""
	
	rtag = random.choice(list(clues.sky.data.tags()))
	return clues.sky.get_cloud(rtag)
		
def randomactuallink_tag():
	"""
	returns a random pair of clouds such that the pair is in god's current
	belief set, and that the clouds wrap tags.
	
	Beware: can be empty.
	"""
	
	istaglink = lambda x: isinstance(x[0].item['id'],str) and isinstance(x[1].item['id'],str)
	return random.choice( [ link for link in clues.god.beliefs if istaglink(tuple(link)) ] )


# small tests

def agent_give_random_opinions(agent = None,howmany = 10):
	
	global god
	
	if agent is None:
		agent = clues.Agent('adoin{}'.format(random.choice(['123','124','21332','123dd','12we','544','adv','ader','grer','trerd','ytbgb','frui'])))
	
	prepost = {}
	rclues = []
	
	for i in range(howmany):
		
		about = randomlink()
		value = random.random()
		
		prepost[about] = {}
		prepost[about]['pre'] = clues.god.believes(about)
		
		randomclue = clues.Clue(about, value, agent) # a clue with random value about a random pair of objects
		# autoconsider being on, now the clue (and the whole queue) should be automatically processed
		# anyway...
		if clues.CLUES:
			clues.god.consider()
		
		rclues.append(randomclue)
		
		prepost[about]['post'] = clues.god.believes(about)
		
		prepost[about]['clue.weight'] = randomclue.weightedvalue()
		
	return (prepost,rclues)

def islands():
	"""
	retrieves the clouds which are completely isolated.
	"""
	godsthoughts = set()
	for thought in clues.god.beliefs:
		godsthoughts.update(thought)
		
	return [cloud for cloud in clues.sky.clouds() if cloud not in godsthoughts]
	
def analyse_islands():
	
	analysis = { 	'per_type': Counter(), 
					'avg_length_of_text' : 0, 
					'per_number_of_starfish_links' : Counter(),
					'avg_number_of_starfish_links' : 0,
					'per_type_of_linked_items' : Counter() }
	
	isl = islands()
	
	totlens = 0
	totlinks = 0
	for i in isl:
		analysis['per_type'].update([i.item['type']])
		lentext = len(clues.ss.grab_text(i.item))
		totlens += lentext
		noflinks = len(i.item['links'])
		analysis['per_number_of_starfish_links'].update([noflinks])
		totlinks += noflinks
		for link in i.item['links']:
			try:
				hitem = clues.sky.data.item(link)
				hitype = hitem['type']
			except KeyError:
				hitype = 'Broken Link'
			analysis['per_type_of_linked_items'].update([hitype])	
			
	analysis['avg_length_of_text'] = totlens / len(isl)
	analysis['avg_number_of_starfish_links'] = totlinks / len(isl)
	
	return analysis

def test_algorithm_impact(algorithm):
	"""
	Creates a GuardianAngel on the algorithm and checks various staff
	pre and post its evaluation cycle.
	"""
	
	ga = clues.GuardianAngel(algorithm)

def downertest():
	print('Testing downer...')
	
	if not clues.god:
		lastsetup()
	
	downer = clues.GuardianAngel(lambda x,y: 0.00001) # returns low value for any pair
	downer.makewhisperer()
	
	print('pre:\n')
	print(god.trusts())
	
	downer.evaluate_all()
	
	print('post:\n')
	print(god.trusts())

def interactive_error_analysis():
	
	if not hasattr(clues,'compared_results'):
		compare_god_beliefs_against_actual_links()
		
	cr = clues.compared_results
	errors = ( cloudid for cloudid in cr if set(cr[cloudid]['suggested_links_ranked']) != set(cr[cloudid]['actual_links']) )
	
	def center(string,width = 100,space = ' '):
		ls = len(string)
		sp = (width - ls) // 2
		return sp * space + string + sp * space
	
	print('-'*100 + '\n' + center('Interactive Error Spotter v0.1',100) + '\n' + '-'*100)
	
	
	def gonext():
		nerror = next(errors)
		print('The system made some mistakes while evaluating links for cloud id {}'.format(nerror))
		cloud = clues.sky.get_cloud(nerror)
		print('The cloud wraps the item [{}]\n'.format(cloud.get_header()))
		sugg = clues.compared_results[nerror]['suggested_links_ranked']
		actual = clues.compared_results[nerror]['actual_links']
		print('Predicted links (ranked): [{}]\n'.format(sugg))
		print('Actual links (unsorted): [{}]\n'.format(actual))
		
		ints = set(actual).intersection(set(sugg))
		print('Caught links: [{}]'.format( list(ints) ))
		print('\t (Percent of total: [{}])'.format(len( ints ) / len(set(actual).union(set(sugg)))))
				
		gbels = {} # from link to god belief' in pair (link,nerror)
		for link in ints:
			pair = sky.pair_by_id(link,nerror) # the cloudpair
			bel = god.believes(pair) 
			gbels[link] = bel
			
		print('Confidence ratios (that the item were linked to item [{}]) were:\n'.format(nerror))
		for entry in gbels:
			print('\t\t {} --> {}'.format((entry,nerror),gbels[entry]))
		
		vals = list(gbels.values())
		if vals:
			avg = sum(gbels.values()) / len(gbels.values())
		else:
			avg = 'n/a'
			
		print('\t .. averaging to {}.'.format(avg))
		
		false_positives = set(sugg).difference(set(actual)) # suggested which are not true
		
		if false_positives:
			wavg = sum([god.believes(sky.pair_by_id(t,nerror)) for t in false_positives]) / len(false_positives)
		else:
			wavg = 'n/a'
			
	
		false_negatives = set(actual).difference(set(sugg)) # true links which were not suggested

		
		print('Confidence ratios *on false positives* averaged to {}.'.format(wavg))
		print('\t And they were {}.\n'.format(list(false_positives)))
		print('False negatives were {}.\n'.format(list(false_negatives)))
		
		print()
		
	def moredata():
		print('Nope yet.')
		
	def writeinsult():
		insult = random.choice(['fuck off','bastard','sucker','fucker','motherfucker','idiot','you stink'])
		print(insult)
	
	while True:
		avail = {	'n': gonext,
					'e' : None,
					'm': moredata,
					'f': writeinsult,
					'' : None}
		
		funcs = [gonext,moredata,writeinsult]
		
		print("'n' or Enter: next, 'e':exit, 'm': more analyses, 'f': more functions")
		choice = input(' >>> ')
		print(' chosen "{}"'.format(choice))
		
		if choice in avail:
			out = avail[choice] # call the function
			if out in funcs:
				out()
			elif out is None:
				if out == 'e':
					break
				elif out == '':
					gonext()
			
			
			
	

# setups

def setup_full_sky():
		
	clues.sky = ss.SemanticSky()
	clues.god = God(sky)
	
	clues.god.consult(consider = True,verbose = True) # consults and considers all guardian angels.
	return True

def setup_partial_sky():
	"""
	Sets up a god with only two guardian angels. Shorter; for testing.
	"""
	
	clues.sky = clues.ss.SemanticSky()
	
	clues.god = clues.God(sky)
	clues.god.consult(2,consider = True,verbose = True)
	return True

def consult_actual_links():
	"""
	Sets up a guardian angel to suggest links corresponding to actual links.
	This may be the first step for a backpropagation.
	"""
	
	knower = clues.GuardianAngel(clues.algs.someonesuggested)
	clues.god.consult([knower],consider = True)
	return True

def fastsetup():
	
	global god
	load_sky('plainsky.log')
	global sky
	god = clues.God(sky)
	clues.god = god
	
	god.spawn_servants()
	gas = god.guardianangels
	
	to = gas[6]
	tf = gas[0]
	
	god.consult(to,consider = True)
	god.consult(tf,consider = True)
	
	return True

def lastsetup():
	print('Loading sky... ',' [{}] '.format(load_sky()))
	clues.ss.stdout.write('Loading god... ')
	clues.ss.stdout.flush()
	clues.ss.stdout.write('  [{}] '.format(load_god()))

	
# analysis of god belief state

def fullcompare():
	
	print()
	print('-'*10,' Fullcompare ','-'*10)
	compare_god_beliefs_against_actual_links()
	variousnumbers()
	clean_results()
	evaluate_cleanresults_recall()
	evaluate_cleanresults_naive()
	percent_related_items()
	print()
	print('-' *33)
	return True
	
def compare_god_beliefs_against_actual_links():
	
	clues.results = {} 	# will store god's belief state in this form:
					# Cloud() : [Cloud()].sorted(key = godsbelief that it is linked to the dict_key)
	
	for pair in clues.sky.iter_pairs():
		godsbelief = clues.god.believes(pair)
		
		if not godsbelief > 0:
			continue
			
		a,b = pair
		
		for d in pair:
			if not clues.results.get(d):
				clues.results[d] = []
				
		clues.results[a].append((godsbelief,b)) # belief that b is in a's links
		clues.results[b].append((godsbelief,a)) # belief that a is in b's links
	
	for cloud in clues.results:
		clues.results[cloud].sort(key = lambda x : -x[0]) # we sort it from the most believed (left) to the least (right)
		
	#sky.data.make_links_symmetric()
	
	clues.compared_results = {}
	
	for cloud in clues.sky.clouds():
		links = cloud.item.get('links',[])
		clues.compared_results[cloud.item['id']] = {}
		clues.compared_results[cloud.item['id']]['actual_links'] = links
		
		second_item_of = lambda x : x[1]
		sranked = [ocloud.item['id'] for ocloud in [second_item_of(result) for result in clues.results.get(cloud,[])] ]
		sranked = list(set(sranked))
		clues.compared_results[cloud.item['id']]['suggested_links_ranked'] = sranked
																		
	del clues.results
	
	print('output saved to clues.compared_results')																							
	return True

def clean_results(crop = 10):
	
	try: 
		res = clues.compared_results
	except BaseException:
		return 'Nothing to clean'
	
	clues.cleanresults = {}
	
	for idi in res:
		if res[idi]['suggested_links_ranked'] or res[idi]['actual_links']:
			realcrop = max(crop, ( len( res[idi]['actual_links'] ) + 3 ) )
			clues.cleanresults[idi] = {}
			clues.cleanresults[idi]['suggested_links_ranked'] = res[idi]['suggested_links_ranked'][:realcrop]
			clues.cleanresults[idi]['actual_links'] = res[idi]['actual_links']
	
	print('output saved to clues.cleanresults.')	
	return True	

def evaluate_cleanresults_recall():
	
	evaluation_recall = {}
	
	cleanresults = clues.cleanresults
	
	for result in cleanresults:
		guessed = cleanresults[result]['suggested_links_ranked']
		actual = cleanresults[result]['actual_links']
		
		rec = len(set(cleanresults[result]['suggested_links_ranked']).intersection(set(cleanresults[result]['actual_links']))) / max((1,len(cleanresults[result]['actual_links'])))
		
		evaluation_recall[result] = rec
	
	recall = sum(evaluation_recall.values()) / len(evaluation_recall.values())
	
	clues.recall = recall
	print('recall : ', recall)
	return recall

def evaluate_cleanresults_naive():
	
	evaluation_naive = {}
	cleanresults = clues.cleanresults
	
	tot = 0
	
	for result in cleanresults:
		if set(cleanresults[result]['suggested_links_ranked']).issuperset(set(cleanresults[result]['actual_links'])):
			num = 1
		elif set(cleanresults[result]['suggested_links_ranked']).intersection(set(cleanresults[result]['actual_links'])) != 0:
			num = len(set(cleanresults[result]['suggested_links_ranked']).intersection(set(cleanresults[result]['actual_links']))) /\
								max((min((len(cleanresults[result]['actual_links']),len(cleanresults[result]['suggested_links_ranked']))),1))
		else:
			num = 0
		
		tot += num	
		evaluation_naive[result] = num
	
	avgtot = tot / len(cleanresults.keys())
	
	print('average total naive evaluation: ',avgtot)
	
	clues.evaluation_naive = evaluation_naive
	return avgtot

def percent_related_items():
	
	noflinks = len([ p for p in permutations(clues.sky.sky,2) ])
	
	iterpairs = clues.sky.iter_pairs()
	ap = len([ pair for pair in iterpairs if clues.algs.someonesuggested(*pair) ]) / noflinks
	
	pp = len(clues.god.beliefs) / noflinks
	
	return {'actual_percent': ap, 'predicted_percent': pp}

def variousnumbers():
	god = clues.god
	print('Number of links detected: ',len(god.beliefs))
	
	if not hasattr(god,'allinks'):
		god.allinks = clues.God.allinks
	
	totnolinks = 0
	diffnlinks = 0
	t = 0
	n = 0
	
	for itemid in god.sky.data.items():
		l = len(god.allinks(itemid))
		if l:
			diffnlinks += l
			t += 1
		totnolinks += l
		
		n += 1
		
	for tagid in god.sky.data.tags():
		l = len(god.allinks(itemid))
		if l:
			diffnlinks += l
			t += 1
		totnolinks += l
		n += 1
		
	if n: avgnolinks = totnolinks / n
	else: avgnolinks = 0
	
	if t: avgnolinks_thresh = diffnlinks / t
	else: avgnolinks_thresh = 0
	
	print('  average number of links per cloud: ',avgnolinks)
	print('  average number of links per cloud, if the cloud has at least one: ',avgnolinks_thresh)
	print()
	
	
	redict = Counter()
	uniquec = Counter()
	accuracy = Counter()
	
	for log in god.logs:
		cluelist = god.logs[log]
		agents = [clue.agent.name for clue in cluelist]
		redict.update(agents)
		
		agents = set(agents)
		if len(agents) == 1:
			uniquec.update(agents)
		
		if clues.algs.someonesuggested(log): # if the link was actually suggested...
			for clue in set(cluelist):
				accuracy[clue.agent] += 1
	
	nametoangel = {ga.name: ga for ga in clues.god.guardianangels}
		
	for entry in redict: # name of an algorithm
		a = entry
		b = redict[a]
		c = uniquec[a]
		
		angel = nametoangel[entry]
		d = accuracy[angel]
		weights = [clue.weightedvalue() for clue in angel.clues]
		confidence = sum(weights) / max(len(angel.clues),1)
		minconf = min(weights)
		maxconf = max(weights)
		print(' @Algorithm {}: \n\tspawned a total of {} clues; of which {} were unique. {} of them were accurate (according to starfish links)'.format(a,b,c,d))
		print('\tAverage confidence of algorithm was {}, with min: {} and max: {}. Trustworthiness = {}.'.format(confidence,minconf,maxconf, angel.stats['trustworthiness']))
	
	cluesperpair = 0
	someclue = 0
	somecluelen = 0
	

	for pair in clues.god.logs:
		cluesperpair += len(clues.god.logs[pair])
		
		if len(clues.god.logs[pair]) > 0:
			someclue += 1
			somecluelen += len(clues.god.logs[pair])

	
	if someclue: avgsomeclue = somecluelen / someclue
	else: avgsomeclue = '(n/a)'
		
	print('  Average number of clues per pair: {}.'
	 '\n  Average number of clues if at least one is present: {}'.format(cluesperpair,avgsomeclue))
	print()
	ranks = clues.god.rankcounter()
	for entry in ranks:
		print('\tThere were {} pairs with {} clues.'.format(ranks[entry],entry))
	print()

# long tests

def longtest():
	
	initime = clues.ss.time.clock()
	
	load_sky('plainsky.log')
	global sky
	god = clues.God(sky)
	
	clues.god = god
	
	god.spawn_servants()
	
	global exceptions
	exceptions = []
	for angel in god.guardianangels:
		god.consult([angel],verbose = True,consider = True)
		store_belief_set(god,'tempbeliefset_afterangel_{}.log'.format(angel.name))
		try:
			fullcompare()
		except BaseException as e:
			exceptions.append(e)
			pass
				
	endtime = clues.ss.time.clock()
	elapsed = endtime - initime
	
	if not exceptions:
		print("[ All done. {} clocks elapsed. ]".format(elapsed))
		return None
		
	else:
		print("[ All done. There were some casualties though ({}). {} clocks elapsed. ] ".format(len(exceptions),elapsed))
		return exceptions

# save & load

def store_belief_set(god = None,nameoffile=None):
	
	time = clues.ss.time.gmtime()
	
	if nameoffile is None:
		nameoffile = 'god_belief_set_{}.log'.format("dmy_{}_{}_{}_hms_{}_{}_{}".format(time.tm_mday,time.tm_mon,time.tm_year,time.tm_hour,time.tm_min,time.tm_sec))
	
	with open(nameoffile,'ab+') as storage:
		
		if god is None:
			G = clues.god
		else:
			G = god
		
		G.store_info()
		
		clues.pickle.dump(G,storage)
	
	return True

def load_god(nameoffile = 'mostrecent'):
	
	if nameoffile == 'mostrecent':
		
		date = clues.ss.time.gmtime()
		
		sec = date.tm_sec
		year = date.tm_year
		month = date.tm_mon
		day = date.tm_mday
		hour = date.tm_hour		
		minu = date.tm_min		

		loopcount = 0
		
		while True:

			nameoffile = 'god_belief_set_{}.log'.format("dmy_{}_{}_{}_hms_{}_{}_{}".format(day,month,year,hour,minu,sec))
			
			try:
				doc = open(nameoffile,'rb')
				break
			except IOError:
				pass
				
			sec -= 1
			if sec <= 0:
				sec += -sec
				sec += 60
				minu -= 1
				if minu <=0:
					minu -= minu
					minu += 60
					hour -= 1
					if hour <= 0:
						hour -= hour
						hour += 24
						day -= 1
						if day <= 0:
							day += -day
							day += 31 # the max
							month -= 1
							if month <= 0:
								month += -month
								month += 12
								year -= 1
								if year < 2014:
									return False
							
			loopcount += 1
			if loopcount > 1000000:
				print('max loops hit')
				return False
			pass
				
		
	else:
		doc = open(nameoffile,'rb')
	
	clues.god = clues.pickle.load(doc)
	global god
	god = clues.god
	global sky
	clues.sky = clues.god.sky
	sky = clues.sky
	
	doc.close()
	
	return True

def store_sky(sky = None,nameoffile = None):

	time = clues.ss.time.gmtime()

	if nameoffile is None:
		nameoffile = 'sky_{}.log'.format("dmy_{}_{}_{}_hms_{}_{}_{}".format(time.tm_mday,time.tm_mon,time.tm_year,time.tm_hour,time.tm_min,time.tm_sec))
	
	with open(nameoffile,'ab+') as storage:
		
		if sky is None:
			S = clues.sky
		else:
			S = sky
		
		clues.pickle.dump(S,storage)
	
	return True

def load_sky(nameoffile = None):
		
	if nameoffile is None:

		date = clues.ss.time.gmtime()
		
		sec = date.tm_sec
		minu = date.tm_min
		hour = date.tm_hour
		year = date.tm_year
		month = date.tm_mon
		day = date.tm_mday
		
		
		loopcount = 0
		
		while True:

			nameoffile = 'sky_{}.log'.format("dmy_{}_{}_{}_hms_{}_{}_{}".format(day,month,year,hour,minu,sec))
			
			try:
				doc = open(nameoffile,'rb')
				break
			except IOError:
				pass
				
			sec -= 1
			if sec <= 0:
				sec += -sec
				sec += 60
				minu -= 1
				if minu <=0:
					minu -= minu
					minu += 60
					hour -= 1
					if hour <= 0:
						hour -= hour
						hour += 24
						day -= 1
						if day <= 0:
							day += -day
							day += 31 # the max
							month -= 1
							if month <= 0:
								month += -month
								month += 12
								year -= 1
								if year < 2014:
									return False
							
			loopcount += 1
			if loopcount > 1000000:
				print('max loops hit')
				return False
			pass
				
	else:
		doc = open(nameoffile,'rb')
	
	clues.sky = clues.pickle.load(doc)
	
	global sky
	sky = clues.sky
	
	doc.close()
	
	return True
