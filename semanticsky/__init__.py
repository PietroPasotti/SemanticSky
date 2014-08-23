#!/usr/bin/python3
# These defaults influence the behaviour of the whole heavens. Handle with care. Touch here for experiments or testing.

"""
Welcome to the heavens.

The heavens have many defaults.
For some examples of how to use this defaults management system, have a 
look at the presets.
"""

# this is where we will look for the data to initialize defaults SemanticSky objects on.
default_data_path = './semanticsky/data/export_maybe_false.pickle'

class __defaultshandler__(dict):
	"""
	A protected dict to interface with defaults handling of semanticsky.
	For an explanation of the defaults you'll have to read the comments
	in the __defaultshandler__.standard_defaults function.
	"""
	
	def __init__(self):
		
		if hasattr(__defaultshandler__,'alreadyinited'):
			raise BaseException('There are too many defaults handlers around.')
		
		super().__init__(self.standard_defaults())
		
		__defaultshandler__.alreadyinited = True
		
		self.changelog = [] # a buffer for recent changes
			
	def standard_defaults(self):
		"""
		readonly. The builtin set of defaults.
		"""
		standard_defaults = {															
			"verbosity" :										2, 						# 0 = all silent. 1 = no progress bars, but a few messages to know how you're doing. 2: even a few insults, sometimes.				
			"punish_false_negatives" : 							False,					# toggles (negative) feedback also on false positives
			"god_learningspeed" : 								0.8, 					# how hard is it for god to come to believe the futile suggestions you produce
			"learningspeed" : 									0.2, 					# how hard is it for god to come to believe that you're a moron
			"negative_feedback_learningspeed_reduction_factor":	50, 					# if differentiate_learningspeeds goes True, this factor divides feedback for negative examples
			"differentiate_learningspeeds" : 					False,					# toggles the differentiation of learningspeeds for all (and only) angels
			"equalization" : 									False, 					# toggles equalization for all (and only) angels
			"normalization_of_trustworthinesses" : 				False, 					# toggles normalization of tws for all agents (see their get_tw method)
			"antigrav_updaterate": 								5,						# the update rate for antigrav point getting (see agents.utils.BeliefBag)
			"default_voting_merge" : 							'plain average', 		# rule that god uses to compute his opinion based on the angels' suggestions
			"default_updaterule" : 								'median_of_all_fbs', 	# rule for computing new beliefs out of previous belief and feedback received
			"default_equalizer" : 								'exponential', 			# rule for equalization: angels learning their biases
			"default_antigravity" : 							'average_of_average_TF',# rule for finding gravity point for equalization
			"default_merger" : 									'classical_merger', 	# rule for computing new belief out of previous belief (after update_rule)
			"default_feedback_rule":							'difference', 			# rule for computing which value the feedback should take
			"log_zero_evaluations" : 							False ,					# toggles logging for zero evaluations of angels: see their evaluate() method.
			"sky_stats" :														# defaults for skies.SemanticSky instances
						{'number_of_words_in_corpus': 			0,						# will count the number of words in the corpus of the sky
						'number_of_tags':						0,						# will count the number of tags
						'number_of_sentences': 					0,						# idem
						'language_recognition_threshold' : 		0.4,					# threshold for skies.utils.guess_language function
						'clouds' : 												# defaults for skies.clouds.Cloud instances
									{'depth':					2,						# *max* number of layers per cloud (note: currently just one is used)
									#'density': None,									# not used
									#'thickness': None,									# not used
									'min_coo_threshold': 		2,						# minimum number of co-occurrences for a word pair to be considered "co-occurring"
									#'min_word_freq_threshold' : 2, 					# not used
									'max_coo_length': 			20,						# max length of the co-occurrence dictionary
									'max_vocab_length': 		30,						# used as crop value for skies.utils.most_freq_words_from_raw_texts
									#'cloud_hierarchy_inducer_threshold': 2.0/3.0		# not used
									}
						},
			"agent_base_stats" :  												# defaults for agents.Agent instances
							{ 'trustworthiness': 				0.6,					# initial trustworthiness
							'contextual_tw' : 					{},						# will map cluetypes to trustworthiness on the cluetype
							'expertises': 						{},						# will collect areas of expertise (where contextual trustworthiness is higher)
							#'communities': [],											# not used
							'blocked' : 						False					# not very much used, but will be
							},
			"angel_base_stats" : 				{"trustworthiness" : 1},				# overrides agents' agent_base_stats in GuardianAngel instances
			"god_base_stats" : 													# overrides angels' angel_base_stats in God(s) instances
				{'beliefbag_overrides' : {'equalization_active' : False}, 				# god needs no equalization. And btw, he receives no feedback whatsoever.
				'power': 'over 9000'} 													# well...
				}
		
		return standard_defaults
		
	def __setitem__(self,x,y,vb_override = False,check_override = False):
		
		if x not in self:
			raise KeyError('{} is not a default. What are you doing?'.format(x))
		
		previous_state = self[x]
		
		super().__setitem__(x,y) # we setitem
		
		if vb_override is not False:
			vb = vb_override
		else:
			vb = self.get('verbosity')
			
		if vb > 0:
			from .tests import wrap
			print(wrap('> DEFAULTS accessed. <','red'))
		
		if check_override is True: # permanent
			self.check_override = True
		
		if check_override == 1: # not permanent
			check_override = True 
		
		if getattr(self,'check_override',check_override) is not True:
			error = self.check()
			if error is not True:
				
				from .tests import wrap,center
				
				print(wrap('-' * 100 ,'red'))
				print(center(wrap("WARNING: some default has been altered in an unfamiliar way.",'red')))
				print(center(wrap('Error message: "{}"'.format(error),'red')))
				print(center(wrap("Change refused. Setting back '{}' to its previous state.".format(x),'red')))
				print(center(wrap("If you know what you're doing, call set_defaults with kwarg 'check_override' set to True.\n This will also disable all future warnings.".format(x),'red')))
				print(wrap('-' * 100 ,'red'))
				
				super().__setitem__(x,previous_state)
			
			else: # if there is no error
				self.changed(previous_state,x) # we buffer the change
			
			
	def changed(self,previous,key):
		
		self.changelog.append((previous,key)) # previous value for self[item], item
	
	def get_changelog(self):
		"""
		Fetches the buffer and resets it.
		"""
		
		clog = self.changelog
		self.changelog = []
		return clog
		
	def check(self):
			"""
			Checks all is fine with the defaults. Some more refined tests
			could also be implemented here.
			"""
			# entries that are assumed throughout the code to have a __call__ method
			callable_entries = ("default_feedback_rule", "default_merger" ,"default_antigravity","default_equalizer","default_updaterule" ,"default_voting_merge")
			
			# entries that are assumed to be either True or False.
			boolean_entries = ("differentiate_learningspeeds","equalization","normalization_of_trustworthinesses","log_zero_evaluations","punish_false_negatives")
			isbool = lambda x: True if x is True or x is False else False
			
			# assumed to be floats between 0 and 1
			floats01 = ("god_learningspeed","learningspeed")
			
			# assumed to be numbers, of virtually any kind
			numbers = ("verbosity","negative_feedback_learningspeed_reduction_factor")
			
			if not all(callable(self[x]) for x in callable_entries):
				error = 'some value in callable_entries ({}) is not callable as it should be: {}'.format(callable_entries,[DEFAULTS[x] for x in callable_entries if not callable(self[x])])
			elif not all(isbool(DEFAULTS[x]) for x in boolean_entries):
				error = 'some value in boolean_entries ({})is not boolean as it should be: {}'.format(boolean_entries,[self[x] for x in boolean_entries if not isbool(self[x])])
			elif not all(isinstance(self[x],float) and 0<=DEFAULTS[x]<=1 for x in floats01):
				error = 'some value in floats01 ({}) is not a float as it should be: {}'.format(floats01,[self[x] for x in floats01 if not isinstance(self[x],float)])
			elif not all(isinstance(self[x],(float,int)) for x in numbers):
				error = 'some value in numbers ({}) is not a numerical entity as it should be: {}'.format(numbers,[self[x] for x in numbers if not isinstance(self[x],(int,float))])
			else:
				error = False
				
			if error:
				return error
			
			vb = self['verbosity']
				
			if vb > 0:
				from .tests import wrap
				print(wrap('> All good. <','red'))	
			
			return True
		
	def display(self):
		"""
		Displays more or less nicely all defaults, regardless of the verbosity.
		"""		
		from .tests import center,wrap,table
		print(center(wrap(' DEFAULTS ','blue'),space = '-'))
		table([[name,self[name]] for name in self if 'stats' not in name ])
		print(center(wrap('DEFAULTS > sky_stats','blue')))
		table([  [name,self['sky_stats'][name]] for name in self['sky_stats'] if name != 'clouds'])
		print(center(wrap('DEFAULTS > sky_stats > clouds','blue')))
		table([[name,self['sky_stats']['clouds'][name]] for name in self['sky_stats']['clouds']])
		print(center(wrap('DEFAULTS > agent_base_stats','blue')))
		table([[name,self['agent_base_stats'][name]] for name in self['agent_base_stats']])
		print(center(wrap('DEFAULTS > angel_base_stats','blue')))
		table([[name,self['angel_base_stats'][name]] for name in self['angel_base_stats']])
		print(center(wrap('DEFAULTS > god_base_stats','blue')))
		table([[name,self['god_base_stats'][name]] for name in self['god_base_stats']])
		print('-' * 100)
		
		return
		
	def display_recent_changes(self):
		
		from .tests import center,wrap,table
		
		totable = []
		clog = self.get_changelog()
		print(center(wrap('Changelog:','red')))
		for previousvalue,key in clog:
			totable.append([ 'changed: {}'.format(key), previousvalue, '-->  {}'.format(self[key]) ])
		
		table(totable)
		
		if not clog:
			print(center("> Empty <"))
			
		return
								
