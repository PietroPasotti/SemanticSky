
from clues import *

"""
Collection of tests to run on the framework.
"""

def setup_full_sky():
	
	global sky,god
	
	sky = ss.SemanticSky()
	god = God(sky)
	
	god.consult(consider = True,verbose = True) # consults and considers all guardian angels.
	return True

def setup_partial_sky():
	"""
	Sets up a god with only two guardian angels. Shorter; for testing.
	"""
		
	global sky,god
	
	sky = ss.SemanticSky()
	
	god = God(sky)
	god.consult(2,consider = True,verbose = True)
	return True

def consult_actual_links():
	"""
	Sets up a guardian angel to suggest links corresponding to actual links.
	This may be the first step for a backpropagation.
	"""
	
	global god
	
	knower = GuardianAngel(algs.someonesuggested)
	god.consult([knower],consider = True)
	return True

def compare_god_beliefs_against_actual_links():
	
	global results,god,sky
	results = {} 	# will store god's belief state in this form:
					# Cloud() : [Cloud()].sorted(key = godsbelief that it is linked to the dict_key)
	
	for pair in sky.iter_pairs():
		godsbelief = _god.believes(pair)
		
		if not godsbelief > 0:
			continue
			
		a,b = pair
		
		for d in pair:
			if not results.get(d):
				results[d] = []
				
		results[a].append((godsbelief,b)) # belief that b is in a's links
		results[b].append((godsbelief,a)) # belief that a is in b's links
	
	for cloud in results:
		results[cloud].sort(key = lambda x : -x[0]) # we sort it from the most believed (left) to the least (right)
		
	#sky.data.make_links_symmetric()
	
	global compared_results
	compared_results = {}
	
	for cloud in sky.clouds():
		links = cloud.item.get('links',[])
		compared_results[cloud.item['id']] = {}
		compared_results[cloud.item['id']]['actual_links'] = links
		
		second_item_of = lambda x : x[1]
		compared_results[cloud.item['id']]['suggested_links_ranked'] = [ocloud.item['id'] for ocloud in 
											[second_item_of(result) for result in results.get(cloud,[])]
																										]
																										
	return True

def clean_results(crop = 10):
	
	try: 
		res = compared_results
	except BaseException:
		return 'Nothing to clean'
	
	global cleanresults
	cleanresults = {}
	
	for idi in res:
		if res[idi]['suggested_links_ranked'] or res[idi]['actual_links']:
			realcrop = max(crop, ( len( res[idi]['actual_links'] ) + 3 ) )
			cleanresults[idi] = {}
			cleanresults[idi]['suggested_links_ranked'] = res[idi]['suggested_links_ranked'][:realcrop]
			cleanresults[idi]['actual_links'] = res[idi]['actual_links']
		
	return True	

def evaluate_cleanresults_recall():
	
	global evaluation_recall,cleanresults
	evaluation_recall = {}
	
	for result in cleanresults:
		guessed = cleanresults[result]['suggested_links_ranked']
		actual = cleanresults[result]['actual_links']
		
		rec = len(set(cleanresults[result]['suggested_links_ranked']).intersection(set(cleanresults[result]['actual_links']))) / max((1,len(cleanresults[result]['actual_links'])))
		
		evaluation_recall[result] = rec
	
	recall = sum(evaluation_recall.values()) / len(evaluation_recall.values())

	print('recall : ', recall)
	return recall

def evaluate_cleanresults_naive():
	
	global evaluation_naive,cleanresults
	evaluation_naive = {}
	
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
	return avgtot

def store_belief_set(nameoffile=None):
	
	time = ss.time.gmtime()
	
	if nameoffile is None:
		nameoffile = 'god_belief_set_{}.log'.format("dmy_{}_{}_{}_s_{}".format(time.tm_mday,time.tm_mon,time.tm_year,tm_sec))
	
	with open(nameoffile,'ab+') as storage:
		global god
		
		pickle.dump(god,storage)
	
	return True
