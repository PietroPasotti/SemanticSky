#!/usr/bin/python3

def average_belief(beliefbag,referencebeliefbag,truthvalue):
	
	avg = lambda itr : sum(itr) / len(itr) if itr else 0
	
	totbels = []
	
	for belief in beliefbag:
		
		if truthvalue is True:
			if belief not in referencebeliefbag: 	# we consider only beliefs that ARE in the reference bbag
				continue
		elif truthvalue is False:
			if belief in referencebeliefbag:		# ... ARE NOT ...
				continue
		else:
			pass									# we take all of them
		
		totbels.append(beliefbag[belief])
		
	return avg(totbels)
