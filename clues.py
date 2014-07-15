import algorithms as algs
import semanticsky as ss
from copy import deepcopy
from group import Group
from semanticsky import pickle
from math import sqrt

CLUES = []
AGENTS = []
GUARDIANANGELS = []
_god = None

@Group
def load_clues_from_default():
	
	try:
		f = open('export_clues.pickle','rb')
		global CLUES
		CLUES = pickle.load(f)
		f.close()
		print('Correctly loaded.')
	
	except Exception:
		return None

	
def export_clues():
	f = open('export_clues.pickle','a+')
	global CLUES
	pickle.dump(CLUES,f)
	print('Correctly dumped.')

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
	
	def __init__(self,about,value,agent = 'god'):
		
		if isinstance(about,frozenset):
			self.cluetype = 'link' 
		elif about in algs.ALL_ALGS:
			self.cluetype = 'feedback' # the clue is about an algorithm's trustworthiness
		elif isinstance(about,Clue): 
			self.cluetype = 'metaclue' # the clue is about the validity of another clue.
		elif isinstance(about,Agent):
			self.cluetype = 'feedback' # the clue is about an agent's trustworthiness
		else:
			raise BaseException('Unrecognized about input: {}.'.format(about))	
			
		self.about = about
		self.value = value
		self.agent = agent
		
		self.handled = False # flag that goes true whenever the clue is processed by God and 'consumed'
		
		global _god
		if agent is 'god' and _god is None:
			Agent('god') 
		
		if hasattr(agent,'clues'):
			agent.clues.append(self)
		
		CLUES.append(self)
	
	def __deepcopy__(self,memo):
		
		ab = self.about # there's no need to copy the about, right?
		va = self.value
		ag = self.agent # nor the agent...
		
		c = Clue(ab,va,ag)
		return c
				
	def __str__(self):
		
		translateclue = {	'link': 'the validity of a link',
							'accuracy': 'the accuracy of an algorithm',
							'metaclue' : 'the usefulness of another clue'}
							
		translatevalue = {		1 : 'accurate',
								-1 : 'inaccurate'}
		
		return "< Clue about {} ({}), which was evaluated '{}' by Agent {}.>".format(translateclue[self.cluetype],self.about,self.value,self.agent)
	
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
		
		return (self.trustworthiness + self.value) / 2
	
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
		
						
		if not isinstance(self,GuardianAngel) and not isinstance(self,God):
			AGENTS.append(self)
		if self.name == 'god':
			self.make_god()
	
	def __str__(self):
		return "< Agent {}.>".format(self.name)
	
	def unique_id(self):
		"""
		What if there are two Agent Smith?
		"""
		
		uniqueid = Agent.idcounter
		Agent.idcounter += 1
		
		uniqueid = self.name + '#' + uniqueid
		return uniqueid
	
	def __deepcopy__(self,memo):
		
		name = deepcopy(self.name)
		a = Agent(name) # so that if it's a special name...
		a.stats = deepcopy(self.stats)
		if self.item:
			a.item = deepcopy(self.item)
		
		return a
		
	def make_god(self):
		
		global _god
		
		if _god is None:
			self = God()
			_god = self
		else:
			self = _god
			
	def evaluate(self,what,howmuch):
		"""
		Formulates a Clue about what, judging it howmuch.
		"""
		
		if self.stats['blocked']:
			return None
		
		if howmuch > 1:
			raise BaseException('Evaluation confidence should not be above one.')
			
		myclue = Clue(what,howmuch,self)
		self.clues.append(myclue)
		return myclue
	
	def receive(self,clue):
		"""
		An agent is the ultimate recipient of a clue: his own trustworthiness
		depends on received clues (that is: clues formulated by others or)
		automatically generated that rate its clues.
		"""
		
		self.stats['trustworthiness'] = ( self.stats['trustworthiness'] + clue.value ) / 2
	
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

