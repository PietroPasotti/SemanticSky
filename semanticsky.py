#!/usr/bin/python3

"""
Python3 code. Compatible with 2.7 with minor modifications(mainly encoding)
"""

import nltk,re,sys,time,random,pickle,math,algorithms
from bs4 import BeautifulSoup, SoupStrainer
from group import Group
import semanticsky_utilityfunctions as utils
from semanticsky_utilityfunctions import * # all functions such as sentence splitting, language recognition, tokenization...
from sys import stdout
from copy import deepcopy

Counter = algorithms.Counter

class Data(object):
	"""
	reimplementation of Tweedejaars' DataWrapper
	Handles the interaction starfish db - semanticsky.
	Can be easily adapted to fit different data structures.
	
	The default one however has the following form:
	
	{	
	'data': {'some_unique_id': { information }}
	'tags': {'some_unique_id': { information }}
	}
	
	"""
	def __init__(self,filepath,fill = True,debug = False):
		
		self.filepath = filepath
		self.oridata = None
		self.debug = debug
		
		self.wrap()
		self.handle_aliases()
		self.induce_words_pairs()
			
	def wrap(self):
		"""
		Loads the pickled export, and gives to each item its own id.
		
		requirement: the data structure should be a dictionary from unique IDs
		to dictionaries.
		
		"""
		
		f = open(self.filepath,'rb')
		self.oridata = pickle.load(f)
		f.close()
		
		for key in self.oridata: # for both items and tags
			for itemIDortagNAME in self.oridata[key]: # each item stores its own id, and tags store their name
				self.oridata[key][itemIDortagNAME]['id'] = itemIDortagNAME

	# DataWrapper functions							
	def item(self,ID):
		"""
		Yields an item in the data, given its unique ID
		"""
		return self.oridata['items'][ID]
		
	def items(self):
		"""
		Generator of IDs of all items.
		"""
		for itemid in self.oridata['items']:
			yield itemid
	
	def items_by_dict(self):
		
		for itemid in self.items():
			yield self.item(itemid)
					
	def tag(self,name):
		return self.oridata['tags'][name]
		
	def tags(self,name = None):
		"""
		A generator for all tags' names.
								  -----
		"""
		for tag in self.oridata['tags']:
			yield tag			

	def remove_invalid_links(self):
		"""
		Removes all links within the data that are invalid due to type or
		authorship. These links should not be proposed by the algorithm
		because the are already automatically added in starfish.
		"""
		for k,v in self.oridata['items'].items():
			tempLinks = v['links'][:]
			for link in v['links']:
				if(self.ignore(v, k, link)):
					tempLinks.remove(link)
					v['links'] = tempLinks[:]

	def ignore(self, item, item_id, link_id):
		""" 
		Indicates whether or not a particular link is valid within the dataset.
		Returns true if the link is invalid and should be ignored
		"""
		link = self.item(link_id)

		# Ignore if link simply is the author of the doucment
		if (item.get('author') == link_id):
			return True

		# Ignore if link is glossary 
		if (link['type'] == 'Glossary'):
			return True

		# Ignore if link is simply a document written by person described by document
		if (item['type'] == 'Person' and link.get('author') == item_id):
			return True

		return False
	
	def proxytag(self,tag):
		"""
		Given a tag, returns the proxy tag for the tag's alias equivalence
		class.
		"""
		
		try:
			for cluster in self.tag_aliases_classes:
				if tag in cluster:
					return cluster[0]  # that is: the proxytag
			
		
		except AttributeError:
			self.handle_aliases()
			return proxytag(self,tag)
	
	def items_per_tag(self,tag):
		"""
		Returns a list of all items (by their id) which are tagged with tag.
		"""
		allitems = []
		
		for itemid in self.items():
			if tag in self.item(itemid)['tags']:
				allitems.append(itemid)
		
		return allitems
		
		
	# aliasing 
	def get_aliases(self,tagid):
		"""
		Returns a list of unique tags (by name) which form an equivalence class;
		the relation is aliasing (synonimy).
		"""
		
		clusters = self.tag_aliases_classes
		
		for cluster in clusters:
			if tagid in cluster:
				return cluster # should be unique!
				 
	def handle_aliases(self):
		"""
		Obtains the following situation:
		
		there is be only one proxy tag per alias group (many aliases will point to one and only one tag)
		if any of the alias group has a glossary, the only left tag will take it as string at the 'glossary'
		dict key.
		
		all glossaries will be assigned to their tag or proxy tag this way, and then be deleted as standalone objects.
		"""
		import cluster
		
		alltags = self.oridata['tags']
		self.tag_aliases_classes = cluster.clusterize1(alltags)
		newbase = deepcopy(self.oridata)
		
		for cluster in self.tag_aliases_classes:
			
			proxytag = cluster[0]
			
			def hasglossary(tag):
				if self.oridata['tags'].get(tag):
					if self.oridata['tags'][tag]['glossary']:
						return True
				return False
			
			glosses = [ t for t in cluster if hasglossary(t) and t is not proxytag ]
			glossaries_to_merge = []
			
			glostext = ''
			if len(glosses) > 1:
				#raise Warning('More than one glossary for alias group [{}]'.format(aliasgroup))
				
				basegloss = glosses[0]
				
				for t in glosses[1:]:
					glossaries_to_merge.append(self.tag(t)['glossary'])
					# these glossaries will be merged in glosses[0]'s one
		
				tag_with_glossary = glosses[0]
				ID_of_glossary = self.tag(tag_with_glossary)['glossary']
				dic_of_glossary = self.item(ID_of_glossary)

				glostext += dic_of_glossary['text']  	# we add the raw text of the glossary
				
				if len(glossaries_to_merge) > 0: # if there are multiple glossaries for alias-class:
					for gloss_id in glossaries_to_merge:
						gdict = self.oridata['items'][gloss_id]
						
						glostext += ' ' + gdict['text']
						
			newbase['tags'][proxytag]['glossary'] = self.item(self.tag(proxytag)['glossary'])['text'] if self.tag(proxytag)['glossary'] else None
			newbase['tags'][proxytag]['aliased_glossary'] = glostext # does NOT include proxytag's glossary; that one is stored under 'glossary'
			cl = deepcopy(cluster)
			cl.remove(proxytag)
			newbase['tags'][proxytag]['alias_of'] = cl

			for tag in cluster:
				if tag != proxytag:
					if tag in newbase['tags']:
						del newbase['tags'][tag]
			
		self.oridata = newbase
		
		if self.debug:
			
			e = BaseException('Failed')
			
			if not len(self.oridata['tags']) == len(self.tag_aliases_classes):
				raise e # no of tags != no of equivalence classes
			
			for tag in self.oridata['tags']:
				clusts_with_tag = 0
				for cluster in self.tag_aliases_classes:
					if tag in cluster:
						clusts_with_tag += 1
				if clusts_with_tag != 1:
					raise e # some tag in more than one cluster
					
			for cluster in self.tag_aliases_classes:
				if self.oridata['tags'][cluster[0]]['alias_of'] != [ t for t in  cluster if t != cluster[0] ]:
					raise e # some tag doesn't alias to its cluster (minus itself)
		
		return None	
	
	# linking
	def make_links_symmetric(self):
		"""
		As per the handle_aliases function, we sort of clusterize the links
		into equivalence classes.
		"""
		
		for part in ['items','tags']:
			
			for item in self.oridata[part].values():
				links = item.get('links')
				if not links:
					continue
				
				allinks = []
				allinks.extend(links)
				
				for link in links:
					itemlink = self.oridata['items'][link] # the item to which the link points
					nlinks = itemlink.get('links') # the links of the linked item(s)
					if nlinks: allinks.extend(nlinks)
				
				item['links'] = allinks
				for link in allinks:
					itemlink = self.oridata['items'][link]
					itemlink['links'] = allinks
				
		return True
				
	# counter building
	def induce_words_pairs(self):
		"""
		After producing a comprehensive corpus of all text available in 
		the database, retrieves two-words compounds. This means, pairs of
		words that often appear together, such as 'free download', 'university
		amsterdam', 'fuck off'.
		"""
		fullcorpus = ' '.join([  grab_text(item) for item in self.items_by_dict()  ])
		totokens = to_tokens_text(fullcorpus,stem = False, stopwords = True) # we want true words, but no useless ones.
		
		wordseqcounter = Counter()
		
		for sent in totokens:
			pos = 0
			for i in range(len(sent)-2):
				worda = sent[pos]
				wordb = sent[pos + 1]
				if worda != wordb:
					wordseqcounter[frozenset({worda,wordb})] += 1	
				pos += 1
				
		### now we crop off values less than some threshold, say two.
		
		cleanwordseqcounter = {pair:value for pair,value in wordseqcounter.items() if value > 2}
		
		self.wordseqcounter = cleanwordseqcounter
				
