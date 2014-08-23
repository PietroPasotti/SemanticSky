#!/usr/bin/python3

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
		
		import pickle
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
		
		alltags = self.oridata['tags']
		from .cluster import clusterize1
		self.tag_aliases_classes = clusterize1(alltags)
		from copy import deepcopy
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
			
			from copy import deepcopy
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
		
		from .utils import to_tokens_text, grab_text
		from collections import Counter
		
		fullcorpus = ' '.join([  grab_text(item) for item in self.items_by_dict() ]) 	# a fully tokenized corpus. For large corpora
																						# this might become a problem?
																						
		totokens = to_tokens_text(fullcorpus,stem = False, stopwords = True) # we want words, but no useless ones.
		
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

	Is essentially a wrapper for a pickled export of (starfish) database.
	Call SemanticSky on a DataWrapper instance (or on a path to a file) 
	to make it work smooth.
	"""
	
	def __init__(self,data = None,stats = None,empty = False,god = None):
		
		from semanticsky import DEFAULTS,_SKY,default_data_path
		from time import clock
		
		self.counters = {	'coo':None,
							'word_freq':None,
							'tag_coo':None,
							'idf_db':None}
		
		if stats is None:
			stats = DEFAULTS['sky_stats']
		if data is None:
			data = Data(default_data_path)
		elif isinstance(data,Data):
			pass
		elif isinstance(data,str):
			try:
				data = Data(data)
			except BaseException as e:
				print("ERROR while loading data to SemanticSky. Probably the path is invalid or the target file is not good.")
				raise e
		else:
			raise BaseException('Unrecognized inputtype for *data* kwarg: {}. Should be a str, Data or None instance instead.'.format(type(data)))
			
		self.data = data	
		self.stats = stats
		self.sky = []
		
		if empty:
			return
		if god is not None: # we can give a god to a sky...
			self.god = god
			return self.init_from_god()
		
		starttime = clock()
		#if not test: # we populate all counters, then the sky.
		self.vb = DEFAULTS['verbosity']
		self.populate_counters()
		_SKY = self # we set the global _SKY to self
		
		if self.vb > 0: 
			print('Populating sky... \n')
		self.populate_sky()
		if self.vb > 0:
			print('\t*Initialization successful* :: [ {} seconds elapsed]\n'.format( (clock() - starttime) ))
			print( ' -'*60)
		
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
				
			from .clouds import Cloud
			cloud = Cloud(self,item)
		
		return None
		
	def populate_counters(self):
		"""
		Populates the internal counters. These will be used by some angels
		such as tf_weighting, to determine faster their evaluations.
		"""
		if self.vb > 0:
			print()
			print( ' -'*60)
			print('Populating sky-level counters: \n\t token co-occurrences... ',end = '')
		
		self.populate_coo_counter()
		if self.vb > 0:
			print('\t [ Done. ]')
		
			print("\t word frequency... ",end = '')
		
		self.populate_word_freq_counter()
		if self.vb > 0:
			print('\t\t [ Done. ]')
			
			print("\t tag co-occurrences... ",end = '')
		
		self.populate_tag_coo_counter()
		if self.vb > 0:	
			print('\t\t [ Done. ]')
			
			print("\t idf database... ",end = '')
		
		self.populate_idf_database()
		if self.vb > 0:
			print('\t\t [ Done. ]')
			print( ' -'*60)
			print()			
		del self.__tokens_temp # frees some memory
		
	def populate_sky(self):
		"""
		This function instantiates a cloud per each item in the database,
		whatever the type, and appends it to the sky.
		"""
		
		from semanticsky.tests import ProgressBar
		from .clouds import Cloud
		
		if self.sky:
			return None
		
	# ITEM CLOUDS
		noitems = len(self.data.oridata['items'])
		if self.vb > 1:
			bar = ProgressBar(noitems,title = "Item clouds ")
		for itemID in self.data.items():
			item = self.getitem(itemID)
			item['id'] = itemID # is a long()
			
			cloud = Cloud(self,item)
			
			if self.vb > 1: bar()
		lself = len(self.sky)
		if self.vb > 0:
			print('\n\t [ {} Clouds. ]\n'.format(lself))
		
	# TAG CLOUDS
		notags = len(self.data.oridata['tags'])
		if self.vb > 1:
			bar = ProgressBar(notags,title =  'Tag clouds ')
		for tagID in self.data.tags():
			tag = self.data.tag(tagID)
			tag['id'] = tagID # is the name of the tag == a str()
			
			cloud = Cloud(self,tag)
			
			if self.vb > 1: bar()
			
		if self.vb > 0:
			print('\n\t [ {} Clouds. ]\n'.format(len(self.sky) - lself) )
		if self.vb > 0:
			print('\n\t Total: [ {} Clouds ] \t : quite a rainy day.\n'.format(len(self.sky)))
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
		from .clouds.core import pair # default pairing system : currently, Link instances.
		
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
		from .clouds.core import pair
		return pair(clouda,cloudb)

	
	### counters population functionsself.oridata['tags']
	def populate_coo_counter(self):
		"""
		Counts co-occurrences in the whole corpus, maybe for weighting or
		idf purposes.
		"""
		from .utils import to_sentences_item,count_coo_sent
		from collections import Counter	
		
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
		from collections import Counter
		wfreq_counter = Counter()
		nsents = 0
		docs = self.__tokens_temp
		
		for doc in docs:
			for sent in doc:
				nsents += 1
				for word in sent:
					wfreq_counter[word] += 1
		
		nofwords = sum(wfreq_counter.values())		
		
		self.counters['word_freq'] = wfreq_counter
		
		self.stats['number_of_words_in_corpus'] = nofwords
		self.stats['number_of_sentences'] = nsents
		self.stats['number_of_tags'] = len(list(self.data.tags()))
	
		return None

	def populate_tag_coo_counter(self):
		"""
		Generates a tag co-occurrence database: the more two tags co-occur,
		the more they are likely to be related.
		"""
		from collections import Counter
		tag_coo_counter = Counter()

		for itemID in self.data.items():
			item = self.getitem(itemID) # retrieves the dictionary
			item_tags = item['tags']
			c = 1
			for tag1 in item_tags:
				for tag2 in item_tags[c:]:
					if tag1 != tag2:
						pair = frozenset({tag1,tag2}) # shouldn't this be a Link instance? More or less same properties (?), but nicer.
						tag_coo_counter[pair] += 1
						c += 1

		self.counters['tag_coo'] = tag_coo_counter
		return None
	
	def populate_idf_database(self):
		"""
		Populates a database of idf weights: word --> idf
		(the words are stemmed!)
		"""
		from collections import Counter
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
			
			from math import log
			idfw = log( (N / nw) ,2)
			idfcounter[word] = idfw
		
		self.counters['idf_db'] = idfcounter
		
		return None
	
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
	
class Link(tuple):
	
	def __new__(typ, itr):
		
		ordr = sorted(itr,key = lambda x: str(x))
		
		return tuple.__new__(typ, ordr)

	def ctype(self):
		"""
		We asume it's a cloud link...
		"""
		from .clouds.core import ctype
		return ctype(self)
		
	@property
	def ids(self):
		
		switch = all(str(x.__class__) == "<class 'semanticsky.skies.clouds.cloud.Cloud'>" for x in self)
		
		if switch:
			return self[0].item['id'],self[1].item['id']
		
		else:
			return self[0],self[1]
		
	def __str__(self):
		
		def gn(i):
			if str(i.__class__) == "<class 'semanticsky.skies.clouds.cloud.Cloud'>":
				return 'c' + str(i.item['id'])
			else:
				return str(i)
			
		toret = gn(self[0]) + ',' + gn(self[1])
		
		return "< Link :: ({}).>".format(toret)
		
	def __repr__(self):
		
		return str(self)
	
	def __iter__(self):
		
		for i in (self[0],self[1]):
			yield i

	def __eq__(self,other):
		
		try:
			o,oo = other
			if (o == self[0] and oo == self[1]) or (o == self[1] and oo == self[0]):
				return True
		except BaseException:
			return False
		
		return False
	
	def __hash__(self):
		
		return hash((self[0],self[1]))
