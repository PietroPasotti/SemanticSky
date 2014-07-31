from collections import Counter
from math import sqrt

			# ALGORITHMS

def cosine(veca,vecb):
	
	sumnum = 0
	alla2 = 0
	allb2 = 0
	for i in range(len(veca)):
		ia = veca[i]
		ib = vecb[i]
		num = ia * ib
		sumnum += num
		
		ia2 = ia**2
		alla2 += ia2
		
		ib2 = ib**2
		allb2 += ib2
	
	ralla2 = sqrt(alla2)
	rallb2 = sqrt(allb2)
	
	denom = ralla2 * rallb2
	if denom:
		cos = sumnum / denom
	else:
		cos = 0
	return cos

class Algorithm():
	"""
	This class is useful for both grouping builtin algorithms and for
	easy implementation of new ones.
	It will be sufficient to call Algorithm(function) on function to add
	the new function as an evaluator. The function will be added to the globals
	ALL_ALGS (unless the flag 'guardian' is set to False), which means that
	calling god's spawn_servants function will evoque it as a GuardianAngel,
	unless it already exists.
	
	Only relevant characteristic of the function, for compatibility and
	comparability with the other functions, is that it outputs uniformly
	floats between zero and one, plain zero if it is unable to detect anything.
	
	Example usage (IDLE):
	
	def myalgorithm(clouda,cloudb):
	
		...
		
		return num # 0.0 <= num <= 1.0
		
	Algorithm(myalgorithm)
	
	god = clues.God()
	god.spawn_servants()
	
	myalgorithm_angel = tuple(ga for ga in god.guardianangels if ga.name == 'myalgorithm')[0]
	
	god.consult(myalgorithm_angel)
	# this will consult the guardianangel which has myalgorithm as decision
	# algorithm.
	"""
	
	
	class builtin_algs():
		"""
		A few ready_made algorithms.
		"""
		
		def tf_weighting(clouda,cloudb,basedbaddress = 'words_tf',use_cosine = True,dbg = False):
			"""
			Tf bag-of-words weighting.
			"""
			tf_rating = 0	
			
			for i in range(len(clouda.layers)):
				
				layera = clouda.layers[i]
				layerb = cloudb.layers[i]
			
				aws = layera[basedbaddress]
				bws = layerb[basedbaddress]
				
				if dbg: print(aws,' '*120,bws)

				allwords = set(aws.keys()).union(set(bws.keys()))
				
				if use_cosine:
					veca = []
					vecb = []
					
					for word in allwords:
						vala = 0
						valb = 0
						
						if aws.get(word):
							vala = aws[word]	
						veca.append(vala)
						
						if bws.get(word):
							valb = bws[word]
						vecb.append(valb)
					
					tf_rating += cosine(veca,vecb)
						
				else:
					for word in allwords:
						atf = aws.get(word,0)
						btf = bws.get(word,0)
						
						if dbg: print(word,' overlap = ', min([atf, btf]))

						tf_rating += float(min( [atf,btf] )) ####### 
						# or maybe: average?
						#tf_rating += float(sum( [atf,btf] )) / 2 
			
			tf_rating = tf_rating / len(clouda.layers)
			
			return tf_rating
				
		def tf_idf_weighting(clouda,cloudb,dbg = False):
			
			return tf_weighting(clouda,cloudb,'words_tfidf',dbg = dbg)
	
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
					
					if totmax:
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
			of the word's neighbours (words that often co-occur with them in the 
			whole corpus), and we compare these sets' coo-values (relative to the 
			two clouds), and not directly the words' ones.
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
			"""
			This algorithm is slow, but fine-grained nearly as much as possible:
			after grabbing the two clouds coo-count dicts, makes a bag of word
			out of it (by splitting the co-occurring pairs) and extends it
			with the co-occurring words of each of these words (where the 
			co-occurrence dict is taken this time from the whole database
			counter, and not from the single cloud's one!). Afterwards these
			extended bags of words get compared.
			
			Example:
			
			cloud a [top_coo] = {('chair','sit') : 4}
			cloud b [top_coo] = {('dust','bin') : 4}
			
			database[top_coo] = {('chair,classroom'):10,
									('dust','classroom'): 11}
			
			thus, despite dust-bin and chair-sit permutations never appearing
			in global coo dict, we can still compare a and b based on the fact
			that chairs appear to be globally relate to classrooms
			and so does dust.
			
			A sort of second-order similarity of coo dicts: noisier, but
			more often granted to return nonzero values.
			"""
			
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
				
				if not cooa or not coob:
					continue
				
				bowa = [] # all words appearing in cooa
				bowb = [] 
				
				for pair in cooa: bowa.extend(pair)
				for pair in coob: bowb.extend(pair)
				
				expandedbowa = set() # all neighbours (in the whole corpus) of all words in cooa
				expandedbowb = set()
				
				for word in bowa:
					expandedbowa.update(neighbours.get(word,set()))
				for word in bowb:
					expandedbowb.update(neighbours.get(word,set()))
				
				if debug:
					print(expandedbowa)
					print()
					print(expandedbowb)
					print()
				
				# add a threshold, maybe? It's already thresholded at 2 or 3, btw.
				
				avalues = Counter() # vector
				bvalues = Counter()
				
				def increm_by_factor(n,factor):
					
					# 0<n<1
					if not n < 1:
						return n
					
					if not 0<factor<1:
						raise BaseException('needs factor in [0,1].')
					
					m = 1-n
					f = m*factor
					return f + n
				
				
				for pair in cooa:
					# take a pair in cooa: if it is in coob, its weight receives a +50%
					# if its words are in coob, its weight receives a +25%
					# if its words are in coob's expanded bag of word, +10%
					
					wa,wb = pair
					if pair in coob: # same pair
						avalues[pair] = increm_by_factor(cooa[pair],0.7)
						continue
					
					if wa in bowb and wb in bowb: # both in other's bow
						
						avalues[pair] = increm_by_factor(cooa[pair],0.5)
						continue
					
					if wa in bowb or wb in bowb: # just one in other's bow
						avalues[pair] = increm_by_factor(cooa[pair],0.3)
						continue	 
					
					if wa in expandedbowb and wb in expandedbowb: # both in expandedbow : common neighbours
						avalues[pair] = increm_by_factor(cooa[pair],0.2)
						continue		
					
					if wa in expandedbowb or wb in expandedbowb: # only a common neighbour
						avalues[pair] = increm_by_factor(cooa[pair],0.1)
						continue
					else:	
						avalues[pair] = cooa[pair]
				
				#weight(cooa,coob,bvalues,bowa,bowb,expandedbowa,expandedbowb) # updates bvalues
				#weight(coob,cooa,avalues,bowb,bowa,expandedbowb,expandedbowa) # updates avalues		
				for pair in coob:
					# take a pair in cooa: if it is in coob, its weight receives a +50%
					# if its words are in coob, its weight receives a +25%
					# if its words are in coob's expanded bag of word, +10%
					
					wa,wb = pair
					if pair in cooa: # same pair
						bvalues[pair] = increm_by_factor(coob[pair],0.7)
						continue
					
					if wa in bowa and wb in bowa: # both in other's bow
						bvalues[pair] = increm_by_factor(coob[pair],0.5)
						continue
					
					if wa in bowa or wb in bowa: # just one in other's bow
						bvalues[pair] = increm_by_factor(coob[pair],0.3)
						continue	 
					
					if wa in expandedbowa and wb in expandedbowa: # both in expandedbow : common neighbours
						bvalues[pair] = increm_by_factor(coob[pair],0.2)
						continue		
					
					if wa in expandedbowa or wb in expandedbowa: # only a common neighbour
						bvalues[pair] = increm_by_factor(coob[pair],0.1)
						continue
					else:	
						bvalues[pair] = coob[pair]

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
					
			return out	/ len(clouda.layers)	# averaged (?)
			
		def tag_overlap(clouda,cloudb):
			"""
			Plain overlap of 'tags' entries of clouds
			"""
			atags = clouda.item.get('tags',[])
			btags = cloudb.item.get('tags',[])
			
			satags = set(atags)
			sbtags = set(btags)
			
			overlap = satags.intersection(sbtags)
			unio = satags.union(sbtags)
			
			return len(overlap) / max(1,len(unio))

		def someonesuggested(clouda,cloudb = None,weight = 1):
			"""
			Naive algorithm that checks whether the two clouds' items were
			linked in the starfish database.
			
			Weight can be used to fine-tune the confidence of the algorithm into
			the informed guess that clouda and cloudb are related.
			"""
			
			
			if cloudb is None:
				clouda,cloudb = clouda # first arg can be a pair
			
			data = clouda.data
			alinks = clouda.item.get('links',[])
			blinks = cloudb.item.get('links', [])
			aid = clouda.item['id']
			bid = cloudb.item['id']
			
			if aid in blinks or bid in alinks:
				return weight
				
			else:
				return 0

		def naive_name_comparison(clouda,cloudb):
			"""
			1) retrieve a's names and b's names
			2) return the overlap, normalized into [0,1]
			"""	
			
			tot = 0
			
			for i in range(len(clouda.layers)):
				anames = set(clouda.layers[0]['names'])
				bnames = set(cloudb.layers[0]['names'])		
				
				den = len(anames.union(bnames))
				if not den: den = 1
				
				tot += len(anames.intersection(bnames)) / den
				
			return tot / len(clouda.layers)
				
		def extended_name_comparison(clouda,cloudb):
			"""
			1) retrieve a's names and b's names
			2) make a list of often-related-with-name keywords from other clouds
			3) compare a and b through the lists of keywords
			"""
			
			tot = 0
			
			for i in range(len(clouda.layers)):
				anames = set(clouda.layers[0]['names'])
				bnames = set(cloudb.layers[0]['names'])
				
				sky = clouda.sky
				
				relevanttoa = []
				relevanttob = []
				
				for cloud in sky.clouds():
					if cloud is clouda or cloud is cloudb:
						continue
					cnames = set(cloud.layers[0]['names'])
					if cnames.intersection(anames):
						relevanttoa.append(cloud)
					if cnames.intersection(bnames):
						relevanttob.append(cloud)
				
				bowa = set()
				bowb = set()
				
				for cloud in relevanttoa:
					bowa.update(cloud.core())
				for cloud in relevanttob:
					bowb.update(cloud.core())
				
				tbows = len(bowa) + len(bowb)
				if not tbows: tbows = 1
				tot += len(bowa.intersection(bowb)) / tbows
			
			return tot / len(clouda.layers)

		def tag_similarity_naive(clouda,cloudb,v = False):
			"""
			co-occurrence of tags in pages
			"""
			
			istaglink = lambda x: isinstance(x[0].item['id'],str) and isinstance(x[1].item['id'],str)
			
			if not istaglink((clouda,cloudb)):
				if v: print('nontag')
				return 0
			
			taga = clouda.item['id']
			tagb = cloudb.item['id']	
			
			if v: print (taga,tagb)
			
			data = clouda.sky.data	
			itaggeda = set(data.items_per_tag(taga))
			itaggedb = set(data.items_per_tag(tagb))	
			
			ovlp = set.intersection(itaggeda,itaggedb)
			smm = set.union(itaggeda,itaggedb)
			
			if not smm : return 0
			else:
				return len(ovlp) / len(smm)
			
		def tag_similarity_extended(clouda,cloudb,v = False):
			"""
			Similarity measure only for tag clouds: measures the overlap of the
			sets of clouds marked by the two tags and return an averaged confidence
			of the relations of these links.
			
			Example
			
			tag a ---> [cloud1, cloud2]
			tag b ---> [cloud1, cloud3]
			tag c ---> [cloud4,	cloud5]
			
			clearly, similarity(cloud1,cloud1) == 1, so tag a and be will be at 
			least 0.5 related since they share half of their clouds; more if cloud2
			and cloud3 are related in gods' beliefs.
			
			then suppose cloud1 and cloud4 are believed to be related by 0.4, and 
			cloud5, cloud2, are related by 0.6, but cloud5 and cloud3 are totally
			unrelated.
			
			then tag c will be much closer to tag a than to tag b.
			
			This analysis is available only when god already has a complete belief set
			"""
			
			istaglink = lambda x: isinstance(x[0].item['id'],str) and isinstance(x[1].item['id'],str)
			
			if not istaglink((clouda,cloudb)):
				if v: print('nontag')
				return 0
			
			taga = clouda.item['id']
			tagb = cloudb.item['id']
			
			if v: print(taga,tagb)
			
			data = clouda.sky.data
			
			itaggeda = data.items_per_tag(taga)
			itaggedb = data.items_per_tag(tagb)
			
			cloudstaggeda = [clouda.sky.get_cloud(iid) for iid in itaggeda] # clouds for all items tagged with taga
			cloudstaggedb = [cloudb.sky.get_cloud(iid) for iid in itaggedb]
			
			from semanticsky_utilityfunctions import pair
			from clues import god
			
			bels = {}
			for a in cloudstaggeda:
				for b in cloudstaggedb:
					if a is not b:
						link = pair(a,b)
						bels[link] = god.believes(link)
			
			denom = len(bels.keys())
			if not denom: denom = 1
			avgres = sum(bels.values()) / denom
			return avgres

		def naive_core_overlap(clouda,cloudb):
			"""
			Simple overlap of the two clouds' cores.
			"""
			
			out = 0
			for i in range(len(clouda.layers)):
				acore = set(clouda.layers[i]['core'])
				bcore = set(cloudb.layers[i]['core'])
				
				ovlp = acore.intersection(bcore)
				union = acore.union(bcore)
				
				if union:
					out += len(ovlp) / len(union)
				
			return out / len(clouda.layers)
			
		def extended_core_overlap(clouda,cloudb):
			"""
			The core's words are used to make a larger bag of probably-related words
			and then these bags are compared.
			"""
			
			coodict = clouda.sky.counters['coo']
			
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
				acore = set(clouda.layers[i]['core'])
				bcore = set(cloudb.layers[i]['core'])
				
				nacore = set()
				nbcore = set()
				
				for word in acore:
					nacore.update(neighbours.get(word,[]))
					nacore.add(word)
				
				for word in bcore:
					nbcore.update(neighbours.get(word,[]))
					nbcore.add(word)
					
				ovlp = len(nacore.intersection(nbcore))
				unio = len(nacore.union(nbcore))
				
				if unio:
					out += ovlp / unio
				
			return out / len(clouda.layers)
				
	def __init__(self,function,guardian = True):
		if guardian: ALL_ALGS.append(function)
		else: NON_GUARDIAN_ALGS.append(function)
		
		algsbyname.append(function.__name__)
		return None
		
ALL_ALGS = [ var for var in Algorithm.builtin_algs.__dict__.values() if hasattr(var,'__call__')]

ALL_ALGS.remove(Algorithm.builtin_algs.someonesuggested)			
NON_GUARDIAN_ALGS = [Algorithm.builtin_algs.someonesuggested]

algsbyname = tuple(alg.__name__ for alg in ALL_ALGS + NON_GUARDIAN_ALGS)

# for backwards compatibility:

def localize():
	"""
	Binds locally all builtin algorithms.
	That is: algorithms.Algorithm.builtin_algs.any
	will be accessible as algorithms.any
	
	For backwards compatibility.
	"""
	toexec = ''
	allalgs = [ var for var in Algorithm.builtin_algs.__dict__.values() if hasattr(var,'__call__')]
	for alg in allalgs:		
		name = alg.__name__
		alg_path = "Algorithm.builtin_algs.{}".format(name)
		toexec += "global {}\n{} = {}\n".format(name,name,alg_path)
	#print('executing :: "\n{}"'.format(toexec))
	exec(toexec)
