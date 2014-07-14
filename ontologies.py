from clues import Agent,ss,pickle

"""
This module implements strategies to extract high-level information from
a clouds network (a SemanticSky).
"""

sky = None

def load_known_communities():
	return pickle.load(open('./known_communities.log'))

def get_community(obj):
	if isinstance(obj,clues.Agent):
		return get_community_agent(obj)
	elif isinstance(obj,dict):
		return get_community_item(obj)
	else:
		raise BaseException('Unrecognized object input {}.'.format(type(obj),' : ',obj))
	
def get_community_agent(agent):
	"""
	Guesses the community of an agent.
	"""
	
	if agent.item is not None:
		item = agent.item
		communities = item.get('communities')
		if communities:
			return communities
			
	known_communities = load_known_communities() # which is a dictionary 'community name' -(is_part_of_relation)-> ('another community name' | None)
	candidates = set()
	
	allclues = agent.clues
	allcommentedclouds = [] # clouds on which the agent has opinated
	allagents = []
	
	# alleditedclouds = [] # clouds which the Agent has contributed to; not implemented
	
	for clue in allclues:
		if isinstance(clue.about,frozenset):
			allcommentedclouds.extend(clue.about)
		elif isinstance(clue.about,Agent):
			allagents.extend(clue.about)
		else:
			pass
	
	for cloud in allcommentedclouds:
		namesp = cloud.layers[0]['names'] + cloud.layers[0]['places'] + cloud.layers[0]['communities']
		candidates.update(set(namesp).intersection(set(known_communities)))
	
	preferred_candidates = set()
	
	for candidate in candidates:
		if candidate not in known_communities.values(): 	# if there is no subcommunity, is a preferred: this means that 
															# the community indication is as specific as it can be.
															# for example, 'Amsterdam Community' is preferred to 'Dutch Community'
			preferred_candidates.add(candidate)
	if not preferred_candidates:
		pass
			
def get_community_item(item):
	return item['communities']
		