class GuardianAngel(Agent,object):
	"""
	A GuardianAngel is a bot: an agent whose decisions are generated by
	an algorithm.
	
	- GuardianAngel don't output clues sponteneously; only when prompted to do so
	by God.
	
	- GuardianAngel can't reinforce or weaken each other: they can take feedback
	only on behalf of normal agents or god.
	"""
	
	zero = 0
	nonzero = 0
	evaluation = {}
	
	def __init__(self,algorithm):
		super().__init__(algorithm.__name__)
		self.algorithm = algorithm
		self.stats['trustworthiness'] = 1 # by default, an algorithm's trustworthiness is always one.
		self.clues = [] # Clues objects
	
	def __str__(self):
		return "< GuardianAngel {} >".format(self.name)
		
	def evaluate(self,what,silent = False):
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
				
		self.evaluation[what] = evaluation # stores the evaluation
		
		if silent:
			return None
				
		myclue = Clue(what,evaluation)
		self.clues.append(myclue)
		self.nonzero += 1
		return myclue
	
	def evaluate_all(self,iterable_clouds):
		"""
		Tells the GuardianAngel to do a full evaluation:
		evaluates each pair of clouds in the iterable (subscriptable).
		"""
				
		for clouda in iterable_clouds:
			i = 1
			for cloudb in iterable_clouds[i:]:
				if clouda is cloudb:
					continue
				pair = frozenset({clouda,cloudb})
				self.evaluate(pair,silent = True) # silent: no clue is spawned
		
			i += 1
	
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
					
