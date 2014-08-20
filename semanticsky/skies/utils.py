#!/usr/bin/python3

from bs4 import BeautifulSoup,SoupStrainer
from collections import Counter
import re,nltk,sys

WORD_RE = re.compile(r"(?:[^\W\d_]|['])+")
dutch_stopwords = []
eng_stopwords = nltk.corpus.stopwords.words('english')
eng_stopwords.extend(['free','high','low','although','brief','nevertheless','nonetheless']) # Extra stops

dutch_recognition_re_s = [ 	('het',	re.compile(r'\bhet\b')),
							('op' ,	re.compile(r'\bop\b')),
							('van', re.compile(r'\bvan\b')),
							('met',	re.compile(r'\bmet\b')),
							('ij',	re.compile(r'\w+ij\w*'))]
				
destemdb = {}
# word --> stem dictionary
revert_destemdb = {}
# stem --> word dictionary (it's a mapping)

def crop_at_nonzero(fl,bot = 4):
	sfl = str(fl)
	
	out = ''
	nonzero = 0
	
	for digit in sfl:
		if digit.isdigit() and int(digit) > 0:
			nonzero += 1
		
		out += digit
		
		if nonzero != 0 and nonzero != bot:
			nonzero += 1 # we want no-1 digits after the first nonzero, not results like 0.0200000000000005, if we want 2 nonzero digits
		
		if nonzero == bot:
			return float(out)
			
	return fl

def lsum(*lists): # list merging tool

        out = []

        if len(lists) == 1:
                unpack = lists[0]
                return lsum(*unpack)
        else:
                for l in lists:
                        out += l
        return out

def clean_destemdb():
	
	global destemdb
	
	transdb = {word : [value for key,value in destemdb.values() if key == word] for word in destemdb}
	# stem --> [words which correspond to the stem]

	global revert_destemdb
	
	for word in transdb:
		transl = Counter(transdb[word]).most_common(1) # we take the topmost
		
		revert_destemdb[transl] = word

def destem(word):

	return destemdb[word]

def split_tag(tag,tolist = False):
	"""
	given "AnyCamelTag"
	returns "Any Camel Tag" or (if tolist): ['Any','Camel','Tag']
	
	if the whole tag is upper, does nothing.'
	"""
	
	if tag.isupper():
		return tag
	
	tmp = tag[:1]

	for letter in tag[1:]:
		if letter.isupper():
			tmp += ' '+letter
		else:
			tmp += letter
	if tolist:
		return tmp.split(' ') 
	return tmp

def guess_language(text,thresh = 0.4):

	matches = 0
	for dword,dutchRe in dutch_recognition_re_s:
		matches += len( dutchRe.findall(text) )

	allwords = WORD_RE.findall(text)

	if matches == 0 or allwords == 0:
		return 'en' 
	elif matches > 20:
		return 'nl'
	elif float(matches) / (float(len(allwords)) - float(matches)) > float(thresh): #self.sky.stats['language_recognition_threshold']:
		return 'nl'

	return 'en'   	# default is english.

def isstopword(word,hint = None):
	
	if hint == 'en':
		if word in eng_stopwords:
			return True
	elif hint == 'nl':
		if word in dutch_stopwords:
			return True
	else:
		if word in dutch_stopwords or word in eng_stopwords:
			return True

	return False
	
def compile_dutch_stop_words():
	
	dlines = None
	with open('/home/pietro/Perceptum/code/starfish/similarity/SemanticSky/semanticsky/data/dutchstops.txt','r') as dstops:
		dlines = dstops.readlines()

	for line in dlines:
		line = line.replace('\n','')
		line = line.strip()
		dutch_stopwords.append(line) # here lines host a single word

def preprocess(text,catchlinks = False):
	"""
	Strips all html from a text.
	Also, we remove explicit (www) links eventually present in the text.	
	if the variable links is filled by a list, set or similar, we update
	it with eventually-found urls in the text.

	returns
	-------

	text stripped of html tags, links
	"""
	
	allinks = set({})
	urlsoup = BeautifulSoup(text,parse_only=SoupStrainer('a'))
	for link in urlsoup:
		if link.get('href'):
			allinks.add(link['href'])

	soup = BeautifulSoup(text)
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

	if catchlinks:
		return text_clean.strip(),cleanlinks
	return text_clean.strip()
	
def grab_text(item,keys = ('name','title','about','text','headline')):
	"""
	Takes as input an item's dictionary; outputs a string.
	"""
	
	val = ''
	if 'tags' in keys:
		keys.remove('tags')
		for tag in item['tags']:
			val += tag + ' '
	
	for k in keys:
		v = item.get(k,'')
		if v:
			vs = str(v)
			val += vs

	return preprocess(val) 