class SemanticSky(object):
	"""
	The Semantic Sky is the background of all clouds; is responsible for some
	higher-level computations and oversees cloud formation and evolution.
	It, so to say, where weather forecasts get interesting.

	Is essentially a wrapper for a pickled-export of starfish database.
	Call SemanticSky on a DataWrapper instance to make it work smooth.
	"""

	default_data = Data('/home/pietro/Perceptum/code/starfish/similarity/TweedejaarsProject/data/expert_maybe_false.pickle')

	default_stats = {	'number_of_words_in_corpus': 0,
			'number_of_tags': 0,
			'number_of_sentences': 0,
			'language_recognition_threshold' : 0.4,
			'clouds' : {'depth':2,
					'density': None,
					'thickness': None,
					'min_coo_threshold': 2,
					'min_word_freq_threshold' : 2, # not used
					'max_coo_length': 20,
					'max_vocab_length': 30,
					'cloud_hierarchy_inducer_threshold': 2.0/3.0}}
	
	### initializers
	def __init__(self,data = default_data,stats = default_stats,empty = False,god = None):

		self.counters = {	'coo':None,
							'word_freq':None,
							'tag_coo':None,
							'idf_db':None}
		
		self.data = data	
		self.stats = stats
		self.sky = []
		
		if empty:
			return
		
		if god is not None:
			self.god = god
			return self.init_from_god()
		
		starttime = time.clock()
		#if not test: # we populate all counters, then the sky.
		self.populate_counters()
			
		stdout.write('Populating sky... \n')
		print()
		stdout.flush()
		self.populate_sky()
		stdout.flush()
		print()
		stdout.write('\t*Initialization successful* :: [ {} seconds elapsed]\n'.format( (time.clock() - starttime) ))
		print()
		print( ' -'*60)
		print()	
	
	def __repr__(self):
		return '< SemanticSky :: {} clouds. >'.format(len(self.sky))
	
	def __str__(self):
		return '< SemanticSky :: {} clouds. >'.format(len(self.sky))
	
	def init_from_god(self):
		"""
		If a god is given, we retrieve as many clouds as we can from his
		internal database and spawn the rest.
		"""
		
		allclouds = []
		for pair in self.god.beliefs:
			if isinstance(pair,frozenset):
				allclouds.extend(pair)
		
		self.sky = allclouds
		
		ids = []
		for cloud in allclouds:
			ids.append(cloud.item['id'])
			
		allids = [i for i in self.data.items()]
		allids.extend([i for i in self.data.tags()])
		
		nothere = [i for i in allids if i not in ids]
		
		for i in nothere:
			try:
				item = self.data.item(i)
			except KeyError:
				item = self.data.tag(i)
			
			cloud = Cloud(self,item)
		
		return None
		
	def populate_counters(self):
		"""
		Populates the internal counters.
		"""
		print()
		print( ' -'*60)
		stdout.write('Populating sky-level counters: \n\t token co-occurrences... ')
		stdout.flush()

		self.populate_coo_counter()
		stdout.write('\t [ Done. ]\n')
		stdout.flush()
		stdout.write("\t word frequency... ")
		stdout.flush()
		self.populate_word_freq_counter()
		stdout.write('\t\t [ Done. ]\n')
		stdout.flush()
		stdout.write("\t tag co-occurrences... ")
		stdout.flush()
		self.populate_tag_coo_counter()
		stdout.write('\t\t [ Done. ]\n')
		stdout.flush()
		stdout.write("\t idf database... ")
		stdout.flush()
		self.populate_idf_database()
		stdout.write('\t\t [ Done. ]\n')
		stdout.flush()		
		del self.__tokens_temp # frees the memory
		print( ' -'*60)
		print()	
			
	def populate_sky(self):
		"""
		This function instantiates a cloud per each item in the database,
		whatever the type, and appends it to the sky.
		"""
		
		if self.sky:
			return None
		
	# ITEM CLOUDS
		noitems = len(self.data.oridata['items'])
		stdout.write('\tItem clouds... 	\t')
		i = 0
		bar = ProgressBar(noitems)
		for itemID in self.data.items():
			item = self.getitem(itemID)
			item['id'] = itemID # is a long()
			cloud = Cloud(self,item)
			
			bar(i)
			i += 1
		stdout.write('\n\t [ {} Clouds. ]\n'.format(i))

	# TAG CLOUDS
		notags = len(self.data.oridata['tags'])
		stdout.write('\tTag clouds... \t\t')
		e = 0
		bar = ProgressBar(notags)
		for tagID in self.data.tags():
			tag = self.data.tag(tagID)
			tag['id'] = tagID # is the name of the tag == a str()
			cloud = Cloud(self,tag)
			
			bar(e)
			e += 1
		stdout.write('\n\t [ {} Clouds. ]\n'.format(e) )
		print('\n\t Total: [ {} Clouds ] \t : quite a rainy day.\n'.format(e+i))
		return None
	
	### iterators
	def iter_layers(self,layerno = 0, cloud = None):
		"""
		Yields all layers [layerno] of all clouds in the sky.
		If a cloud is given, returns the layer.
		"""

		if cloud:
			yield cloud.layers[layerno]
			return
		else:
			for cloud in self.sky:
				yield clouds.layers[layerno]
		
	def clouds(self):
		"""
		Generator for all clouds in the sky.
		"""

		for cloud in self.sky:
			yield cloud
	
	def clouds_by_id(self):
		
		for cloud in self.clouds():
			yield cloud.item['id']
	
	def iter_pairs(self,source = None):
		"""
		A generator for all pairwise-coupled clouds.
		"""

		i = 0
		
		if not source:
			source = self.sky
		if not hasattr(source,'__getitem__'):
			raise BaseException('Sorry, I need something with a __getitem__ attribute. Got a {}.'.format(type(source)))

		for clouda in source:
			for cloudb in source[i:]:
				if clouda != cloudb:
					yield pair(clouda,cloudb)
			
			i += 1


	### data gathering functions
	def getitem(self,ID):
		"""
		Returns the DICTIONARY of an item, given its id.
		
		Note: doesn't return the cloud, but the item.
		"""
		return self.data.item(ID)

	def get_cloud(self,ID):
		"""
		Looks for and returns a cloud with given ID.
		ID can of course both be an int and a str.
		
		If the lookup fails, raises a ValueError
		"""
		
		for cloud in self.clouds():
			if cloud.ID == ID:
				return cloud
		
		raise ValueError('No cloud with ID {}'.format(ID))
			
	def gettag(self,ID):
		"""
		Returns the dictionary of a tag.
		"""
		return self.data.tag(ID)
	
	def pair_by_id(self,ID1,ID2=None):
		"""
		Returns a link, given two ids as a tuple or as two separate values.
		"""
		
		if (isinstance(ID1,int) or  isinstance(ID1,str)) and ID2 is None:
			raise TypeError('Need two values.')
		elif ID2 is not None:
			pass
		else:
			ID1,ID2 = ID1
		
		clouda = self.get_cloud(ID1)
		cloudb = self.get_cloud(ID2)
		
		return pair(clouda,cloudb)

	
	### counters population functionsself.oridata['tags']
	def populate_coo_counter(self):
		"""
		Counts co-occurrences in the whole corpus, maybe for weighting or
		idf purposes.
		"""
		
		DOCS = []

		for item in self.data.items(): # iterates through item IDs
			itemdict = self.getitem(item) # returns the dictionary of the item, given its ID
			sents = to_sentences_item(itemdict) # breaks an item down to tokens: [['']]
			DOCS.append(sents)

		self.__tokens_temp = DOCS

		coo_counter = Counter()
		
		for doc in DOCS:
			for sent in doc:
				coos = count_coo_sent(sent)
				for key,value in coos:
					coo_counter[key] += value

		self.counters['coo'] = coo_counter
		return None		
	
	def populate_word_freq_counter(self):
		"""
		Generates a word frequency counter of all the database.
		"""
		wfreq_counter = Counter()

		docs = self.__tokens_temp
		
		for doc in docs:
			for sent in doc:
				for word in sent:
					wfreq_counter[word] += 1
		
		nofwords = sum(wfreq_counter.values())		
		
		self.counters['word_freq'] = wfreq_counter
		
		self.stats['number_of_words_in_corpus'] = nofwords
		return None

	def populate_tag_coo_counter(self):
		"""
		Generates a tag co-occurrence database: the more two tags co-occur,
		the more they are likely to be related.
		"""
		tag_coo_counter = Counter()

		for itemID in self.data.items():
			item = self.getitem(itemID) # retrieves the dictionary
			item_tags = item['tags']
			c = 1
			for tag1 in item_tags:
				for tag2 in item_tags[c:]:
					if tag1 != tag2:
						pair = frozenset({tag1,tag2})
						tag_coo_counter[pair] += 1
						c += 1

		self.counters['tag_coo'] = tag_coo_counter
		return None
	
	def populate_idf_database(self):
		"""
		Populates a database of idf weights: word --> idf
		(the words are stemmed!)
		"""
		
		idfcounter = Counter()
		N = len(self.__tokens_temp) # number of documents of the whole database (i.e. no of items)
			
		for word in self.counters['word_freq']:
			nw = 0 # number of docs with word
			for doc in self.__tokens_temp:
				
				isthere = False
				
				for sent in doc:
					if word in sent:
						isthere = True
						break
					if isthere:
						break
				
				if isthere:
					nw += 1
					
			idfw = math.log( (N / nw) ,2)
			idfcounter[word] = idfw
		
		self.counters['idf_db'] = idfcounter
		
		return None
	
	### networking functions
	def base_network(self):
		
		net = {}
		
		for cloud in self.clouds():
			net[cloud] = cloud.links(False) # will return a list of clouds
		
		return net
	
	### tagclouds handling
	def remove_tag_clouds(self):
		"""
		Removes from the sky all clouds around a tag.
		"""
		
		for cloud in self.sky:
			if cloud.cloudtype == 'tags':
				self.sky.remove(cloud)
				del cloud
		return True
					
