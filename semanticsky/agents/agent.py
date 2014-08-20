#!/usr/bin/python3

from .utils import BeliefBag,Feedback,belief_rules
from copy import deepcopy

class Agent(object):
	
	idcounter = 0	
	def __init__(self,name,supervisor):
		
		self.name = name
		self.supervisor = supervisor
		self.stats = { 	'trustworthiness': 0.6,
						'contextual_tw' : {}, # will map cluetypes to trustworthiness on the cluetype
						'expertises': {},
						'communities': [],
						'blocked' : False}
		
		Agent.idcounter += 1
		self.ID = deepcopy(Agent.idcounter)
						
		self.item = None 	# this can be set to the agent's corresponding starfish item (a dict),
							# 	if the agent's user has a page
		
		self.clues = []       			# stores the produced clues; quite useless in production code
		self.produced_feedback = set()	
		self.received_feedback = {} 	# will store the feedbacks received.
		
		self.beliefs = BeliefBag(self)
	
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
	
	def isduplicate_fb(self,feedback):
		"""
		Checks whether we already have feedbacked the very same thing.
		"""
		
		for ofeedback in self.produced_feedback:
			if feedback == ofeedback:
				return True
		return False
		
	def feedback(self,destination,about,value,sign,checkforduplicates = True):
		"""
		Produces a feedback object and sends it to destination.
		"""
		
		fb = Feedback(self,destination,about,value,sign)
		
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
		
		self.beliefs[what] = howmuch # records the evaluation
		clue = Clue(what,float(howmuch),self,autoconsider = consider, trace = 'Agent.evaluate',supervisor = self.supervisor)
		return clue
		
	def believes(self,about):
		"""
		Looks up for the about in the spawned clues, and returns
		value and weightedvalue for it.
		"""
		
		if not self.beliefs[belief] > 0:
			return self.beliefs[belief] # if it's zero, it won't change by weighting or equalizing. Right?
		
		# agents never equalize. Right?
		
		return self.weighted(belief) # but they weight.

	def weighted(self,belief,value = None):
		"""
		Returns the weighted value for belief.
		"""
		if value: # can be provided in case we want to weight an equalized value
			pass
		else:
			value = self.beliefs[belief] # fetch the raw_value
		
		
		from semanticsky.tests import ctype
		weight = self.get_tw( ctype(belief) ) 	# fetches the contextual tw if available, else the overall trustworthiness.
												# if DEFAULTS['normalization of tws'] is True, also, this takes care of it at Agent's level.
		
		return value * weight 
		
	# FEEDBACK and WHISPERING
	def receive_feedback(self,feedback,verbose = False):
		"""
		Agent in the past has evaluated [about]. Now someone tells him
		that the correct evaluation should instead be [value].
		"""
		
		about = feedback.about
		origin = feedback.origin
		value = feedback.value	
		
		if not self.received_feedback.get(about):
			self.received_feedback[about] = []
			
		self.received_feedback[about].append(feedback)
		
		if ss.ispair(about):
			ctype = ss.utils.ctype(about)
			
			if not self.stats['contextual_tw'].get(ctype):
				self.stats['contextual_tw'][ctype] = self.stats['trustworthiness'] 	# if no relative trustworthiness is available for that ctype, we initialize
			
			if feedback.sign == '-' and differentiate_learningspeeds:
				LS = learningspeed / negative_feedback_learningspeed_reduction_factor
				# for negative feedback we give less impacting feedback.
			else:
				LS = learningspeed
			
			self.stats['contextual_tw'][ctype] = default_updaterule(self.stats['contextual_tw'][ctype], feedback, LS, self)	
			
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
						'contextual_tw': {} }
						
		self.received_feedback = {}
		
		return True

	# TRUSTWORTHINESS	
	@property
	def trustworthiness(self):
		self.stats['trustworthiness'] = sum(self.stats['contextual_tw'].values()) / len(self.stats['contextual_tw']) if self.stats['contextual_tw'] else self.stats['trustworthiness']
		return self.stats['trustworthiness']

	def reltrust(self,ctype):
		"""
		Returns the relative trustworthiness about clues of type ctype.
		If there is no data on that, returns 0.
		"""
		return self.stats['contextual_tw'].get(ctype,0):

	def normalize_tw(self,weight):
		"""
		Transforms a weight into a weight relative to the agent's maximum
		relative trustworthiness, so that some tw is always one.
		"""
		
		return weight / max(self.stats['contextual_tw'].values()) # returns a value between 0 and 1
	
	def get_tw(self,ctype):
		"""
		Returns the relative tw if available; else returns overall trustworthiness
		"""
		
		contextual = self.contextual_trustworthiness(ctype)
		
		if contextual:
			from semanticsky import DEFAULTS 
			if DEFAULTS['normalization_of_trustworthinesses']: # defaults to false
				return self.normalize_tw(contextual)
			else:
				return contextual
		else:
			return self.trustworthiness
			
	def contextual_trustworthiness(self,ctype):
		"""
		Returns self's trustworthiness relative to the clue's contenttype,
		False if he has none.
		"""
		
		reltw = self.stats['contextual_tw'].get(ctype,False)
		
		return reltw
