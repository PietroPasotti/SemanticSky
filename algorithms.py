from collections import Counter

			# ALGORITHMS


def tf_weighting(clouda,cloudb,basedbaddress = 'words_tf'):
	
	tf_rating = 0	
	
	for i in range(len(clouda.layers) - 1):
		
		layera = clouda.layers[i]
		layerb = cloudb.layers[i]
		
		aws = layera[basedbaddress]
		bws = layerb[basedbaddress]
		
		allwords = set(aws.keys()).union(set(bws.keys()))

		for word in allwords:
			atf = aws.get(word,0)
			btf = bws.get(word,0)
			
			tf_rating += float(min( [atf,btf] )) ####### 
			# or maybe: average?
			#tf_rating += float(sum( [atf,btf] )) / 2 
		
	return tf_rating
		
def tf_idf_weighting(clouda,cloudb):
	
	return tf_weighting(clouda,cloudb,'words_idf')

def coo_dicts_all_metrics(clouda,cloudb):
	
	out = {}
	
	out['neighbour'] = coo_dicts_neighbour(clouda,cloudb)
	out['overlap'] = coo_dicts_overlap(clouda,cloudb,debug = True)
	out['extended neighbour'] = coo_dicts_extended_neighbour(clouda,cloudb)
	return out
	
def coo_dicts_overlap(clouda,cloudb,version = 1,debug = False):
	"""
	version 1 returns a pair-to-pair correspondence check. That correspondence
	is very valuable, but rare.
	In case it performs badly, version 2 is more permissive and splits the pairs
	using single words as term of comparison. Implementation of Grefenstette (1994)
	algorithm.
	
	version 3 attempts a merge between the two: valuable v1-correspondences 
	go to increment v2 ones.
	"""
	
	value1 = 0
	value2 = 0
	value3 = 0
	
	for i in range(len(clouda.layers)):
		cooa = clouda.layers[i]['top_coo']
		coob = cloudb.layers[i]['top_coo']
		
		value1_temp = 0
		if version in [1,3] or debug: 									# VERSION 1
			for pair in list(cooa)+list(coob):
				basevalue = min ( cooa.get(pair,0) , coob.get(pair,0) )
			
				allv = 	sum( list(cooa.values()) + list(coob.values()) )
				
				if allv: value1_temp += float(basevalue / allv )
				else: value1_temp += 0
		
		allwords = set({})
		value2_temp = 0
		if version in [2,3] or debug: 									# VERSION 2
			
			for pair in list(cooa)+list(coob):
				allwords.update(pair)
			
			totmin = 0
			totmax = 0
			
			for word in allwords:				
				wacounter = sum( [ cooa[pair] for pair in cooa if word in pair ] )
				wbcounter = sum( [ coob[pair] for pair in coob if word in pair ] )
				
				totmax += max((wacounter,wbcounter))
				totmin += min((wacounter,wbcounter))
				
			value2_temp += totmin / totmax
	
		value3_temp = 0
		if version == 3 or debug:								# VERSION 3
			value3_temp += max([value1_temp,value2_temp])
		
		value1 += value1_temp
		value2 += value2_temp
		value3 += value3_temp
		
	if debug:
		return {'value1 (coo pairs overlap)': value1,'value2 ( Grefenstette )':value2}
	if version == 1:
		return value1
	elif version == 2:
		return value2		
	elif version == 3:
		return value3
	else:
		raise BaseException('Unrecognized version name: {}'.format(version))

def coo_dicts_overlap_v1(clouda,cloudb):
	return coo_dicts_overlap(clouda,cloudb,version = 1)

def coo_dicts_overlap_v2(clouda,cloudb):
	return coo_dicts_overlap(clouda,cloudb,version = 2)

def coo_dicts_neighbour(clouda,cloudb):
	"""
	For each word in each pair in a or b's top_coo dicts, we create the set
	of the word's neighbours (words that coo with them), and we compare these sets'
	coo-values, and not directly the words' ones.
	"""
	
	out_value = 0
	
	for i in range(len(clouda.layers)):
		cooa = clouda.layers[i]['top_coo']
		coob = cloudb.layers[i]['top_coo']
		
		allwa = set()
		allwb = set()
		for pair in cooa:
			allwa.update(pair)
		for pair in coob:
			allwb.update(pair)
			
		 # we weight the pairs:
		weighted_cooa = Counter()
		weighted_coob = Counter()
		for cdic in (cooa,coob):
			if cdic is cooa:
				ocdic = coob
				allmywords = allwa
				weighted_target = weighted_coob
			else: 
				ocdic = cooa
				allmywords = allwb
				weighted_target = weighted_cooa
			
			for pair in ocdic:
				if pair in cdic: # if the pair is also in the other dic, full weight
					weighted_target[pair] = ocdic[pair]
					continue
				
				w1,w2 = pair
				if w1 in allmywords and w2 in allmywords: # if both words are in the other dic, but not in the same pair, half weight
					weighted_target[pair] = ocdic[pair]*0.5
					continue
				
				if w1 in allmywords or w2 in allmywords: # if just one of them is in the other dic, quarter weight
					weighted_target[pair] = ocdic[pair]*0.25
					continue
					
				#weighted_target[pair] = 0 	# if both of the words are unknown to the other dic's vocabulary, zero weight
											# so we can as well omit the pair from the dictionary. each pair has some nonzero weight, now,
											# in at least one dictionary
			
		totmin = 0
		totmax = 0
		
		for pair in list(cooa)+list(coob):				
			wacounter = weighted_cooa[pair] # is a counter, so a nonexisting pair will yield 0
			wbcounter = weighted_coob[pair]
			
			totmax += max((wacounter,wbcounter))
			totmin += min((wacounter,wbcounter))
		
		if totmax:
			out_value += totmin / totmax
		else:
			out_value += 0
		

	return out_value				
				
