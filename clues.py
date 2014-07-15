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
			self.cluetype = 'accuracy' # the clue is about an algorithm's accuracy
		elif isinstance(about,Clue): 
			self.cluetype = 'metaclue' # the clue is about the validity of another clue.	
		else:
			raise BaseException('Unrecognized about input: {}.'.format(about))	
			
		self.about = about
		self.value = value
		self.agent = agent
		
		global _god
		if agent is 'god' and _god is None:
			Agent('god') 
		
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
		
class Agent(object):
	
	idcounter = 0
	clues = []
	def __init__(self,name = 'Anonymous'):
		
		self.name = name
		self.stats = { 	'trustworthiness': 0.5,
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
				
class God(Agent,object):
	"""
	The Allmighty.
	"""
	beliefs = {} # a belief is a facts --> [0,1] confidences mapping
	
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
		return target_clue.receive(metaclue) # the metaclue's value will in the end average up or down the target_clue's author's trustworthiness
		
	def handle_link(self,linkclue):
		"""
		where linkclue is a clue about the existence of a link, ( or about
		the similarity of two clouds, if you wish, this function makes god's
		ineffable beliefs change (a bit) accordingly.
		
		God does listen at his Agents' complaints, but they'll have to scream 
		aloud enough.
		"""
		
		self.update_beliefs(linkclue)

	def handle_accuracy(self,clue):
		"""
		Handles clues about algorithms.
		"""
		
		algname = clue.about
		alg = [alg for alg in self.guardianangels if alg.name == algname]
		alg = alg[0]
		alg.receive(clue)
	
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
			logline = "[{}] : {}".format( ss.time.ctime(),str(clue))
			logs.write(str(logline))
			
		if not hasattr(self,'logs'):
			self.logs = {}
		
		about = clue.about
		author = clue.agent.unique_id
		value = clue.value
		
		if not self.logs.get(about):
			self.logs[about] = []
		
		log = (author,)
		
		self.logs[about].append(())
	
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
		"""
		
		global CLUES
		
		if not CLUES:
			raise BaseException('No clue.')
		
		if number > 0:
			restr_clues = CLUES[:number]
			CLUES = CLUES[number:]	
			toread = restr_clues
		else:
			toread = CLUES
			
		for clue in toread:
			if clue.cluetype in ['link','accuracy','metaclue','agent_report']:
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
			
		if isinstance(angels,int) and angels < 0: 	# if we only want to consult angel 2, we call self.consult(-2)
			angels = [self.guardianangels[int(sqrt(angels ** 2))]]
		elif isinstance(angels,int):				# if we only want to consult the first three angels, we call self.consult(3)
			newa = []
			for i in range(angels):		
				angel = self.guardianangels[i]
				newa.append(angel)
			angels = newa
		else:										# else: all angels are consulted.
			angels = self.guardianangels
			
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
		
		if verbose: print('Examinating opinions...')
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
		"""

	def update_beliefs(self,clue):
		"""
		Where clue is a clue about anything believable by god.
		"""
		
		try: 
			self.beliefs = self.beliefs		
		except AttributeError:
			self.beliefs = {}

		if not self.beliefs.get(clue.about,False):
			self.beliefs[clue.about] = 0 # the initial belief is zero: if asked 'do you believe x?' default answer is 'no'
					
		previous_belief = self.beliefs[clue.about] 		
		try:
			after_update = ( previous_belief + (clue.value + clue.trustworthiness / 2) ) / 2
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
	global _god
	_god = God()
	
	





