import clues
import random
from itertools import permutations
from collections import Counter
import pickle

someonesuggested = clues.algs.Algorithm.builtin_algs.someonesuggested

god = None
sky = None
knower = None

# compatibility
clues.algs.localize()


"""
Collection of tests to be run on the framework.
"""

# Utilities

def currentgod():
	global god
	print('God is ',god)
	
	if god is None:
		return

	print('\nand his birthdate is: ',god.birthdate)
	print('\nhis consultations registry is: ',god.consultations_registry())
	
class color:
	
	brightblue = 	"\033[1;34;40m"
	white = 		"\033[1;37;40m"
	black_bg   = 	"\033[0;30;47m"      
	black   = 		"\033[0;30;40m"      
	darkgray = 		"\033[1;30;40m"
	red_bg =  		"\033[0;31;47m"
	red = 	 		"\033[0;31;40m"
	brightred = 	"\033[1;31;40m" 
	green_bg = 		"\033[0;32;47m" 
	green = 		"\033[0;32;40m" 
	brightgreen = 	"\033[1;32;40m" 
	brown_bg = 		"\033[0;33;47m"
	brown = 		"\033[0;33;40m"
	yellow = 		"\033[1;33;40m"
	blue_bg = 		"\033[0;34;47m"
	blue = 			"\033[0;34;40m"
	magenta_bg = 	"\033[0;35;47m"
	magenta = 		"\033[0;35;40m"
	brightmagenta = "\033[1;35;40m"
	cyan_bg = 		"\033[0;36;47m"
	cyan = 			"\033[0;36;40m"
	brightcyan = 	"\033[1;36;40m"
	lightgrey_bg = 	"\033[0;37;40m" 
	lightgrey = 	"\033[0;37;40m" 
	white = 		"\033[1;37;40m"
	underline_bg = 	"\033[0;4;37;40m"
	underline = 	"\033[0;4;30;40m"
	end =  			"\033[0m"
	
def wrap(string,col):
	if hasattr(color,col):
		try:
			colorcode = getattr(color,col)
			return colorcode + string + color.end
		except BaseException:
			print('ERROR:',col)
			return ''

clues.wrap = wrap # makes it available there.
		
def blue(string):
	return wrap(string,'brightblue')

def red(string):
	return wrap(string,'red')

def underline(string):
	return wrap(string,'underline')
	
def table(lines,maxwidth = 100,maxheight = None,spacing = 1,index = '>'):
	"""
	Given an input of type list(list(str())), tries to organize it into a
	nice row/column way.
	
	e.g. [[1,21,3],[30,4,444]] becomes 
	
	1,  21, 3
	30, 4,  444
	
	"""
	
	# we uniform it:
	for i in range(len(lines)):
		while len(lines[i]) < max(len(row) for row in lines):
			lines[i].append('')
	
	cwidth = lambda x: max(len(str(column)) for column in [lines[u][x] for u in range( len(lines) ) ]  )
	# returns the width of the column such that all squares fit into it
	
	for i in range(len(lines)):
		for u in range(len(lines[i])):
			content = str(lines[i][u]) # the content of the box
			content += ' '*(cwidth(u) - len(content))
			lines[i][u] = content
	
	for i in range(len(lines)):
		
		for column in lines[i]:
			
			if column.strip(): # if not all's whitespace
				toprint = wrap(index,'red') + str(column) + ' '*spacing
			else:
				toprint = ' '*spacing + str(column)
			clues.ss.stdout.write(toprint)
		
		clues.ss.stdout.write('\n')
		clues.ss.stdout.flush()
		
def center(string,width = 100,space = ' '):
	ls = len(string)
	sp = (width - ls) // 2
	return sp * space + string + sp * space

def cropfloat(fl,no = 4):
	return float(str(fl)[:no])

