#keywords - class entirely for getting keywords from sources

from math import ceil
from nltk import pos_tag
from nltk import word_tokenize
from nltk.stem import SnowballStemmer
import re

#used to obtain most used keywords from a set of sources
class KeyWords:
	#set of pos tags we weant
	wanted_tags = set(['FW','JJ','JJR','JJS','NN','NNS','NNP','NNPS','RB','RBR', \
		'RBS','UH','VV', 'VVD', 'VVN', 'VVP'])
	
	def __init__(self, orig_kwords = [], filters = []):
		self.kwords_lem = {}			#holds lemmatized_word:count pairs
		self.kwords_lst = {}			#holds lemmatized_word:word_list pairs
		self.count_src = 0				#number of sources categorized
		self.count_wrds = 0				#number of words we've looke through
		self.orig_kwords = orig_kwords	#prevents duplicate keywords
		self.filters = filters			#regex filters for removing unwanted patterns

		for ind in range(len(self.filters)):
			self.filters[ind] = re.compile(self.filters[ind])
	
	#add a source to the word list
	def add_source(self, source, lang = "english"):
		self.count_src = self.count_src+1

		words = pos_tag(word_tokenize(source))	#get tokenized,pos-tagged words
		stemmer = SnowballStemmer("english")	#get snowball stemmer instance
		
		#go through all stemmed words
		for w in words:
			
			word = w[0].lower()
			pos = w[1]

			#check filters
			mtch = False
			for fl in self.filters:
				mtch = mtch or fl.match(word)
			
			#only want the word if we don't want to filter it
			if not mtch:
				#only care if it's been tagged in wanted tags
				if (not (word in self.orig_kwords)) and (pos in KeyWords.wanted_tags):
					stem = stemmer.stem(word)
					
					#save in count dictionary and word list dictionary
					if not (stem in self.kwords_lem):
						self.kwords_lem[stem] = 0
					if not (stem in self.kwords_lst):
						self.kwords_lst[stem] = set()
						
					self.kwords_lem[stem] = self.kwords_lem[stem]+1
					self.kwords_lst[stem].add(word)
					
				self.count_wrds = self.count_wrds+1
		
	#retrieves the top keywords from all sources
	def calc_top(self, percent=0.05):
	
		words = {}	#holds count:[word_list] pairs
		num_words = ceil(percent*self.count_wrds) #only want a percentage of the words
	
		#get a way to easily pick top words
		for w in self.kwords_lem:
			if (len(words.keys()) == 0):
				words[self.kwords_lem[w]] = [w]
			else:
				if self.kwords_lem[w] in words:
					words[self.kwords_lem[w]].append(w)
				else:
					words[self.kwords_lem[w]] = [w]
		
		ret = []
		ret_words = 0
		
		#get the top percentage of words based on count
		while ret_words < num_words:
			m = max(words.keys())
			
			for lem in words[m]:
				ret = ret + list(self.kwords_lst[lem])
				
			ret_words = ret_words + len(words[m])
			
			del words[m]
			
		return ret