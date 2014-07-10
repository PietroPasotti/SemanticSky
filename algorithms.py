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
	
def coo_dicts_overlap(clouda,cloudb,version = 1,debug = False):
	"""
	version 1 returns a pair-to-pair correspondence check. That correspondence
	is very valuable, but rare.
	In case it performs badly, version 2 is more permissive and splits the pairs
	using single words as term of comparison.
	
	version 3 attempts a merge between the two: valuable v1-correspondences 
	go to increment v2 ones.
	"""
	
	value1 = 0
	value2 = 0
	value3 = 0
	
	for i in range(len(clouda.layers)):
		cooa = clouda.layers[i]['top_coo']
		coob = cloudb.layers[i]['top_coo']
		
		values1_temp = Counter()
		if version in [1,3]: 									# VERSION 1
			for pair in list(cooa)+list(coob):
				basevalue = min ( cooa.get(pair,0) , coob.get(pair,0) )
			
				allv = 	sum( list(cooa.values()) + list(coob.values()) )
				
				if allv: values1_temp[pair] += float(basevalue / allv )
				else: values1_temp[pair] += 0
		
		allwords = set({})
		values2_temp = Counter()
		if version in [2,3]: 									# VERSION 2
			for pair in list(cooa)+list(coob):
				allwords.update(pair)
			
			for word in allwords:				
				wacounter =  sum( [ cooa[pair] for pair in cooa if word in pair ] )
				wbcounter =  sum( [ coob[pair] for pair in coob if word in pair ] )
				
				if cooa: f1 = wacounter / sum(cooa.values()) # all counts for pairs with word in them / total counts
				else: f1 = 0
				if coob: f2 = wbcounter / sum(coob.values()) 
				else: f2 = 0
				
				values2_temp[word]  +=  (f1 + f2) / 4 # we average them
	
		value3_temp = 0
		if version == 3 or debug:
			for word in allwords:										# VERSION 3
				word_value2 = values2_temp[word]
				word_value1 = values1_temp[word]
				
				value3_temp += max([word_value2,word_value1])
			
		
		value1 += sum(values1_temp.values())
		value2 += sum(values2_temp.values())
		value3 += value3_temp
		
	
	if debug:
		return {'value1': value1,'value2':value2,'value3':value3,'temp1':values1_temp,'temp2':values2_temp}
	
	if version == 1:
		return value1
	elif version == 2:
		return value2		
	elif version == 3:
		return value3
	else:
		raise BaseException('Unrecognized version name: {}'.format(version))
	
def coo_dicts_neighbour(clouda,cloudb):
	pass
def tag_overlap(clouda,cloudb):
	pass
