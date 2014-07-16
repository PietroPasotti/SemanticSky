
import clues
import random
from itertools import permutations

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


# small tests

def agent_give_random_opinions(agent = None,howmany = 10):
	
	global god
	
	if agent is None:
		agent = clues.Agent('adoin{}'.format(random.choice(['123','124','21332','123dd','12we','544','adv','ader','grer','trerd','ytbgb','frui'])))
	
	prepost = {}
	
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
		
		prepost[about]['post'] = clues.god.believes(about)
		
		prepost[about]['clue.weight'] = randomclue.weightedvalue()
		
	return prepost
		

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


# analysis of god belief state

def compare_god_beliefs_against_actual_links():
	
	global results,god,sky
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
		clues.compared_results[cloud.item['id']]['suggested_links_ranked'] = [ocloud.item['id'] for ocloud in 
											[second_item_of(result) for result in clues.results.get(cloud,[])]
																										]
																										
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


# save & load

def store_belief_set(god = None,nameoffile=None):
	
	time = clues.ss.time.gmtime()
	
	if nameoffile is None:
		nameoffile = 'god_belief_set_{}.log'.format("dmy_{}_{}_{}_s_{}".format(time.tm_mday,time.tm_mon,time.tm_year,tm_sec))
	
	with open(nameoffile,'ab+') as storage:
		
		if god is None:
			G = clues.god
		else:
			G = god
		
		pickle.dump(G,storage)
	
	return True

def load_god(nameoffile = 'mostrecent'):
	
	if nameoffile == 'mostrecent':
		nameoffile = 'god_belief_set_'
		
		date = clues.ss.time.gmtime()
		
		sec = date.tm_sec
		year = date.tm_year
		month = date.tm_mon
		day = date.tm_mday
		
		loopcount = 0
		
		while True:

			nameoffile = 'god_belief_set_{}.log'.format("dmy_{}_{}_{}_s_{}".format(day,month,year,sec))
			
			try:
				doc = open(nameoffile,'rb')
				break
			except IOError:
				pass
				
			sec -= 1
			if sec <= 0:
				sec += -sec
				sec += 60
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
			if loopcount > 10000:
				return False
			pass
				
		
	else:
		doc = open(nameoffile,'rb')
	
	clues.god = clues.pickle.load(doc)
	clues.sky = clues.god.sky
	
	doc.close()
	
	return True

