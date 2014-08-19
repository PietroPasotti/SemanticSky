

from semanticsky import skies
from semanticsky import clues
#from semanticsky import tests

DEFAULTS = {
"god_learningspeed" : 								0.8, # how hard is it for god to come to believe the futile suggestions you produce
"learningspeed" : 									0.2, # how hard is it for god to come to believe that you're a moron
"negative_feedback_learningspeed_reduction_factor":	50, # if differentiate_learningspeeds goes True, this factor divides feedback for negative examples
"differentiate_learningspeeds" : 					False,
"equalization" : 									False,
"normalization_of_trustworthinesses" : 				False,
"default_updaterule" : 								clues.utils.belief_rules.TWUpdateRule.set_update_rule('median_of_all_fbs'), # rule for computing new beliefs out of previous belief and feedback received
"default_equalizer" : 								clues.utils.belief_rules.TWUpdateRule.set_equalizer('exponential'), # rule for equalization: angels learning their biases
"default_antigravity" : 							belief_rules.TWUpdateRule.set_antigravity('average_of_average_TF'), # rule for finding gravity point for equalization
"default_merger" : 									belief_rules.TWUpdateRule.set_merger('classical_merger'), # rule for computing new belief out of previous belief (after update_rule)
"default_feedback_rule":							clues.utils.belief_rules.TWUpdateRule.set_feedback_rule('difference')} # rule for computing which value the feedback should take
