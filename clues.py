import algorithms as algs
import semanticsky as ss
from copy import deepcopy
from group import Group
from semanticsky import pickle
from math import sqrt

CLUES = []
AGENTS = []
GUARDIANANGELS = []
god = None

inertia = 0.2 # pertenth of the previous belief which is maintained no-matter-what

class Clue(object):
	"""
	A Clue object stores information about some other object or virtual entity
	such as a relation, and asserts something about its trustworthiness.
	Is a (meant-to-be) universal mean of evaluation.
	
	Clues can be about:
	
	- pairs of Cloud items; then the clue means 'I suspect that these two clouds
	are (not) related'
	
	- an Agent (or GuardianAngel); then the clue means 'This agent's clues
	are (not very) trustworthy.'
	
	To express the degree of confidence in those who produce the clue into
	the clue itself, each clue comes with a 'value' property. The value of
	a clue is its INTENDED strength. Its effective strength depends on its
	author's trustworthiness (which yes, depends on the feedback received
	on her own clues.)
	"""
	
	def __init__(self,about,value,agent = 'god',autoconsider = True):
		"""
		Autoconsider: toggles queuing of clues.
		"""
		
		if isinstance(about,frozenset):
			self.cluetype = 'link' 
		elif about in algs.ALL_ALGS:
			self.cluetype = 'feedback' # the clue is about an algorithm's trustworthiness
		elif isinstance(about,Clue): 
			self.cluetype = 'metaclue' # the clue is about the validity of another clue.
		elif isinstance(about,Agent):
			self.cluetype = 'feedback' # the clue is about an agent's trustworthiness
		elif type(about) == GuardianAngel:
			self.cluetype = 'feedback'
		elif isinstance(about,God):
			return None
		else:
			typelist = [str(x) for x in [Clue,Agent,GuardianAngel,list,frozenset]]
			raise BaseException('Unrecognized about input: {}; which is of type {}.\n'
							'Accepted types are {}.'.format(str(about),type(about),typelist))	
			
		self.about = about
		self.value = value
		
		global god
		if agent == 'god' and god is None:
			agent = Agent('god')
		
		self.agent = agent
		
		god.log(self)  #('   <<< [Warning:] unlogged Clue. God is missing. >>>')
		
		if hasattr(agent,'clues'):
			agent.clues.append(self)
			
		if autoconsider:
			god.consider(self)
		else:
			CLUES.append(self)	
	
	def __str__(self):

		return "< {}-type Clue about {}, valued {} by {}. >".format(self.cluetype,self.about,self.value,self.agent)
	
	def __repr__(self):
		
		return "< {}-type Clue about {}, valued {} by {}. >".format(self.cluetype,self.about,self.value,self.agent)

	@property
	def trustworthiness(self):
		"""
		The trustworthiness of a clue is the one of he who formulated it.
		"""
		return self.agent.stats['trustworthiness']
		
	def receive(self,clue):
		"""
		There also are clues about clues: if the outcome of a clue (the 
		modification of a weight) proves useful, clues can be spawned that
		rate the former clue valuable (or worthless): In this case, the 
		clue backpropagates to its agent (the author) the positive (or 
		negative) feedback.
		"""
		
		return self.agent.receive(clue)
	
	def weightedvalue(self):
		
		return self.trustworthiness * self.value
	
	def delete(self):
		"""
		Removes the clue from wherever it may be.
		"""
		
		shit = 'shit'
																		# CLUES
		if self in CLUES: CLUES.remove(self)
		if self in CLUES: print(shit,1)
				
																		# GOD LOGS
		if self in god.logs[self.about]: god.logs[self.about].remove(self)
		if self in god.logs[self.about]: print(shit,2)
																		# AGENT.clues
		self.agent.clues.remove(self)
		if self in self.agent.clues: print(shit,3)
																		# target agent's .logs
		if self.cluetype == 'feedback':
			self.about.logs.remove(self)
			if self in self.about.logs: print(shit,4)
			
		# self.__dict__ = {} ### risky, and horrible. But makes sure that calling on the clue again will raise an error
		
		return None	
		
	def revaluate(self):
		"""
		Forces its agent to revaluate the about.
		"""
		
		return self.agent.revaluate(self)
	
