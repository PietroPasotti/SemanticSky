
from semanticsky.skies.utils import ctype
from semanticsky.clues import equalization
import semanticsky.clues.utils.belief_rules

class BeliefBag(dict,object):
	
	def __init__(self,owner,antigrav_updaterate = 5):
		dict.__init__(self,owner.evaluation)
		
		self.owner = owner
		self.equalizer = twupdate_rules.EQUALIZER # defaults to there, but each angel could in principle have its own, e.g. if he receives TOO much neg feedback after this.
		self.antigravity_getter = twupdate_rules.ANTIGRAVITY
		self.equalization_active = equalization
		
		self.weightset = owner.stats['relative_tw']
		self.antigrav_updaterate = antigrav_updaterate
		self.antigrav = None # gravity point is not set at start
		self.factor = 0 # boh
		
		if self.weightset and self.antigravity_getter:
			self.update_antigrav()
	
	def __str__(self):
		return "< BeliefBag of {}. >".format(self.owner.shortname())

	def __repr__(self):
		return "< BeliefBag of {}. >".format(self.owner.shortname())
		
	def raw_items(self):
		return self.items()

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
		
		return self.weightset[ctype(item)] * self.equalized(item) if self.equalization_active else self.weightset[ctype(item)] * self[item]

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
			eqcurves = [item for item in twupdate_rules.TWUpdateRule.builtin_equalizers.curves.__dict__ if hasattr(item,'__call__')]
			
			for e in eqcurves: # looks up for the curve which matches his equalizer's __name__
				if e.__name__ == self.equalizer.__name__:
					self.equalization_curve = e
					break
		
		if self.equalization_curve.__name__ == 'linear':
			transformed = self.equalization_curve(self[item],self.antigrav,self.factor) # we equalize on unweighted confidence ratings
		else:
			transformed = self.equalization_curve(self[item],self.antigrav)	
		
	def __setitem__(self,item,value):
		super().__setitem__(item,value)
		self.touch()
		
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
	
		

	
	
	
