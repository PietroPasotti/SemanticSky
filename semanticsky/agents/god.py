 #!/usr/bin/python3
					
from .angel import GuardianAngel
					
class God(GuardianAngel,object):
	"""
	The Allmighty.
	"""
	
	godcount = 0
	
	def __init__(self,sky = None,supervisor = None, overrides = {}):
		"""
		We totally override the GuardianAngel's init method, because they 
		need a supervisor; we don't. But if a supervisor is given, we can
		then link God to another God which takes decisions on the former's.
		Also, god doesn't have yet an algorithm. Even though a generalization
		of this procedure could lead to God and Angels being instances of
		the same class.
		
		overrides, if given, should be a dict from some keywords such as
		"merging_strategy", 'default_merger' or "learningspeed" to some 
		function capable of reacting appropriately to the typical inputs.
		Look at agents.utils.belief_rules for inspiration.
		"""
		
		import semanticsky
		from semanticsky import DEFAULTS
		from .agent import Agent
		from .utils import BeliefBag
		from time import gmtime
		from copy import deepcopy
		
		self.sky = sky
		self.birthdate = gmtime											# can be used to distinguish between multiple gods.
		self.guardianangels = []
		self.whisperers = []											# will hold a list of agents that trigger feedback whenever they clue on something.	
		self.cluebuffer = []											# holds the clues that are processed by god. Mainly for testing.
		self.logs = {}													# holds all processed clues per belief.
		self.name = 'Yahweh'
		self.stats = deepcopy(DEFAULTS['agent_base_stats'])
		self.stats.update(DEFAULTS['angel_base_stats'])
		self.stats.update(DEFAULTS['god_base_stats'])   				# override all previous stages
		self.beliefbag = BeliefBag(self,None,**self.stats['beliefbag_overrides']) # we'll override the believes method, so as not to ask for equalization or weighting.
		self.godid = deepcopy(God.godcount)
		God.godcount += 1

		semanticsky._GOD = self		
		
		if "merging_strategy" in overrides:
			merging = overrides["merging_strategy"]
		else:
			merging = DEFAULTS['default_voting_merge']
		self.voting_merging_strategy = merging # this is what god does to merge his angel's opinions into one.
		
		if "learningspeed" in overrides:
			ls = overrides["learningspeed"]
		else:
			ls = DEFAULTS['god_learningspeed']
		self.learningspeed = ls
		
		if 'default_merger' in overrides:
			merge = overrides['default_merger']
		else:
			merge = DEFAULTS['default_merger']
		self.learning_merger = merge

	def __str__(self):
		return "< The Lord {} >".format(self.godid)
	
	def __repr__(self):
		from semanticsky.tests import wrap
		return wrap("< The Lord :: {} >".format(self.godid),'brightblue')
	
	def receive(self,clue):
		from semanticsky import DEFAULTS
		if DEFAULTS['verbosity'] > 0:
			print('God accepts no feedback, mortal. Agent {} will be brutalized for this.'.format(clue.agent))
		return None
			
	def get_sky(self):
		"""
		If a semanticsky has already been instantiated, loads it as god's
		own sky.
		"""
		
		try:
			from semanticsky import _SKY # the last loaded sky can always be found there.
		except ImportError:
			_SKY = None
			
		self.sky = _SKY
		
		if _SKY is not None:
			return True
		else:
			return False
		
	
	# HANDLERS	
	def has_already_guessed(self,clue):
		"""
		Looks up for the about in god's beliefs and checks the history:
		if the clue's agent has already clued on the same topic, returns
		the previous clue.
		Else, returns False.
		"""
		
		about = clue.about
		cluelist = self.logs.get(about,[])
			
		agent = clue.agent
		hisclues = [c for c in cluelist if c.agent is agent]
		
		# since a clue logs herself as soon as it's created,
		# we'll need to return only the second one, if there is one
		
		if len(hisclues) >= 2:
			return hisclues[0] # at the second place there will be the last clue spawned
		else:
			return False
	
	def update_beliefs(self,clue):
		"""
		Where clue is a clue about anything believable by god.
		"""
		
		preclue = self.has_already_guessed(clue)
		if preclue: # if the agent has already clue'd about that link or object, we assume he has changed his mind:
			self.logs[clue.about].remove(preclue)	# his previous clue is erased from the history
													# and the value of the belief in about is updated to the average of the values still in the history
		###### UPDATE part
		
		from semanticsky.tests import avg
		from semanticsky import DEFAULTS
		
		previous_value = self.believes(clue.about)
		new_value = self.voting_merging_strategy(clue.weightedvalue for clue in self.logs[clue.about]) # we compute the new should-be-value of the belief
		
		new_learned_value = self.learning_merger(previous_value,new_value,self.learningspeed)
		### we use the default merge! function of previous value, new value and learningspeed
		
		self.beliefbag[clue.about] = new_learned_value
	
	
	# LOGGERS
	def log(self,clue):
		"""
		Whenever a clue gets processed by God (or otherwise 'consumed'),
		we log it. Then we will be able to run analyses on the logs, so as
		to determine whether an agent (or algorithm) gave feedback
		whose effects (creation of a new link, downweighting of an algorithm
		or other agent) were appreciated (through more same-direction feedback)
		by other agents.
		"""
		#with open('./clues.log','w+') as logs:
		#	logline = "time::<{}> clue::<{}>\n".format( ss.time.ctime(),str(clue)) # markers for re retrieving
		#	logs.write(str(logline))
			
		if not hasattr(self,'logs'):
			self.logs = {}
		
		about = clue.about
		
		if not self.logs.get(about):
			self.logs[about] = []
		
		log = clue
		
		self.logs[about].append(log)
	
	def lenlogs(self):
		"""
		Calculates the number of logs stored.
		"""
		from semanticsky.skies.utils import lsum
		return len(lsum(list(self.logs.values())))
		
	def iter_logged_clues(self):
		"""
		Returns a generator for all clues in god's logs.
		"""
		
		for loglist in self.logs.values():
			for log in loglist:
				yield log

	def clear_all(self):
		"""
		Clears most records of himself and all of his guardian angels.
		"""
		
		from .utils import BeliefBag
		
		self.beliefbag = BeliefBag(self)
		self.logs = {}
		
		for guardian in self.guardianangels:
			guardian.clear_all()
		
		return
	
	def locate(self,clue):
		"""
		Tries to lookup the clue in god's logs.
		If there is a match, returns the entry and the whole log queue.
		"""
		logs = self.getlogs(clue.about)
		return {clue.about : logs } if logs else False

	def getlogs(self,about):
		"""
		returns the logs for a given pair
		"""
		return self.logs.get(about,[])
	
	def trusts(self,agents = [],local = True):
		"""
		Returns a trustdict, or a single value if agents is a single Agent.
		If *local* is set to false, prints a table instead.
		"""
		
		trustdict = {}
		
		if not agents:
			agents = self.guardianangels
		elif not isinstance(agents,list):
			agents = [agents]
		else:
			pass
			
		for agent in agents:
			trustdict[agent] = {'overall' : agent.trustworthiness}
			trustdict[agent].update(agent.stats['contextual_tw'])
		if local:	
			return trustdict
		else:
			from semanticsky.tests import table
			
			trusttable = []
			
			for entry in trustdict:
				entrytable = []
				entrytable += [[repr(entry)]] # the agent: one row
				entrytable += [ ['\toverall : \t' + str(entry.trustworthiness) ] ]
				entrytable += [ ['\tcontextual_tw'] ]
				for relkey in entry.stats['contextual_tw']:
					entrytable +=  [ [ '\t\t' + str(relkey) +'    '+ str(entry.stats['contextual_tw'][relkey])  ] ]
				trusttable += entrytable
				
			table(trusttable)
		
	def unlog(self,angel):
		"""
		Removes all suggestions received from angel from the logs.
		"""
		
		for log in self.logs:
			for clue in self.logs[log]:
				if clue.agent is angel:
					self.logs[log].remove(clue)
		return True
		
		
	# WHISPERING
	def whisperer(self,agent):
		"""
		Adds agent to self.whisperers.
		Now agent can whisper to God.
		"""
		
		self.whisperers.append(agent)
			
	def whisperpipe(self,clue):
		"""
		Easy-access iswhisperer + whisper combo. 
		"""
		
		if self.iswhisperer(clue.agent):
			return self.whisper(clue)
		else:
			return None
	
	def iswhisperer(self,agent):
		"""
		Boolean.
		"""
		
		if agent in self.whisperers:
			return True
		else:
			return False
	
	def whisper(self,clue):
		"""
		The crucial bit of the whole whispering stuff.
		This function delegates to the clue's agent (the whisperer) the duty
		of generating feedback on the cluelist which is the content of
		god.logs[clue.about].
		
		Thus, all those who clued on about (except the whisperer itself)
		will receive feedback from the whisperer.
		
		Can also be used to override the whisperers list.
		
		Then, it takes the previous value and backpropagates a feedback,
		influencing its main (?) authors' trustworthiness.
		"""
		
		whispering = clue.agent		
		targets = self.logs.get(clue.about,[]) 	# we check whether the clue's about is logged

		whispering.give_feedback(targets,verbose = False) # whispering, in the case of GA's,
		#	has the effect of asking them to evaluate the whole cluelist... thus, they will spawn feedbacks for each of them		
		return None
	

	# GUARDIAN ANGELS, CONSULT and CONSIDER			
	def spawn_servants(self,overwrite = False):
		"""
		Creates all GuardianAngels available in .utils.algorithms.ALL_ALGS
		(that by *shouldn't* include training algorithms).
		"""	
		
		from .utils.algorithms import ALL_ALGS
				
		print('Spawning guardians...')
		
		if overwrite: 
			self.guardianangels = []
		
		for algorithm in ALL_ALGS:
			GA = GuardianAngel(algorithm,self)
			self.guardianangels.append(GA)
				
		return True
	
	def express_all(self,guardians = None,verbose = True):
		"""
		For ga in self.guardianangels (or [guardians], if provided):
		ga.express()
		"""
		if guardians is None:
			guardians = self.guardianangels
			
		for ga in guardians:
			ga.express(verbose = verbose)
		
	def consider(self, cluelist = None):
		"""
		God will shot a quick glance to the useless complaints of the mortals.
		
		Number can be a positive integer, a list of clues
		or a single clue.
		
		- None: will consider all the clues from the global queue 
		semanticsky._CLUES
		
		- clue: will only consider this clue.
		
		- list of clues: will consider them all.
		
		Considering a clue means that god will 1 ) BUFFERIZE it (mainly for
		testing purposes, but who knows), 2 ) LOG it, 3 ) UPDATE_BELIEFS with
		it; that means: taking into account its contents for the purposes
		of its belief state.
		
		"""
	
		from semanticsky.clues import Clue
		
		if isinstance(cluelist,Clue):
			toread = [cluelist]
		elif isinstance(cluelist,list) and all(isinstance(x,Clue) for x in cluelist):
			toread = cluelist
		elif cluelist is None:
			from semanticsky import _CLUES
			toread = _CLUES
		else:
			raise BaseException('Bad input for God.consider: {}.'.format(cluelist))
						
		for clue in toread:
			
			######### BUFFERIZE
			if clue not in self.cluebuffer:
				self.bufferize(clue)

			######### LOG
			self.log(clue)
			
			self.whisperpipe(clue) # check whether we have to whisper the clue, and in case does it.
			
			from .knower import Knower
			if not isinstance(clue.agent,Knower): # if the clue'r is a Knower (that is, ideally: a trainer), we won't update the beliefs. Can be removed if we are sure the knower will never express its clues.
				self.update_beliefs(clue) # then we update the beliefs
			
	def consult(self,angels = False,verbose=True,consider = False,local = False):
		"""
		Consults all or some guardian angels asking for their opinion about
		the whole network.
		Ideally, this function should be called at the beginning of
		the whole process only, or if weights get thoroughly screwed
		up.
		This function results in God re-virginating his belief states
		to a GuardianAngel-only informed belief state.
		
		Please note: might be computationally heavy, depending on the angels.
		"""
		
		if verbose:
			from semanticsky import DEFAULTS
			vb = DEFAULTS['verbosity']
		else:
			vb = 0
		
		if vb > 0:
			import time
			initime = time.clock()
		
		if not hasattr(self,'guardianangels'):
			self.spawn_servants()
		
		if not hasattr(self,'sky'):
			if not self.get_sky():
				from semanticsky.skies import SemanticSky
				self.sky = SemanticSky() # we initialize a new sky from the currently loaded dataset.
		
		if angels is False:							# default: all angels are consulted.
			angels = self.guardianangels			
		elif isinstance(angels,int) and angels < 0: 	# if we only want to consult angel 2, we call self.consult(-2)
			angels = [self.guardianangels[int(sqrt(angels ** 2))]]
		elif isinstance(angels,int) and angels is not False:	# if we only want to consult the first three angels, we call self.consult(3)
			newa = []
			for i in range(angels):		
				angel = self.guardianangels[i]
				newa.append(angel)
			angels = newa
		elif isinstance(angels,list):					# if a list of angels is explicitly provided
			angels = angels
		elif isinstance(angels,GuardianAngel):
			angels = [angels]
		else:
			raise TypeError('Unrecognized input type: {}'.format(type(angels)))
					
		if verbose:
			from semanticsky import DEFAULTS
			vb = DEFAULTS['verbosity']
		else:
			vb = 0
			
		if vb > 0:
			print('\t>>> consulting: ',' '.join([str(angie) for angie in angels]))
				
		for angel in angels: # the list of opinions thus will be in the same order
			angel.evaluate_all(verbose = verbose)
				# angel will evaluate all pairs and spawn a clue for each one (clues get autoconsidered)
			
		if consider:
			self.consider() # though, CLUES should be rather empty
		
		import time
		elapsed = time.clock() - initime
		
		angelsno = len(angels)
		if vb > 1: 
			print('\n\t\t {} angels consulted. [ {} elapsed ]\n\n'.format(angelsno,elapsed)+ '-'*110) 
		
	def consult_missing(self,verbose = True, consider = False,local = False):
		"""
		Asks god to consult (& consider) all the guardianangels who weren't
		so far.
		"""
		
		reg = self.consultations_registry()
		toconsult = []
		for ga in reg:
			if not reg[ga] and isinstance(ga,GuardianAngel):
				toconsult.append(ga)
		
		self.consult(toconsult,verbose,consider,local)
	
	def lookup_expertises(self,local = False):
		"""
		Forces all angels to lookup_expertise() and returns them.
		"""
		exps = {}
		for ga in self.guardianangels:
			ga.lookup_expertises()
			exps[ga] = ga.stats['expertises']
		
		self.stats['expertises'] = exps
		
		if local:
			return exps
		
		return
		
	def consultations_registry(self):
		"""
		Returns a dict from guardianangels to [True,False,0], depending on whether
		they already were consulted or not or just aren't in self.guardianangels.
		"""
		
		registry = {}
		
		for ga in self.guardianangels:
			registry[ga] = ga.consulted
		
		gasbyname = [ga.name for ga in self.guardianangels]
		
		from .utils.algorithms import algsbyname
		
		for alg in algsbyname:
			if alg not in gasbyname:
				registry[alg] = 0
		
		return registry
	
	def get_angel_plus(self,algorithm):
		"""
		Like get_angel, but also creates the angel and appends it to self.
		guardianangels if not present already.
		"""
		
		if not callable(algorithm): # checks that algorithm is really an algorithm
			raise TypeError('Bad input type: I need something callable, got an {} instead'.format(type(algorithm)))
			
		angel = [ga for ga in self.guardianangels if ga.name == algorithm.__name__]
		
		if len(angel) > 1:
			raise BaseException("Something wrong: duplicates are around. *angel* is {}".format(angel))
		
		if not angel:
			from .angels import GuardianAngel
			angel = GuardianAngel(algorithm)
			self.guardianangels.append(angel)
		else:
			angel = angel[0]
			
		return angel
	
	def get_angel(self,algorithm):
		"""
		Returns the guardianangel with the given algorithm (or alg.__name__).
		If he hasn't it, returns false.
		"""
		
		if callable(algorithm):
			name = algorithm.__name__
		else:
			name = algorithm
			
		angel = [ga for ga in self.guardianangels if ga.name == name]
		
		if len(angel) != 1:
			raise BaseException("Something wrong: *angel* is {}".format(angel))
	
		angel = angel[0]
			
		return angel
		
	def block(self,agent):
		if not isinstance(agent,Agent):
			raise BaseException('Not an agent.')
		agent.stats['blocked'] = True
	
	def most_trustworthy(self,ctype,crop = 3):
		"""
		returns (crop) of its guardianangels which are most trustworthy
		about links of contenttype ctype.
		"""
		
		ctype = list(ctype) 
		ctype.sort(reverse = True) # we make sure the letters are in the right order
		ctype == ''.join(ctype)
		
		trustranks = {}
		for i in self.guardianangels:
			rel = i.reltrust(ctype)
			trustranks[i] = rel
			
		ranked = list(trustranks)
		ranked.sort(key = lambda x: trustranks[x],reverse = True)
		
		return ranked[:crop]
	
	def remove_tag_similarity_angels(self):
		"""
		Just for testing. Useful, for tag_similarity angels screw the results.
		"""
		
		self.guardianangels = [ga for ga in self.guardianangels if 'tag_similarity' not in ga.name]

	
	# BELIEF MANAGEMENT
	def believes(self,something):
		"""
		Returns the extent to which god believes something. If something
		is not in the belief set, returns zero.
		Warning: this is the current state of the belief set. If something
		has changed without a clue being spawned (such as trustworthinesses
		all around) then the belief state might be not up-to-date.
		
		Belief pipeline for God is:
		[raw beliefs]
		
		Thus, self.beliefbag.toplevel() will return the raw beliefset.
		"""
		return self.beliefbag[something]

	def refresh(self,verbose = True):
		"""
		for belief in self.beliefbag:
		self.rebelieves(belief)
		"""
		
		if verbose:
			from semanticsky import DEFAULTS
			vb = DEFAULTS['verbosity']
		else:
			vb = 0
		
		topno = len(self.beliefbag)
		if topno and vb > 1:
			from semanticsky.tests import ProgressBar
			bar = ProgressBar(topno,title = 'Refreshing')
		
		for belief in self.beliefbag:
			if verbose and topno:

				if vb > 1: 
					bar()
						
			self.rebelieves(belief) # will update beliefs

	def rebelieves(self,something):
		"""
		If something is logged and there are clues about it, simply refreshes
		the belief.
		Else, asks all guardians to evaluate it. (which will in turn produce
		clues and eventually update the belief).
		
		Returns the updated value of the belief.
		"""
		
		if something in self.logs and self.logs[something]:
			
			tempclues = self.logs[something]
			del self.logs[something]
			
			for clue in tempclues:
				self.consider(clue) # we can't just call update_beliefs on it, because update_beliefs looks for all clues in the logs, and we just cleared them.
									# this way, the clue gets 1) (re-)logged, 2) bufferized, 3) whispered, if necessary, 4) belief_updated.
									# otherwise, we could just make self.logs[something] = [], self.log(clue), self.update_beliefs(clue)
		else:
			for ga in self.guardianangels:
				ga.evaluate(something)
				
		return self.believes(something)
		
	def expert_believes(self,something,crop = 3,tw = False):
		"""
		Returns the belief value as if only those who are most trustworthy
		about the contenttype of something were taken into account.
		"""
		
		ctype = ss.utils.ctype(something)
		
		if not tw:
			tw = self.most_trustworthy(ctype,crop)
		
		opinions = []
		for i in tw:
			opinions.append(i.belief_with_feedback(something))
			
		return sum(opinions) / len(opinions)

	def expert_belief_assessment(self,crop = 3,local = False):
		"""
		Produces a new belief set where only the top (crop) experts per each
		ctype are considered.
		"""
		
		experts = {}
		
		from .utils import BeliefBag
		out = BeliefBag(self)
		
		tlen = len(self.beliefbag)
		from semanticsky.tests import ProgressBar
		from semanticsky import DEFAULTS
		vb = DEFAULTS['verbosity']
		if vb > 1:
			bar = ProgressBar(tlen)

		for belief in self.beliefbag:
			ctype = ss.utils.ctype(belief)
			if not experts.get(ctype,False):
				experts[ctype] = self.most_trustworthy(ctype,crop)
			cexperts = experts[ctype]
			
			if vb > 1: bar()
				
			rebelief = self.expert_rebelieves(belief,crop,cexperts) # retrieves a weighted sum of what these experts believe about belief
			
			out[belief] = rebelief
		
		if vb > 0: 
			print('Expert judgement compiled; crop = {}, saved to self.expert_belief_assessm'.format(crop))	
		self.expert_belief_assessm = out
		
		if local:
			return out
		else:
			return True
		
	def clean_trivial_beliefs(self):
		"""
		Removes from the beliefs zero's: the default is zero already.
		"""
		
		for belief in list(self.beliefbag):
			if not self.beliefbag[belief] > 0:
				del self.beliefbag[belief]

	def believes_link_by_id(self,anid,anotherid):
		if not hasattr(self,'sky'):
			self.get_sky()
			
		cloud1 = self.sky.get_cloud(anid)
		cloud2 = self.sky.get_cloud(anotherid)
		
		from semanticsky.skies.sky import Link
		pair = (cloud1,cloud2)
		
		return self.believes(pair)
	
	def allinks(self,cloud_or_id):
		"""
		If given a cloud, returns all clouds linked to it; if given an id,
		returns the same but by id.
		"""	
		
		allc = []
		import semanticsky.skies as ss
		if isinstance(cloud_or_id,ss.Cloud):
			for cloud in self.sky.clouds():
				if self.believes(pair(cloud_or_id,cloud)):
					allc.append(cloud)
					
		if isinstance(cloud_or_id,(str,int)):
			for pair in self.beliefbag:
				if cloud_or_id in [c.item['id'] for c in pair]:
					
					otherl = [cloud for cloud in pair if cloud.item['id'] != cloud_or_id ]
					other = otherl[0]

					allc.append(other)
		
		return allc

	def reassess(self,listofitems = None):
		"""
		Forces god to re-assess (parts of) his belief state. If for example 
		we removed a key clue from a well-grounded belief, then we may ask
		him to reassess the belief in order to check the new value of the 
		belief.
		
		*listofitems*, if given, must be a list of links or believable items
		or a clue (or list of clues).
		"""
		
		from semanticsky.tests import ispair,avg
		from semanticsky.clues import Clue
		
		if sispair(listofitems):
			listofitems = [listofitems]
		elif isinstance(listofitems,Clue):
			listofitems = [listofitems.about]
		elif isinstance(listofitems,list) and all(isinstance(x,Clue) for x in listofitems):
			listofitems = [clue.about for clue in listofitems]
		elif isinstance(listofitems,list): # a list of links
			listofitems = listofitems
		elif listofitems is None:
			listofitems = self.beliefbag
		else:
			raise BaseException('Bad input: type {}'.format(type(listofitems)))
		
		for belief in listofitems: # list of belief-keys to reassess
			
			clues = self.logs[belief] # all the clues which led to the current belief's value
			self.beliefbag[belief] = 0 # we reset the belief state regarding that item
			
			for clue in clues:
				self.update_beliefs(clue) # this will automatically fill update back the belief state
				
		return None
	
	# CLEANING
	def remove_tag_clouds(self): # to check...
		"""
		For all guardianangels, and from its own beliefs and logs, eliminates
		all traces of clues whose about contains a tag cloud or a tag id.
		"""

		beliefsets = tuple( tuple(tuple(pair for pair in self.beliefbag)) + tuple(tuple(pair for pair in ga.beliefbag) for ga in self.guardianangels) )
		# type should be ((frozenset({cloud(),cloud()}),),)
		
		toclean = [self.beliefbag,self.logs,self.sky]
		for ga in self.guardianangels:
			if hasattr(ga,'remove_tag_clouds'): # in case there's a god there...
				ga.remove_tag_clouds()
				continue
				
			toclean.append(ga.beliefbag) # toclean is a list of belief sets from which we want to remove tag clouds
		
		istagcloud = lambda x: True if x.cloudtype == 'tags' else False
		istagpair = lambda x: True if istagcloud(tuple(x)[0]) or istagcloud(tuple(x)[1]) else False
		
		for beliefset in beliefsets:
			for belief in beliefset:

				try:
					if not istagpair(tuple(belief)):
						continue
				except BaseException:
					print('skipping ',belief)
					continue

				for target in toclean:
					if belief in target:
						target.remove(belief)
						
		toclean = []				
		for ga in self.guardianangels:
			toclean.append(ga.clues)
		
		for beliefset in beliefsets:
			for belief in beliefset:
				
				try:
					if not istagpair(tuple(belief)):
						continue
				except BaseException:
					continue
				
				for target in toclean:
					if belief in target:
						target.remove(belief)
		
	def clean_feedback(self):
		"""
		As if none of the guardianangels had ever received feedback:
		cleans the trustworthiness db.
		"""
		
		for ga in self.guardianangels:
			ga.clean_feedback()
			
		#self.clean_feedback() uncomment this if you are refitting god to act as a guardianangel
		
		return True

	# BUFFERING
	def bufferize(self,clue):
		"""
		Adds a clue to an internal buffer.
		"""
		self.cluebuffer.append(clue)
		
	def getbuffer(self):
		"""
		Empties the buffer and returns its previous content.
		"""
		
		bffr = self.cluebuffer
		
		self.cluebuffer = []
		
		return bffr
		
	def cleanbuffer(self):
		"""
		Just empties the cluebuffer.
		"""
		
		self.cluebuffer = []


	# EVALUATION FUNCTIONS -- for testing
	def regrets(self,only_on_true_links = False):
		"""
		The regrets of god.
		"""
		
		from semanticsky.agents.utils import regret
		
		if not hasattr(self,'knower'):
			from semanticsky.tests import getknower
			self.knower = getknower(self) # knower is born with evaluation and all the rest
		
		return regret( self.beliefbag ,self.knower.beliefbag, only_on_true_links = only_on_true_links)
		
	def guardians_regrets(self,guardians = None,only_on_true_links = False):
		"""
		Regrets for the guardians.
		"""
		
		if guardians:
			angels = guardians
		else:
			guardians = self.guardianangels
		
		out = {}
		
		for guardian in guardians:
			out[guardian.name] = guardian.regrets(only_on_true_links = only_on_true_links)
		
		return out
	
	def printregrets(self):
		
		totable = [['agent','regret']]
		
		totable.append([str(self),self.regrets()])
		for ga in self.guardianangels:
			totable.append([str(ga),ga.regrets()])
			
		from semanticsky.tests import table
		table(totable)
		
		return
	
