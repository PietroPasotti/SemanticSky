
class presets():
	"""
	A few functions to (help you) set some key options in semanticsky.
	"""
	
	def equalization_on(equalization_function = 'exponential'):
		from semanticsky import set_default,DEFAULTS
		from semanticsky.agents.utils import belief_rules
		
		set_default('equalization',True)
		set_default('default_equalizer',belief_rules.TWUpdateRule.set_equalizer(equalization_function))
		
		DEFAULTS.display_recent_changes()
	
	def differentiate_lss_by(factor = 50):
		from semanticsky import set_default,DEFAULTS
				
		set_default('differentiate_learningspeeds',True)
		set_default('negative_feedback_learningspeed_reduction_factor',factor)
		
		DEFAULTS.display_recent_changes()
		
	def normalize_trustworthinesses():
		from semanticsky import set_default,DEFAULTS
				
		set_default('normalization_of_trustworthinesses',True)
		
		DEFAULTS.display_recent_changes()
	
	