def coo_dicts_extended_neighbour(clouda,cloudb,debug = False):
	sky = clouda.sky
	coodict = sky.counters['coo']
	
	if debug:
		print(clouda.item)
		print(cloudb.item)
	
	neighbours = {}
	for pair in coodict:
		wa,wb = pair
		
		if not neighbours.get(wa):
			neighbours[wa] = []
		if not neighbours.get(wb):
			neighbours[wb] = []	
				
		neighbours[wa].append(wb)
		neighbours[wb].append(wa)
	
	out = 0
	
	for i in range(len(clouda.layers)):
		cooa = Counter(clouda.layers[i]['top_coo'])
		coob = Counter(cloudb.layers[i]['top_coo'])
		
		bowa = [] # all words appearing in cooa
		bowb = [] 
		
		for pair in cooa: bowa.extend(pair)
		for pair in coob: bowb.extend(pair)
		
		expandedbowa = [] # all neighbours (in the whole corpus) of all words in cooa
		expandedbowb = []
		
		for word in bowa:
			expandedbowa.extend(neighbours[word])
		for word in bowb:
			expandedbowb.extend(neighbours[word])
		
		if debug:
			print(expandedbowa)
			print()
			print(expandedbowb)
			print()
		
		# add a threshold, maybe? It's already thresholded at 2 or 3, btw.
		
		avalues = Counter() # vector
		bvalues = Counter()
		
		def weight(cooa,coob,bvalues,expandedbowb):
			for pair in cooa:
				wa,wb = pair
				if pair in coob:
					bvalues[pair] += coob[pair] # full weight
					continue
				
				if wa in bowb and wb in bowb:
					bvalues[pair] += coob[pair]*0.75 # 3/4 weight
					continue
				
				if wa in bowb or wb in bowb:
					bvalues[pair] += coob[pair]*0.5 # half weight
					continue	 
				
				if wa in expandedbowb and wb in expandedbowb:
					bvalues[pair] += coob[pair]*0.25 # quarter weight
					continue		
				
				if wa in expandedbowb or wb in expandedbowb: # only a common neighbour
					bvalues[pair] += coob[pair]*0.10 # very little weight
					continue
					
				bvalues[pair] += 0
		
		weight(cooa,coob,bvalues,expandedbowb) # updates bvalues
		weight(coob,cooa,avalues,expandedbowa) # updates avalues
		
		# now avalues and bvalues are the weighted vectors we wanted, and we can apply Grefenstette
		
		if debug:
			print(avalues)
			print()
			print(bvalues)
			print()
		
		totmin = 0
		totmax = 0
		
		for pair in list(avalues)+list(bvalues):				
			waval = avalues[pair]
			wbval = bvalues[pair]
			
			totmax += max( ( waval , wbval ) )
			totmin += min( ( waval , wbval ) )
		
		if totmax:	
			out += totmin / totmax
		else:
			out += 0
			
	return out		
	
def tag_overlap(clouda,cloudb):
	return 0

def all_algs_check(clouda,cloudb):
	
	outdict = { tf_weighting : None,
				tf_idf_weighting : None,
				coo_dicts_overlap_v1: None,
				coo_dicts_overlap_v2: None,
				coo_dicts_neighbour: None,
				coo_dicts_extended_neighbour: None,
				tag_overlap: None}
				
	for alg in outdict:
		outdict[alg] = alg(clouda,cloudb)
	
	return outdict
			
def nearestneighbours(clouda):
	sky = clouda.sky.clouds()
	
	clues = {}
	
	for cloudb in sky:
		if clouda is cloudb:
			continue
			
		proximities = all_algs_check(clouda,cloudb) 		
		
		# get the most optimistic one, unless it's too optimistic (we avoid 1's) although it should never be.
		
		top_proximity = max(proximities.values())
		clues[frozenset({clouda,cloudb})] = top_proximity
	
	return clues

ALL_ALGS = [	tf_weighting,
				tf_idf_weighting,
				coo_dicts_overlap_v1,
				coo_dicts_overlap_v2,
				coo_dicts_neighbour,
				coo_dicts_extended_neighbour,
				tag_overlap		]	
	

