#!/usr/bin/python3

"""
Base class for all Gods, GuardianAngels and Knowers.
"""

class Agent(object):
	
	idcounter = 0	
	
	def __init__(self,name,supervisor):
		
		from .utils import BeliefBag
		from copy import deepcopy
		from semanticsky import DEFAULTS
		
		self.name = name
		self.supervisor = supervisor
		self.stats = deepcopy(DEFAULTS['agent_base_stats'])
		
		Agent.idcounter += 1
		self.ID = deepcopy(Agent.idcounter)
						
		self.item = None 	# this can be set to the agent's corresponding starfish item (a dict),
							# 	if the agent's user has a page
		
		self.clues = []       			# stores the produced clues; quite useless in production code
		self.produced_feedback = set()	
		self.received_feedback = {} 	# will store the feedbacks received.
		
		self.beliefbag = BeliefBag(self)
	
	def __str__(self):
		return "< Agent {}. >".format(self.name)
	
	def __repr__(self):
		from semanticsky.tests import wrap
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
	
	def isduplicate_fb(self,feedback):
		"""
		Checks whether we already have feedbacked the very same thing.
		"""
		
		for ofeedback in self.produced_feedback:
			if feedback == ofeedback:
				return True
		return False
		
	def feedback(self,destination,about,value,sign):
		"""
		Produces a feedback object and sends it to destination.
		"""
		
		from .utils import Feedback
		Feedback(self,destination,about,value,sign)
				
		#destination.receive_feedback(fb)
		#self.record_given_feedback(fb) # this is now done by Feedback.go()
		
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
		
		from semanticsky.clues import Clue
		
		if self.stats['blocked']:
			return None
		
		if not 0 < howmuch <= 1:
			raise BaseException('Evaluation confidence should be in [0,1].')
		
		self.beliefbag[what] = howmuch # records the evaluation
		clue = Clue(what,float(howmuch),self,autoconsider = consider, trace = 'Agent.evaluate',supervisor = self.supervisor)
		return clue
		
	def believes(self,about):
		"""
		Looks up for the about in the spawned clues, and returns
		value and weightedvalue for it.
		
		Full belief pipeline for agent is:
		[raw belief, weighted belief] 
		"""
		
		if not self.beliefbag[belief] > 0:
			return self.beliefbag[belief] # if it's zero, it won't change by weighting or equalizing. Right?
		
		# agents never equalize. Right?
		
		return self.weighted(belief) # but they weight.

	def weighted(self,belief,value = None):
		"""
		Returns the weighted value for belief.
		"""
		if value: # can be provided in case we want to weight an equalized value
			pass
		else:
			value = self.beliefbag[belief] # fetch the raw_value
		
		
		from semanticsky.skies.clouds.core import ctype
		weight = self.get_tw( ctype(belief) ) 	# fetches the contextual tw if available, else the overall trustworthiness.
												# if DEFAULTS['normalization of tws'] is True, also, this takes care of it at Agent's level.
		
		return value * weight 
		
	# FEEDBACK and WHISPERING
	def receive_feedback(self,feedback,verbose = False):
		"""
		Agent in the past has evaluated [about]. Now someone tells him
		that the correct evaluation should instead be [value].
		"""
		from semanticsky.skies.clouds.core import ctype
		from semanticsky import DEFAULTS
		
		if not self.received_feedback.get(feedback.about):
			self.received_feedback[feedback.about] = []
			
		self.received_feedback[feedback.about].append(feedback)
		
		c = ctype(feedback.about)
			
		if not self.stats['contextual_tw'].get(c):
			self.set_contextual_tw(c, self.trustworthiness) 	# if no relative trustworthiness is available for that ctype, we initialize it to the overall value
			
		if feedback.sign == '-' and DEFAULTS['differentiate_learningspeeds']:
			LS = DEFAULTS['learningspeed'] / DEFAULTS['negative_feedback_learningspeed_reduction_factor']
			# for negative feedback we (can) give less impacting feedback.
		
		else:
			LS = DEFAULTS['learningspeed']
		
		self.stats['contextual_tw'][c] = DEFAULTS['default_updaterule'](self.get_tw(c), feedback, LS, self)	
		
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
						'contextual_tw': {} }
						
		self.received_feedback = {}
		
		return True

	# TRUSTWORTHINESS	
	@property
	def trustworthiness(self):
		"""
		Returns the average of all the contextual trustworthinesses the
		agent has, if any, else self.stats['trustworthiness'], which
		is then likely to be (the initial default for virgin angels).
		"""
		
		self.stats['trustworthiness'] = sum(self.stats['contextual_tw'].values()) / len(self.stats['contextual_tw']) if self.stats['contextual_tw'] else self.stats['trustworthiness']
		return self.stats['trustworthiness']

	def reltrust(self,ctype):
		"""
		Returns the relative trustworthiness about clues of type ctype.
		If there is no data on that, returns 0.
		"""
		return self.stats['contextual_tw'].get(ctype,0)

	def normalize_tw(self,weight):
		"""
		Transforms a weight into a weight relative to the agent's maximum
		relative trustworthiness, so that some tw is always one.
		"""
		
		return weight / max(self.stats['contextual_tw'].values()) # returns a value between 0 and 1
	
	def set_contextual_tw(self,ctype,value):
		"""
		Does what it says and nothing more.
		"""
		
		self.stats['contextual_tw'][ctype] = value
	
	def get_tw(self,ctype):
		"""
		Returns the relative tw if available; else returns overall trustworthiness
		"""
		
		contextual = self.get_contextual_trustworthiness(ctype)
		
		if contextual:
			from semanticsky import DEFAULTS 
			if DEFAULTS['normalization_of_trustworthinesses']: # defaults to false
				return self.normalize_tw(contextual)
			else:
				return contextual
		else:
			return self.trustworthiness
			
	def get_contextual_trustworthiness(self,ctype):
		"""
		Returns self's trustworthiness relative to the clue's contenttype,
		False if he has none.
		"""
		
		reltw = self.stats['contextual_tw'].get(ctype,False)
		
		return reltw