def crop_at_nonzero(fl,bot = 2):
	sfl = str(fl)
	
	out = ''
	nonzero = 0
	
	for digit in sfl:
		if digit.isdigit() and int(digit) > 0:
			nonzero += 1
		
		out += digit
		
		if nonzero != 0 and nonzero != bot:
			nonzero += 1 # we want no-1 digits after the first nonzero, not results like 0.0200000000000005, if we want 2 nonzero digits
		
		if nonzero == bot:
			return float(out)
			
	return fl


# randomizers

def randomcloud():
	return random.choice(sky.sky)

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
	Creates a GuardianAngel on the algorithm and checks various stuff
	pre and post its evaluation cycle.
	"""
	
	print(center('> Testing impact of algorithm {} <'.format(algorithm.__name__),space = '-'))

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
					
# setups

def setup_full():
	
	print('hold comfy... this will take a long while.')
		
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
	
	knower = clues.GuardianAngel(someonesuggested,ghost = True)
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
	
	print('Loading evaluations of guardianangels...')
	load_evaluations_to_gas(gas,'./guardianangels/evaluations/')
	
	equate_all_links() # Equates all links! otherwise the evaluations won't match
	
	for ga in gas:
		print(ga,' is expressing its feelings...')
		ga.express()
	
	global knower
	knower = clues.Knower()
	
	return True

def lastsetup():
	print('Loading sky... ',' [{}] '.format(load_sky()))
	clues.ss.stdout.write('Loading god... ')
	clues.ss.stdout.flush()
	clues.ss.stdout.write('  [{}] '.format(load_god()))

def knowersetup():
	
	if not god:
		
		try:
			load_god()
		except AttributeError:
			clues.algs.localize()
			load_god()
	
	global knower
	knower = clues.Knower()	
	knower.evaluate_all()
	
	god.trusts()
	


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
	morenumbers()
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
		
		sranked.sort(key = lambda x : god.believes(sky.pair_by_id(x,cloud.item['id'])) )
		
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
	
	recall = sum(evaluation_recall.values()) / len(tuple( evaluation_recall[result] for result in evaluation_recall if cleanresults[result]['actual_links']))
	# we count, for recall purposes, only those items which HAVE some links!
	
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
	ap = len([ pair for pair in iterpairs if someonesuggested(*pair) ]) / noflinks
	
	pp = len(clues.god.beliefs) / noflinks
	
	return {'actual_percent': ap, 'predicted_percent': pp}

def variousnumbers():
	god = clues.god
	
	global knower
	
	if not knower:
		print( '(creating the Knower...)')
		knower = clues.GuardianAngel(someonesuggested,ghost = True)
		knower.evaluate_all(express = False)
		print()
		
	if not len(knower.evaluation):
		knower.evaluate_all(express = False)
	
	print('Number of links detected: ',len(god.beliefs),' versus {} (valid) links currently existing in starfish.'.format(len(knower.evaluation)))
	
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
		
		if not clues.ss.ispair(log):
			continue
		
		cluelist = god.logs[log]
		agents = [clue.agent.name for clue in cluelist]
		redict.update(agents)
		
		agents = set(agents)
		if len(agents) == 1:
			uniquec.update(agents)
		
		if someonesuggested(log): # if the link was actually suggested...
			for clue in set(cluelist):
				accuracy[clue.agent] += 1
	
	nametoangel = {ga.name: ga for ga in clues.god.guardianangels}
		
	for entry in redict: # name of an algorithm
		a = entry
		b = redict[a]
		c = uniquec[a]
		
		if entry == 'someonesuggested':
			continue
		angel = nametoangel[entry]
		d = accuracy[angel]
		weights = [clue.weightedvalue() for clue in angel.clues]
		confidence = sum(weights) / max(len(angel.clues),1)
		minconf = min(weights)
		maxconf = max(weights)
		perc = str(d / b)
		if len(perc) > 4:
			perc = perc[:4]
			
		avconf_corr = 0
		corrclues = [clue.weightedvalue() for clue in angel.clues if someonesuggested(clue.about)]
		avconf_corr = sum(corrclues) / len(corrclues) if corrclues else 'n/a'
			
		print(' @Algorithm {}: \n\tspawned a total of {} clues; of which {} were unique. {} of them were accurate (according to starfish links) ( {} %)'.format(a,b,c,d,perc))
		print('\tAverage confidence of algorithm was {}, with min: {} and max: {}. '
		'\n\tAverage confidence on accurate clues: {}'
		'\n\tTrustworthiness = {}.'.format(confidence,minconf,maxconf, avconf_corr, angel.stats['trustworthiness']))
	
	cluesperpair = 0 # total number of clues
	corclues = 0 # number of clues in favour of correct links
	corspotted = 0 # number of correct links believed to some extent by god
	
	nologs_to_nopairs = Counter()
	nologs_to_nopairs_if_correct = Counter()
	
	for pair in clues.god.logs:
		
		if not clues.ss.ispair(pair):
			continue
		
		lenlog = len(clues.god.logs[pair])
		cluesperpair += lenlog
		if someonesuggested(pair):
			corspotted += 1
			corclues += lenlog
		
		nologs_to_nopairs[lenlog] += 1
		if pair in knower.evaluation:
			nologs_to_nopairs_if_correct[lenlog] += 1
		

	totnoclues = cluesperpair / len(god.logs) # average number of clues per log
	totcorclues = corclues / corspotted if corspotted else 'n/a' # average number of clues per link if link is correct 
	
	print('  Average number of clues per pair: {}.'.format(totnoclues))
	print('  Average number of clues per actually-linked-pair: {}'.format(totcorclues))
	
	avgconf = sum(god.believes(x) for x in knower.evaluation) / len(knower.evaluation)
	print('  Average final confidence in actually existing links: {}'.format(avgconf))
	print()
	ranks = clues.god.rankcounter()
	for entry in ranks:
		correct = nologs_to_nopairs_if_correct[entry] # number of correct links with (entry) number of logged clues
		pcorrect = cropfloat(correct/ranks[entry],5) if correct else 0
		
		# entry = number of clues
		allconfs = tuple(god.believes(pair) for pair in god.logs.keys() if len(god.logs[pair]) == entry and clues.ss.ispair(pair))
		avgconfs = crop_at_nonzero(sum(allconfs) / len(allconfs),3) if allconfs else 'n/a'
		
		print('\tThere were {} pairs with {} clues. \tOf them, {} were actually correct. \t({}%) \t [ average confidence: {} ]'.format(ranks[entry],entry,correct,pcorrect,avgconfs))
	print()

def find_duplicates(vb=False):
	"""
	Prints 'err' whenever it finds a duplicate in gods' logs: an agent's name
	should never be twice in some log's cluelist.
	"""
	for log in god.logs:
		names = tuple(clue.agent.name for clue in god.logs[log])

		if len(set(names)) != len(names):
			duplicates = Counter(names)

			for name in duplicates:
				if duplicates[name] > 1:
					print('ERROR: log {}; agent {} is logged {} times.'.format(clue,name,duplicates[name]))	
		if vb:
			print(names)

def morenumbers():
	nontagclouds = tuple( cloud for cloud in clues.sky.clouds() if cloud.cloudtype != 'tags')
	
	print(' - we are not going to consider tag clouds at this stage -')
	print('Number of nontag clouds: ',(len(nontagclouds)))
	
	nntpairs = god.sky.iter_pairs(nontagclouds) # yields permutations of nontagclouds
	
	allnntpairs = tuple(nntpairs)
	totcomb = tuple(god.believes(pair) for pair in allnntpairs)
	avgtotcomb = sum(totcomb) / len(totcomb)
	
	avgsome = sum(totcomb) / len(tuple( val for val in totcomb if val > 0 )) # only divide by nonzero ones	
	
	global knower
	if knower is None:
		print('Loading knower...')
		knower = clues.GuardianAngel(someonesuggested,ghost = True)
		knower.evaluate_all(express = False)	
	
	truepairs = tuple(pair for pair in god.sky.iter_pairs(nontagclouds) if knower.evaluation.get(pair))
	tottrue = tuple(god.believes(pair) for pair in truepairs)
	avgtruecomb = sum(tottrue) / len(tottrue)
	
	print("\nGod's average belief on all their possible combinations: {}".format(crop_at_nonzero(avgtotcomb,4)))
	print("God's average belief on the nonzero ones (i.e. if some angel has clue'd about them): ", crop_at_nonzero(avgsome,4)  )
	print("God's average belief on the actual (Starfish) ones: {}".format(crop_at_nonzero(avgtruecomb,4)))
	
	responsibles = Counter()
	for true in truepairs:
		agents = [clue.agent for clue in god.logs.get(true,[])]
		responsibles.update(agents)
		
	print('Responsibilities are as follow:')
	print('[The weighted/unweighted gap can be used as a measure of the feedback effect.]\n')
	for agent in responsibles:
		avgtrueconf = tuple(clue.value for clue in agent.clues if clue.about in truepairs)
		totavgtrueconf = sum(avgtrueconf) / len(avgtrueconf) # average unweighted confidence on true
		evaluation = tuple(agent.evaluation.values())
		totavgconf = sum(evaluation) / len(evaluation) #... and on every link
		
		weightedtrueconf = tuple(clue.weightedvalue()for clue in agent.clues if clue.about in truepairs )
		avgweightedtrueconf = sum(weightedtrueconf) / len(weightedtrueconf) # average weighted confidence on true links
		totweightedconf = tuple(clue.weightedvalue()for clue in agent.clues )
		avgtotweightedconf = sum(totweightedconf) / len(totweightedconf) # average weighted confidence on all links
		
		values = (blue(agent.name),responsibles[agent],len(agent.clues),crop_at_nonzero((responsibles[agent] / len(agent.clues)),4),crop_at_nonzero(totavgtrueconf,4),crop_at_nonzero(totavgconf,4), crop_at_nonzero(avgweightedtrueconf,4), crop_at_nonzero(avgtotweightedconf,4))
		print('\tAgent {} spawned {} correct clues (against {} total clues spawned: {}%),\n\ttheir average confidence was {}, (overall confidence averaged to {}),\n\tonce weighted: {} (against {} total).\n'.format(*values))

def interactive_error_analysis():
	
	if not hasattr(clues,'compared_results'):
		compare_god_beliefs_against_actual_links()
		
	cr = clues.compared_results
	errors = ( cloudid for cloudid in cr if set(cr[cloudid]['suggested_links_ranked']) != set(cr[cloudid]['actual_links']) )
	reddned = wrap('Interactive Error Spotter v0.1','brightred')
	print('-'*100 + '\n' + center(reddned,100) + '\n' + '-'*100)
	
	global CURERROR
	CURERROR = None
	
	def gonext():
		nerror = next(errors)
		global CURERROR
		CURERROR = nerror
		cloud = clues.sky.get_cloud(nerror)
		
		print('The system made some mistakes while evaluating links for cloud id [{}], that is: [{}].'.format(nerror,cloud.get_header()))
		sugg = clues.compared_results[nerror]['suggested_links_ranked']
		actual = clues.compared_results[nerror]['actual_links']
		
		
		
		print('Predicted links (ranked): {}\n'.format(sugg))
		print('Actual links (unsorted): {}\n'.format(actual))
		
		ints = set(actual).intersection(set(sugg))
		print('Caught links: [{}]'.format( list(ints) ))
		print('\t (Accuracy: [{}])'.format(len( ints ) / len(set(actual).union(set(sugg)))))
		
		try:
			print('\t (Recall: [{}])'.format(  len( ints.intersection(set(actual)) ) / len(ints) ))
		except ZeroDivisionError:
			print('(Nothing to recall.)')
			
		print()
		print(center(' CONFIDENCE RATIOS BY ALGORITHM '))
		
		gbels = {} # from link (int) to god belief' in the pair (link,nerror)
		for link in ints:
			pair = sky.pair_by_id(link,nerror) # the cloudpair
			bel = god.believes(pair) 
			bel = float(str(bel)[:4])
			gbels[link] = bel
			
		print('Confidence ratios (on wrong links containing item [{}]) *and responsibles* are:\n'.format(nerror))
		for entry in gbels:
			
			logs = god.logs[ sky.pair_by_id(entry,nerror) ]
			if not logs:
				print(entry,nerror,'FUCK',sky.pair_by_id(entry,nerror), sky.pair_by_id(entry,nerror) in god.beliefs,sky.pair_by_id(entry,nerror) in god.logs )
				return
			
			agents = set(log.agent for log in logs)
			
			responsibles = ', '.join([agent.name for agent in agents])
			
			print('\t\t {} --> {}\t\t [{}]'.format((entry,nerror),gbels[entry],responsibles))
		
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
	
	def moredata():
		print()
		print(center('> more data <',100,'-'))
		print()
		global CURERROR
		error = CURERROR
		
		cloud = clues.sky.get_cloud(error)
		
		sugg = clues.compared_results[error]['suggested_links_ranked']
		actual = clues.compared_results[error]['actual_links']		
		
		missed = set(actual).difference(set(sugg)) # false negatives
		caught = set(actual).intersection(set(sugg)) # right
		excess = set(sugg).difference(set(actual)) # false positives
		
		cmissed = tuple(sky.get_cloud(cid) for cid in missed)
		ccaught = tuple(sky.get_cloud(cid) for cid in caught)
		cexcess = tuple(sky.get_cloud(cid) for cid in excess)
		
		m = Counter(cid.item['type'] for cid in cmissed)
		c = Counter(cid.item['type'] for cid in ccaught)
		e = Counter(cid.item['type'] for cid in cexcess)
		
		print('By type: ')
		for counter in [(m,'false negatives'),(c,'correct links'),(e,'false positives')]:
			if not counter[0]:
				continue
			print('\t [{}] links by type:'.format(counter[1]))
			print('\t\t    ',counter[0])
		
		gt = clues.ss.grab_text
		erritem = sky.data.item(error)
		lerror = len(gt(erritem,list(erritem.keys())))
		
		em = tuple(len(gt(cloud.item,list(cloud.item.keys()))) for cloud in cmissed)
		ec = tuple(len(gt(cloud.item,list(cloud.item.keys()))) for cloud in ccaught)
		ee = tuple(len(gt(cloud.item,list(cloud.item.keys()))) for cloud in cexcess)
		
		print('By approximate quantity of text: ')
		print('\t ( item {} had {} characters of text )'.format(error,lerror))
		print()
		for count in [(em,'false negatives'),(ec,'correct links'),(ee,'false positives')]:
			
			print('\t for [{}]:'.format(count[1]))
			
			if not count[0]:
				print('\t\t Nothing to report.')
				continue
			
			if count[0]:
				avg = sum(count[0])/len(count[0])
				print('\t\t average: {}'.format(avg))
			
			def approx(num,steps = [10,100,500,1000,1500,2000,2500,3000,3500,4000,5000,8000,10000],numeric = False,upperbound = False):
				
				if num < min(steps):
					if upperbound: return min(steps)
					if numeric: return (0,num,min(steps))
					return '{} < {} (min)'.format(num,min(steps))
				
				if num > max(steps):
					if upperbound: return max(steps)
					if numeric: return (steps[len(steps)-2],num,max(steps))
					return '{} > {} (max)'.format(num,max(steps))
					
				prestep = 0
				for step in steps:
					
					if num <= step:
						if upperbound: return step
						if numeric: return (prestep,num,step)
						return '{} < {} < {}'.format(prestep,num,step)
					
					prestep -= prestep
					prestep += step
					
				raise BaseException("Shouldn't reach this.")
			
			upperbounds = Counter(approx(lencount,upperbound = True) for lencount in count[0])
			
			print("\t\t length of text // number of items:")
			print()
			for ub in upperbounds.most_common(): # [(key,value)]
				print("\t\t\t >> {} items had less than {} characters.".format(ub[1],ub[0]))
		
		print()
		print(center(' MAIN RESPONSIBLES FOR FALSE POSITIVES '))
		
		sugg = clues.compared_results[error]['suggested_links_ranked']
		actual = clues.compared_results[error]['actual_links']
		
		reportdict = {'false positive': {}} # false positives and false negatives
		falsepos = set(sugg).difference(set(actual))
		
		for i in falsepos: # these are all false positives for this error! That is: all other cloud IDs who ever were wrongly paired with error.
			
			# agents who clue'd on (i,error) link
			
			link = sky.pair_by_id(i,error)
			cluelist = god.logs.get(link)

			agnames = tuple(clue.agent.name for clue in cluelist)
		
			for agent in agnames:
				if agent in reportdict['false positive']:
					errtimes = reportdict['false positive'][agent][0] # agent clue'd one time on a wrong link of that category
				else:
					errtimes = 0
					
				errtimes += 1
				
				hisclues = [clue for clue in cluelist if clue.agent.name == agent]
				hisclue = hisclues[0]
				value = hisclue.value
				
				if agent in reportdict['false positive']:
					preavg = reportdict['false positive'][agent][1]
					avg = (preavg + value) / 2
				else:
					avg = value
					
				reportdict['false positive'][agent] = (errtimes,avg) # number of times agent mistaked, average confidence in his mistakes
					
		print()
		for i in reportdict['false positive']:	
			print("\tAgent {} clue'd {} times; with an avg confidence (unweighted) of {}."
			"".format(i,reportdict['false positive'][i][0],crop_at_nonzero(reportdict['false positive'][i][1])))
		
	### Main Loop
	
	while True:
		avail = {	'n': gonext,
					'e' : None,
					'm': moredata,
					'F': fullcompare,
					'M': morenumbers,
					'' : None}

		print()
		print("'n' or Enter: next, 'e':exit, 'm': more data, 'F': full compare (unspecific), 'M': more numbers")
		print()
		
		choice = input(' :) ')
		choice = choice.strip()
		print(center(wrap(' chosen "{}" ','yellow').format(choice),100,space = wrap('-','brightcyan')))
		print()
		
		if choice in avail:
			out = avail[choice] 
			if hasattr(out,'__call__'):
				out() # call the function
			else:
				if choice == 'e':
					print()
					print(wrap('exiting','brightblue'))
					print()
					break
				elif choice == '':
					print(center(wrap('building report for next item... ','brightblue')))
					print(center('',space = '-'))
					gonext()

def thresholded_accuracy_recall(thresh = 0.5):
	
	predictedlinks = tuple(i for i in god.beliefs if god.believes(i) >= thresh)
	
	avgconf = 0
	for i in predictedlinks:
		avgconf = (avgconf + god.believes(i)) / 2
	
	# recall = (relevant \cap retrieved) / relevant
	recall 			= len(set(predictedlinks).intersection(set(knower.evaluation.keys()))) / len(knower.evaluation.keys())
	# precision  = (relevant \cap retrieved) / retrieved
	precision 		= len(set(predictedlinks).intersection(set(knower.evaluation.keys()))) / len(predictedlinks)
	
	table( [ ['precision',precision],['recall',recall] ] )
	
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
		nameoffile = './gods/god_belief_set_{}.log'.format("dmy_{}_{}_{}_hms_{}_{}_{}".format(time.tm_mday,time.tm_mon,time.tm_year,time.tm_hour,time.tm_min,time.tm_sec))
	
	with open(nameoffile,'ab+') as storage:
		
		if god is None:
			G = clues.god
		else:
			G = god
		
		G.store_info()
		
		clues.pickle.dump(G,storage)
	
	print('God pickled to {}.'.format(nameoffile))
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

			nameoffile = './gods/god_belief_set_{}.log'.format("dmy_{}_{}_{}_hms_{}_{}_{}".format(day,month,year,hour,minu,sec))
			
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
	
	print('Loading god from {}.'.format(nameoffile))
	
	clues.algs.localize()
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
		nameoffile = './gods/sky_{}.log'.format("dmy_{}_{}_{}_hms_{}_{}_{}".format(time.tm_mday,time.tm_mon,time.tm_year,time.tm_hour,time.tm_min,time.tm_sec))
	
	with open(nameoffile,'ab+') as storage:
		
		if sky is None:
			S = clues.sky
		else:
			S = sky
		
		clues.pickle.dump(S,storage)
	
	print('Sky pickled to {}.'.format(nameoffile))
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

			nameoffile = './gods/sky_{}.log'.format("dmy_{}_{}_{}_hms_{}_{}_{}".format(day,month,year,hour,minu,sec))
			
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
	
	print('Loading Sky from {}...'.format(nameoffile))
	clues.sky = clues.pickle.load(doc)
	
	global sky
	sky = clues.sky
	
	doc.close()
	
	
	return True

def makeglobal(deity):
	
	print('Now clues.god, tests.god point to {}'.format(deity))
	print(' and clues.sky, tests.sky point to {}'.format(deity.sky))
	
	clues.god = deity
	clues.sky = deity.sky
	global god,sky
	god = deity
	sky = deity.sky
	
def load_evaluations_to_gas(gaslist,filepath):
	
	if not filepath[len(filepath)-1] == '/':
		print('Needs be a folder.')
		return False
	
	excps = []
	
	for ga in gaslist:
		
		if ga.consulted and ga.evaluation:
			continue
			
		try:
			with open(filepath + ga.name + '.eval','rb') as f:
				ga.evaluation = pickle.load(f)
				ga.consulted = True
	
		except BaseException as e:
			excps.append(e)
	
	return excps if excps else True
	
def store_weights(gaslist,filepath = './guardianangels/weights/'):
	
	excps = []
	
	for ga in gaslist:
		try:
			with open(filepath + ga.name + '.weight','rb') as f:
				
				weight = pickle.load(f)
				ga.stats['trustworthiness'] = weight['overall']
				ga.stats['relative_tw'] 	= trust['relative_tw']
				
		except BaseException as e:
			excps.append(e)
			pass
			
	return excps

def load_weights_to_gas(gaslist,filename = './guardianangels/evaluations/'):
	
	with open(filename,'rb') as f:
		trusts = pickle.load(f)
		
		for angel in gaslist:
			trusts = {ga.name: trusts[ga] for ga in trusts}
			angel.stats['trustworthiness'] = trust[angel.name]['overall']
			angel.stats['relative_tw'] = trust[angel.name]['relative_tw']
	
	return True
			
# patch

def equate_all_links(deity = None):
	"""
	When unpickling evaluations, we often have that clouds made out of the same items
	are no longer properly indexed in dictionaries: they appear as different
	pairs altogether.

	This function only acts on evaluations of guardianangels of the given deity
	or of the default god, setting their evaluations to a common vocabulary
	of cloud pairs.
	"""
	global sky
	if not sky:
		print('need a sky')
		return None
	
	if not deity:
		global god
		deity = god
		
	pid = lambda x: (tuple(x)[0].item['id'], tuple(x)[1].item['id'])	

	print('Parallelising beliefs...')
		
	for ga in god.guardianangels:
		for link,ev in ga.evaluation.items():
			del ga.evaluation[link]
			itlinks = pid(link)
			
			truelink = sky.pair_by_id(*itlinks)

			ga.evaluation[truelink] = ev
	
	return True
	