class Agent(object):
	
	idcounter = 0
	clues = []
	def __init__(self,name = 'Anonymous'):
		
		self.name = name
		self.stats = { 	'trustworthiness': 0.6,
						'expertises': [],
						'communities': [],
						'blocked' : False}
						
		self.item = None 	# this can be set to the agent's corresponding starfish item (a dict),
							# 	if the agent's user has a page
		
		self.logs = [] 		# will store all feedback clues received by the agent
						
		if not isinstance(self,GuardianAngel) and not isinstance(self,God):
			AGENTS.append(self)
		if self.name == 'god':
			self.make_god()
	
	def __str__(self):
		return "< Agent {}.>".format(self.name)
	
	def __repr__(self):
		return "< Agent {}.>".format(self.name)
	
	def unique_id(self):
		"""
		What if there are two Agent Smith?
		"""
		
		uniqueid = Agent.idcounter
		Agent.idcounter += 1
		
		uniqueid = self.name + '#' + str(uniqueid)
		return uniqueid
	
	def __deepcopy__(self,memo):
		
		name = deepcopy(self.name)
		a = Agent(name) # so that if it's a special name...
		a.stats = deepcopy(self.stats)
		if self.item:
			a.item = deepcopy(self.item)
		
		return a
		
	def make_god(self):
		
		global god
		
		if god is None:
			self = God()
			god = self
		else:
			self = god
			
	def evaluate(self,what,howmuch):
		"""
		Formulates a Clue about what, judging it howmuch.
		"""
		
		if self.stats['blocked']:
			return None
		
		if howmuch > 1:
			raise BaseException('Evaluation confidence should not be above one.')
			
		clue = Clue(what,float(howmuch),self)
		#self.clues.append(myclue) # Clue already does it
		return clue
	
	def revaluate(self,clue):
		"""
		Asks an agent to reconsider his clue.
		"""
		
		if clue not in self.clues:
			raise Warning('Not a clue of mine: {}. I am {}.'.format(clue,self))
			return None
			
		if clue.value > 0:
			self.nonzero -= 1
		
		clue.delete()
		
	def receive(self,clue):
		"""
		An agent is the ultimate recipient of a clue: his own trustworthiness
		depends on received clues (that is: clues formulated by others or
		automatically generated that rate its clues.)
		"""
		
		global inertia
		
		inertial_trust = self.stats['trustworthiness'] * inertia
		
		tw = ( self.stats['trustworthiness'] + clue.value ) / 2 + inertial_trust
		self.stats['trustworthiness'] = min([ tw, 1.0 ])
		
		self.logs.append(clue)
	
	def suggest_link(self,link,confidence):
		"""
		A link must be of type frozenset({Cloud(),Cloud()}).
		The belief in that link's validity is clued +1 by the agent.
		"""
		error = False
		if not (isinstance(link, frozenset) and len(link) == 2):
			error = True 
		
		tuplelink = tuple(link)
		if not (isinstance(tuplelink[0],ss.Cloud) and isinstance(tuplelink[1],ss.Cloud)):
			error = True
		if error:
			raise BaseException('Bad link type: {} ; frozenset({Cloud(),Cloud()}) needed.'.format(type(link)))
			
		self.evaluate(link,confidence)
	@property
	def iswhisperer(self):
		
		if self in god.whisperers:
			return True
		else:
			return False	
	@property
	def trustworthiness(self):
		return self.stats['trustworthiness']
		
	def makewhisperer(self,agod = None):
		"""
		Adds the agent to god's own whisperlist
		"""
		if not agod:
			agod = god
		return agod.whisperer(self)
	
	def whisper(self,what,howmuch = None):
		"""
		Spawns a clue straight into god's whisperpipe, bypassing the whisperer
		check.
		"""
		
		if not howmuch: # we assume what is a clue
			if not isinstance(what,Clue):
				raise TypeError('Bad input: {}.'.format(what))
			god.whisper(clue)
		
		# otherwise we make one
			
		clue = self.evaluate(what,howmuch)
		god.whisper(clue)
		