DEFAULTS = __defaultshandler__()

from semanticsky import skies
from semanticsky import agents
from semanticsky import clues
from .presets import presets

def set_default(name,value,vb_override = False,check_override = False):
	"""
	Alias to DEFAULTS.__setitem__.
	"""
	
	return DEFAULTS.__setitem__(name,value,vb_override,check_override)

def check_defaults():
	"""
	alias of DEFAULTS.check()
	"""
	return DEFAULTS.check()

def display_defaults():
	"""
	Alias to DEFAULTS.display()
	"""
	return DEFAULTS.display()

# INIT DEFAULTS (silently)
def __init_defaults__():
	"""
	Useful to init, or to reset, all defaults to initial value.
	"""
	set_default("default_updaterule" , 			agents.utils.belief_rules.TWUpdateRule.set_update_rule( DEFAULTS['default_updaterule'] ),0,1) 
	set_default("default_equalizer",	 		agents.utils.belief_rules.TWUpdateRule.set_equalizer( DEFAULTS["default_equalizer"] ),0,1) 
	set_default("default_antigravity", 			agents.utils.belief_rules.TWUpdateRule.set_antigravity( DEFAULTS["default_antigravity"] ),0,1)
	set_default("default_merger",	 			agents.utils.belief_rules.TWUpdateRule.set_merger( DEFAULTS["default_merger"] ),0,1)
	set_default("default_feedback_rule",	 	agents.utils.belief_rules.TWUpdateRule.set_feedback_rule( DEFAULTS["default_feedback_rule"] ),0,1)
	set_default("default_voting_merge",			skies.utils.avg,0) # average. Also checks that all not-(re)inited defaults are allright.
	DEFAULTS.get_changelog() # clear changelogs
	
_SKY = None 	# a newly created sky will be stored here
_GOD = None 	# same for gods
_CLUES = [] 	# global queue of clues that can be processed by anyone.
_KNOWER = None 	# stores the last knower instantiated

def printout_globals():
	"""
	Just for utility, prints out the content of the globals _SKY, _GOD,
	_KNOWER, and the lenght of _CLUES. Ignores DEFAULTS['verbosity'].
	"""
	from .tests import wrap,table
	
	table([
		[ '\t_SKY         ' , _SKY ],
		[ '\t_GOD         ' , _GOD ],
		[ '\t_KNOWER      '	, _KNOWER],
		[ '\t_CLUES (len) ' , wrap(str(len(_CLUES)),'brightcyan')]
	])
	
__init_defaults__()
display_defaults()
