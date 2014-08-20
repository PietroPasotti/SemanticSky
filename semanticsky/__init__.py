#!/usr/bin/python3
	
## These defaults influence the behaviour of the whole heavens. Handle with care. Touch here for experiments or testing.



# this is where we will look for the data to initialize defaults SemanticSky objects on.
data_path = './semanticsky/data/export_maybe_false.pickle'

DEFAULTS = {															
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
"sky_stats" :															# defaults for skies.SemanticSky instances
			{'number_of_words_in_corpus': 0,								# will count the number of words in the corpus of the sky
			'number_of_tags': 0,											# will count the number of tags
			'number_of_sentences': 0,										# idem
			'language_recognition_threshold' : 0.4,							# threshold for skies.utils.guess_language function
			'clouds' : 													# defaults for skies.clouds.Cloud instances
						{'depth':2,											# *max* number of layers per cloud (note: currently just one is used)
						#'density': None,									# not used
						#'thickness': None,									# not used
						'min_coo_threshold': 2, 							# minimum number of co-occurrences for a word pair to be considered "co-occurring"
						#'min_word_freq_threshold' : 2, 					# not used
						'max_coo_length': 20,								# max length of the co-occurrence dictionary
						'max_vocab_length': 30,								# used as crop value for skies.utils.most_freq_words_from_raw_texts
						#'cloud_hierarchy_inducer_threshold': 2.0/3.0		# not used
						}
			}
		}

from semanticsky import skies
from semanticsky import agents
from semanticsky import clues

def set_default(name,value,vb_override = False,check_override = False):
	"""
	Makes sure that you're not doing any bullshit while modifying the defaults.
	Also all internal modifications should use this function.
	"""
	
	DEFAULTS[name] = value
	
	# entries that are assumed throughout the code to have a __call__ method
	callable_entries = ("default_feedback_rule", "default_merger" ,"default_antigravity","default_equalizer","default_updaterule" ,"default_voting_merge")
	
	# entries that are assumed to be either True or False.
	boolean_entries = ("differentiate_learningspeeds","equalization","normalization_of_trustworthinesses")
	isbool = lambda x: True if x is True or x is False else False
	
	# assumed to be floats between 0 and 1
	floats01 = ("god_learningspeed","learningspeed")
	
	# assumed to be numbers, of virtually any kind
	numbers = ("verbosity","negative_feedback_learningspeed_reduction_factor")
	if check_override is False:
		# we control all is fine
		if not all(callable(DEFAULTS[x]) for x in callable_entries):
			error = 'some value in callable_entries ({}) is not callable: {}'
			''.format(callable_entries,[DEFAULTS[x] for x in callable_entries if not callable(DEFAULTS[x])])
		elif not all(isbool(DEFAULTS[x]) for x in boolean_entries):
			error = 'some value in boolean_entries ({})is not a float: {}'
			''.format(boolean_entries,[DEFAULTS[x] for x in boolean_entries if not isbool(DEFAULTS[x])])
		elif not all(isinstance(DEFAULTS[x],float) and 0<=DEFAULTS[x]<=1 for x in floats01):
			error = 'some value in floats01 ({}) is not a float: {}'
			''.format(floats01,[DEFAULTS[x] for x in floats01 if not isinstance(DEFAULTS[x],float)])
		elif not all(isinstance(DEFAULTS[x],(float,int)) for x in numbers):
			error = 'some value in numbers ({}) is not a numerical entity: {}'
			''.format(numbers,[DEFAULTS[x] for x in numbers if not isinstance(DEFAULTS[x],(int,float))])
		else:
			error = False
			
		if error:
			raise BaseException(error)

	if vb_override is not False:
		vb = vb_override
	else:
		vb = DEFAULTS['verbosity']
		
	if vb > 0:
		from .tests import wrap
		print(wrap('DEFAULTS accessed.','red'))
	if vb > 1:
		from .tests import center
		print(center(' DEFAULTS ',space = '-'))
		from .tests import table
		table([[name,DEFAULTS[name]] for name in DEFAULTS if name != 'sky_stats'])
		print(center('DEFAULTS > sky_stats'))
		table([  [name,DEFAULTS['sky_stats'][name]] for name in DEFAULTS['sky_stats'] if name != 'clouds'])
		print(center('DEFAULTS > sky_stats > clouds'))
		table([[name,DEFAULTS['sky_stats']['clouds'][name]] for name in DEFAULTS['sky_stats']['clouds']])
		print('-' * 100)
			
	return True
	
# INIT DEFAULTS (silently)
set_default("default_updaterule" , 			agents.utils.belief_rules.TWUpdateRule.set_update_rule( DEFAULTS['default_updaterule'] ),0,True) 
set_default("default_equalizer",	 		agents.utils.belief_rules.TWUpdateRule.set_equalizer( DEFAULTS["default_equalizer"] ),0,True) 
set_default("default_antigravity", 			agents.utils.belief_rules.TWUpdateRule.set_antigravity( DEFAULTS["default_antigravity"] ),0,True)
set_default("default_merger",	 			agents.utils.belief_rules.TWUpdateRule.set_merger( DEFAULTS["default_merger"] ),0,True)
set_default("default_feedback_rule",	 	agents.utils.belief_rules.TWUpdateRule.set_feedback_rule( DEFAULTS["default_feedback_rule"] ),0,True)
set_default("default_voting_merge",			skies.utils.avg) # average

_SKY = None 	# a newly created sky will be stored here
_GOD = None 	# same for gods
_CLUES = None 	# global queue of clues that can be processed by anyone.
