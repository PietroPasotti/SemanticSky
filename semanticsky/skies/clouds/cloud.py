#!/usr/bin/python3

				
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
		return "< Cloud [{}] at {}. >".format(self.ID,id(self))
	
	def __str__(self):
		return "< Cloud [{}]. >".format(self.ID)
	
	def __hash__(self):
		return hash(self.item['id'])
	
	@property
	def depth(self):
		return len(self.layers)
	@property
	def itemtype(self):
		return self.item['type']
				
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
		
		from ..utils import re,Group,preprocess
		
		re_names_array = [	re.compile(r"[A-Z][a-z]+\s[A-Z][a-z]+\b"), 				# captures "Arianna Betti"
							re.compile(r"[A-Z][.].*?\s[A-Z][a-z]+\b"),				# captures "J.R. Tolkien", "N. Brouwer" and "A.Cozza".
							re.compile(r"[A-Z][a-z]+\s[A-Za-z]+\s[A-Z][a-z]+"),		# captures "University of Amsterdam" and "Rosa de Hoog", as well as "Tiziano Caio Mario".		
							re.compile(r"[A-Z][a-z]+,(?:\s?[A-Z]\.)+?"), 			# captures "Betti, A." these are the last one to be extracted, so that we won't ruin other names
							re.compile(r"[A-Z]+[A-Z0-9]{1-5}") 						# captures 'FNWI', 'UVA' and 'ECTN', and also 'ECT2N'. also, VU																
							]
						
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
	
	def links(self,numbers = True):
		
		if numbers:
			return self.item.get('links',None)
		else: 
			return [self.sky.get_cloud(ID) for ID in self.item.get('links',[])] # list of clouds the cloud's item is linked to
		
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
		
		from ..utils import Counter, most_freq_words_from_raw_texts,  update_coo_dict_with_raw_text, guess_language
		
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
		from ..utils import to_tokens_text
		
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
