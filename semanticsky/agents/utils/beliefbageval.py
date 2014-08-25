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

def monitor_tf_gap_through_bags(beliefbags,referencebeliefbag):
	
	evolutions = [] # we assume all bags have the same owner
	
	for bag in beliefbags:
		
		avgtrue = average_belief(bag,referencebeliefbag,True)
		avgfalse = average_belief(bag,referencebeliefbag,False)
		
		gap = avgtrue - avgfalse # true's average *should* be higher: a positive value means high gap, and vice versa
		
		evolutions.append(gap)
	
	return evolutions

def god_raw_beliefbag(god):
	
	avg = lambda itr : sum(itr) / len(itr) if itr else 0
	
	rawbag = {}
	
	for belief in god.beliefbag:
		rawbag[belief] = avg([angel.beliefbag[belief] for angel in god.guardianangels if belief in angel.beliefbag]) # plain average of all nonzero evaluations
		
		# warning: slightly differs from actual raw evaluation insofar as no learningspeed is taken into account. Just plain average.
	
	return rawbag

def multiangel_tf_gap_through_bags(listofangels):
	
	knower = listofangels[0].supervisor.knower
	god = listofangels[0].supervisor
	
	referencebag = knower.beliefbag
	
	out = {angel.name : None for angel in listofangels}
	
	from semanticsky import DEFAULTS
	equalization = DEFAULTS['equalization']
	from semanticsky.agents.utils import BeliefBag
	
	for angel in listofangels:
		bag0 = BeliefBag(angel,angel.beliefbag.raw_belief_set())
		if equalization:
			bag1 = BeliefBag(angel,angel.beliefbag.equalized_belief_set())
			bag2 = BeliefBag(angel,angel.beliefbag.weighted_belief_set())
		else:
			bag1 =	BeliefBag(angel,angel.beliefbag.weighted_belief_set())
		
		evolution_of_angel = monitor_tf_gap_through_bags([bag0,bag1,bag2] if equalization else [bag0,bag1],referencebag) 
		# should return a list of two / three floats, that is: the gap. unweighted[,equalized],weighted
		
		out[angel.name] = evolution_of_angel
	
	# god's
	out['god'] = monitor_tf_gap_through_bags([BeliefBag(god, god_raw_beliefbag(god)),god.beliefbag], referencebag)
	# the rawbag of a god is always the same (unless somehow his angel's *raw* beliefsets change, and this shouldn't be the case).
	# the toplevel bag however changes. right?
	# god has no equalization/weighting, so all we can monitor is the pre/post **his angel's** full belief pipeline.
	
	return out
	
