#!/usr/bin/python3

from semanticsky.skies.utils import ctype,avg,diff,pull_tails,Group
import math

class TWUpdateRule(object):
	"""
	Groups a set of core algorithms for easy access and edit.
	
	*update rules* encompass all those rules used to compute the new value of
	a belief given alls sorts of priors such as the previous belief and the
	feedback received on its regard.
	
	*mergers* are algorithms for determining which the new value of the belief
	should be, given the output of the update rule and the previous belief.
	The most classical one relies on learning speed / rate.
	
	*antigravity* algorithms are used to determine the antigravity point 
	of a [0,1] distribution of (strength of) (unweighted) beliefs. That is
	the point such that most beliefs with a feedback that confirms their being
	justified (i.e. True in some sense) are greater than it, and all the
	beliefs whose feedback confirms their being false are smaller than it.
	Intuitively, all algorithms are somewhat good at doing whatever they do.
	So, their average of correct decisions will lie (a bit) above their average
	of wrong decisions. Antigravity point lies somewhere between the two,
	and is used as a radiation center to push the values closer to the extremes
	of the [0,1] spectrum, when we suspect their being biased towards one of
	the sides or when we want to get rid of long tail distributions.
	The default antigravity point is simply the average of the averages 
	of the good decisions and the bad ones.
	
	*equalizers* use the antigravity point of a distribution of beliefs
	to transform all beliefs' strength according to some rule, thus extremising
	beliefs' values such that belief strengths usually associated with good
	decisions be pushed upwards, and vice versa. This way, hopefully, future
	decisions with the same strength (that hopefully will be true as well)
	will be overrated and thus produce better results. (The angel will decide
	to shoot high or low, knowing his bias.) Builtin rules include a circular 
	increment, exponential and linear shift.
	"""	
	
	def default_merger(oldvalue,newvalue,learningspeed):
		"""
		Fetches the globally set MERGER variable, which should point to
		a function returning some combination of oldvalue, newvalue 
		and learningspeed.
		"""
		
		global MERGER
		
		try:
			return MERGER(oldvalue,newvalue,learningspeed)
		except NameError as e:
			raise NameError('No MERGER was set as default. To do so, use TWUpdateRule.set_merger(function) for some function.')
		
	def set_merger(function):
		
		global MERGER
		
		if isinstance(function,str):
			try:
				function = getattr(TWUpdateRule.builtin_mergers, function)
			except AttributeError:
				raise AttributeError('Bad choice. Builtin mergers are: {}.'.format([function.__name__ for function in TWUpdateRule.builtin_mergers.__dict__.values() if hasattr(function,'__call__')]))
		
		if not hasattr(function,'__call__'):
			raise BaseException('The provided function is not callable.')
		
		MERGER = function
		
		return MERGER

	def set_equalizer(function):
		
		global EQUALIZER
		
		if isinstance(function,str):
			try:
				function = getattr(TWUpdateRule.builtin_equalizers, function)
			except AttributeError:
				raise AttributeError('Bad choice. Builtin equalizers are: {}.'.format([function.__name__ for function in TWUpdateRule.builtin_equalizers.__dict__.values() if hasattr(function,'__call__')]))
		
		if not hasattr(function,'__call__'):
			raise BaseException('The provided function is not callable.')
		
		EQUALIZER = function
		
		return EQUALIZER
	
	def set_antigravity(function):
		
		global ANTIGRAVITY
		
		if isinstance(function,str):
			try:
				function = getattr(TWUpdateRule.builtin_antigravity, function)
			except AttributeError:
				raise AttributeError('Bad choice. Builtin antigravity point getters are: {}.'.format([function.__name__ for function in TWUpdateRule.builtin_antigravity.__dict__.values() if hasattr(function,'__call__')]))
		
		if not hasattr(function,'__call__'):
			raise BaseException('The provided function is not callable.')
		
		ANTIGRAVITY = function
		
		return ANTIGRAVITY
	
	def set_feedback_rule(function):
		
		global FEEDBACKRULE
		
		if isinstance(function,str):
			try:
				function = getattr(TWUpdateRule.builtin_feedback_rules, function)
			except AttributeError:
				raise AttributeError('Bad choice. Builtin feedback rules are: {}.'.format([function.__name__ for function in TWUpdateRule.builtin_feedback_rules.__dict__.values() if hasattr(function,'__call__')]))
		
		if not hasattr(function,'__call__'):
			raise BaseException('The provided function is not callable.')
		
		FEEDBACKRULE = function
		
		return FEEDBACKRULE
	
	def set_update_rule(function):
		
		global UPDATERULE
		
		if isinstance(function,str):
			try:
				function = getattr(TWUpdateRule.builtin_update_rules, function)
			except AttributeError:
				raise AttributeError('Bad choice. Builtin update rules are: {}.'.format([function.__name__ for function in TWUpdateRule.builtin_update_rules.__dict__.values() if hasattr(function,'__call__')]))
		
		if not hasattr(function,'__call__'):
			raise BaseException('The provided function is not callable.')
		
		UPDATERULE = function
		
		return UPDATERULE
		
	class builtin_feedback_rules():
		"""
		This class groups a few algorithms for computing the value of
		a feedback to a clue, given all sorts of initial parameters.
		
		For instance, one way is to give feedback whose meaning is 'your
		evaluation was worth *value*'; another is to give feedback the
		meaning of which is 'your evaluation should have been *value*':
		which corresponds to the dummy.
		"""
		
		def dummy(clue,feedbacking_agent):
			"""
			Returns the value of the clue's about according to feedbacking_agent:
			that is: what would feedbacking_agent have valued the clue's 
			about.
			"""
			
			return feedbacking_agent.evaluation.get(clue.about,0)
			
		def difference(clue,feedbacking_agent):
			"""
			Returns a value the closer to 0 the most the (UNWEIGHTED) evaluation
			of the feedbacking_agent and the evaluation suggested by the 
			clue differ.
			"""
			
			diff = lambda x,y: max([x,y]) - min([x,y])
			
			adiff = diff(clue.value,feedbacking_agent.evaluation.get(clue.about,0))
			
			return adiff
		
	class builtin_mergers():
		
		def dummy(oldvalue,newvalue,learningspeed):
			"""
			Dummy.
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
		
		def dummy(oldvalue,feedback,learningspeed,recipient):
			"""
			Dummy.
			"""
			
			return oldvalue
		
		def step_by_step_ls(oldvalue,feedback,learningspeed,recipient):
			"""
			The return value is simply a function of the old one, the received
			feedback (that is a 'this should be the answer' indication) and 
			the learning speed.
			"""
			
			suggested_value = (oldvalue + feedback.value) / 2
			
			return TWUpdateRule.default_merger(oldvalue,suggested_value,learningspeed)
		
		def forgetful_average(oldvalue,feedback,learningspeed,recipient):
			"""
			We pretend that the previous value was one. Who knows what might
			happen.
			"""
			return average_of_all_fbs(1,feedback,learningspeed,recipient)
		
		def average_of_all_fbs(oldvalue,feedback,learningspeed,recipient):
			"""
			A more stable feedback calculator: the trustworthiness for a given
			ctype is in this case the average of all feedback ever received
			about that pair.
			"""
			
			allfeedback = tuple(x for x in recipient.supervisor.knower.produced_feedback if ctype(x.about) == ctype(feedback.about) and x.destination is recipient)
						
			allvalues = tuple(fb.value for fb in allfeedback)
			
			newvalue = sum(allvalues) / len(allvalues) if allvalues else 0.5 # # tocheck
			
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
	
	class builtin_antigravity():
		
		def dummy(beliefset,angel):
			"""
			Dummy.
			Returns the middle point of the array of values extracted from 
			the beliefset (that is: a dictionary from beliefs to [0,1] floats).
			"""
			
			return max(beliefset.values()) / 2
		
		def average_of_average_TF(beliefset,angel):
			"""
			Returns a point, from the given beliefset's values, corresponding
			to the average of two points A, B such that:
			A is the average strength of all beliefs which have been confirmed 
			positively true (that is: their object is indeed true, whatever your
			confidence in it was.)
			B '' ... confirmed false.
			"""
			
			trues = []
			falses = []
			
			for belief in beliefset:
				if belief in angel.received_feedback:
					if angel.received_feedback[belief][0].sign == '+': # not very neat though...
						trues.append(beliefset[belief])
			
					else:
						falses.append(beliefset[belief])
				# if no feedback was ever received, this means that it's not a confirmed truth or falsity, so we do nothing about it
			
			centerf = avg(falses)
			centert = avg(trues)
			
			return(avg((centerf,centert)))
			
	class builtin_equalizers():
		"""
		This class groups functions for transforming the output of Guardian
		Angels' raw evaluations. Given as input an evaluation set (or a part of it)
		these functions should return a transformed evaluation set which
		can then be used to give actual output.
		"""
		
		class curves():
			"""
			Collector of (often lambda) functions used to compute equalized
			points: for easy access in case we don't want to equalize a full
			belief set and we already have the gravity point.
			"""
			
			def dummy(x,g):
				dummy = lambda x,y : x
				return dummy(x,g)
				
			def linear(x,g,f):
				curve = lambda oldvalue,antigrav,factor: oldvalue + factor if oldvalue > antigrav else oldvalue - factor if oldvalue < antigrav else oldvalue
				return curve(x,g,f)
				
			def exponential(x,g):
				curve = lambda x,g : x ** (1 + (g-x) / (1-g)) if x > g else x ** (1 + (g-x) / (g)) if x < g else x
				return curve(x,g)
			
			def circular():
				def curve(x,antigrav,maxbonus = False):
					
					if antigrav < x:
						output = x+((1-x)*(((1-antigrav)/2)/(((1-antigrav)/2)-((1-((1-antigrav)/2))-x)))) 
					elif antigrav > x:
						output = x-((x)*(((1-antigrav)/2)/(((1-antigrav)/2)-((1-((1-antigrav)/2))-x))))
					else:
						output = x
					
					if maxbonus:
						if diff(x,output) > maxbonus:
							if x < output:
								return x + maxbonus
							elif x > output:
								return x - maxbonus
					
					return output
					
				return curve
						
		def dummy(beliefset,angel = None,antigravity_override = None):
			"""
			Dummy.
			
			angel is required if we need to retrieve information such as
			received feedback, or so.
			"""
			
			return beliefset
		
		def linear(beliefset,angel,top = 1,factor = 0.2,antigravity_override = None):
			"""
			Performs a translation of all beliefsets after retrieving
			a gravity point as for the exponential equalizer.
			All samples are moved *factor* the other direction w.r.t. the
			gravity point 			
			
			curve = lambda oldvalue,antigrav,factor: oldvalue + factor 
									if oldvalue > antigrav else 
									oldvalue - factor if oldvalue < antigrav 
									else oldvalue
			"""
			
			if antigravity_override:
				antigrav = antigravity_override(beliefset,angel)
			else:
				antigrav = ANTIGRAVITY(beliefset,angel)
			# this is the point where the pushing moment will originate from.
			
			newbset = {}
			
			curve = lambda oldvalue,antigrav,factor: oldvalue + factor if oldvalue > antigrav else oldvalue - factor if oldvalue < antigrav else oldvalue
			
			for belief,value in beliefset.items():
				
				newvalue = curve(oldvalue,antigrav,factor)
					
				if newvalue > 1: # cut outsiders
					newvalue = 1
				elif newvalue < 0:
					newvalue = 0
				
				newbset[belief] = newvalue
				
			return newbset
		
		def exponential(beliefset,angel,antigravity_override = None):
			"""
			This function pushes to the borders of the [0,1] spectrum the 
			values of the beliefset. This is achieved by first computing 
			the medium point between the positive items (that is: the beliefs
			for which we have a confirmation that they are true) and the
			negative ones (for which we KNOW they are NOT true).
			Then, we take the medium point to be the zero of two exponentials,
			whose touchpoints will be the 0 and the 1 of the output spectrum
			of the belief set.
			
			curve = lambda x,g: x ** (1 + (g-x) / (1-g)) 	if x > g else 
								x ** (1 + (g-x) / (g)) 		if x < g else
								x

			Then, all values get scaled accordingly and the resulting beliefset
			is returned.
			"""
			if antigravity_override:
				antigrav = antigravity_override(beliefset,angel)
			else:
				antigrav = ANTIGRAVITY(beliefset,angel)
							
			curve = lambda x,g : x ** (1 + (g-x) / (1-g)) if x > g else x ** (1 + (g-x) / (g)) if x < g else x

			newbset = {}
			
			for belief,value in beliefset.items():
			
				newvalue = curve(value,antigrav)
				
				if newvalue > 1: # cut outsiders
					newvalue = 1
				elif newvalue < 0:
					newvalue = 0			
			
				newbset[belief] = value
				
			return newbset
			
		def circular(beliefset,angel,maxbonus = False,antigravity_override = None):
			"""
			Similar to exponential, but we take the circles whose radius
			is equal to the distance between the medium point of  the 
			average of positives negatives and zero / one.
			This means that values closer to the center will move a bit
			less, and values that trespass the medium point between 1 and
			the gravity point get moved straight to 1.
			
			If G is very close to 0 or 1, though, this might result in 
			excessive shift of close-to-0.5 values, which we might want to
			stay where they were.
			To trigger thresholding against this behaviour, you can set
			*maxbonus* to some value that won't be overcome by the shift
			factor of the old value.
			def curve():	
				
				if antigrav < x:
					output = x+((1-x)*(((1-antigrav)/2)/(((1-antigrav)/2)
						-((1-((1-antigrav)/2))-x)))) 
				elif antigrav > x:
					output = x-((x)*(((1-antigrav)/2)/(((1-antigrav)/2)
						-((1-((1-antigrav)/2))-x))))
				else:
					output = x
					
			After all, that's not really a circle but, well, it was inspired
			by one.
			"""
			if antigravity_override:
				antigrav = antigravity_override(beliefset,angel)
			else:
				antigrav = ANTIGRAVITY(beliefset,angel)	
					
			def curve(x,antigrav,maxbonus = False):
				
				if antigrav < x:
					output = x+((1-x)*(((1-antigrav)/2)/(((1-antigrav)/2)-((1-((1-antigrav)/2))-x)))) 
				elif antigrav > x:
					output = x-((x)*(((1-antigrav)/2)/(((1-antigrav)/2)-((1-((1-antigrav)/2))-x))))
				else:
					output = x
				
				if maxbonus:
					if diff(x,output) > maxbonus:
						if x < output:
							return maxbonus
						elif x > output:
							return - maxbonus
				
				return output	
			
			newbset = {}
			
			for belief,value in beliefset.items():
			
				newvalue = curve(value,antigrav)
				
				if newvalue > 1: # cut outsiders
					newvalue = 1
				elif newvalue < 0:
					newvalue = 0			
			
				newbset[belief] = value
				
			return newbset
		