class God(Agent,object):
	"""
	The Allmighty.
	"""
	beliefs = {} # a belief is a facts --> [0,1] confidences mapping
	
	def __init__(self,sky = None):
		super().__init__()
		
		if sky:
			self.sky = sky
		
		self.whisperers = []
		
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
	
	def receive(self,clue):
		
		print('God accepts no feedback, mortal.')
		return None


	# HANDLERS and LOGGERS
	def handle_metaclue(self,metaclue):
		"""
		This is a handler for clues about clues1: someone is complaining 
		that a clue1 was useless, or that it was very good.
		Propagate the clue to the agent of clue1.
		"""
		
		target_clue = metaclue.about # the clue which is rated by the metaclue
		metaclue.handled = True
		return target_clue.receive(metaclue) # the metaclue's value will in the end average up or down the target_clue's author's trustworthiness
		
	def handle_link(self,linkclue):
		"""
		where linkclue is a clue about the existence of a link, ( or about
		the similarity of two clouds, if you wish, this function makes god's
		ineffable beliefs change (a bit) accordingly.
		
		God does listen at his Agents' complaints, but they'll have to scream 
		aloud enough.
		"""
		linkclue.handled = True
		return self.update_beliefs(linkclue)
		
	def handle_feedback(self,clue):
		"""
		Handles clues about algorithms and agents.
		"""
		about = clue.about
		
		if isinstance(about, Agent):
			clue.handled = True
			return	about.receive(clue)
			
		elif isinstance(about,str):
			algname = about
			alg = [alg for alg in self.guardianangels if alg.name == algname]
			alg = alg[0]
			clue.handled = True
			return alg.receive(clue)
	
	def log(self,clue):
		"""
		Whenever a clue gets processed by God (or otherwise 'consumed'),
		we log it. Then we will be able to run analyses on the logs, so as
		to determine whether an agent (or algorithm) gave feedback
		whose effects (creation of a new link, downweighting of an algorithm
		or other agent) were appreciated (through more same-direction feedback)
		by other agents.
		"""
		with open('./clues.log','+a') as logs:
			logline = "time::<{}> clue::<{}>\n".format( ss.time.ctime(),str(clue)) # markers for re retrieving
			logs.write(str(logline))
			
		if not hasattr(self,'logs'):
			self.logs = {}
		
		about = clue.about
		#author = clue.agent.unique_id
		#value = clue.value
		
		if not self.logs.get(about):
			self.logs[about] = []
		
		log = clue
		
		self.logs[about].append(log)

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
		
		if isinstance(agent,Agent):
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
		Then, it takes the previous value and backpropagates a feedback,
		influencing its main (?) authors' trustworthiness.
		"""
		
		whispering = clue.agent
		
		targets = []
		
		hist = self.logs.get(clue.about) 	# we check whether the clue's about is logged
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
	
	def consider(self, number = 0):
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
		
		if not CLUES:
			print('No clue.')
			return None
		
		if number > 0:
			restr_clues = CLUES[:number]
			CLUES = CLUES[number:]	
			toread = restr_clues
		elif isinstance(number,Clue):
			toread = [number]
		elif isinstance(number,list) and isinstance(number[0],Clue):
			toread = number
		else:
			toread = CLUES
			CLUES = []
			
		for clue in toread:
			if clue.cluetype in ['link','feedback','metaclue']:
				handler = getattr(self, 'handle_{}'.format(clue.cluetype) )
				handler(clue) # the handler will handle
			else:
				raise BaseException('Unrecognized cluetype: {}.'.format(clue.cluetype))
					
	def consult(self,angels = False,verbose=False,consider = False,local = False):
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
		else:
			raise TypeError('Unrecognized input type: {}'.format(type(angels)))
					
		if verbose: print('angels is: ',' '.join([str(angie) for angie in angels]))
			
		clouds = list(self.sky.clouds())		
		for angel in angels: # the list of opinions thus will be in the same order
			
			if verbose: print('Consulting {}'.format(str(angel)))
			angel.evaluate_all(clouds)
			opinion = angel.evaluation
			
			for pair in opinion: # pairs of clouds
				judgement = opinion[pair] # the judg of angel on pair
				if not opinions.get(pair):
					opinions[pair] = []
				opinions[pair].append(opinion[pair])
		
		# now opinion is of list(dict( {frozenset({Cloud(),Cloud()}) : [ float() ] }  )) type. each dict is a frozenset({clouda,cloudb}) --> [0,1] mapping
		# 	for all links in the database; that is: all possible combinations of clouds.
		
		if verbose: print('Examining opinions...')
		if verbose: 
			ss.stdout.write('[')
			ss.stdout.flush()
		
		counter = 0
		for pair in opinions:
			counter += 1
			if verbose and counter % 1000 == 0:
				ss.stdout.write('.')
				ss.stdout.flush()
			judgements = opinions[pair] # a vector of [0,1] floats, as long as the angels list is
			for i in range(len(judgements)):
				judgement = judgements[i]
				author = self.guardianangels[i]
				newclue = Clue(pair,judgement,author)
			# now god formulates a clue on the guardian's behalf: this way we don't clog the guardian's logs
		if verbose: 
			ss.stdout.write('].  [ {} opinions considered. ]'.format(len(opinions)))
			ss.stdout.flush()
		
		# finally we can call a consider_clues: all listed clues (they get queued automatically, when spawned)
		#	are processed and evaluated by the Lord
		
		if consider:
			self.consider()
		
		elapsed = ss.time.clock() - initime
		
		angelsno = len(angels)
		if verbose: print(' {} angels consulted. [ {} elapsed ]'.format(angelsno,elapsed))

	def ask(self,what):
		"""
		Opens a new question. A question is a special clue without a
		'value' attribute.
		
		Questions are open for answering by agents.
		"""
	
	def has_already_guessed(self,clue):
		"""
		Looks up for the about in god's beliefs and checks the history:
		if the clue's agent has already clued on the same topic, returns
		the previous clue.
		Else, returns False.
		"""
		about = clue.about
		if about in self.beliefs:
			cluelist = self.beliefs[about]
		else:
			cluelist = []
			
		agent = clue.agent
		hisclues = [c for c in cluelist if c.agent == agent]
		if hisclues:
			return hisclues[0]
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
			self.logs[clue.about].remove(prelue)	# his previous clue is erased from the history
													# and the value of the belief in about is updated to the average of the values still in the history
			self.beliefs[clue.about] = sum([c.weightedvalue() for c in self.logs[clue.about]]) / len(self.logs[clue.about])
		
		try:
			after_update = ( previous_belief + (clue.value + clue.trustworthiness) / 2 ) / 2
		except	Exception:
			after_update = 0.0000001

		# positive factor: the previous belief. If previous belief was high, to take it down will take some effort.
		# negative factor: the value of a clue: that is, the strength and direction of the clue.
		# 	the negative factor in turn is affected by the trustworthiness of he who formulated it.
		#	by logging these clues' execution, we can know when an Agent gave 'bad' feedback: that is, feedback that was
		#	later contradicted by many feedbacks on the opposite direction.
		
		self.beliefs[clue.about] = after_update		
		self.log(clue)

	
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
	

		
			
#	def suggest_link(self,link):
			
def init_base():
	global sky
	sky = ss.SemanticSky()
	global god
	god = God()
	
	knower = GuardianAngel(algs.someonesuggested)
	god.consult([knower],consider = True)
	god.consult(consider = True)
	
	print('[ all done. ]')
	
	





