
from semanticsky_utilityfunctions import ctype
import twupdate_rules

class BeliefBag(dict,object):
	
	def __init__(self,owner,iterable,equalizer,weightset = None,antigravity = None,antigrav_updaterate = 5):
		super().__init__()
		
		self.owner = owner
		self.equalizer = equalizer
		self.antigravity_getter = antigravity
		if equalizer:
			self.equalization_active = True
		if weightset is None:
			weightset = {}	
		self.weightset = weightset
		self.antigrav_updaterate = antigrav_updaterate
		self.antigrav = None # gravity point is not set at start
		self.factor = 0 # boh
		
		if weightset and antigravity:
			self.update_antigrav()
		
	def raw_items(self):
		return self.items()
		
	def iter_weighted_items():
		
		for item,value in self.raw_items():
			yield (item, self.weighted(item))
		
	def iter_equalized_items():	
		
		for item,value in self.raw_items():
			yield (item,self.equalized(item))
	
	def set_weight(self,ctype,weight):
		
		self.weightset[ctype] = weight
		self.touch()
		
	def weighted(self,item):
		
		return self.weightset(ctype(item)) * self.equalized(item)

	def equalized(self,item):
		
		if not self.equalization_active:
			raise BaseException('Equalization is not active.')
			
		equitem = self.transform_equalization(item)
		return equitem
		
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
		if not hasattr(self,'antigravity_getter'):
			self.antigravity_getter = twupdate_rules.ANTIGRAVITY
			
		if to:
			self.antigrav = to
		else:
			self.antigrav = self.antigravity_getter(self,self.owner)
	
	def transform_equalization(self,item):

		if self.equalizer is None:
			raise BaseException('Equalization is not active, or equalizer is missing.')		

		if not hasattr(self,'equalization_curve'):
			getcurve = True
		elif self.equalization_curve.__name__ != self.equalizer.__name__:
			getcurve = True
			
		if getcurve:
			eqcurves = [item for item in twupdate_rules.TWUpdateRule.builtin_equalizers.curves.__dict__ if hasattr(item,'__call__')]
			
			for e in eqcurves:
				if e.__name__ == self.equalizer.__name__:
					mycurve = e
					break
					
			self.equalization_curve = e
		
		if self.equalization_curve.__name__ == 'linear':
			transformed = self.equalization_curve(self.weighted(item),self.antigrav,self.factor)
		else:
			transformed = self.equalization_curve(self.weighted(item),self.antigrav)	
		
		return transformed
		

	
	
	
