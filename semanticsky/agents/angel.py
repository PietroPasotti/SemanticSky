#!/usr/bin/python3

from copy import deepcopy
from ..agents import Agent

class GuardianAngel(Agent,object):
	"""
	A GuardianAngel is a bot: an agent whose decisions are generated by
	an algorithm.
	
	- GuardianAngels don't output clues sponteneously; only when prompted to do so
	by God.
	
	- GuardianAngels can't reinforce or weaken each other: they can take feedback
	only on behalf of normal agents or god. (or a special agent such as a
	Knower() instance, which is a training machine for semanticsky.)
	"""
	
	guardianid = 0
	
	def __init__(self,algorithm,supervisor,ghost = False,whisperer = False):
		super().__init__(algorithm.__name__,supervisor)
		
		self.clear_all() # initializes various properties
		
		self.supervisor = supervisor
		self.algorithm = algorithm
		self.stats['trustworthiness'] = 1 # by default, an algorithm's trustworthiness is always one.
		self.__doc__ = self.algorithm.__doc__
		GuardianAngel.guardianid += 1 # counts the GA's spawned
		self.ID = deepcopy(GuardianAngel.guardianid)
		
		if whisperer:
			self.makewhisperer()
			
	def __str__(self):
		return "< GuardianAngel {} of {}>".format(self.name,self.supervisor)
		
	def __repr__(self):
		from semanticsky.tests import wrap
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
		return hash(self.ID)
	
	def shortname(self):
		"""
		Returns a max 4-characters name.
		"""
		import semanticsky.agents.utils.algorithms as algs
		
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
	
	def clear_all(self):
		"""
		(Re)initializes most records.
		"""
		from .utils import BeliefBag
		from copy import deepcopy

		self.zero = 0									# keeps track of 0-valued evaluations produced
		self.nonzero = 0								# keeps track of nonzero evaluations
		self.beliefs = BeliefBag(self)					# will contain all beliefs and handle their weighting, equalizing...
		self.stats = deepcopy(Agent.base_stats_dict)	# stats such as trustworthiness (absolute and contextual)...
		self.produced_feedback = set()					# the name says it all
		self.received_feedback = {}						# idem
		self.clues = []									# will host all produced clues
		self.consulted = False							# this flag goes true iff self.evaluate_all is called on god's sky's full cloudlist (preferably through self.consult() or God.consult(self)).
	
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
		
		if what in self.evaluation:
			evaluation = self.beliefs[what]
		
		else:
			try:
				evaluation = self.algorithm(*what)
				self.beliefs[what] = evaluation # stores the evaluation
				
			except BaseException as e:
				print('ERROR: what == ',what)
				raise e
		
		if not evaluation > 0:
			self.zero += 1
			return 0
		else:
			self.nonzero += 1		
		
		if silent:
			return evaluation
		
		from semanticsky.clues import Clue
		return Clue(what,evaluation,self,autoconsider = consider,trace = 'GuardianAngel.evaluate',supervisor = self.supervisor)
		
	def evaluate_all(self,iterpairs = None,express = True,verbose = True):
		"""
		Tells the GuardianAngel to do a full evaluation:
		evaluates each pair of clouds in the iterable (subscriptable).
		
		evaluate_all(express = False) + express() is equivalent
		to evaluate_all()
		
		Iterpairs defaults to the supervisors' sky's full 2-permutations 
		of clouds. May take long!
		"""
		
		if self.beliefs and iterpairs is None:
			print( """Warning("Warning: evaluation wasn't empty!" Returning...)""")
			return
		if self.clues and express == True:
			print( """Warning("Warning: clues nonempty!")\nsetting express to False.""")
			express = False
			
		if verbose:
			from semanticsky import DEFAULTS
			vb = DEFAULTS['verbosity']
		else:
			vb = 0
		if vb > 0:	
			from tests import wrap
			print('\nSummoning {}...'.format( wrap(str(self),'brightred')) )
		
		if iterpairs is None:
			pairlist = tuple(self.supervisor.sky.iter_pairs())
			self.consulted = True
		else:
			pairlist = iterpairs
				
		li = len(pairlist)
		
		if vb > 1: print('\n>evaluating its way through a {}-item cloud pairlist.<'.format(li))
		
		if vb > 1: bar = semanticsky.tests.ProgressBar(li,title = '{} :: Evaluation'.format(self.shortname()) )
		for pair in pairlist:
			
			if vb > 1:
				bar()

			self.evaluate(pair,silent = False if express else True) # silent: no clue is spawned
	
	def express(self,number = 0,verbose = True):
		"""
		Transforms into clues all the evaluations the angel has in its 
		beliefbag.
		"""
		
		from semanticsky import DEFAULTS
		if verbose:
			vb = DEFAULTS['verbosity']
		else:
			vb = 0
		
		allbeliefs = tuple(self.beliefs.keys())
		
		if not number: 
			number = len(allbeliefs)
		
		if not len(number) > 0:
			if vb > 0:
				print('Nothing to express.')
			return False
		
		if vb > 0: print(repr(self),' is expressing...')
		if vb > 1: bar = ss.ProgressBar(number,title = '{} :: Expressing'.format(self.shortname()))
		
		for i in range(number):
			pair = allbeliefs[i]
			if vb > 1: bar()
			
			value = self.beliefs[pair]
			clue = Clue(pair,value,self,trace = 'GuardianAngel.evaluate',supervisor = self.supervisor)
		
		print()
		return True
	
	def believes(self,belief):  # full pipeline: use this!
		"""
		Full belief pipeline. If equalization and weighting are on and
		available (the belief is of a ctype for which a contextual_tw is
		available, and DEFAULTS['equalization'] is True), returns the equalized
		and then weighted value for self.beliefs[belief].
		Else, returns the LAST value available in the pipeline. (I.e. if weighting
		is available but equalization is not, returns the weighted.)
		
		0 - raw belief value (algorithm output)
		1 - equalized value
		2 - weighted value
		
		"""
		if not self.beliefs[belief] > 0:
			return self.beliefs[belief] # if it's zero, it won't change by weighting or equalizing. Right?
		
		from semanticsky import DEFAULTS
		if DEFAULTS['equalization']:
			value = self.beliefs.equalized(pair) # fetch the equalized value if available
		else:
			value = self.beliefs[pair] # returns 0 if item wasn't evaluated, 0.0 if it was but the evaluation was null
		
		return self.weighted(belief,value) # agent level
	
	def trusted(self):
		"""
		Prints nicely the god.trusts(self) outcome.
		"""
		
		return self.god.trusts(self,local = False)
	
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
					from semanticsky.tests import crop_at_nonzero
					self.stats['expertises'][tw] = crop_at_nonzero(value,4)
		
		return True
	
	def regrets(self,only_on_true_links = False):
		"""
		Computes the regrets of the toplevel belief pipeline available:
		that is, the self.believes output for all the beliefset.
		"""
		
		from .utils import regret
		from semanticsky.tests import diff
		
		return regret(self.beliefs.toplevel() ,self.evaluator.knower.beliefs)