class GuardianAngel(Agent,object):
	"""
	A GuardianAngel is a bot: an agent whose decisions are generated by
	an algorithm.
	
	- GuardianAngel don't output clues sponteneously; only when prompted to do so
	by God.
	
	- GuardianAngel can't reinforce or weaken each other: they can take feedback
	only on behalf of normal agents or god.
	"""

	def __init__(self,algorithm):
		super().__init__(algorithm.__name__)
		
		self.zero = 0
		self.nonzero = 0
		self.evaluation = {}
		self.algorithm = algorithm
		self.stats['trustworthiness'] = 1 # by default, an algorithm's trustworthiness is always one.
		self.clues = [] # Clues objects
		self.consulted = False
		
		GUARDIANANGELS.append(self)
		
	def __str__(self):
		return "< GuardianAngel {} >".format(self.name)
		
	def __repr__(self):
		return "< GuardianAngel {} >".format(self.name)
		
	def evaluate(self,what,silent = False,consider = True):
		"""
		what must be a pair-of-clouds instance, for the moment.
		
		returns the clue.
		
		In silent mode, only the evaluation is returned. Useful for when
		god wants to choose between its GuardianAngel the best judgement
		before taking it into account.
		"""
		
		try:
			evaluation = self.algorithm(*what)
		except BaseException as e:
			print('what == ',what)
			raise e
		
		if not evaluation > 0:
			self.zero += 1
			return None
		else:
			self.nonzero += 1		
		
		self.evaluation[what] = evaluation # stores the evaluation
		
		if silent:
			return None
				
		myclue = Clue(what,evaluation,self,autoconsider = consider)
		
		return myclue
	
	def evaluate_all(self,iterpairs = None,express = True,verbose = True):
		"""
		Tells the GuardianAngel to do a full evaluation:
		evaluates each pair of clouds in the iterable (subscriptable).
		
		evaluate_all(express = False) + express() is equivalent
		to evaluate_all()
		"""
		
		if iterpairs is None:
			iterpairs = sky.iter_pairs()
			self.consulted = True
			
		pairlist = list(iterpairs)
		li = len(pairlist)
		
		
		print('>judging over a {}-item cloud pairlist.<'.format(li))
		
		i = 0
		for pair in pairlist:
			
			if verbose:
				ss.bar(i/li)
				
			if express:
				self.evaluate(pair) 
			else:
				self.evaluate(pair,silent = True) # silent: no clue is spawned
				
				
			i += 1
			
	def revaluate_all(self,iterable_clouds = None, express = True, verbose = True):
		"""
		Deletes all angel's clues and reruns an evaluate_all on the clues' abouts
		"""
		
		allinks = [clue.about for clue in self.clues]
		
		def customiter(linkslist):
			 for link in linkslist:
				 yield link
			
		for clue in self.clues:
			clue.delete()
		
		self.evaluate_all(customiter(allinks),express,verbose)
		
		god.reassess(allinks) # makes god check again
		
	def express(self,number = 0):
		"""
		Transforms into clues the evaluations previously produced.
		"""
		
		if not number: 
			number = len(self.evaluation.keys())
		
		if not len(self.evaluation.keys()) > 0:
			return False
		
		for i in range(number):
			pair = list(self.evaluation.keys())[i]
			value = self.evaluation[pair]
			clue = Clue(pair,value,self)
		
		return True
	
	# comparison functions
	def agrees(self,other = None):
		"""
		Returns a count of the percent of links he agrees about with all
		other angels.
		"""
		
		if not other:
			others = god.guardianangels
		
		if other:
			if not isinstance(other,list):
				others = [other]
		
		out = {}
		
		for angel in others:
			
			
			if angel is self:
				continue

			outangel = {}
			
			pairsagreedon = 0
			agreement = 0
			for pair in angel.evaluation:
				if self.evaluation.get(pair):
					myeval = self.evaluation[pair]
					hiseval = angel.evaluation[pair]
					agreement += min(myeval,hiseval)
					pairsagreedon += 1
					
			totpairs = len(set(angel.evaluation).union(set(self.evaluation)))
	
			outangel['average agreement'] = agreement / totpairs
			outangel['pairs agreed upon'] = pairsagreedon
			
			out[angel] = outangel
		
		return out
			
