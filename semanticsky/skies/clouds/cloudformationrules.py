#!/usr/bin/python3

"""
This file hosts a LayerBuilder class, that allows to load more or less custom
cloud formation rules. Its call method receives as input a dictionary and
invokes all cloud formation rules loaded on it before returning the layers.
"""

class LayerBuilder():
	
	def __init__(self,cloud,pipeline_override = False,autobuild = True):
		
		self.cloud = cloud
		if pipeline_override:
			self._pipeline = LayerBuilder.get_pipeline(pipeline_override) # must be a string!
		self.oritem = cloud.item
		
		if autobuild:
			self.build_layers()
		else:
			return	
		
	def __call__(self,item,layerno):
		"""
		Updates the *layerno* layer of self.cloud following the full pipeline.
		"""
		
		
		for rule in self.pipeline()[layerno]:
			
			# we squeeze in also self, in case we need to backreference to some weird things. See tfidf rule for example.
			item,output = rule(item,self) 	# output should be a tuple (str, any_data).
										# item can be unchanged or changed, depending on the rules. Some rules might do cleaning, for example.
										# item will not be stored.
			if not output:
				continue
			
			if isinstance(output[0],tuple): # then we are facing multiple outputs
				toutput = output
				for output in toutput:
					if output[0] in self.cloud.layers[layerno]:
						getattr(self.cloud.layers[layerno][output[0]],'update', getattr(self.cloud.layers[layerno][output[0]], 'add' ,  getattr(self.cloud.layers[layerno][output[0]], 'extend' )  )  )( self.cloud.layers[layerno][output[0]], output[1] ) 
						# we try not to lose data: we might have multiple rules that retrieve urls, for example.
					else:	 
						self.cloud.layers[layerno][output[0]] = output[1]
			else:
				if output[0] in self.cloud.layers[layerno]:
					getattr(self.cloud.layers[layerno][output[0]],'update', getattr(self.cloud.layers[layerno][output[0]], 'add' ,  getattr(self.cloud.layers[layerno][output[0]], 'extend' )  )  )( self.cloud.layers[layerno][output[0]], output[1] ) 
					# we try not to lose data: we might have multiple rules that retrieve urls, for example.
				else:	 
					self.cloud.layers[layerno][ output[0] ] = output[1] # we just set it to the new value.
								
		return
		
	def build_layers(self):
		
		for layerno in self.pipeline(): # all the layers the former is capable to form
			try:
				self.cloud.layers[layerno] = {}
			except BaseException:
				self.cloud.layers.append({})
			
			self(self.cloud.item,layerno)
		
	@property
	def pipeline(self):
		
		if hasattr(self,'_pipeline'):
			return self._pipeline
		
		from semanticsky import DEFAULTS	
		pipeline_name = DEFAULTS['layerformer_defaults']['main_pipeline']
		# we lookup the pipeline in the builtins.
		self._pipeline = LayerBuilder.get_pipeline(pipeline_name)
		return self._pipeline
	
	def get_pipeline(pipename):
		
		pipeline = getattr(LayerBuilder.builtin_pipelines,pipename)
		return pipeline
		
	class builtin_layerrules():
		"""
		Follows a bunch of rules I used to form clouds for Starfish items.
		Each rule takes as input the output of the previous one, and gets 
		some information out of it / modifies it in some way.
		"""
		
		def tags(item,builder):
			"""
			This must be done before the item's text is crushed down to string.
			"""
			
			# assumes item is still a dictionary.
			allts = item.get('tags',[])
			aliases = item.get('alias_of')
			if aliases: allts.extend(aliases)
			
			return item, ('tags', allts)
		
		def crunch_down_to_string(item,builder):
			
			# Fatal Python error: Cannot recover from stack overflow.
			
			def lookupdate(value):
				
				out = ''

				if isinstance(value,str):
					out += ' '
					out += value

				elif isinstance(value,(tuple,list)):
					for subval in value:
						out += ' '
						out += lookupdate(subval)
						
				elif isinstance(value,dict):
					for subval in value.values():
						out += ' '
						out += lookupdate(subval)

				else: # we force into string.
					out += ' '
					out += str(value)
					
				
				return out
						
			tostring = ''
			for key,value in item.items():
				
				if key == 'tags': ## we don't add tags to the stringed text, otherwise we mess up names and tf_idf counts!
					continue 
				
				tostring += lookupdate(value)
				tostring += ' '
				
			tostring.strip()
			return tostring,{} # we could also have used ..utils.grab_text()
			
		def preprocess(item,builder): # cleans html
			"""
			This should always be the first rule if the item has html formatted 
			parts.
			Returns all the info it can get from hrefs.
			"""
			
			from ..utils import BeautifulSoup,SoupStrainer,re
			
			allinks = set({})
			urlsoup = BeautifulSoup(item,parse_only=SoupStrainer('a'))
			for link in urlsoup:
				if link.get('href'):
					allinks.add(link['href'])

			soup = BeautifulSoup(item)
			for link in soup:
				if link.get('href'):
					allinks.add(link['href'])
				
			text_stripped_html = soup.get_text()

			http = re.compile(r"http://.+?\s",re.U)
			allinks.update( http.findall(text_stripped_html) )

			text_stripped_https = http.sub(' ',text_stripped_html)

			www = re.compile(r"www'\..+?\s",re.U)
			allinks.update( www.findall(text_stripped_https) )

			### clean up the links
			cleanlinks = set({})
			for link in allinks:
				link1 = link.strip()
				link2 = link1.strip('.,;:')
				cleanlinks.add(link2)

			text_clean = www.sub(' ',text_stripped_https)

			### final replacements: white spaces, tabs and newlines
			whitespace = re.compile(r'\s+')
			text_clean = whitespace.sub(' ',text_clean)

			return text_clean.strip(), ('web_sources' , cleanlinks) # now item is a plain chunk of text, and we also return some urls
				
		def guess_language(item,builder):
			"""
			Does what it says. Just, in a quite stupid way.
			"""
			
			from ..utils import re
			thresh = builder.cloud.stats['language_recognition_threshold']
			
			dutch_recognition_re_s = [ 	('het',	re.compile(r'\bhet\b')),
										('op' ,	re.compile(r'\bop\b')),
										('van', re.compile(r'\bvan\b')),
										('met',	re.compile(r'\bmet\b')),
										('ij',	re.compile(r'\w+ij\w*'))]
				
				# yes, this is very stupid. I needed something quick...	Sorry.				
										
			matches = 0
			for dword,dutchRe in dutch_recognition_re_s:
				matches += len( dutchRe.findall(item) )
				
			WORD_RE = re.compile(r"(?:[^\W\d_]|['])+")
			allwords = WORD_RE.findall(item)

			if matches > 20 or float(matches) / (float(len(allwords)) - float(matches)) > float(thresh):
				ln = 'nl'
			else:
				ln = 'en'   	# default is english.
					
			return item, ('language' , ln )
					
		def names(item,builder):
			"""
			Looks for an 'author', a 'name' field and retrieves them. Also,
			performs a small regex search on all he can find to look for
			Capitalized Sequences Of Words that if not names, are at least
			probably important. (Unless that's a german item).
			"""
			
			from ..utils import re,preprocess
			
			re_names_array = [	re.compile(r"[A-Z][a-z]+\s[A-Z][a-z]+\b"), 				# captures "Arianna Betti"
							re.compile(r"[A-Z][.].*?\s[A-Z][a-z]+\b"),				# captures "J.R. Tolkien", "N. Brouwer" and "A.Cozza".
							re.compile(r"[A-Z][a-z]+\s[A-Za-z]+\s[A-Z][a-z]+"),		# captures "University of Amsterdam" and "Rosa de Hoog", as well as "Tiziano Caio Mario".		
							re.compile(r"[A-Z][a-z]+,(?:\s?[A-Z]\.)+?"), 			# captures "Betti, A." these are the last one to be extracted, so that we won't ruin other names
							re.compile(r"[A-Z]+[A-Z0-9]{1-5}") 						# captures 'FNWI', 'UVA' and 'ECTN', and also 'ECT2N'. also, VU																
							]
			
			implausible_contents = (re.compile(r"[0-9]"),re.compile(r"\(.*\)"))				
			
			allnames = []
			
			for reg in re_names_array:
				N = reg.findall(item)
				
				cleanN = []
				
				for name_candidate in N:
					good = True
					
					for imp in implausible_contents:# we purge off implausible names
						if imp.findall(name_candidate):
							good = not good
							break
						
					if good:

						if ',' in name_candidate: # From Betti, A. to A. Betti.
							cn = name_candidate.split(',')
							cn.reverse()
							cn = ' '.join(cn)
							
						cn = re.sub(re.compile(r"\s+"),' ',name_candidate)
						cn = cn.strip()							
						
						cleanN.append(cn)
						#text_clean_of_names = text_clean_of_names.replace(name_candidate, ' ') # we remove the names, for they only add noise.						

				allnames.extend(cleanN)
			
			spaces = re.compile(r"\s+")
			uniformitem = re.sub(spaces,' ',item)
			
			return uniformitem, ('names', allnames)
		
		def tf_and_tfidf(item,builder):
			"""
			Fetches the top of its tf/tf_idf dictionaries.
			"""
				
			from ..utils import most_freq_words_from_raw_text,Counter
			from math import log
			
			tf = Counter()
			idf = Counter()
			
			maxvoclength = builder.cloud.stats['max_vocab_length']
			for word,wordcount in most_freq_words_from_raw_text(item,crop = maxvoclength):
				
				wordfreq = wordcount / len(item.split(' '))
				tf[word] += wordfreq
				
				nw = 0 # number of items in which word appears.
				for doc in builder.cloud.sky._tokens_temp:
					for sentence in doc:
						if word in sentence:
							nw += 1
							break
							
				N = len(builder.cloud.sky._tokens_temp)
				try:
					idf[word] = log( (N / nw) ,2)
				except ZeroDivisionError:
					# then the word is a tag! We added them to the item's string a few steps ago, but they aren't counted in the sky's _tokens_temp.
					# print("word {} not found! Weird, isn't it?".format(word))
					# we ignore them(?)
					
					# fixed: shouldn't happen anymore (removed tags from stringed text.)
					pass
					
			return item, (('words_tfidf', idf), ('words_tf' , tf))
		
		def top_coo(item,builder):
			"""
			Topmost of a coo dictionary.
			"""
			from ..utils import Counter, update_coo_dict_with_raw_text
			coodict = Counter()
			
			update_coo_dict_with_raw_text(coodict,item)
			
			minfreq = builder.cloud.stats['min_coo_threshold']
			maxln = builder.cloud.stats['max_coo_length']
			
			if len(item) < 200:
				pass # if there is very little text, we are less picky, and keep all coos
			else:
				coodict = Counter({ el:value for el,value in coodict.most_common(maxln) if coodict[el] >= minfreq })
			
			return item, ('top_coo' , dict(coodict))
		
		def core(item,builder):
			"""
			Produces a plain list of words that are (very likely to be)
			keywords for this cloud.
			requires tf_idf() to have been called first.
			"""
			from ..utils import to_tokens_text
			
			candidates = []
			
			idfs = []
			for i in range(len(builder.cloud.layers)):
				idfdict = builder.cloud.layers[i]['words_tfidf']
				idflist = list(idfdict.keys())
				
				idflist.sort(key = lambda x: idfdict[x]) 
				idflist.reverse() # from max to min 
				
				idfs.extend(idflist) # deeper layers go automatically below
			
			header = builder.oritem.get('title',builder.oritem.get('headline','')) # look for title, headline
			body = builder.oritem.get('about',builder.oritem.get('text','')) # look for body
			
			s_tokheader = to_tokens_text(header)
			tokheader = []
			for s in s_tokheader:
				tokheader.extend(s)
			
			for word in idfs[:min((len(idfs),30))]:
				if word in tokheader: # can return [] or [[str()]] types
					candidates.append(word)
			
			return item, ('core', candidates[:min((len(candidates),15))])			
				
		def google_lookup(item,builder):	
			"""
			Heh, it would be really nice.
			"""
			
			return item, ('google_lookup_out', []) 
		
		def communities(item,builder):
			"""
			Sooner or later...
			"""
			
			return item, ('communities',[])
			
	class builtin_pipelines():
		"""
		A pipeline is a dictionary from layer-level to ordered sequences 
		of rules that can be applied to obtain the layers of a cloud. 
		We can also suggest that there might be different pipelines for 
		different types of items.
		"""

		def Starfish_pipeline():
			"""
			Dunno. All I could come up with. Currently, only the zero-layer
			pipeline is implemented. Extendable at will.
			
			
			""" # this docstring will become really cool once cloudformationrules is imported...
			
			
			
			lr = LayerBuilder.builtin_layerrules
			
			pipeline = {0: 	[lr.tags, 										# retrieves the (given) tags for the starfish item
							lr.crunch_down_to_string,						# then we transform the item into a string of all the text we can catch.
							lr.preprocess,									# strips off html tags and other rubbish, thereby also retrieving urls 
							lr.guess_language,								# does what it says, but in a very stupid way
							lr.names,										# retrieves all names we can find in the raw text.
							lr.top_coo,										# coo dictionary
							lr.tf_and_tfidf,								# tf and tf-idf dictionaries
							lr.core]										# core!
							}
			
		
			return pipeline
			
# fill docstrings of pipelines:

for builtinpipeline in LayerBuilder.builtin_pipelines.__dict__.values():
	if not callable(builtinpipeline):
		continue
		
	pipeline = builtinpipeline() # we get it
	
	for no,layerpipe in pipeline.items():
		builtinpipeline.__doc__ += 'Layer {}:\n'.format(no)
		for function in layerpipe:
			builtinpipeline.__doc__ += "Step {}: {} : {}\n".format(layerpipe.index(function),function.__name__,function.__doc__)
