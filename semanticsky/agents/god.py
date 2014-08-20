 #!/usr/bin/python3
					
import time
from .angels import GuardianAngel
					
class God(GuardianAngel,object):
	"""
	The Allmighty.
	"""
	
	godid = 0
	
	
	def __init__(self,sky = None,merging_strategy_override = False):
		
		from semanticsky import DEFAULTS
		
		self.sky = sky
		self.birthdate = time.gmtime()
		self.guardianangels = []
		self.whisperers = []
		self.cluebuffer = []
		self.logs = {}
		self.ccount = 0 # keeps track of number of clues processed
		self.totcluecount = 0
		self.ignoreds = []
		self.name = 'Yahweh'
		self.beliefs = {}
		
		if merging_strategy_override:
			merging = merging_strategy_override
		else:
			merging = DEFAULTS['default_voting_merge']
		self.merging_strategy = merging # this is what god does to merge his angel's opinions into one.
				
		God.godid += 1
		self.godid = God.godid
		
		global god
		god = self
			
	def get_sky(self):
		"""
		If a semanticsky has already been instantiated, loads it as god's
		own sky.
		"""
		
		global sky
		
		if sky: 
			self.sky = sky
			return True
		else:
			return False
	
	def __str__(self):
		return "< The Lord {} >".format(self.godid)
	
	def __repr__(self):
		from semanticsky.tests import wrap
		return wrap("< The Lord :: {} >".format(self.godid),'brightblue')
	
	def receive(self,clue):
		ag = clue.agent
		clue.delete()
		del clue
		print('God accepts no feedback, mortal. Agent {} will be brutalized for this.'.format(ag))
		return None
	
	@property
	def cluecount(self):
		"""
		Keeps track of the number of clues that pass through god. Resets 
		at every call; stores to ___totcluecount
		"""
		
		if not hasattr(self,'ccount') or not hasattr(self,'totcluecount'):
			self.ccount = 0
			self.totcluecount = 0
		
		oldcount = self.cluecount
		self.cluecount = 0
		self.totcluecount += oldcount
		return oldcount
	
		
	# HANDLERS	
	def handle_link(self,linkclue):
		"""
		where linkclue is a clue about the existence of a link, ( or about
		the similarity of two clouds, if you wish, this function makes god's
		ineffable beliefs change (a bit) accordingly.
		
		God does listen at his Agents' complaints, but they'll have to scream 
		aloud enough.
		"""
		return self.update_beliefs(linkclue)
		
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
		
		if len(hisclues) == 2:
			return hisclues[0] # at the second place there will be the next one
		else:
			return False
	
	def update_beliefs(self,clue):
		"""
		Where clue is a clue about anything believable by god.
		"""
		
		if not self.beliefs.get(clue.about,False):
			self.beliefs[clue.about] = 0 # the initial belief is zero: if asked 'does God believe x?' default answer is 'no'
		
		preclue = self.has_already_guessed(clue)
		if preclue: # if the agent has already clue'd about that link or object, we assume he has changed his mind:
			self.logs[clue.about].remove(preclue)	# his previous clue is erased from the history
													# and the value of the belief in about is updated to the average of the values still in the history
		###### UPDATE ALGORITHM
		
		global god_learningspeed
		from belieftests import avg
		
		previous_value = self.believes(clue.about)
		new_value = avg(clue.weightedvalue() for clue in self.logs[clue.about])
	
		new_learned_value = updaterules.MERGER(previous_value,new_value,god_learningspeed)
		
		### we use the default merge!! function of previous value, new value and learningspeed
		
		self.beliefs[clue.about] = new_learned_value
	
	
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
		
		return len(ss.lsum(list(self.logs.values())))
		
	def flowlogs(self):
		"""
		Returns a generator for all clues in god's logs.
		"""
		
		for loglist in self.logs.values():
			for log in loglist:
				yield log
	
	def get_clues(self,about):
		"""
		Retrieves all clues that had some impact on god's current
		belief state about about.
		"""
		
		if not hasattr(self,'logs'):
			print('Impossible to fetch logs right now. Will need to access the file(?)')
		
		return self.logs[about] # a list of clues
	
	def get_agents(self,about,flat = False): # deprecated
		"""
		Fetches all responsibles for a certain belief: that is, all agents
		who took part to some extent in the current state, divided along 
		the criterion: they voted for more or less than the current
		state
		
		If flat is true, returns a simple list of the authors
		
		"""
		
		uppers = 'uppers'
		downers = 'downers'
		
		
		out = {uppers : [], downers: []}
		
		allc = self.get_clues(about)
		
		if flat:
			return [c.agent for c in allc]
		else:
			for c in allc:
				if c.value >= self.beliefs[about]:
					out[uppers].append(c.agent)
				else:
					out[downers].append(c.agent)
			
		return out

	def clear_all(self):
		"""
		Clears all logs of himself and all his guardian angels.
		"""
		
		self.beliefs = {}
		self.logs = {}
		for guardian in self.guardianangels:
			guardian.clues = []
			guardian.stats['trustworthiness'] = 1
		
		global AGENTS
			
		for agent in AGENTS:
			agent.stats['trustworthiness'] = 0.6
			
		return True

	def store_info(self):
		"""
		Useful for pickling god.
		"""
		
		global CLUES,AGENTS,belief_inertia
		
		self.CLUES = CLUES
		self.AGENTS = AGENTS
		self.inertia = belief_inertia
		
		return True
	
	def locate(self,clue):
		"""
		Tries to lookup the clue in god's logs.
		If there is a match, returns the entry and the whole log queue.
		"""
		
		for entry in self.logs:
			if clue in self.logs[entry]:
				return {entry:self.logs[entry]}
		
		return False		

	def getlogs(self,pair):
		"""
		returns the logs for a given pair
		"""
		return self.logs.get(pair,[])
				
	def ranklogs(self):
		"""
		Returns a dict from len(logs[log]) to log.
		"""
		
		rlogs = {}
		
		for log in self.logs:
			llist = tuple(self.logs[log])
			if not rlogs.get(len(llist)):
				rlogs[len(llist)] = []
			rlogs[len(llist)].append(log)
		
		return rlogs
	
	def rankcounter(self):
		"""
		Returns a counter from number of cluelist per log to number of logs
		with that length.
		"""
	
		rlogs = self.ranklogs()
		
		rlen = {number : len(rlogs[number]) for number in rlogs}
		
		return rlen
	
	def trusts(self,agents = [],local = True):
		"""
		Returns a trustdict, or a single value if agents is a single Agent.
		"""
		
		trustdict = {}
		
		if not agents:
			#global AGENTS
			
			#agents = AGENTS
			agents = self.guardianangels
			
		elif not isinstance(agents,list):
			agents = [agents]
		elif isinstance(agents,Agent):
			return agents.trustworthiness 
		else:
			pass
			
		for agent in agents:
			trustdict[agent] = {'overall' : agent.trustworthiness}
			trustdict[agent].update(agent.stats['relative_tw'])
		if local:	
			return trustdict
		else:
			from tests import table
			
			trusttable = []
			
			for entry in trustdict:
				entrytable = []
				entrytable += [[repr(entry)]] # the agent: one row
				entrytable += [ ['\toverall : \t' + str(entry.trustworthiness) ] ]
				entrytable += [ ['\trelative_tw'] ]
				for relkey in entry.stats['relative_tw']:
					entrytable +=  [ [ '\t\t' + ss.utils.ctype_to_type(relkey) +'\t'+ str(entry.stats['relative_tw'][relkey])  ] ]
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
	def update_whisperers(self):
		"""
		Updates god's whisperers list. That is: all agents or algorithms
		that have the power to start a backpropagation.
		"""
		global AGENTS
		
		self.whisperers = [agent for agent in AGENTS if agent.stats['blocked'] is False]
	
	def whisperer(self,agent):
		"""
		Adds agent to self.whisperers.
		Now agent can whisper to God.
		"""
		
		if isinstance(agent,Agent) or isinstance(agent,GuardianAngel):
			self.whisperers.append(agent)
		else:
			raise TypeError('Unrecognized input type for God.whisperer: {}'.format(type(agent)))
		return None
	
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
									# suppose for example that god has a strong belief (1) in x, due to A's very confident +1 suggestion. (logged)
									# then a whisperer rates x 0.4, which is lower than 1.
									# then, since A is a whisperer, the (x,0.4) clue will be whispered and not just considered 

		whispering.give_feedback(targets,verbose = False) # whispering, in the case of GA's,
		#	has the effect of asking them to evaluate the whole cluelist... thus, they will spawn feedbacks for each of them		
		return None
	

	# GUARDIAN ANGELS, CONSULT and CONSIDER			
	def spawn_servants(self,overwrite = False):
		"""
		Creates all GuardianAngels
		"""	
		
		from semanticsky.agents.utils.algorithms import ALL_ALGS
		from semanticsky.agents import GuardianAngel
				
		print('Spawning guardians...')
		
		self.guardianangels = []
		
		algos = ALL_ALGS # plain list of all algorithms defined in algorithms
		
		gasbyalg = [ga.algorithm for ga in self.guardianangels]
		
		for algorithm in algos:
			if algorithm not in gasbyalg:
				GA = GuardianAngel(algorithm,self)
				self.guardianangels.append(GA)
				
		return True
	
	def express_all(self,guardians = None,vb = True):
		"""
		For ga in self.guardianangels (or [guardians], if provided):
		ga.express()
		"""
		if guardians is None:
			guardians = self.guardianangels
			
		for ga in guardians:
			ga.express()
		
	def consider(self, number = False,verbose = False):
		"""
		God will shot a quick glance to the useless complaints of the mortals.
		
		Number can be a positive integer, a list of clues
		or a single clue.
		
		- int+: will consider (up to) number clues from the global queue
		CLUES
		
		- clue: will only consider the clue.
		
		- list of clues: will consider them all.
		
		"""
		
		global CLUES

		if isinstance(number, int) and number is not False and number > 0:
			restr_clues = CLUES[:number]
			CLUES = CLUES[number:]	
			toread = restr_clues
			if verbose: print('reading {} CLUES...'.format(number))
			if not CLUES:
				if verbose: print('No clue!')
				return None
		elif isinstance(number,Clue):
			toread = [number]
			if verbose: print('reading clue...')
		elif isinstance(number,list) and isinstance(number[0],Clue):
			toread = number
			if verbose: print('reading clues...')
		else:
			toread = CLUES
			CLUES = []
			if verbose: print('reading all CLUES...')
			if not CLUES:
				print('No clue!')
				return None
						
		for clue in toread:
			
			######### bufferize
			if clue not in self.cluebuffer:
				self.bufferize(clue)
			
			self.ccount += 1
			if verbose: print(toread)
			self.log(clue)
			if clue.cluetype in ['link','feedback']:
				handler = getattr(self, 'handle_{}'.format(clue.cluetype) )
				if clue.cluetype != 'feedback':
					self.whisperpipe(clue) # check whether we have to whisper the clue, and in case does it.
				
				if not isinstance(clue.agent,Knower): # if the clue'r is a knower, we won't update the beliefs.
					handler(clue) # then the handler will handle
				
				
				
			else:
				raise BaseException('Unrecognized cluetype: {}.'.format(clue.cluetype))
					
	def consult(self,angels = False,verbose=True,consider = False,local = False):
		"""
		Consults all or some guardian angels asking for their opinion about
		the whole network.
		Ideally, this function should be called at the beginning of
		the whole process only, or if weights get thoroughly screwed
		up.
		This function results in God re-virginating his belief states
		to a GuardianAngel-only informed belief state.
		
		Please note: computationally very heavy.
		
		"""
		initime = ss.time.clock()
		opinions = {} 	# will collect pairs-of-clouds to [0,1] judgements for each guardianangel
						# result is of type {frozenset({Cloud(),Cloud()} : [float()] )}
		
		if not hasattr(self,'guardianangels'):
			self.spawn_servants()
		
		if not hasattr(self,'sky'):
			self.get_sky()
		
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
			print('    >>> angels is: ',' '.join([str(angie) for angie in angels]))
				
		for angel in angels: # the list of opinions thus will be in the same order
			angel.evaluate_all(verbose = verbose)
				# angel will evaluate all pairs and spawn a clue for each one (clues get autoconsidered)
			
		if consider:
			self.consider() # though, CLUES should be rather empty
		
		elapsed = ss.time.clock() - initime
		
		angelsno = len(angels)
		if verbose: 
			print('\n\t\t {} angels consulted. [ {} elapsed ]\n\n'.format(angelsno,elapsed)+ '-'*110) 

	def ask(self,what):
		"""
		Opens a new question. A question is a special clue without a
		'value' attribute.
		
		Questions are open for answering by agents.
		"""
	
	def consult_next(self,verbose = True, consider = False,local = False):
		"""
		Consults one non-yet-consulted angel
		"""
		
		for angel in self.guardianangels:
			if isinstance(angel,GuardianAngel) and not angel.consulted:
				return self.consult(angel,verbose,consider,local)
		
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
	
	def expertises(self):
		"""
		Forces all angels to lookup_expertise() and returns them.
		"""
		exps = {}
		for ga in self.guardianangels:
			ga.lookup_expertises()
			exps[ga] = ga.stats['expertises']
			
		return exps
		
	def consultations_registry(self):
		"""
		Returns a dict from guardianangels to [True,False], depending on whether
		they already were consulted or not.
		"""
		
		registry = {}
		
		for ga in self.guardianangels:
			registry[ga] = ga.consulted
		
		gasbyname = [ga.name for ga in self.guardianangels]
		
		for alg in algs.algsbyname:
			if alg not in gasbyname:
				registry[alg] = 0
		
		return registry
	
	def get_angel_plus(self,algorithm):
		"""
		Like get_angel, but also creates the angel and appends it to self.
		guardianangels if not present already.
		"""
		
		if not hasattr(algorithm,'__call__') and not getattr(algs,algorithm.__name__): # checks that algorithm is really an algorithm
			raise TypeError('Bad input type: I need an algorithm from algorithms, got an {} instead'.format(type(algorithm)))
			
		
		angel = [ga for ga in self.guardianangels if ga.name == algorithm.__name__]
		
		if len(angel) != 1:
			raise BaseException("Something wrong: angel is {}".format(angel))
		
		if not angel:
			angel = GuardianAngel(algorithm)
			self.guardianangels.append(angel)
		else:
			angel = angel[0]
			
		return angel
	
	def get_angel(self,algorithm):
		"""
		Returns the guardianangel with the given algorithm.
		If he hasn't it, returns false.
		"""
		angel = [ga for ga in self.guardianangels if ga.name == algorithm.__name__]
		
		if len(angel) != 1:
			raise BaseException("Something wrong: angel is {}".format(angel))
	
		angel = angel[0]
			
		return angel
		
	def ignore(self,agent):
		if not isinstance(agent,Agent):
			raise BaseException('Not an agent.')
		self.ignoreds.append(agent)
	
	def most_trustworthy(self,ctype,crop = 3):
		"""
		returns (crop) of its guardianangels which are most trustworthy
		about links of contenttype ctype.
		"""
		
		ctype = list(ctype) # we make sure they're in the right order
		ctype.sort(reverse = True)
		ctype == ''.join(ctype)
		
		trustranks = {}
		for i in self.guardianangels:
			rel = i.reltrust(ctype)
			trustranks[i] = rel
			
		ranked = list(trustranks)
		ranked.sort(key = lambda x: trustranks[x],reverse = True)
		
		return ranked[:crop]
	
	def remove_tag_similarity_angels(self):
		
		self.guardianangels = [ga for ga in self.guardianangels if ga.name not in ['tag_similarity_naive','tag_similarity_extended']]
	
	# BELIEF MANAGEMENT
	def believes(self,something):
		"""
		Returns the extent to which god believes something. If something
		is not in the belief set, returns zero.
		"""
		return self.beliefs.get(something,0.0)

	def rebelieves(self,something,weight = True,silent = True):
		"""
		Bypass for the clues mechanism:
		directly asks to all of his trustees (GuardianAngels only) how much 
		they believe or not something.
		
		By default, [weight] takes into account the belief_with_feedback
		of each angel into (something).
		
		This clearly entails that if the ga's evaluation is empty or ill
		formed, the result will always be wrong.
		
		WARNING: modifies god's belief bank to match the output. Thus, all
		effects of learningspeed are lost.
		"""
		
		if something in self.logs and self.logs[something]:
			self.beliefs[something] = ss.avg( [log.weightedvalue() for log in self.logs[something]] )
		
		else:
			for ga in self.guardianangels:
				ga.evaluate(something)
		
	def rebelieves_iter(self,someiter,weight = True,update = False):
		"""
		Bypass for the clues mechanism:
		directly asks to all of his trustees (GuardianAngels only) how much 
		they believe or not something.
		
		By default, [weight] takes into account the belief_with_feedback
		of each angel into (something).
		
		If update is set to false, the rebelief also affects god's current
		state (i.e. his beliefs are updated to the output of rebelief).
		Useful for refresh.
		
		wants an iterable.
		"""
		
		if not hasattr(something,"__iter__"):
			someiter = iter(something)
			returndecision = False
		else:
			someiter = something
			returndecision = True

		for pair in someiter:
			
			decision = self.rebelieves(something,weight,update)
					
		if returndecision:
			try:
				return decision
			except UnboundLocalError: # this means that there were no opinions, or no angels
				pass
		
	def expert_rebelieves(self,something,crop = 3,tw = False):
		"""
		Returns the rebelief value only for those who are most trustworthy
		about the contenttype of something.
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
		
		out = {}
		
		tlen = len(self.beliefs)
		from semanticsky.tests import ProgressBar
		bar = ProgressBar(tlen)
		
		for belief in self.beliefs:
			ctype = ss.utils.ctype(belief)
			if not experts.get(ctype,False):
				experts[ctype] = self.most_trustworthy(ctype,crop)
			cexperts = experts[ctype]
			
			bar() # status bar
				
			rebelief = self.expert_rebelieves(belief,crop,cexperts) # retrieves a weighted sum of what these experts believe about belief
			
			out[belief] = rebelief
		
		print('Expert judgement compiled; crop = {}, saved to self.expert_belief_assessm'.format(crop))	
		self.expert_belief_assessm = out
		
		if local:
			return out
		else:
			return True
		
	def clean_trivial_beliefs(self):
		"""
		Removes from the beliefs zero's: the default IS zero already.
		"""
		
		for belief in list(self.beliefs):
			if not self.beliefs[belief] > 0:
				del self.beliefs[belief]

	def believes_link_by_id(self,anid,anotherid):
		if not hasattr(self,'sky'):
			self.get_sky()
			
		cloud1 = self.sky.get_cloud(anid)
		cloud2 = self.sky.get_cloud(anotherid)
		
		pair = ss.pair(cloud1,cloud2)
		
		return self.believes(pair)
	
	def allinks(self,cloud_or_id):
		"""
		If given a cloud, returns all clouds linked to it; if given an id,
		returns the same but by id.
		"""	
		
		allc = []
		import semanticsky as ss
		if isinstance(cloud_or_id,ss.Cloud):
			for cloud in self.sky.clouds():
				if self.believes(pair(cloud_or_id,cloud)):
					allc.append(cloud)
					
		if isinstance(cloud_or_id,str) or isinstance(cloud_or_id,int):
			for pair in self.beliefs:
				if cloud_or_id in [c.item['id'] for c in pair]:
					
					otherl = [cloud for cloud in pair if cloud.item['id'] != cloud_or_id ]
					other = otherl[0]

					allc.append(other)
		
		return allc
	
	def refresh(self,verbose = True):
		"""
		for belief in self.beliefs:
		self.rebelieves(belief)
		"""
		
		topno = len(self.beliefs)
		if topno:
			from semanticsky.tests import ProgressBar
			bar = ProgressBar(topno,title = 'Refreshing')
		
		for belief in self.beliefs:
			if verbose and topno:

				bar()
						
			self.rebelieves(belief,silent = False) # will update beliefs
	
	def reassess(self,listofitems = None):
		"""
		Forces god to re-assess his belief state. If for example we removed
		a key clue from a well-grounded belief, then we may ask him to reassess
		the belief in order to check the new value of the belief.
		
		listofitems, if given, must be a list of links or believable items
		or a clue.
		"""
		from semanticsky.tests import ispair,avg
		from semanticsky.clues import Clue
		
		if ss.ispair(listofitems):
			listofitems = [listofitems]
		elif isinstance(listofitems,Clue):
			listofitems = [listofitems.about]
		elif isinstance(listofitems,list): # a list of links
			oldbeliefs = listofitems
		elif listofitems is None:
			oldbeliefs = self.beliefs
		else:
			raise BaseException('Bad input: type {}'.format(type(listofitems)))
		
		for belief in oldbeliefs: # list of belief-keys to reassess
			
			bclues = self.logs[belief] # all the clues which led to the current belief's value
			agented = [clue for clue in bclues if clue.agent not in self.guardianangels]
			
			opinions =  []
			for clue in agented:
				opinions.append(clue.weightedvalue())
			
			for angel in self.guardianangels:
				opinions.append(angel.belief_with_feedback(belief))
				
			self.beliefs[belief] = avg(opinions) # denom always != 0 in any case...
		
		return None
	
	def prune_below_unweighted(self,number):
		"""
		Tells God to eliminate from beliefs and logs the beliefs whose unweighted
		confidence is below number.
		"""
		
		for belief in self.beliefs:
			val = self.rebelieves(belief)
			if val <= number:
				if belief in self.beliefs:
					del self.beliefs[belief]
				if belief in self.logs:
					del self.logs[val]
				
	def prune_below_weighted(self,number):
		"""
		Tells God to eliminate from beliefs and logs the beliefs whose weighted
		confidence is below number.
		"""
		for belief in self.beliefs:
			val = self.rebelieves(belief,weight = False)
			if val <= number:
				if belief in self.beliefs:
					del self.beliefs[belief]
				if belief in self.logs:
					del self.logs[val]			
	
	def iter_logged_clues(self):
		"""
		A generator for all clues in the logs.
		"""
		
		for cluelist in self.logs.values():
			for clue in cluelist:
				yield clue
				
				
	# CLEANING
	def remove_tag_clouds(self):
		"""
		For all guardianangels, and from its own beliefs and logs, eliminates
		all traces of clues whose about contains a tag cloud or a tag id.
		"""

		beliefsets = tuple( tuple(tuple(pair for pair in self.beliefs)) + tuple(tuple(pair for pair in ga.beliefs) for ga in self.guardianangels) )
		# type should be ((frozenset({cloud(),cloud()}),),)
		
		toclean = [self.beliefs,self.logs]
		for ga in self.guardianangels:
			toclean.append(ga.evaluation)
		
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
		
		return True

	# BUFFERING
	def bufferize(self,clue):
		"""
		Adds a clue to an internal buffer.
		"""
		self.cluebuffer.append(clue)
		
	def getbuffer(self):
		"""
		Empties the buffer and returns it previous content.
		"""
		
		bffr = self.cluebuffer
		
		self.cluebuffer = []
		
		return bffr
		
	def cleanbuffer(self):
		"""
		empties the cluebuffer.
		"""
		
		self.cluebuffer = []


	# EVALUATION FUNCTIONS -- for testing
	def regrets(self,only_on_true_links = False):
		"""
	
		"""
		
		if not hasattr(self,'knower'):
			from semanticsky.tests import getknower
			self.knower = getknower(self)
			
		if not self.knower.evaluation:
			self.knower.evaluate_all(express = False)
		
		return regret( self.beliefs ,self.knower.evaluation, only_on_true_links = only_on_true_links)
		
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
	
