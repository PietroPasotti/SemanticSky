#!/usr/bin/python3

				
class Cloud(object):
	"""
	A Cloud is a semantic web of information, hierarchically ordered
	from the innermost to the outermost (a relatedness measure already).
	The cloud's layers can then be compared with other clouds' same-level
	layers to get a higher-order proximity index.
	"""

	def __init__(self,sky,item):

			self.item = item
			self.ID = item['id']
			self.data = sky.data
			self.sky = sky
			self.layers = [[]]
			self.stats = self.sky.stats['clouds'] # will probably be aliased. and this is good, I think.
			
			# how to build a cloud:
			from .cloudformationrules import LayerBuilder
			
			builder = LayerBuilder(self,autobuild = True) # this will let the builder fill the layers of this little cloud.
			
			if self not in sky.sky:
				sky.sky.append(self)
			
	def __repr__(self):
		return "< Cloud [{}] at {}. >".format(self.ID,id(self))
	
	def __str__(self):
		return "< Cloud [{}]. >".format(self.ID)
	
	def __hash__(self):
		return hash(self.item['id'])
	
	@property
	def depth(self):
		return len(self.layers)
	@property
	def itemtype(self):
		return self.item['type']
				
	def ctype(self):
		"""
		Returns the type of the wrapped item, such as 'Person', 'Glossary'
		or the such. Returns 'tag' if none is found.
		"""
		
		return self.item.get('type','tag')
	
	def links(self,numbers = True):
		
		if numbers:
			return self.item.get('links',None)
		else: 
			return [self.sky.get_cloud(ID) for ID in self.item.get('links',[])] # list of clouds the cloud's item is linked to
		
	def istagcloud(self):
		
		if isinstance(self.item['id'],str):
			return True
		else:
			return False
	
	def get_header(self):
		"""
		Returns a useful short description of the item, for human recognition.
		"""
		
		if self.cloudtype == 'tags':
			return self.item['id']
			
		return self.item.get('name',self.item.get('title'))
			
	def is_empty(self):
		"""
		Returns true iff the cloud does not contain 'enough' information.
		Example: if the cloud's center is a person, and the only info we have
		is his name.
		"""
		
		# naive approach:
		item = self.item
		stringitem = [ str(value) for value in item.values() ]
		
		if len(stringitem) <= 1000:
			return True
		else:
			return False

