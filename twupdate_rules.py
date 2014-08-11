#!/usr/bin/python3

from semanticsky_utilityfunctions import ctype

class TWUpdateRule(object):
	
	def default_merger(oldvalue,newvalue,learningspeed):
		"""
		Fetches the globally set MERGER variable, which should point to
		a function returning some combination of oldvalue, newvalue 
		and learningspeed.
		"""
		
		global MERGER
		
		try:
			return MERGER(oldvalue,newvalue,learningspeed)
		except NameError:
			
			raise NameError('No MERGER was set as default. To do so, use TWUpdateRule.set_merger(function) for some function.')
		
	def set_merger(function):
		
		global MERGER
		
		if isinstance(function,str):
			try:
				function = getattr(TWUpdateRule.builtin_mergers, function)
			except AttributeError:
				raise AttributeError('Bad choice. Builtin mergers are: {}.'.format([function.__name__ for function in builtin_mergers.__dict__.values() if hasattr(function,'__call__')]))
		
		if not hasattr(function,'__call__'):
			raise BaseException('The provided function is not callable.')
		
		MERGER = function
		
		return MERGER
		
	class builtin_mergers():
		
		def nomerge(oldvalue,newvalue,learningspeed):
			"""
			Toy merger.
			"""
			return newvalue
		
		def classical_merger(oldvalue,newvalue,learningspeed):
			"""
			The most canonical one.
			"""
			
			return oldvalue - (oldvalue - newvalue) * learningspeed
			
	class builtin_update_rules():
		"""
		Some ready_made update rules.
		Note that currently most rules base their calculations only on
		feedback received from the Knower.
		"""
		
		def step_by_step_ls(oldvalue,feedback,learningspeed,recipient):
			"""
			The return value is simply a function of the old one, the received
			feedback (that is a 'this should be the answer' indication) and 
			the learning speed.
			"""
			
			return TWUpdateRule.default_merger(oldvalue,feedback.value,learningspeed)
			
		def average_of_all_fbs(oldvalue,feedback,learningspeed,recipient):
			"""
			A more stable feedback calculator: the trustworthiness for a given
			ctype is in this case the average of all feedback ever received
			about that pair.
			"""
			
			allfeedback = tuple(x for x in recipient.supervisor.knower.produced_feedback if ctype(x.about) == ctype(feedback.about) and x.destination is recipient)
						
			allvalues = tuple(fb.value for fb in allfeedback)
			
			newvalue = sum(allvalues) / len(allvalues) if allvalues else 0.5
			
			return TWUpdateRule.default_merger(oldvalue,newvalue,learningspeed)

		def average_of_most_recent_fbs(oldvalue,feedback,learningspeed,recipient,crop = 10):
			
			allfeedback = tuple(x for x in recipient.supervisor.knower.produced_feedback if ctype(x.about) == ctype(feedback.about) and x.destination is recipient)			
			if crop > len(allfeedback):
				topmost_crop = allfeedback[len(feedback) - crop: ]
			
			else:
				topmost_crop = allfeedback
			
			allvalues = tuple(fb.value for fb in topmost_crop)
			
			newvalue = sum(allvalues) / len(allvalues)
			
			return TWUpdateRule.default_merger(oldvalue,newvalue,learningspeed)

		def median_of_all_fbs(oldvalue,feedback,learningspeed,recipient):
			"""
			Even more stable: takes the median of all feedback ever received
			about that pair.
			"""
			
			allfeedback = tuple(x for x in recipient.supervisor.knower.produced_feedback if ctype(x.about) == ctype(feedback.about) and x.destination is recipient)			
			
			allvalues = tuple(fb.value for fb in allfeedback)
			
			sorts = sorted(allvalues)
			
			if len(sorts) % 2 != 0:
				center = sorts[(len(sorts)-1) // 2 ] # the middle value
			else:
				centers = sorts[(len(sorts) // 2) -1 : (len(sorts) // 2) +1]
				center = sum(centers) / 2
				
			return TWUpdateRule.default_merger(oldvalue,center,learningspeed)
		
		def median_of_most_recent_fbs(oldvalue,feedback,learningspeed,recipient,crop = 10):
			
			allfeedback = tuple(x for x in recipient.supervisor.knower.produced_feedback if ctype(x.about) == ctype(feedback.about) and x.destination is recipient)			
			
			if crop > len(allfeedback):
				topmost_crop = allfeedback[len(feedback) - crop: ]
			
			else:
				topmost_crop = allfeedback			
				
			allvalues = tuple(fb.value for fb in topmost_crop)
			
			sorts = sorted(allvalues)
			
			if len(sorts) % 2 != 0:
				center = sorts[(len(sorts)-1) // 2 ] # the middle value
			else:
				centers = sorts[(len(sorts) // 2) -1 : (len(sorts) // 2) +1]
				center = sum(centers) / 2
				
			return TWUpdateRule.default_merger(oldvalue,center,learningspeed)

TWUpdateRule.set_merger('classical_merger')