def to_sentences_text(item):
	"""
	Tokenizes a body of text down to sentences using PunktSentenceTokenizer.
	Wants as input either a string or an item ID. (if item is a starfish item (i.e. a dictionary), 
	passes it to grab_text to retrieve it from the db)
	"""
	if not isinstance(item,str):
		item = grab_text(item)

	#text = preprocess(item) # strips off HTML tags
	T = nltk.tokenize.PunktSentenceTokenizer()
	return T.tokenize(item) 

def to_tokens_sent(sentence,word_len_thresh = 3,stem = True,stopwords = True):
	"""
	Given a string, breaks it down to words using PunktWordTokenizer
	returns a list of strings
	"""
	global destemdb
	
	punct = re.compile(r'[\_\-\.\,\;\:\!\?\=\^\"\'\`,\@\#\*\[\]\(\)\|\{\}\$\%\&\<\>]')

	W = nltk.tokenize.PunktWordTokenizer()
	towords = W.tokenize(sentence) # now a list of strings
	cleantowords = []
	
	for word in towords:
		word = punct.sub(' ', word) # we strip off weird things
		word = word.strip() # we strip off spaces
		if (word not in ['', ' ']) and len(word) > word_len_thresh and not word.isdigit() and not isstopword(word.lower()):
			if stem:
				stemmer = nltk.stem.LancasterStemmer()
				tword = stemmer.stem(word.lower())
				destemdb[word] = tword
			else:
				tword = word
				
			if stopwords and isstopword(word.lower()):
				continue # we ignore the word
			cleantowords.append(tword)

	return cleantowords	  

def to_tokens_text(text,stem = True,stopwords = True):
	
	output = []
	
	for sent in to_sentences_text(text):
		s = to_tokens_sent(sent,stem = stem,stopwords = stopwords)
		output.append(s)
	
	return output

def to_sentences_item(item):
	"""
	Input: an item's dict
	Returns a list(list(str())) instance
	"""

	return [ to_tokens_sent(sentence) for sentence in to_sentences_text(item) ]

def count_coo_sent(sentence,crop=None):
	"""
	takes as input a [str()] instance and returns a Counter with co_occurring
	pairs counts
	"""
	if not isinstance(sentence,list):
		raise TypeError('Bad.')
	coo_counter = Counter()
	c = 1
	for word1 in sentence[:len(sentence)-1]:
		for word2 in sentence[c:]:
			c += 1
			if word1 != word2:
				pair = frozenset({word1,word2})
				coo_counter[pair] += 1

	return coo_counter.most_common(crop) # this will return either the most common n counts, or all of them if crop == None # IS NOT A COUNTER!

def update_coo_dict_with_sent(coo_dict,sent):
	return coo_dict.update(count_coo_sent(sent))
	
def update_coo_dict_with_text(coo_dict,text):
	if isinstance(text,str) or isinstance(text,unicode):
		return update_coo_dict_with_raw_text(coo_dict,text)
	
	totcoo = Counter()
	for sent in text:
		coodic = count_coo_sent(sent)
		totcoo.update(coodic)
	return totcoo

def count_coo_raw_text(text):
	"""
	Takes as input a string of text, which may contain sentences or be a single one.
	returns a Counter instance.
	
	"""
	
	if not hasattr(text,'split'):
		raise TypeError('Bad input: {}'.format(type(text)))
	
	sents = to_sentences_text(text)
	tempcoodict = Counter()
	for sent in sents:
		tts = to_tokens_sent(sent)
		# tts should be [str()]
		coocount = count_coo_sent(tts) # is not a counter!!
		for pair,count in coocount:
			tempcoodict[pair] +=  count
			
	return tempcoodict
	
def update_coo_dict_with_raw_text(coo_dict,text):
	
	coodict = count_coo_raw_text(text)
			
	# we do the update
	for pair in coodict: 
		coo_dict[pair] += coodict[pair]		
	
	return 

def most_freq_words_from_raw_text(text,crop = None):
	
	sents = to_sentences_text(text)
	tokens = [ to_tokens_sent(sent) for sent in sents ]
	
	fcounter = Counter()
	for sent in tokens:
		fcounter.update(sent)
	
	return fcounter.most_common(crop)

def most_freq_words_from_raw_texts(texts,crop = None):
	
	totcount = Counter()
	for text in texts:
		textcount = most_freq_words_from_raw_text(text) # is a list of key,value tuples.
		for key,value in textcount:
			totcount[key] += value

	return totcount.most_common(crop)

