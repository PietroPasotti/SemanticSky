#!/usr/bin/python3

import clues

METALGS = []

class MetaAngel(clues.GuardianAngel,object):
	def __init__(self,metalgorithm):
		super().__init__(metalgorithm)
		
	def __repr__(self):
		return clues.wrap("< MetaAngel {}. >".format(self.name),'brightgreen')
		
class MetaAlgorithm:
	
	class builtin_metalgs:
		
		def manyclues(clouda,cloudb):
			"""
			This algorithm just returns closer to one the most the pair
			is clue'd about by other algorithms.
			"""
			
			pair = clues.ss.pair
			
			god = clues.god
			
			link = pair(clouda,cloudb)
			maxloglen = max(len(log) for log in clues.god.logs.values())

			loglenforpair = len(god.logs.get(link,[]))
			
			return loglenforpair / maxloglen

			
			
	
	def __init__(self,function):
		
		METALGS.append(function)
		clues.algs.algsbyname.append(function.__name__)
		return None