class Cloud(object):
	"""
	A Cloud is a semantic web of information, hierarchically ordered
	from the innermost to the outermost (a relatedness measure already).
	The cloud's layers can then be compared with other clouds' same-level
	layers to get a higher-order proximity index.
	"""

	def __init__(self,sky,item):

			self.item = item
			self.ID = item['id']
			self.data = sky.data
			self.sky = sky
			self.layers = [[]]
			
			self.populate()
			
			if self not in sky.sky:
				sky.sky.append(self)
			
	def __repr__(self):
		return "< Cloud [{}] at {} >".format(self.ID,id(self))
	
	def __str__(self):
		return "< Cloud [{}]. [ {} layers. ] >".format(self.ID, len(self.layers))
	
	def __hash__(self):
		return hash(self.item['id'])
	
	@property
	def depth(self):
		return len(self.layers)
	@property
	def itemtype(self):
		return self.item['type']
	@property
	def cloudtype(self):
	
		if isinstance(self.item['id'],str):
			return 'tags'
		else:
			return 'items'
				
	def ctype(self):
		"""
		Returns the type of the wrapped item, such as 'Person', 'Glossary'
		or the such. Returns 'tag' if none is found.
		"""
		
		return self.item.get('type','tag')
	
	
	### data_getters
	def populate(self,depth = None):
		"""
		Populates up to depth layers (from the innest to the outmost)
		with semantic information about the core of the cloud: its item.

		If you want to EXTEND the layer depth by 1 or more levels, use a 
		different function.
		"""

		if not self.layers[0]: # we ensure there is a base from which to expand
			self.retrieve_zero_layer()

		for d in range(self.sky.stats['clouds']['depth'] - 1): # the zero layer counts as depth 1

			base = self.layers[d]
			self.expand_from_base(base)

		return None
		
	def clean(self,listofstr):
		"""
		Does the job of cleaning each of the str in listofstr to an
		uniform and comparable way. To do this:

		1) strips off html tags and strange characters.
		2) retrieves and removes from the text all urls.
		3) also retrieves all (Capitalized Tuples of Words)

		returns
		-------

		{	'text': [],
			'names' : [],
			'web_links': set()}

		"""
		
		if isinstance(listofstr,str):
			listofstr = [listofstr]
		
		out = {	'text': [],
			'names' : [],
			'web_links': set()}
		
		re_names_array = [	re.compile(r"[A-Z][a-z]+\s[A-Z][a-z]+\b"), 				# captures "Arianna Betti"
							re.compile(r"[A-Z][.].*?\s[A-Z][a-z]+\b"),				# captures "J.R. Tolkien", "N. Brouwer" and "A.Cozza".
							re.compile(r"[A-Z][a-z]+\s[A-Za-z]+\s[A-Z][a-z]+"),		# captures "University of Amsterdam" and "Rosa de Hoog", as well as "Tiziano Caio Mario".		
							re.compile(r"[A-Z][a-z]+,(?:\s?[A-Z]\.)+?"), 			# captures "Betti, A." these are the last one to be extracted, so that we won't ruin other names
							re.compile(r"[A-Z]+[A-Z0-9]{1-5}") 						# captures 'FNWI', 'UVA' and 'ECTN', and also 'ECT2N'. also, VU																
							]
							
		#oldarray = [	re.compile(r"[A-Z][a-z]+\s[A-Z][a-z]+\b"), 				
		#					re.compile(r"[A-Z][.].*?\s[A-Z][a-z]+\b"),			
		#					re.compile(r"[A-Z][a-z]+\s[A-Za-z]+\s[A-Z][a-z]+"),	
		#					re.compile(r"[A-Z][a-z]+,(?:\s?[A-Z]\.)*?")	]
			
		clean1 = []	
		@Group
		def handle_links_and_preprocessing():
			for string in listofstr:
				nohtml,links = preprocess(str(string),True)
				out['web_links'].update(links)
				if nohtml:
					clean1.append(nohtml)

		clean2 = []
		@Group
		def handle_names():
			for sent in clean1:
				if not hasattr(sent,'split'): 
					raise BaseException('Wat wat wat: s is {}'.format(sent))
				text_clean_of_names = sent
				
				for reg in re_names_array:
					N = reg.findall(text_clean_of_names)
					# we purge off implausible names
					implausible_contents = (re.compile(r"[0-9]"),re.compile(r"\(.*\)"))
					cleanN = []
					
					for name_candidate in N:
						good = True
						
						for reg in implausible_contents:	
							if reg.findall(name_candidate): # if there is some match
								good = not good
								break
							
						if good:

							if ',' in name_candidate:
								cn = name_candidate.split(',')
								cn.reverse()
								cn = ' '.join(cn)
								
							cn = re.sub(re.compile(r"\s+"),' ',name_candidate)
							cn = cn.strip()							
							
							cleanN.append(cn)
							#text_clean_of_names = text_clean_of_names.replace(name_candidate, ' ') # we remove the names, for they only add noise.						
	
					out["names"].extend(cleanN)
				clean2.append(text_clean_of_names)
				
			# we remove some duplicates
			out['names'] = list(set(out['names'])) # even though: a name occurring often hints at the relevance of the person!
			
		clean3 = []
		@Group
		def uniform_text():
			spaces = re.compile(r"\s+")
			for s in clean2:
				nospaces = spaces.sub(' ',s)
				clean3.append(nospaces)

		out['text'] = clean3

		return out
	
	def iter_proximities(self,others):
		"""
		This function is a generator.
		for each Cloud in others:
		yield proximity(self,other)
		"""
		
		for cloud in others:
			yield self.proximity(cloud)
		
	def proximity(self,other):
		"""
		Other must be a Cloud.
		returns all the common features plus a
		quick-to-assess number between zero and 1 which will be a more-or
		-less initial proximity metric.

		returns
		-------

		tuple(list(),float())
		"""
		import algorithms
		algs = { 			'tf_weighting' : 		algorithms.tf_weighting,
							'tf_idf_weighting': 	algorithms.tf_idf_weighting,
							'coo_dicts_overlap': 	algorithms.coo_dicts_overlap,
							'coo_dicts_neighbour' : algorithms.coo_dicts_neighbour,
							'tag_overlap': 			algorithms.tag_overlap}

		if other is self: # proximity here should be 1, but we don't need a reflexive relation
			return 1
			
		out = {}
		for alg in algs:
			ALG = algs[alg]
			
			out[alg] = 0
			if alg == 'coo_dicts_overlap': 
				out[alg] = {}
				for version in [1,2,3]:
					outcome = ALG(self,other,version)
					out[alg]['version {}'.format(version)] = outcome
			else:
				outcome = ALG(self,other)
				out[alg] = outcome
			
		return out
	
	def links(self,numbers = True):
		
		if numbers:
			return self.item.get('links',None)
		else: 
			return [self.sky.get_cloud(ID) for ID in self.item.get('links',[])] # list of clouds the cloud's item is linked to
	
	def nearest_neighbours(self):
		return nearestneighbours(self)
	
	def core(self):
		"""
		Produces a plain list of words that are (very likely to be)
		keywords for this cloud.
		"""
		
		allws = []
		for i in range(len(self.layers)):
			allws.extend(self.layers[i]['core'])
		
		if not allws:
			self.get_core()
		
			for i in range(len(self.layers)):
				allws.extend(self.layers[i]['core'])		
		
		return allws
		
	def istagcloud(self):
		
		if isinstance(self.item['id'],str):
			return True
		else:
			return False
	
	def get_header(self):
		"""
		Returns a useful short description of the item, for human recognition.
		"""
		
		if self.cloudtype == 'tags':
			return self.item['id']
			
		return self.item.get('name',self.item.get('title'))
		
	### growers
	def retrieve_zero_layer(self):
		"""
		Builds up a zero layer from the item's direct information we have
		from starfish's database.
		"""

		zero_layer = {	'core' : [],
						'words_tfidf': {},
						'words_tf' : {},
						'top_coo' : None,
						'communities' : [],
						'names': set(),
						'places': [],
						'language': None,
						'web_sources': set(),
						'tags' : set() }
		
		item = self.item

		if item['type'] == "Person":
			zero_layer['names'].update([item['name']])
			
		nucleus = [self.item.get('text',''),self.item.get('about',''),self.item.get('headline',''),self.item.get('title',''),self.item.get('aliased_glossary','')]		
		if self.item.get('glossary'): # if the item is a tag, crucial part of the description will be the glossary.
									  # the aliases-handling which took place at DataWrapper level will ensure that
									  # there is only one tag per alias-group, and that its glossary is a string
			nucleus.append(self.item['glossary'])
			
		out = self.clean(nucleus)

		ctexts = out['text']
		clinks = out['web_links']
		cnames = out['names']

		zero_layer['web_sources'].update(clinks)
		zero_layer['names'].update(cnames)
		zero_layer['tags'].update( self.item.get('tags',[]) )
		zero_layer['tags'].update( self.item.get('alias_of',[]) )
		
		# COO Handling
		coodict = Counter()
		for text in ctexts: update_coo_dict_with_raw_text(coodict,text)
		minfreq = self.sky.stats['clouds']['min_coo_threshold']	
		maxln = self.sky.stats['clouds']['max_coo_length']
		if len(ctexts) < 200:
			pass # if there is very little text, we are less picky, and keep all coos
		else:
			coodict = Counter({ el:value for el,value in coodict.most_common(maxln) if coodict[el] >= minfreq })
		zero_layer['top_coo'] = dict(coodict)
		
		# WORD FREQUENCY + IDF Handling
		maxfqlen = self.sky.stats['clouds']['max_vocab_length']
		idfcount = Counter()
		tfcount = Counter()
		for word,wordcount in most_freq_words_from_raw_texts(ctexts,crop = maxfqlen):
			lentexts = len(' '.join(ctexts).split(' '))
			wordfreq = wordcount / lentexts
			
			tfcount[word] += wordfreq
			
			try:
				wordidf = self.sky.counters['idf_db'][word]
			except BaseException:
				self.sky.populate_counters()
				wordidf = self.sky.counters['idf_db'][word]
			
			word_tf_idf = wordfreq * wordidf
			
			idfcount[word] +=  word_tf_idf
		
		zero_layer['words_tf'] = dict(tfcount)
		zero_layer['words_tfidf'] = dict(idfcount)
		
		# LANGUAGE Handling	
		zero_layer['language'] = guess_language( ' '.join(ctexts) )

		self.layers = [zero_layer]
		
		return None
		
	def expand_from_base(self,base):
		"""
		Takes as input a base: that is, a dictionary with some information,
		(such as a layer, typically) and creates a new layer to append to 
		self.layers.

		Currently empty.

		"""

		good = base is self.layers[0]

		#neighbours = self.get_closest_items()
		

		return 
	
	def is_empty(self):
		"""
		Returns true iff the cloud does not contain 'enough' information.
		Example: if the cloud's center is a person, and the only info we have
		is his name.
		"""
		
		# naive approach:
		item = self.item
		stringitem = [ str(value) for value in item.values() ]
		
		if len(stringitem) <= 1000:
			return True
		else:
			return False

	def google_lookup(self,query):
		"""
		given a string query, formats it into a google search and retrieves
		the results. We then compare every result with what we already have.
		If we don't have anything, we compare it with the clouds'
		nearest neighbours. If there are too many of them (e.g. all have
		proximity 0) then we just take the first n results for good.
		"""
		
	def get_core(self):
		"""
		Produces a plain list of words that are (very likely to be)
		keywords for this cloud.
		"""
		
		candidates = []
		
		idfs = []
		for i in range(len(self.layers)):
			idfdict = self.layers[i]['words_tfidf']
			idflist = list(idfdict.keys())
			
			idflist.sort(key = lambda x: idfdict[x]) 
			idflist.reverse() # from max to min 
			
			idfs.extend(idflist) # deeper layers go automatically below
		
		header = self.item.get('title',self.item.get('headline',''))
		body = self.item.get('about',self.item.get('text',''))
		
		s_tokheader = to_tokens_text(header)
		tokheader = []
		for s in s_tokheader:
			tokheader.extend(s)
		
		for word in idfs[:min((len(idfs),30))]:
			if word in tokheader: # can return [] or [[str()]] types
				candidates.append(word)
		
		for i in range(len(self.layers)):
			self.layers[i]['core'] = candidates[:min((len(candidates),15))]