class God(Agent,object):
	"""
	The Allmighty.
	"""
	
	beliefs = {} # a belief is a facts --> [0,1] confidences mapping
	
	def __init__(self,sky = None,god = None):
		super().__init__()
		
		if sky:
			self.sky = sky
		
		del self.item
		self.birthdate = ss.time.gmtime()
		self.whisperers = []
		self.logs = {}
		self.stats['trustworthiness'] = 1
		
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
		return "< The Lord >"
	
	def __repr__(self):
		return "< The Lord >"
	
	def receive(self,clue):
		
		print('God accepts no feedback, mortal.')
		return None


	# HANDLERS
	def handle_metaclue(self,metaclue):
		"""
		This is a handler for clues about clues1: someone is complaining 
		that a clue1 was useless, or that it was very good.
		Propagate the clue to the agent of clue1.
		"""
		
		target_clue = metaclue.about # the clue which is rated by the metaclue
		return target_clue.receive(metaclue) # the metaclue's value will in the end average up or down the target_clue's author's trustworthiness
		
	def handle_link(self,linkclue):
		"""
		where linkclue is a clue about the existence of a link, ( or about
		the similarity of two clouds, if you wish, this function makes god's
		ineffable beliefs change (a bit) accordingly.
		
		God does listen at his Agents' complaints, but they'll have to scream 
		aloud enough.
		"""
		return self.update_beliefs(linkclue)
		
	def handle_feedback(self,clue):
		"""
		Handles clues about algorithms and agents.
		"""
		about = clue.about
		
		if isinstance(about, Agent):
			return	about.receive(clue)
			
		elif isinstance(about,str):
			algname = about
			alg = [alg for alg in self.guardianangels if alg.name == algname]
			alg = alg[0]
			return alg.receive(clue)
	
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
		hisclues = [c for c in cluelist if c.agent == agent]
		
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
		
		if not getattr(self,'beliefs'):
			self.beliefs = {}
			
		if not self.beliefs.get(clue.about,False):
			self.beliefs[clue.about] = 0 # the initial belief is zero: if asked 'do you believe x?' default answer is 'no'
					
		previous_belief = self.beliefs[clue.about]
		
		preclue = self.has_already_guessed(clue)
		if preclue: # if the agent has already clue'd about that link or object, we assume he has changed his mind:
			self.logs[clue.about].remove(preclue)	# his previous clue is erased from the history
													# and the value of the belief in about is updated to the average of the values still in the history
			self.beliefs[clue.about] = 0
			
			if self.logs[clue.about]: 
				self.consider(self.logs[clue.about])
		
		###### UPDATE ALGORITHM
		
		global inertia
		
		VALUE = clue.weightedvalue()
		
		if not previous_belief > 0: # no previous belief: inertia doesn't apply
			after_update = 	VALUE
		
		else:
			if VALUE > previous_belief: # the belief is growing:
				# inertia will push it down
				inertia_strength = (VALUE - previous_belief) * inertia # if inertia is 0.3, the 30% of all 'changes of mind' will be ignored
			
			elif previous_belief > VALUE: # belief is being devaluated
				
				inertia_strength = (previous_belief - VALUE) * inertia
			
			else:
				inertia_strength = 0
			
			after_update = ( (VALUE + previous_belief) / 2 ) - inertia_strength
		
		#####


		# positive factor: the previous belief. If previous belief was high, to take it down will take some effort.
		# negative factor: the value of a clue: that is, the strength and direction of the clue.
		# 	the negative factor in turn is affected by the trustworthiness of he who formulated it.
		#	by logging these clues' execution, we can know when an Agent gave 'bad' feedback: that is, feedback that was
		#	later contradicted by many feedbacks on the opposite direction.
		
		self.beliefs[clue.about] = after_update		
	
	
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
		#author = clue.agent.unique_id
		#value = clue.value
		
		if not self.logs.get(about):
			self.logs[about] = []
		
		log = clue
		
		self.logs[about].append(log)
	
	def lenlogs(self):
		"""
		Calculates the number of logs stored.
		"""
		
		return len(ss.lsum(list(self.logs.values())))
		
		
	
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
		
		global CLUES,AGENTS,inertia
		
		self.CLUES = CLUES
		self.AGENTS = AGENTS
		self.inertia = inertia
		
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
	
	def trusts(self,agents = []):
		"""
		Returns a trustdict, or a single value if agents is a single Agent.
		"""
		
		trustdict = {}
		
		if not agents:
			agents = AGENTS
			agents.extend(self.guardianangels)
		elif not isinstance(agents,list):
			agents = [agents]
		elif isinstance(agents,Agent):
			return agents.trustworthiness 
		else:
			pass
			
		for agent in agents:
			trustdict[agent] = agent.trustworthiness
			
		return trustdict

	
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
		This function takes a clue and compares its contents with the current
		belief state.
		
		Can also be used to override the whisperers list.
		
		Then, it takes the previous value and backpropagates a feedback,
		influencing its main (?) authors' trustworthiness.
		"""
		
		whispering = clue.agent
		
		targets = []
		
		hist = self.logs.get(clue.about,[]) 	# we check whether the clue's about is logged
									# suppose for example that god has a strong belief (1) in x, due to A's very confident +1 suggestion. (logged)
									# then a whisperer rates x 0.4, which is lower than 1.
									# then, since A is a whisperer, the (x,0.4) clue will be whispered and not just considered 
		
		responsibles = {c.agent for c in hist}
		
		responsibilities = {} # will map responsibles to their clue(s' average) value
		
		for responsible in responsibles:
			allhisclues = [c for c in hist if c.agent is responsible] # in case this agent spawned multiple clues about this item...
			if len(allhisclues) > 1:
				val = sum([c.value for c in allhisclues]) / len(allhisclues)
			else:
				val = allhisclues[0].value
			responsibilities[responsible] = val
			
		for responsible in responsibilities:
			# now we automatically spawn a clue about the agent: we will grade him up or down depending on how much was his clue close to this one..

			if responsible is whispering: # you cant' whisper about yourself
				continue
				
			vals = (clue.value,responsibilities[responsible])
			
			our_rating = 1 - (max(vals) - min(vals)) # between 0 and 1, depends on how much the two evaluations differ 
			
			Clue(responsible, our_rating, agent = whispering)
				# we spawn a clue on the whisperer's behalf, about the responsible's trustworthiness
			
		return None
	

	# GUARDIAN ANGELS, CONSULT and CONSIDER			
	def spawn_servants(self):
		"""
		Creates all GuardianAngels
		"""	
		
		global GUARDIANANGELS
		GUARDIANANGELS = []
		self.guardianangels = []
		
		algos = algs.ALL_ALGS # plain list of all algorithms defined in algorithms
		
		for algorithm in algos:
			GA = GuardianAngel(algorithm)
			GUARDIANANGELS.append(GA)
			self.guardianangels.append(GA)
	
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
				print('No clue!')
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
			if clue.cluetype in ['link','feedback','metaclue']:
				handler = getattr(self, 'handle_{}'.format(clue.cluetype) )
				self.whisperpipe(clue) # check whether we have to whisper the clue
				handler(clue) # the handler will handle
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
			
			if verbose: print('Consulting {}'.format(str(angel)))
			angel.evaluate_all()
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
			if not angel.consulted:
				return self.consult(angel,verbose,consider,local)
		
	def consult_missing(self,verbose = True, consider = False,local = False):
		"""
		Asks god to consult (& consider) all the guardianangels who weren't
		so far.
		"""
		
		reg = self.consultations_registry()
		toconsult = []
		for ga in reg:
			if not reg[ga]:
				toconsult.append(ga)
		
		self.consult(toconsult,verbose,consider,local)
	
	def consultations_registry(self):
		"""
		Returns a dict from guardianangels to [True,False], depending on whether
		they already were consulted or not.
		"""
		
		registry = {}
		
		for ga in self.guardianangels:
			
			registry[ga] = ga.consulted
		
		return registry
	
	
	# BELIEF MANAGEMENT
	def believes(self,something):
		"""
		Returns the extent to which god believes something. If something
		is not in the belief set, returns zero.
		"""
		return self.beliefs.get(something,0.0)
	
	def clean_trivial_beliefs(self):
		"""
		Removes from the beliefs zero's: the default IS zero already.
		"""
		
		newbeliefs = {}
		
		for belief in iter(list(self.beliefs.keys())):
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
	
	def refresh(self,topno = 0,verbose = True):
		"""
		For each logged clue, takes the author and asks him to reassess
		the clue's value.
		"""
		
		so = ss.stdout
		topno = max((topno,len(self.logs)))
		
		i = 0
		for belief in self.logs:
			if verbose:
				ss.bar(i/topno)
				
			del self.beliefs[belief]
			prelogs = deepcopy(self.logs[belief]) # previously existing logs
			del self.logs[belief] # delete the entry
			
			for clue in prelogs:
				clue.revaluate()
							
			if i >= topno:
				break
			
			i += 1
		
		if verbose:
			if topno:
				so.write(' [ Done {}. ]'.format(topno))
			else:
				so.write(' [ All done. ]')
			so.flush()

	
	# IGNORE and REASSESS
	def ignore(self,agents):
		"""
		Produces a new god whose logs have been cleaned of all agents' clues
		and calls a rededuce() so that the new belief state is newly produced
		from the remaining clues.
		
		returns the new god, and stores it in a temporary global.
		"""
		
		newgod = God()
		
		for belief in self.beliefs:
			newgod.logs[belief] = [ clue for clue in self.beliefs[belief] if clue.agent not in agents ]
		
		newgod.reassess()
		
		global _temp_newgod
		_temp_newgod = newgod
		
		return newgod
	
	def reassess(self,listofitems = None):
		"""
		Forces god to re-assess his belief state. If for example we removed
		a key clue from a well-grounded belief, then we may ask him to reassess
		the belief in order to check the new value of the belief.
		
		listofitems, if given, must be a list of links or believable items
		"""
		
		if ss.ispair(listofitems):
			listofitems = [listofitems]
		
		if isinstance(listofitems,list): # a list of links
			oldbeliefs = listofitems
		elif listofitems is None:
			oldbeliefs = deepcopy(self.beliefs)
		else:
			raise BaseException('Bad input: type {}'.format(type(listofitems)))
		
		for belief in oldbeliefs:
			
			bclues = self.logs[belief] # all the clues which led to the current belief's value
			if belief in self.beliefs:
				del self.beliefs[belief] # we delete the old one
			self.consider(bclues) # and create an updated one
		
		return None
		
def init_base():
	global sky
	sky = ss.SemanticSky()
	global god
	god = God()
	
	knower = GuardianAngel(algs.someonesuggested)
	god.consult([knower],consider = True)
	god.consult(consider = True)
	
	print('[ all done. ]')
	
	





