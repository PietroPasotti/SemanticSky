#!/usr/bin/python3

"""
Fairly important functions out here.

Ctype is essential for contextual trustworthiness to work, and pair
determines the standard type of cloud-pairing we use for belief sets and so on.
Handle with care.
"""

def ctype(something):
	"""
	This function is responsible for determining the context of an item:
	that is, its contenttype (ctype). Thus, it should return anything we 
	want to contextualize the evaluations to.
	"""
	
	from semanticsky.skies import Link,Cloud
	
	if str(type(something)) == "<class 'semanticsky.skies.sky.Link'>": # we delegate to its clouds' ctype methods.
		# I know this sucks, but unpickled Links aren't recognized as Link instances.
		
		ta,tb = something
		
		ct = [ta.ctype(),tb.ctype()]
		ct.sort()
		return '-'.join(ct)
		
	elif str(type(something)) ==  "<class 'semanticsky.skies.clouds.cloud.Cloud'>":
		return ta.ctype()
	
	else:
		raise BaseException('Wat :: {}.'.format(something))

def pair(cloud,cloudb):
	""" Simply wraps two objects in a Link. """
	
	from semanticsky.skies import Link
	
	if cloud is cloudb:
		raise BaseException('Same cloud == No good.')
		
	return Link((cloud,cloudb))