class Link(tuple):
	
	def __new__(typ, itr):
		
		ordr = sorted(itr,key = lambda x: str(x))
		
		return tuple.__new__(typ, ordr)

	def ctype(self):
		return ctype(self)
		
	def longctype(self):
		return ctype_to_type(self.ctype())
	
	@property
	def ids(self):
		
		return self[0].item['id'],self[1].item['id']
	
	def __str__(self):
		
		return "< Link :: ({},{}).>".format(*self.ids)
		
	def __repr__(self):
		
		return str(self)
				
class SuperCloud(Cloud):
	
	def __init__(self,cloudlist,automerge = True):
		
		if not isinstance(cloudlist,list):
			raise TypeError()
		
		for cloud in cloudlist:
			if not isinstance(cloud,Cloud):
				raise TypeError()
		
		self.cloudlist = cloudlist
		self.IDlist = tuple(cloud.item['id'] for cloud in cloudlist)
		if automerge: self.merge()
		
	def merge(self):
		
		"""
		Makes its layers be the sum of the underlying clouds' layers.
		Rather failsafe, at the moment.
		"""
		
		for cloud in self.cloudlist:
			for i in range(len(cloud.layers)):
				
				for key in cloud.layers[i]:
					try:
						self.layers[i][key] += cloud.layers[i]
						continue
					except BaseException():
						pass
					try:
						self.layers[i][key].update( cloud.layers[i] )
						continue
					except BaseException():
						pass					

					try:
						self.layers[i][key].extend(cloud.layers[i])
						continue
					except BaseException():
						pass
						
		
			
		
		
