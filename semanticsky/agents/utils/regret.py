
#!/usr/bin/python3

def regret(beliefs,truths,only_on_true_links = False):
	"""
	Computes regret of a set of beliefs relative to an iterable of absolute
	truths. Set of beliefs is assumed to be a dict-like object, and truths
	any iterable which yields (a subset of) its keys.
	
	There are two ways to compute regrets: one is by taking into account
	only all known-to-be-true links. The other one also takes into account
	all false positives (and is the default).
	
	regret only on true is computed as follows:
	regret = sum(difference(belief_in_(x) ,1) for all x in TRUTHS)
	
	regret on all links (default) is computed as follows:
	regret = sum(difference(belief_in_(x) ,1) for all x in TRUTHS)
	regret += sum(difference(belief_in_(x), 0) for all x in beliefs if x 
													not in TRUTHS)
	"""
	regret = 0
	
	for belief in truths:
		value = beliefs.get(belief,0) # beliefbag's __getitem__ will return 0 if belief is not found in beliefbag, but beliefbag.toplevel() needs not be a BeliefBag instance
		regret += 1-value
		
	if only_on_true_links is False:
		for belief in beliefs: 
			if belief not in truths:
				regret += beliefs[belief]
		
		# if we compute regrets on ALL links (also false positives), we also give regrets based on how hard the belief is on all items which are not in truths
		# but ARE in beliefs.
	
	return regret
 
