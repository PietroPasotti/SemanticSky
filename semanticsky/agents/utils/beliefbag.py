
class BeliefBag(dict,object):
	
	def __init__(self,owner,contents = None,**overrides):
		dict.__init__(self) # a beliefbag is always initialized empty.
		
		if contents: # but we can 
			self.update(contents)
		
		from semanticsky import DEFAULTS
		
		self.owner = owner
		self.equalizer = DEFAULTS['default_equalizer'] # defaults to there, but each angel could in principle have its own, e.g. if he receives TOO much neg feedback after this.
		self.antigravity_getter = DEFAULTS['default_antigravity']
		self.equalization_active = DEFAULTS['equalization']
		self.antigrav_updaterate = DEFAULTS['antigrav_updaterate']
		
		self.touchcounter = 0 # when it hits *antigrav_updaterate*, triggers self.update_antigrav() and then it resets
		self.antigrav = None # gravity point is not set at start
		#self.factor = 0 # boh

		self.__dict__.update(overrides) # we can overwrite some kwargs to personalise in fancy ways the bag's attributes.
		
		if self.weightset:
			self.update_antigrav()
		
	@property
	def weightset(self):
		return self.owner.stats['contextual_tw']
	
	def __str__(self):
		return "< BeliefBag of {}. >".format(self.owner.name)

	def __repr__(self):
		from semanticsky.tests import wrap
		return wrap("< BeliefBag of {}. >".format(self.owner.name),'brightmagenta')

	def __setitem__(self,item,value):
		super().__setitem__(item,value)
		if self.equalization_active:
			self.touch()
		
	def __getitem__(self,item):
		"""
		If a belief is just not there, we return 0.
		If something was already evaluated, and was judged 0, the return
		value is 0.0 (a float). This way we can distinguish between not-yet
		evaluated items and already-evaluated (but zero) items, provided
		we have set the DEFAULT store_zero_evaluations to True.
		Otherwise, it's all 0.
		
		WARNING: returns raw evaluations.
		"""
		try:
			return super().__getitem__(item)
		except KeyError:
			return 0		

	def items(self,iknowwhatimdoing = False):
		"""
		To avoid confusions...
		"""
		if not iknowwhatimdoing:
			raise BaseException("Ambiguous. Use raw_items instead.")
			
		return super().items()
	
	def raw_items(self):
		return self.items(True)
		
	def weighted_items(self):
		return self.raw_belief_set().items()
	
	def equalized_items(self):
		return self.equalized_belief_set().items()
		
	def raw_belief_set(self):
		return dict(self.raw_items())

	def weighted_belief_set(self):		
		return dict(self.iter_weighted_items())

	def equalized_belief_set(self):
		return dict(self.iter_equalized_items())
		
	def iter_weighted_items(self):
		
		for item,value in self.raw_items():
			yield (item, self.weighted(item))
		
	def iter_equalized_items(self):	
		
		for item,value in self.raw_items():
			yield (item,self.equalized(item))
	
	def set_weight(self,ctype,weight):
		
		self.weightset[ctype] = weight
		self.touch()
		
	def weighted(self,item):
		
		from semanticsky.skies.clouds.core import ctype
		# looks for contextual_tw; else retrieves overall trustworthiness
		reltw = self.weightset.get(ctype(item), self.owner.trustworthiness)
		return reltw * self.equalized(item) if self.equalization_active else reltw * self[item]

	def equalized(self,item):
		
		if not self.equalization_active or self.equalizer is None:
			raise BaseException('Equalization is not active, or equalizer is missing.')		

		if not hasattr(self,'equalization_curve'):
			getcurve = True
		elif self.equalization_curve.__name__ != self.equalizer.__name__:
			getcurve = True
		else:
			getcurve = False
			
		if getcurve:
			from ..utils import belief_rules
			eqcurves = [item for item in belief_rules.TWUpdateRule.builtin_equalizers.curves.__dict__.values() if hasattr(item,'__call__')]
			
			for e in eqcurves: # looks up for the curve which matches his equalizer's __name__
				if e.__name__ == self.equalizer.__name__:
					self.equalization_curve = e
					break
		
		if self.equalization_curve.__name__ == 'linear':
			transformed = self.equalization_curve(self[item],self.antigrav,self.factor) # we equalize on unweighted confidence ratings
		else:
			transformed = self.equalization_curve(self[item],self.antigrav)	
		
		return transformed
		
	def touch(self):
		
		self.touchcounter += 1
		
		if self.touchcounter >= self.antigrav_updaterate:
			self.update_antigrav()
			self.touchcounter = 0
	
	def set_antigravity_getter(self,function):
		
		self.antigravity_getter = function
		return
	
	def update_antigrav(self,to = None):
			
		if to:
			self.antigrav = to
		else:
			self.antigrav = self.antigravity_getter(self,self.owner)
	
	def toplevel(self):
		"""
		Returns a dictionary which is the outcome of the full pipeline
		given the current defaults. See Agent.believes or the subclass
		method for a longer description.
		
		What the toplevel beliefbag is depends on the pipeline we're using.
		This can be modified all in one by toying with agents and angels'
		believes function.
		"""
		
		# if the belief pipeline is ['raw','equalized','weighted'] as it originally was, then we could as well
		# return self.weighted_belief_set() and get the same result.
		
		return {x : self.owner.believes(x) for x in self}
	
	