def neighbours(a,b,word):
	"""
	Extracts from two counters all the words which appear coupled with word
	at least once.
	"""
	
	na = [pair for pair in a if word in pair] 
	naa = set()
	for pair in na: naa.update(pair)
	
	nb = [pair for pair in b if word in pair] 
	nbb = set()
	for pair in nb: nbb.update(pair)
	
	if naa: naa.remove(word)
	if nbb: nbb.remove(word)
	return naa,nbb

def compute_values(countera,counterb,word,coothresh = 2):
	pairs_with_word_A = [pair for pair in countera if word in pair and countera[pair] > coothresh ]
	pairs_with_word_B = [pair for pair in counterb if word in pair and counterb[pair] > coothresh ]
	
	overlaps_word_in_counters = 0
	
	for pair in pairs_with_word_A: overlaps_word_in_counters += countera[pair]
	for pair in pairs_with_word_B: overlaps_word_in_counters += counterb[pair]
	
	# overlaps gets weighted by total number of coo counts:
	avalues = sum( [ value for value in countera.values() if value >= coothresh ] )
	bvalues = sum( [ value for value in counterb.values() if value >= coothresh ] )
	factor = avalues + bvalues / 2
	
	nowA,nowB = neighbours(countera,counterb,word)
	
	intersection = float(len( nowA.intersection(nowB) ))
	symmetric_difference = float(len( nowA.difference(nowB).union(nowB.difference(nowA))))
	
	if factor: ovlp_words_value = overlaps_word_in_counters / factor
	else: ovlp_words_value = 0.	
	if symmetric_difference: neighb_value = intersection / symmetric_difference
	else: neighb_value = 0.
	
	return neighb_value , ovlp_words_value

default_thresholds = {	'neighb_intersect_thresh' 	: 2,
						'coo_count_thresh' 			: 2, # booh
						'bothhere_bonus' 			: 1.5 }	

def overlap_of_coo_counters(countera,counterb,thresholds = default_thresholds, crop = 0):
	
	neighb_intersect_thresh = 	thresholds['neighb_intersect_thresh']
	coo_count_thresh = 			thresholds['coo_count_thresh']
	bothhere_bonus = 			thresholds['bothhere_bonus']

	out0 = 0.0 # the output will be a float, followed by
	out1 = [[],[],[],[]] # where we will store n) [topmost n-level matches]
	
	awords = set()
	bwords = set()

	for a,b in countera:
		awords.update((a,b))
	for a,b in counterb:
		bwords.update((a,b))
	
	allwords = awords.union(bwords)
	
	for word in allwords:
		neighb_value, plain_overlap_value = compute_values(countera,counterb,word,coo_count_thresh) # this returns two floats
		
		#----------------------------------------------------------------------------------------------------#
		if word in awords and word in bwords: # level 1-0 match requisite: 'we both are here'
			bothhere = True
		else:
			bothhere = False			
		if neighb_value > neighb_intersect_thresh: # level 0-2 match requisite
			neighbour = True
		else:
			neighbour = False
		#----------------------------------------------------------------------------------------------------#
		
		if neighbour and bothhere: 		# LEVEL 0
				
			value = neighb_value + plain_overlap_value # that is: how many they have in common / how many they don't, + how much they overlap in counters / total values of counters
			value = value * bothhere_bonus
			level = 0
		
		elif bothhere: 					# LEVEL 1
			
			value = plain_overlap_value # already weighted w.r.t. total number of cooccurrences
			level = 1
		
		elif neighbour: 				# LEVEL 2
			
			value = neighb_value
			level = 2
				
		else:							# LEVEL 3
			
			value = 0
			level = 3
							
		out1[level].append( (word,value) )
	
	for match_level in out1:
		match_level.sort(key = lambda x: x[1]) # we sort them by their values.
		
	if crop: 
		outn = [ level[ : crop] for level in out1 ] # we return only topmost values
		for i in len(outn-1): 
			out1[i] = outn[i]
		
	out0 = 0
	
	for level in out1:
		if level: # i.e. if it's nonempty
			try:
				allvalues = [  v for w,v in out1[out1.index(level)]  ]
				totvalue = sum(allvalues) # sum all values (for any word)
			except BaseException as e:
				print(out1)
				raise e
				
			out0 += totvalue
	
	return out0,out1

