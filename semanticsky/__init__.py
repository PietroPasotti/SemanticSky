
DEFAULTS = {
"god_learningspeed" : 								0.8, # how hard is it for god to come to believe the futile suggestions you produce
"learningspeed" : 									0.2, # how hard is it for god to come to believe that you're a moron
"negative_feedback_learningspeed_reduction_factor":	50, # if differentiate_learningspeeds goes True, this factor divides feedback for negative examples
"differentiate_learningspeeds" : 					False,
"equalization" : 									False,
"normalization_of_trustworthinesses" : 				False,
"default_voting_merge" : 							'plain average', # rule that god uses to compute his opinion based on the angels' suggestions
"default_updaterule" : 								'median_of_all_fbs', # rule for computing new beliefs out of previous belief and feedback received
"default_equalizer" : 								'exponential', # rule for equalization: angels learning their biases
"default_antigravity" : 							'average_of_average_TF', # rule for finding gravity point for equalization
"default_merger" : 									'classical_merger', # rule for computing new belief out of previous belief (after update_rule)
"default_feedback_rule":							'difference'} # rule for computing which value the feedback should take

from semanticsky import agents
from semanticsky import skies
from semanticsky import clues

# INIT DEFAULTS
DEFAULTS['default_updaterule'] = 		agents.utils.belief_rules.TWUpdateRule.set_update_rule( DEFAULTS['default_updaterule'] )
DEFAULTS["default_equalizer"] =	 		agents.utils.belief_rules.TWUpdateRule.set_equalizer( DEFAULTS["default_equalizer"] ) 
DEFAULTS["default_antigravity"] = 		agents.utils.belief_rules.TWUpdateRule.set_antigravity( DEFAULTS["default_antigravity"] )
DEFAULTS["default_merger"] = 			agents.utils.belief_rules.TWUpdateRule.set_merger( DEFAULTS["default_merger"] )
DEFAULTS["default_feedback_rule"] = 	agents.utils.belief_rules.TWUpdateRule.set_feedback_rule( DEFAULTS["default_feedback_rule"] )
DEFAULTS["default_voting_merge"] = 		skies.utils.avg # average
