#!/usr/bin/python3
	
class Clue(object):
	"""
	A Clue object stores information about some other object or virtual entity
	such as a relation, and asserts something about its trustworthiness.
	Is a (meant-to-be) universal mean of evaluation.
	
	Clues can be about:
	
	- pairs of Cloud items; then the clue means 'I suspect that these two clouds
	are (not) related'
	
	- an Agent (or GuardianAngel); then the clue means 'This agent's clues
	are (not very) trustworthy.'
	
	To express the degree of confidence in those who produce the clue into
	the clue itself, each clue comes with a 'value' property. The value of
	a clue is its INTENDED strength. Its effective strength depends on its
	author's trustworthiness (which yes, depends on the feedback received
	on her own clues.)
	
	Example usage:
	
	# you can create a custom agent: pietro = clues.Agent('pietro')
	# and then myclue = Clue(link,0.3,pietro)
	# or better pietro.evaluate(link,0.3)
	# if agent is not given, author of the clue will be 'Anonymous'
	myclue = Clue(link,0.3)
	# myclue will be considered by god and it's beliefstate will be influenced
	# by its weighted value; that is: a combination of its confidence (0.3
	# in this case) and the trustworthiness of its author, by default 0.6.
	"""
	
	def __init__(self,about,value,agent = 'Anonymous',autoconsider = True, trace = None,supervisor = None):
		"""
		Autoconsider: toggles queuing of clues.
		"""
		
		from semanticsky import DEFAULTS
		from semanticsky.skies import Link
		
		self.cluetype = 'link'
		if not str(about.__class__) == "<class 'semanticsky.skies.Link'>":
			self.about = Link(about)

		self.about = about
		self.value = value
		self.trace = trace
		
		if not supervisor: 
			if DEFAULTS['verbosity'] > 1:
				print("Warning: No supervisor was specified for {}. Might become messy with more than one god around.".format(self))
			from semanticsky import _GOD
			supervisor = god
		
		self.supervisor = supervisor			
		self.agent = agent
		
		if hasattr(agent,'clues'):
			agent.clues.append(self)
		
		if autoconsider and supervisor:
			self.supervisor.consider(self) # there the clue gets logged
		else:
			from semanticsky import _CLUES
			_CLUES.append(self)	
	
	def __str__(self):
		from semanticsky.tests import crop_at_nonzero
		return "< Clue about {0.ids}, valued {} by {0.agent}. >".format(self,crop_at_nonzero(self.value,4))
		
	def __repr__(self):
		from semanticsky.tests import crop_at_nonzero
		return "< Clue about {0.ids}, valued {} by {0.agent}. >".format(self,crop_at_nonzero(self.value,4))
		
	@property
	def trustworthiness(self):
		"""
		The trustworthiness of a clue is the one of he who formulated it.
		"""
		return self.agent.get_tw(self.contenttype) # returns the relative-to-self's contenttype trustworthiness OR the agent's overall tw if the former is unavailable
	
	@property
	def contenttype(self):
		"""
		Returns the content-type of the two clouds' items if the about is a link.
		"""
		
		about = self.about
		
		try:
			return self.about.ctype() # Link objects have it
		except AttributeError:
			try:
				from semanticsky.skies.clouds.core import ctype
				return ctype(about)
			except BaseException as e:
				raise TypeError("Error: [{}]. Unhandleable self.about's contenttype: {} (of type {}).".format(e,about,type(about)))
		
	def ctype(self): 
		"""
		Alias to contenttype, which btw should replace it someday.
		"""
		return self.contenttype
	
	@property
	def weightedvalue(self):
		"""
		Self-explanatory.
		"""
		return self.trustworthiness * self.value
	
	@property
	def ids(self):
		"""
		Tries to delegate to self.about.ids. If absent, assumes that 
		self.about is a tuple-or-list-like pair of objects each of which 
		has an 'item' attribute such that obj.item.__getattr__('id')
		returns an unique-to-the-object ID.
		
		In other words:
		return tuple(self.about[x].item['id'] for x in (0,1))
		
		Note: things might get quite screwed up if the order of the items
		is random. That's the reason for the skies.Link class (an ordered
		tuple, basically).
		"""
		
		if hasattr(self.about,'ids'):
			return self.about.ids # delegates ids to Link.ids
		else:
			ab = tuple(self.about)
			return tuple(ab[x].item['id'] for x in (0,1))
		