class ProgressBar():
	
	def __init__(self,topnumber,barlength=100,title = 'Progress',updaterate = 1,monitor = False,displaynumbers = False):
		
		self.barlength = barlength
		self.title = title
		self.updaterate = updaterate
		if not topnumber > 0:
			raise BaseException('Topnumber <= 0!')
		self.topnumber = topnumber
		self._preperc = 0
		self.monitor = monitor
		self.displaynumbers = displaynumbers

	def __call__(self,title = False,index='auto'):
		
		if title:
			self.title = title
		
		if index == 'auto':
			if not hasattr(self,'index'):
				self.index = 0
			else:
				self.index += 1
				
			index = self.index
			
		progress = float(index / self.topnumber)
		
		# updaterate, if set to 1, forces to update only when there is a 1% difference.
	
		barLength = self.barlength - len(self.title)
		status = ""
	
		if progress >= 1:
			progress = 1
			percentage = 100
		else:
			percentage = progress * 100

		preperc = self._preperc
		diffperc = percentage - preperc
		
		if diffperc > self.updaterate: # only prints if the progress has advanced by (self.updaterate)% points
			self._preperc = percentage
			pass
		elif index == 0: # OR if the index is 0
			pass
		elif self.topnumber -1 == index: # OR if the index is at 100%
			pass
		else:
			return None 
	
		displayedp = round(percentage) if index != self.topnumber -1 else 100
		block = int(round(barLength*progress))
		
		if not self.displaynumbers:
			text = "\r{}: [{}] {}% ".format(self.title,"."*block + " "*(barLength-block), displayedp)
		else:
			text = "\r{}: [{}] [{}/{}] ".format(self.title,"."*(block) + " "*(barLength-block), index + 1,self.topnumber)
		
		print(text,end = '' if progress != 1 else '\n')
	
	def tickon(self):
		
		print('+',end = '')
		
	def tickoff(self):
		
		print('\b ',end = '')
				
def ispair(pair):
	if isinstance(pair,frozenset) and len(pair) == 2 or isinstance(pair,tuple):
		pair = tuple(pair)
		import semanticsky as ss
		if isinstance(pair[0],ss.Cloud) and isinstance(pair[1],ss.Cloud):
			return True
		elif str(pair[0].__class__) == "<class 'semanticsky.Cloud'>" and str(pair[1].__class__) == "<class 'semanticsky.Cloud'>":
			return True

	return False

def pair(cloud,cloudb):
	""" Simply wraps two objects in a frozenset. """
	
	if cloud is cloudb:
		raise BaseException('Same cloud == No good.')
		
	return frozenset((cloud,cloudb))

def ctype(pair):
	
	if ispair(pair):
		about = pair
	else:
		about = pair.about

	clouda,cloudb = about
	typea,typeb = clouda.item.get('type','tag'),cloudb.item.get('type','tag') # if it hasn't got an item type, it must be a tag
	
	global codedict
	codedict = {'tag': 				'T',
				'Information': 		'I',
				'Glossary':			'G',
				'Question':			'Q',
				'Good Practice':	'O',
				'Project':			'R',
				'Person':			'P',
				'Content':			'C',
				'Topic':			'J',
				'Pedagogy':			'Y',
				'Technology':		'H',
				'Event':			'E'}
	
	ta = codedict[typea]
	tb = codedict[typeb]
	
	ctype = [ta,tb]
	ctype.sort()
	
	return ''.join(ctype) # a two-letter string
	
def ctype_to_type(ctype):
	
	ctypes = list(ctype)
	global codedict
	
	inverted = {codedict[key]:key for key in codedict}
	
	outctype = []
	for c in ctypes:
		cty = inverted[c]	
		cty = cty[:4]
		outctype += [cty]
	
	return '-'.join(outctype)
	
def avg(itr):
	return sum(itr) / len(itr) if itr else 0

def diff(iterator):
	return max(iterator) - min(iterator)

def regret(beliefs,truths):

	regret = 0
	
	for belief in beliefs:
		if belief in truths:
			regret += 1 - beliefs[belief]
		else:
			regret += beliefs[belief]
	
	for belief in truths:
		if belief not in beliefs:
			regret += 1
	
	return regret

def normalize(iterator,topvalue = 1):
	# shrinks down all values in iterator between 0 and topvalue

	cp = tuple(iterator)
	
	maximum = max(cp) 
	
	nl = []
	
	for c in cp:
		nl.append(c/maximum)
	
	del cp
	
	final = []
	
	ratio = topvalue / max(nl)
	for n in nl:
		final.append(n * ratio)
	
	return final
		
def pull_tails(iterator,top = 1,bottom = 0):
	cp = tuple(iterator)
	nw = []
	for x in cp:
		if x < bottom:
			nw.append(bottom)
		elif x > top:
			nw.append(top)
		else:
			nw.append(x)
	return nw
	
compile_dutch_stop_words() # we want it precompiled	
	
class Group():
	def __init__(self,function,*args,**kwargs):
		function(*args,**kwargs)
	


