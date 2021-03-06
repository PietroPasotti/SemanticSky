#!/usr/bin/python3

# need ss, DEFAULTS, and 
from ..agents import GuardianAngel

class Knower(GuardianAngel,object):
	"""
	A class designed to train SemanticSky, together with the algorithm
	.utils.algorithms.Algorithm.builtin_algs.someonesuggested.
	"""
	
	def __init__(self,supervisor,algorithm = False,silence = False):
		if algorithm is False:
			from .utils.algorithms import Algorithm
			algorithm = Algorithm.builtin_algs.someonesuggested
			
		super().__init__(algorithm, supervisor,whisperer = True)
		
		knower = self
		supervisor.knower = self
		self.name = 'Knower'
		self.shortname = lambda : 'know'
		
		import semanticsky
		semanticsky._KNOWER = self
		
		if not silence:
			self.evaluate_all(express = False) # the knower should never express,
			# so as to not influence directly god's belief state!
		return

	def __str__(self):
		return "< The Knower >"
		
	def __repr__(self):
		from semanticsky.tests import wrap
		return wrap("< The Knower >",'brightgreen')
	
	def express(self,*args,**kwargs):
		raise BaseException("The Knower shouldn't express!")
	
	def new_supervisor(self,deity,clear = True):
		"""
		Assigns a new supervisor to the knower and clears all preceding logs,
		if *clear*.
		
		Warning: do NOT use unless the DEFAULTS with whom the former god
		and the new gods were created are the same! Otherwise weird
		things might happen.
		"""
		
		self.supervisor = deity
		self.makewhisperer()
		deity.knower = self # todo: a god should support more than one knower / trainer

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
		from semanticsky.clues import Clue
		from semanticsky import DEFAULTS
		
		if verbose is True:
			vb = DEFAULTS['verbosity']
		else:
			vb = 0
		
		if str(cluelist.__class__) in ["<class 'semanticsky.agents.angel.GuardianAngel'>","<class 'semanticsky.agents.agent.Agent'>"]:
			cluestovalue = cluelist.clues
		elif isinstance(cluelist,list) or hasattr(cluelist,'__iter__'):
			cluestovalue = tuple(cluelist)
		elif isinstance(cluelist,Clue):
			cluestovalue = [cluelist]
		else:
			raise BaseException('Unrecognized input type.')
		
		ln = len(cluestovalue)
		i = 0
		
		if ln == 0:
			if vb > 0:
				print( 'Knower :: Feedback, empty.')
			return True
		
		elif ln <= 50 and vb > 0:
			print('Knower :: Feedbacking (short).')
			vb = 0		

		if vb > 1:
			from semanticsky.tests import ProgressBar
			targetname = getattr(cluelist,'shortname','')
			if callable(targetname): # shortname
				targetname = '({})'.format(targetname())
			bar = ProgressBar(ln,title = '{} :: Feedback{}'.format(self.name, targetname ))
		
		for clue in cluestovalue:
			
			if vb > 1:
				bar()

			if clue.agent is self:
				continue
			
			feedback_production_rule = DEFAULTS['default_feedback_rule']	# FEEDBACK RULE
			punish_false_negatives = DEFAULTS['punish_false_negatives'] 	# PUNISH
			
			if not self.believes(clue.about) and not punish_false_negatives:
				# if the clue's about is not in my evaluation and we're not supposed to punish false negatives, we won't give feedback to this clue.
				# : it's just an 'I dunno, I have no opinion here.'
				continue # we skip the clue
			
			myrating = feedback_production_rule(clue,self)
			
			sign = '+' if self.beliefbag[clue.about] else '-' # the sign of a feedback is + iff, whatever the confidence of the feedbacked is, his suspect was correct (that is: also the feedbacker has a nonzero belief in it)
			# insofar as the link is actually there.
			
			# self's opinion on the clue's about.
			self.feedback(clue.agent,clue.about,myrating, sign)  # actually produces a Feedback object and sends it through
		
		if verbose:
			print()
		return True
	
	def feedback_all(self,verbose = True):
		god = self.supervisor
		
		if verbose: 
			print()
			i = 0
		
		ln = len(god.logs)
		from semanticsky.tests import ProgressBar
		bar = ProgressBar(ln , title = '{} :: feedback_all'.format(self.shortname()))
		for link,clues in god.logs.items():
			
			if verbose:
				i += 1
				bar()
			
			self.give_feedback(clues,verbose = False) # vb off
		
		if verbose: 
			print()
