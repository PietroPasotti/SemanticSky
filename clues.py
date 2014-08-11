#!/usr/bin/python3

import algorithms as algs
import semanticsky as ss
from copy import deepcopy
from group import Group
import twupdate_rules as updaterules

pickle = ss.pickle
sqrt = algs.sqrt
crop_at_nonzero = ss.crop_at_nonzero
default_updaterule = updaterules.TWUpdateRule.builtin_update_rules.step_by_step_ls

CLUES = []
AGENTS = []
GUARDIANANGELS = []
god = None
anonymous = None
codedict = None 
knower = None

learningspeed = 0.2 # inertia in receiving feedback: how hard is it for god to come to believe that you're a moron
belief_inertia = 0.1 # pertenth of the previous belief which is maintained no-matter-what

class Feedback(object):
	
	def __init__(self,origin,destination,about,value):
		"""
		Lighter than clues, and no need for god's mediation.
		"""
		
		self.origin = origin
		self.destination = destination
		self.about = about
		self.value = value
	
	def __add__(self,other):
		"""
		Feedback's value!
		"""
		return self.value + other
		
	def __le__(self,other):
		if self.value <= other:
			return True
		else:
			return False
	
	def __ge__(self,other):
		if self.value >= other:
			return True
		else:
			return False
	
	def __float__(self):
		return float(self.value)
	
	def __int__(self):
		return int(self.value)
	
	def __radd__(self,other):
		
		return self + other

	def __key(self):
		return (self.value, self.destination.unique_name(), self.origin.unique_name(), self.about)

	def __eq__(x, y):
		return x.__key() == y.__key()

	def __hash__(self):
		return hash(self.__key())

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
	
	Example usage:
	
	# you can create a custom agent: pietro = clues.Agent('pietro')
	# and then myclue = Clue(link,0.3,pietro)
	# or better pietro.evaluate(link,0.3)
	# if agent is not given, author of the clue will be 'Anonymous'
	myclue = Clue(link,0.3)
	# myclue will be considered by god and it's beliefstate will be influenced
	# by its weighted value; that is: a combination of its confidence (0.3
	# in this case) and the trustworthiness of its author, by default 0.6.
	"""
	
	def __init__(self,about,value,agent = 'Anonymous',autoconsider = True, trace = None,supervisor = None):
		"""
		Autoconsider: toggles queuing of clues.
		"""
		
		self.cluetype = 'link'
		if not str(about.__class__) == "<class 'semanticsky.Link'>":
			self.about = ss.Link(about)

		self.about = about
		self.value = value
		self.trace = trace
		if not supervisor:
			global god
			supervisor = god
		
		self.supervisor = supervisor			
		self.agent = agent
		
		if self.cluetype == 'feedback':
			if hasattr(agent,'feedbackclues'):
				agent.feedbackclues.append(self)
		else:	
			if hasattr(agent,'clues'):
				agent.clues.append(self)
			
		if autoconsider:
			self.supervisor.consider(self) # there the clue gets logged
		else:
			CLUES.append(self)	
	
	def __str__(self):
		return "< Clue about {}, valued {} by {}. >".format(self.ids,crop_at_nonzero(self.value,4),self.agent)
		
	def __repr__(self):
		
		return "< Clue about {}, valued {} by {}. >".format(self.ids,crop_at_nonzero(self.value,4),self.agent)
		
	@property
	def trustworthiness(self):
		"""
		The trustworthiness of a clue is the one of he who formulated it.
		"""
		
		return self.agent.get_tw(self) # returns the relative-to-self's contenttype trustworthiness OR the agent's overall tw if the former is unavailable
	
	@property
	def contenttype(self):
		"""
		Returns the type of the two clouds' items if the about is a link.
		"""
		
		about = self.about
		if isinstance(about,Agent):
			return 'AA' # that is: feedback
		else:
			try:
				return ss.utils.ctype(about)
			except BaseException as e:
				print ('Unknown about type: {} (of type {}).'.format(about,type(about)))
				raise e
			
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
		if self in self.supervisor.logs[self.about]: self.supervisor.logs[self.about].remove(self)
		if self in self.supervisor.logs[self.about]: print(shit,2)
																		# AGENT.clues
		if self in self.agent.clues: self.agent.clues.remove(self)
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
	
	@property
	def ids(self):
		return tuple(cloud.item['id'] for cloud in self.about)

class Agent(object):
	
	idcounter = 0	
	def __init__(self,name,supervisor):
		
		self.name = name
		self.supervisor = supervisor
		self.stats = { 	'trustworthiness': 0.6,
						'relative_tw' : {}, # will map cluetypes to trustworthiness on the cluetype
						'expertises': {},
						'communities': [],
						'blocked' : False}
		
		Agent.idcounter += 1
		self.ID = deepcopy(Agent.idcounter)
						
		self.item = None 	# this can be set to the agent's corresponding starfish item (a dict),
							# 	if the agent's user has a page
		
		self.clues = []       # stores the produced clues
		self.produced_feedback = set()
		self.received_feedback = {} 	# will store the feedbacks received.
						
		if not isinstance(self,GuardianAngel) and not isinstance(self,God):
			AGENTS.append(self)
	
	def __str__(self):
		return "< Agent {}. >".format(self.name)
	
	def __repr__(self):
		from tests import wrap
		return wrap("< Agent {}. >".format(self.name),'red')
	
	def __hash__(self):
		
		return self.ID
	
	def unique_name(self):
		"""
		What if there are two Agent Smith?
		"""
		uniqueid = self.name + '#' + str(self.ID)
		return uniqueid
	
	def shortname(self):
		return 'Agent#{}'.self.ID
	
	def __deepcopy__(self,memo):
		
		name = deepcopy(self.name)
		a = Agent(name) # so that if it's a special name...
		a.stats = deepcopy(self.stats)
		if self.item:
			a.item = deepcopy(self.item)
		
		return a
	
	def isduplicate_fb(self,feedback):
		"""
		Checks whether we already have feedbacked the very same thing.
		"""
		
		for ofeedback in self.produced_feedback:
			if feedback == ofeedback:
				return True
		return False
		
	def feedback(self,destination,about,value,checkforduplicates = True):
		"""
		Produces a feedback object and sends it to destination.
		"""
		
		fb = Feedback(self,destination,about,value)
		
		if fb in destination.received_feedback.get(about,[]): # this is true also if there is an exactly equivalent feedback there! (though being a different object)
			return
		
		destination.receive_feedback(fb)
		self.record_given_feedback(fb)
		
		return
	
	def record_given_feedback(self,feedback):
		"""
		Stores the information about a given feedback.
		"""
		
		self.produced_feedback.add(feedback)

	# EVALUATION
	def evaluate(self,what,howmuch,consider = True):
		"""
		Formulates a Clue about what, judging it howmuch.
		"""
		
		if self.stats['blocked']:
			return None
		
		if not 0 < howmuch <= 1:
			raise BaseException('Evaluation confidence should be in [0,1].')
			
		clue = Clue(what,float(howmuch),self,autoconsider = consider, trace = 'Agent.evaluate',supervisor = self.supervisor)
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
		self.evaluate(clue.about)
		del clue
		
	def receive(self,clue):
		"""
		An agent is the ultimate recipient of a clue: his own trustworthiness
		depends on received clues (that is: clues formulated by others or
		automatically generated that rate its clues.)
		"""
		
		global learningspeed
	
		
		self.logs.append(clue) # we add the clue to logs.
		self.received_feedback.append(ss.crop_at_nonzero(clue.value,3))
		
		#self.logs = [c for c in self.logs if c.agent != clue.agent] # no multiple feedback	

		# reevaluate everything (?)
		
		tw = 1
		for logged in self.logs: # updates on the whole logs
			ctype = clue.contenttype
				
			inertial_trust = self.stats['trustworthiness'] * learningspeed
			
			ow = tw
			tw -= tw
			tw += (( ow + logged.weightedvalue() ) / 2 )+ inertial_trust
			
		self.stats['trustworthiness'] = min([ tw, 1.0 ])
	
	def believes(self,about):
		"""
		Looks up for the about in the spawned clues, and returns
		value and weightedvalue for it.
		"""
		
		value = 0
		weightedvalue = 0
		
		for clue in self.clues:
			if clue.about == about:
				value += clue.value
				weightedvalue += clue.weightedvalue()
				break
	
		return [value,weightedvalue]
		
	# FEEDBACK and WHISPERING
	def receive_feedback(self,feedback,verbose = False):
		"""
		Agent in the past has evaluated [about]. Now someone tells him
		that his evaluation was worth [value].
		"""
		
		about = feedback.about
		origin = feedback.origin
		value = feedback.value	
		
		if not self.received_feedback.get(about):
			self.received_feedback[about] = []
			
		self.received_feedback[about].append(feedback)
		
		if ss.ispair(about):
			ctype = ss.utils.ctype(about)
			
			if not self.stats['relative_tw'].get(ctype):
				self.stats['relative_tw'][ctype] = self.stats['trustworthiness'] 	# if no relative trustworthiness is available for that ctype, we initialize
			
			self.stats['relative_tw'][ctype] = default_updaterule(self.stats['relative_tw'][ctype], feedback, learningspeed,self)	
			
		else:
			print('feedback ignored: about unhandleable (type :  {})'.format(type(about)))
				
	def makewhisperer(self):
		"""
		Adds the agent to god's own whisperlist
		"""
		return self.supervisor.whisperer(self)
	@property
	def iswhisperer(self):
		
		if self in self.supervisor.whisperers:
			return True
		else:
			return False	

	def clean_feedback(self):
		"""
		Resets its trustworthiness logs, as if no feedback had ever happened.
		"""
		
		self.stats = {	'trustworthiness':1,
						'relative_tw': {} }
		self.received_feedback = {}
		
		return True

	# TRUSTWORTHINESS	
	@property
	def trustworthiness(self):
		self.stats['trustworthiness'] = sum(self.stats['relative_tw'].values()) / len(self.stats['relative_tw']) if self.stats['relative_tw'] else self.stats['trustworthiness']
		return self.stats['trustworthiness']
	
	def get_tw(self,clue):
		"""
		Returns the relative tw if available; else returns overall trustworthiness
		"""
		
		relative = self.relative_trustworthiness(clue)
		
		if relative:
			return relative
		else:
			return self.trustworthiness
			
	def relative_trustworthiness(self,clue):
		"""
		Returns self's trustworthiness relative to the clue's contenttype,
		False otherwise.
		"""
		ctype = clue.contenttype
		
		reltw = self.stats['relative_tw'].get(ctype,False)
		
		return reltw

class GuardianAngel(Agent,object):
	"""
	A GuardianAngel is a bot: an agent whose decisions are generated by
	an algorithm.
	
	- GuardianAngel don't output clues sponteneously; only when prompted to do so
	by God.
	
	- GuardianAngel can't reinforce or weaken each other: they can take feedback
	only on behalf of normal agents or god.
	"""
	
	guardianid = 0
	
	def __init__(self,algorithm,supervisor,ghost = False,whisperer = False):
		super().__init__(algorithm.__name__,supervisor)
		
		self.supervisor = supervisor
		
		self.zero = 0
		self.nonzero = 0
		self.evaluation = {}
		self.algorithm = algorithm
		self.stats['trustworthiness'] = 1 # by default, an algorithm's trustworthiness is always one.
		self.clues = [] # Clues objects
		self.consulted = False
		self.logs = []
		self.ghost = ghost
		self.__doc__ = self.algorithm.__doc__
		
		GuardianAngel.guardianid += 1 # counts the GA's spawned
		self.ID = deepcopy(GuardianAngel.guardianid)
		
		GUARDIANANGELS.append(self)
		
		if ghost: # we tell god to ignore self.
			if not hasattr(god,'ignoreds'):
				god.ignoreds = [] # for backwards compatibility
			god.ignore(self)
			self.ghost = True
			
		if whisperer:
			self.makewhisperer()
			
	def __str__(self):
		return "< GuardianAngel {} of {}>".format(self.name,self.supervisor)
		
	def __repr__(self):
		from tests import wrap
		return wrap("< GuardianAngel {} >".format(self.name),'brightcyan')
	
	def __eq__(self,other):
		"""
		Returns true iff the NAME of the two angels is the same; that's
		equivalent to 'having the same algorithm'. 
		"""
		
		try:
			if self.name == other.name or self.algorithm == other.algorithm:
				return True
		except BaseException:
			pass
			
		return False
	
	def __hash__(self):
		return self.ID
	
	def shortname(self):
		"""
		Returns a max 4-characters name.
		"""
		
		transdict = {algs.tf_weighting : 'tf',
			algs.tf_idf_weighting: 'idf',
			algs.coo_dicts_overlap_v1 : 'coo1',
			algs.coo_dicts_overlap_v2 : 'coo2',
			algs.coo_dicts_neighbour : 'cooN',
			algs.coo_dicts_extended_neighbour: 'Ecoo',
			algs.tag_overlap:'tago',
			algs.extended_name_comparison: 'Enam', 
			algs.naive_name_comparison: 'name',
			algs.tag_similarity_naive: 'tags',
			algs.tag_similarity_extended : 'Etag',
			algs.naive_core_overlap : 'core',
			algs.extended_core_overlap : 'corE',
			algs.someonesuggested: 'know'}
			
		return transdict.get(self.algorithm,self.name[0:5])	
	
	# consultation and evaluation functions
	def consult(self):
		self.supervisor.consult(self)
			
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
			return 0
		else:
			self.nonzero += 1		
		
		self.evaluation[what] = evaluation # stores the evaluation
		
		if silent:
			return evaluation
				
		if not self.ghost:
			myclue = Clue(what,evaluation,self,autoconsider = consider,trace = 'GuardianAngel.evaluate',supervisor = self.supervisor)
			return myclue
		else:
			return None
	
	def evaluate_all(self,iterpairs = None,express = True,verbose = True):
		"""
		Tells the GuardianAngel to do a full evaluation:
		evaluates each pair of clouds in the iterable (subscriptable).
		
		evaluate_all(express = False) + express() is equivalent
		to evaluate_all()
		"""
		
		if self.evaluation:
			print( """Warning("Warning: evaluation wasn't empty!" Returning...)""")
			return
		if self.clues and express == True:
			print( """Warning("Warning: clues nonempty!")\nsetting express to False.""")
			express = False
			
		if verbose: 
			from tests import wrap
			print('\nSummoning {}...'.format( wrap(str(self),'brightred')) )
		
		if iterpairs is None:
			iterpairs = self.supervisor.sky.iter_pairs()
			self.consulted = True
			
		pairlist = tuple(iterpairs)
		del iterpairs
		li = len(pairlist)
		
		print('\n>evaluating its way through a {}-item cloud pairlist.<'.format(li))
		
		i = 0
		bar = ss.ProgressBar(li,title = '{} :: Evaluation'.format(self.shortname()) )
		for pair in pairlist:
			
			if verbose:
				bar(i)
			
			silence = False if express else True
			self.evaluate(pair,silent = silence) # silent: no clue is spawned
				
				
			i += 1
	
	def revaluate(self,what,express = True):
		"""
		"""
		if clue not in self.clues:
			raise Warning('Not a clue of mine: {}. I am {}.'.format(clue,self))
			return None
			
		if clue.value > 0:
			self.nonzero -= 1
		
		clue.delete()
		self.evaluate(clue.about,consider = express)
		self.supervisor.reassess(clue)
					
	def revaluate_all(self,iterable_clouds = None, express = True, verbose = True):
		"""
		Deletes all angel's clues and reruns an evaluate_all on the clues' abouts
		"""
		
		allinks = tuple(clue.about for clue in self.clues)
		
		customiter = iter(allinks)
			
		for clue in self.clues:
			clue.delete()
		
		self.evaluate_all(customiter(allinks),express,verbose)
		
		self.supervisor.reassess(allinks) # makes god check again
		
	def express(self,number = 0):
		"""
		Transforms into clues the evaluations previously produced.
		"""
		
		if not number: 
			number = len(self.evaluation.keys())
		
		if not len(self.evaluation.keys()) > 0:
			print('Nothing to express.')
			return False
		
		print(repr(self),' is expressing...')
		bar = ss.ProgressBar(number,title = '{} :: Expressing'.format(self.shortname()))
		for i in range(number):
			pair = list(self.evaluation.keys())[i]
			bar(i)
			
			value = self.evaluation[pair]
			clue = Clue(pair,value,self,trace = 'GuardianAngel.evaluate',supervisor = self.supervisor)
		print()
		return True

	def belief_without_feedback(self,pair):
		return self.evaluation.get(pair,0)
	
	def belief_with_feedback(self,pair):
		return self.evaluation.get(pair,0) * self.stats['relative_tw'].get(ss.utils.ctype(pair),self.trustworthiness )
	
	def reltrust(self,ctype):
		"""
		Returns the relative trustworthiness about clues of type ctype.
		If there is no data on that, returns 0.
		"""
		return self.stats['relative_tw'].get(ctype,0)
	
	def trusted(self):
		"""
		Prints nicely the god.trusts(self) outcome.
		"""
		
		return self.god.trusts(self,local = False)
	
	# comparison functions
	def agrees(self,other = None):
		"""
		Returns a count of the percent of links he agrees about with all
		other angels.
		"""
		
		if not other:
			others = self.supervisor.guardianangels
		
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
	
	def reset_all_but_stats(self):
		"""
		returns a new guardian angel with self's stats and everything else
		clean.
		"""
		
		stats = deepcopy(self.stats)
		
		newga = GuardianAngel(self.algorithm,self.supervisor)
		newga.stats = stats
		return newga
		
	# expertises
	def lookup_expertises(self):
		"""
		Tries to guess which areas he is (most) expert in.
		At the moment, simply updates self.stats['expertises'] with
		whatever he is deemed to be confident enough (relative_tw).
		Enough == 'higher than average'.
		"""
		
		avg = sum(self.stats['relative_tw'].values()) / len(self.stats['relative_tw']) if self.stats['relative_tw'] else 0
		
		for tw,value in self.stats['relative_tw'].items():
			if value > avg:
				if tw not in self.stats['expertises']:
					self.stats['expertises'][tw] = crop_at_nonzero(value,4)
		
		return True
	
class Knower(GuardianAngel,object):
	
	def __init__(self,supervisor):
		
		global knower
		
		if knower:
			raise BaseException('The Knower is already out there!')
			
		
		super().__init__(algs.Algorithm.builtin_algs.someonesuggested,supervisor,whisperer = True)
		knower = self
		supervisor.knower = self

	def __str__(self):
		return "< The Knower >"
		
	def __repr__(self):
		from tests import wrap
		return wrap("< The Knower >",'brightgreen')
	
	def new_supervisor(self,deity,clear = True):
		"""
		Assigns a new supervisor to the knower and clears all preceding logs,
		if [clear].
		"""
		
		self.supervisor = deity
		self.makewhisperer()

		if clear:
			# we assume the previous evaluation was good: we keep it.
			
			# we try to restore the state as if he never expressed.
			for clue in self.clues:
				clue.delete()
			self.clues = []
			
		return

	def give_feedback(self,cluelist = None,verbose = True):
		"""
		Cluelist can be either an Agent instance or an iterable yielding clues.
		In the first case, takes all agent's clues and gives his own feedback
		to them.
		Overrides whisperpipe.
		"""
		
		if str(cluelist.__class__) in ["<class 'clues.GuardianAngel'>","<class 'clues.Agent'>"]:
			cluestovalue = cluelist.clues
		elif isinstance(cluelist,list):
			cluestovalue = cluelist
		elif isinstance(cluelist,Clue):
			cluestovalue = [cluelist]
		else:
			raise BaseException('Unrecognized input type.')
		
		ln = len(cluestovalue)
		i = 0
		
		if ln == 0:
			if verbose:
				print( 'Knower :: Feedback, empty.')
			return True
		
		elif ln <= 100 and verbose:
			print('Knower :: Feedbacking (short).')
			verbose = False			
		
		bar = ss.ProgressBar(ln,title = 'Knower :: Feedback')
		for clue in cluestovalue:
			
			if verbose:
				bar()

			if clue.agent is self:
				continue
				
			eva = self.evaluation.get(clue.about,0) # evaluation is 0 iff not 1
				
			#diff = lambda x,y: max([x,y]) - min([x,y])

			#vals = (clue.value,eva) # how much SELF evaluates it and the other does
			
			# previously it was: our_rating = 1 - diff(*vals) # between 0 and 1, depends on how much the two evaluations differ 
			
			our_rating = eva
			
			# self's opinion on the clue's about.
			self.feedback(clue.agent,clue.about,our_rating,checkforduplicates = False)  # actually produces a Feedback object and sends it through
		
		if verbose:
			print()
		return True
	
	def feedback_all(self,verbose = True):
		god = self.supervisor
		
		if verbose: 
			print()
			i = 0
		
		ln = len(god.logs)
		bar = ss.ProgressBar(ln , title = '{} :: feedback_all'.format(self.shortname()))
		for link in god.logs:
			
			if verbose:
				i += 1
				bar(i)
			
			resps = tuple(clue.agent for clue in god.logs[link])
			for resp in resps:
				self.feedback(resp,link,self.evaluation.get(link,0))
		
		if verbose: 
			print()
							
class God(object):
	"""
	The Allmighty.
	"""
	
	beliefs = {} # a belief is a facts --> [0,1] confidences mapping
	godid = 0
	default_merge = lambda x : sum(x) / len(x)
	
	def __init__(self,sky = None,merging_strategy = default_merge):
		
		self.sky = sky
		self.birthdate = ss.time.gmtime()
		self.guardianangels = []
		self.whisperers = []
		self.cluebuffer = []
		self.logs = {}
		self.ccount = 0 # keeps track of number of clues processed
		self.totcluecount = 0
		self.ignoreds = []
		self.name = 'Yahweh'
		
		self.merging_strategy = merging_strategy # this is what god does to merge his angel's opinions into one.
				
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
		from tests import wrap
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
		
		if isinstance(clue.about,Agent):
			print('warning: updating beliefs with a feedback clue')
		
		if clue.agent in self.ignoreds:  ######### IGNORING
			return None
		
		if not getattr(self,'beliefs'):
			self.beliefs = {}
		
		if not self.beliefs.get(clue.about,False):
			self.beliefs[clue.about] = 0 # the initial belief is zero: if asked 'do you believe x?' default answer is 'no'
					
		previous_belief = self.beliefs[clue.about]
		
		preclue = self.has_already_guessed(clue)
		if preclue: # if the agent has already clue'd about that link or object, we assume he has changed his mind:
			self.logs[clue.about].remove(preclue)	# his previous clue is erased from the history
													# and the value of the belief in about is updated to the average of the values still in the history

		###### UPDATE ALGORITHM
		
		global belief_inertia
		inertia = belief_inertia
		
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

		whispering.give_feedback(targets,refresh = True) # whispering, in the case of GA's,
		#	has the effect of asking them to evaluate the whole cluelist... thus, they will spawn feedbacks for each of them		
		return None
	

	# GUARDIAN ANGELS, CONSULT and CONSIDER			
	def spawn_servants(self,overwrite = False):
		"""
		Creates all GuardianAngels
		"""	
		
		print('Spawning guardians...')
		
		global GUARDIANANGELS
		if overwrite: GUARDIANANGELS = []
		if overwrite: self.guardianangels = []
		
		algos = algs.ALL_ALGS # plain list of all algorithms defined in algorithms
		
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
		
		If update is set to false, the rebelief also affects god's current
		state (i.e. his beliefs are updated to the output of rebelief).
		Useful for refresh.
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
		bar = ss.ProgressBar(tlen)
		i = 0
		for belief in self.beliefs:
			ctype = ss.utils.ctype(belief)
			if not experts.get(ctype,False):
				experts[ctype] = self.most_trustworthy(ctype,crop)
			cexperts = experts[ctype]
			
			bar(i) # status bar
				
			rebelief = self.expert_rebelieves(belief,crop,cexperts) # retrieves a weighted sum of what these experts believe about belief
			
			out[belief] = rebelief
			
			i += 1
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
		self.beliefs[belief] = self.rebelieves(belief)
		"""
		
		so = ss.stdout
		topno = len(self.beliefs)
		if topno:
			bar = ss.ProgressBar(topno,title = 'Refreshing')
		
		i = 1
		for belief in self.beliefs:
			if verbose and topno:
				i += 1			
				bar(i)
			
			
			self.rebelieves(belief,silent = False) # will update beliefs
	
	def reassess(self,listofitems = None):
		"""
		Forces god to re-assess his belief state. If for example we removed
		a key clue from a well-grounded belief, then we may ask him to reassess
		the belief in order to check the new value of the belief.
		
		listofitems, if given, must be a list of links or believable items
		or a clue.
		"""
		
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
				
			self.beliefs[belief] = sum(opinions) / len(opinions) #denom always != 0
		
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
						
		global CLUES
		toclean = [CLUES]				
		for ga in self.guardianangels:
			toclean.append(ga.clues)
		
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

import meta_angels as metangels

def set_update_rule(name):
	
	global default_updaterule
	default_updaterule = getattr(updaterules.TWUpdateRule.builtin_update_rules,name)
	
default_updaterule = set_update_rule('step_by_step_ls')

	
	

