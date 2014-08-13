
import clues
ctype = clues.ss.ctype

class Kronos(clues.God):
	
	"""
	The highest-level deity (for the moment) in the flourishing pantheon
	of Semantic Sky.
	
	Plainly ignoring his god's decisions, he recalculates them based on
	a different metrics. Learning from the GuardianAngels' mistakes and 
	the feedback they received, he computes the factor by which the angels'
	contextual decisions need be multiplied with in order to get as close
	as possible to the suggestions as they emerge from the feedback.
	"""
	
	def __init__(self,*args,**kwargs):
		super().__init__(self,*args,**kwargs)
		
		self.feedbackmap = {}
		self.weights = {}
		
	def __str__(self):
		from tests import wrap
		return wrap("< Chronos :: {} >".format(self.godid),'brightgreen')
	
	def __repr__(self):
		from tests import wrap
		return wrap("< Chronos :: {} >".format(self.godid),'brightgreen')		
	
	@property
	def ctypes(self):
		
		if not hasattr(self,'__allctypes__'):
			self.__allctypes__ = set(ctype(belief) for belief in self.beliefs)
		
		return self.__allctypes__
		
	def get_weights(self):
		"""
		Creates a database of weights for all angel/ctype combinations,
		such that the angel's average output (in terms of confidence ratios)
		once weighted by these, becomes the optimal output (according to
		the feedback so far received by the angel).
		"""
		
		if not hasattr(self,'knower'):
			from belieftests import getknower
			self.knower = getknower(self)
		
		if not self.knower.produced_feedback:
			raise BaseException('No feedback yet.')
		
		for cty in self.allctypes:
			
	
	def relativize(self,belief,angel):
		
		weight_for_ctype = self.weights[angel][ctype(belief)]
		confidence = angel.belief_with_feedback(belief) # already takes relative_tw into account!
		
		
		
	
	def believes(self,something):
		
		weighted_angel_suggestions = []
		
		avg = lambda x: sum(x) / len(x) if x else 0
		
		for clue in self.logs.get(something,[]):
			value = self.relativize(clue.about,clue.agent)
			weighted_angel_suggestions.append(value)
			
		return avg(weighted_angel_suggestions)
	
	
		
		
