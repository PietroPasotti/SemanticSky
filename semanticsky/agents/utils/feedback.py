 #!/usr/bin/python3

class Feedback(object):
	
	def __init__(self,origin,destination,about,value,sign):
		"""
		Lighter than clues, and no need for god's mediation.
		"""
		
		self.origin = origin
		self.destination = destination
		self.about = about
		self.value = value
		self.sign = sign
		
		if self in destination.received_feedback.get(about,[]): # if this is a duplicate of a preexisting feedback: we do nothing.
			return
		else:
			self.go()
			return
			
	def go(self):
		"""
		When we're sure the feedback is not a duplicate, we make it go:
		
		- we have the origin record the production of the feedback
		- and the destination receive it: actually process it and update 
			its contextual trustworthiness accordingly
		- finally: we have god update its belief set
		"""	
		
		self.origin.record_given_feedback(self) # we have the origin record the production of the feedback
		self.destination.receive_feedback(self) # and the destination receive it: actually process it and update its contextual trustworthiness accordingly.
		
		self.origin.supervisor.rebelieves(self.about) # finally: we have god update its belief set!
		return
		
	def __add__(self,other):
		"""
		Feedback's value!
		"""
		return self.value + other
		
	def __le__(self,other):
		if self.value <= other:
			return True
		else:
			return False
	
	def __ge__(self,other):
		if self.value >= other:
			return True
		else:
			return False
	
	def __float__(self):
		return float(self.value)
	
	def __int__(self):
		return int(self.value)
	
	def __radd__(self,other):
		
		return self + other

	def __key(self):
		return (self.value, self.destination.unique_name(), self.origin.unique_name(), self.about)

	def __eq__(x, y):
		return x.__key() == y.__key()

	def __hash__(self):
		return hash(self.__key())
