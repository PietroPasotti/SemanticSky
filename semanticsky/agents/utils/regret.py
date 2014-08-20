
#!/usr/bin/python3

def regret(beliefs,truths,only_on_true_links = False):
	"""
	Computes regret of a set of beliefs relative to an iterable of absolute
	truths. Set of beliefs is assumed to be a dict-like object, and truths
	any iterable which yields (a subset of) its keys.
	"""
	regret = 0
	
	for belief in beliefs:
		if belief in truths:
			regret += 1 - beliefs[belief]
		else:
			if not only_on_true_links:
				regret += beliefs[belief]
	
	for belief in truths:
		if belief not in beliefs:
			regret += 1
	
	return regret
 
