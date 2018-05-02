"""
File: data-model
Creator: Cicely Lambright
Desc: Has classes to hold node/edge data for easier parsing and data collection
"""

from enum import Enum
from math import ceil
from nltk import pos_tag
from nltk import word_tokenize
from nltk.stem import SnowballStemmer
from sys import maxsize

#multiple types for different uses
class Type(Enum):
	NONE = 0
	
	#twitter node types
	TW_USER = 1
	TW_HASHTAG = 2
	
	#twitter edge types
	TW_STATUSHT = 3
	TW_HTHT = 4
	TW_RETWEET = 5
	TW_USR_MENTION = 6
	TW_FOLLOW = 7
	TW_FRIEND = 8
	
#class to hold all tweet ids in a set
#used for making sure we are getting no duplicate tweets
class TweetLib:
	
	tweets = set()	#holds all the tweet ids
	
	#constructor - clear set
	def __init__(self):
		self.tweets = set()

	#check if tweet id hasn't been seen before. 
	#id - tweet id
	#return - True if id is original
	def is_new(self, id):
		if not (id in self.tweets):
			self.tweets.add(id)
			return True
		else:
			return False
#used to obtain most used keywords from a set of sources
class KeyWords:
	#set of pos tags we weant
	wanted_tags = set(['FW','JJ','JJR','JJS','NN','NNS','NNP','NNPS','RB','RBR', \
		'RBS','UH','VV', 'VVD', 'VVN', 'VVP'])
	
	def __init__(self, orig_kwords = []):
		self.kwords_lem = {}			#holds lemmatized_word:count pairs
		self.kwords_lst = {}			#holds lemmatized_word:word_list pairs
		self.count_src = 0				#number of sources categorized
		self.count_wrds = 0				#number of words we've looke through
		self.orig_kwords = orig_kwords	#prevents duplicate keywords
	
	#add a source to the word list
	def add_source(self, source):
		self.count_src = self.count_src+1
		
		words = pos_tag(word_tokenize(source))	#get tokenized,pos-tagged words
		stemmer = SnowballStemmer("english")	#get snowball stemmer instance
		
		#go through all stemmed words
		for w in words:
			word = w[0]
			pos = w[1]
			
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

#contains all of the graph data - nodes & edges
class Nodes:

	node_list = {}			#node key:value pairs - holds a node_id:node_object pair
	#edge_list = {}			#edge key:value pairs - holds an edge_id:edge_object pair
	
	#node sizes - node that for networkx, default node size is 300
	max_node_size = 600		#default max node size
	min_node_size = 200		#default min node size
	
	#default node colors - can be changed via config file
	colors = {Type.NONE:"#FFFFFF",Type.TW_USER:"#01DF01", Type.TW_HASHTAG:"#8904B1"}
	
	#constructor
	def __init__(self):
		#empty both lists & reset values
		self.node_list = {}
		#self.edge_list = {}
		self.max_node_size = 600
		self.min_node_size = 200
		colors = {Type.NONE:"#FFFFFF",Type.TW_USER:"#01DF01", Type.TW_HASHTAG:"#8904B1"}
		
		self.favorites = 0	#total number of favorites
		self.retweets = 0
		self.total_edges = 0
		self.total_followers = 0
		
	#adds a node to the list of nodes
	#id - node id (for twitter - user id strings or all lowercase hashtag string)
	#name - name to be put as node label (for twitter - username or hashtag text)
	#type - see type class for options
	#pst_id - id of post (for twitter - tweet id)
	#return - whether the node was created new or not
	def add_node(self,id,name,type,favorites,retweets,is_retweet,init_importance = 1,pst_id = None):
		new_add = False		#tells us whether the node was newly added
		
		#only add if node not currently present
		if not (id in self.node_list):
			self.node_list[id] = Node(id, name, type, favorites, retweets, 0, init_importance)
			new_add = True
			
		if not (pst_id == None):
			self.node_list[id].add_post_id(id)
		
		self.node_list[id].add_retw_self(is_retweet)	
		self.node_list[id].add_favs(favorites)
		self.node_list[id].add_retw(retweets)
		self.favorites = self.favorites + favorites
		self.retweets = self.retweets + retweets
		
		return new_add
			
	def add_follower(id, follower_lst):
		if id in self.node_list:
			self.node_list[id].add_follower(follower_lst)
			self.total_followers = self.total_followers + len(follower_lst)
			
	def add_friend(id, friend_lst):
		if id in self.node_list:
			self.node_list[id].add_friend(friend_lst)
			
	def get_user_links(self):
		#get edges for followers/friends relations here
		for nd in self.node_list:			
			for fr in self.node_list[nd].friends:
				if fr in self.node_list:
					self.add_edge(nd,str(fr),TW_FRIEND)
			for fo in self.node_list[nd].followers:
				if fo in self.node_list:
					self.add_edge(nd,str(fo),TW_FOLLOW)
		
	
	#adds an edge to the list of edges
	#id1 - a node id
	#id2 - a node id
	#type - see type class for options
	#count - used if there is already a count on connections between two nodes, starts as 1
	def add_edge(self, id1, id2, type, count=1):
		self.node_list[id1].add_edge(id2, type, count)
		self.node_list[id2].add_edge(id1, type, count)
		
		self.total_edges = self.total_edges + 1
			
	#retrieve node ids (all of them)
	#return - a set of keys for nodes
	def get_nodes(self):
		return self.node_list.keys()
		
	#returns a single node based on a given key
	#key - given string to retreive a node
	#return - a node object
	def get_node(key):
		return self.nodes_list[key]

	#returns a dictionary object for labeling nodes with a node_key:node_label format
	#returnn - dictionary of key-label pairs for all nodes
	def get_node_labels(self):
		ret = {}
		
		for key in self.node_list:
			ret[key] = self.node_list[key].get_label()
			
		return ret
		
	#returns edge ids
	#return - a set of keys for edges
	def get_edges(self):
		#return self.edge_list.keys()
		ret = set()
		
		for key in self.node_list:
			ret = ret.union(self.node_list[key].get_edge_tuples())
				
		return ret
	
	#returns a single node's color based on it's key
	#return - a dictionary of key-color pairs for all nodes
	def get_node_color(self, key):
		node = self.node_list[key]
		return self.colors[node.type]
		
	#gets the json for the nodes object
	#return - a json object for the entire nodes instance
	def get_json(self):
		json_obj = {"graph":{"nodes":[],"favorites":self.favorites, "retweets":self.retweets}}
		
		for node_key in self.node_list:
			json_obj["graph"]["nodes"].append(self.node_list[node_key].get_json())
		
		return json_obj
		
	#makes a nodes object form a json
	#json_obj - the json that will describ e the nodes instance
	def pop_from_json(self, json_obj):
		self.favorites = json_obj["graph"]["favorites"]
		self.retweets = json_obj["graph"]["retweets"]
		for nd in json_obj["graph"]["nodes"]:
			self.add_node(nd["id"],nd["name"],Type(nd["type"]),nd["favorites"],nd["retweets"],nd["self_retweets"])
			
			for pst_id in nd["pst_id"]:
				self.node_list[nd["id"]].add_post_id(pst_id)
				
			for ed in nd["edges"]:
				for ty_set in ed["details"]:
					self.node_list[nd["id"]].add_edge(ed["node_id"], Type(ty_set["type"]), ty_set["count"])
				
		#for ed in json_obj["graph"]["edges"]:
		#	self.add_edge(ed["id"][0], ed["id"][1], Type(ed["type"]), ed["count"])
			
	#configures the graph's general colors from a config file
	#config - input json
	def config_from_json(self, config):
		#set the values based on input
		if 'none_color' in config:
			self.colors[Type.NONE] = config['none_color']
		if 'tw_user_color' in config:
			self.colors[Type.TW_USER] = config['tw_user_color']
		if 'tw_hashtag_color' in config:
			self.colors[Type.TW_HASHTAG] = config['tw_hashtag_color']
		if 'max_node_size' in config:
			self.max_node_size = config['max_node_size']
		if 'min_node_size' in config:
			self.min_node_size = config['min_node_size']
			
	#retrives the top nodes given our ranking criteria
	#num - number of nodes we want to get
	#data_count - total number of data points we've looked through
	################################################################################
	def get_top_nodes(self, num, data_count):
		self.get_user_links()
	
		min_ht = maxsize
		max_ht = 0
		min_us = maxsize
		max_us = 0
	
		#num should an integer > 0
		if num < 1:
			num = 1
		
		num = ceil(num)
		
		top = {} #dictionary of top nodes
		min_key = "" #minimum key so we can easily replace it
	
		#get top nodes from the calculated node value
		for key in self.node_list:
			val = self.node_list[key].get_importance(data_count, self.favorites, self.retweets, self.total_edges, self.total_followers)
			
			if (self.node_list[key].type == Type.TW_USER):
				if (val < min_us):
					min_us = val
				elif (val > max_us):
					max_us = val
			elif (self.node_list[key].type == Type.TW_HASHTAG):
				if (val < min_ht):
					min_ht = val
				elif (val > max_ht):
					max_ht = val
					
		#normalize hashtags to fit in normal user range b/c of variance in determining importance
		# and the need to put them on a similar scale
		# formula:
		#	x = (x + (y0 - x0)) * ((y1-y0)/(x1-x0))
		#	where 	x = initial value for target
		#			x0 = minimum of initial range
		#			x1 = maximum of initial range
		#			y0 = minimum of target range
		#			y1 = maximum of target range
		#	note: if (x1 - x0) = 0 and/or (y1-y0) = 0, use 1 instead of 0 to provide identity
		for key in self.node_list:
			if (self.node_list[key].type == Type.TW_HASHTAG):
				add_dif = (min_us - min_ht)
				new_range = max_us - min_us
				old_range = max_ht - min_ht
				
				if(new_range == 0):
					new_range = 1
				if(old_range == 0):
					old_range = 1
				
				self.node_list[key].importance = (self.node_list[key].importance + add_dif) * (new_range/old_range)

		#get top nodes from the calculated node value
		for key in self.node_list:
			val = self.node_list[key].importance
		
			#if top is underfilled, fill it as much as possible, while updating the min key if necessary
			if (len(top.keys()) == 0):	#take whatever if there's nothin in top
				top[key] = val
				min_key = key
			elif (len(top.keys()) < num): #take in enough to fill top, but update min key
				top[key] = val
				
				if val > top[min_key]:
					min_key = key
			elif (val > top[min_key]): #after filled, only add if the value is better than the min and update min
				del(top[min_key])
				top[key] = val
				min_key = key			
			
		new_nodes = {}
		
		#clear out the trash nodes
		for key in self.node_list:
			if (key in top):
				new_nodes[key] = self.node_list[key]
		self.node_list = new_nodes
		
		#clear out the trash edges
		for key in self.node_list:
			for ed in self.node_list[key].get_edge_keys():
				if not (ed in self.node_list):
					self.node_list[key].del_edge(ed)		
		
#node object - contains a single graph node
class Node:
	
	id = ""				#id - identifier for node
	name = ""			#name - what to label the node as
	type = Type.NONE	#type - helps indicate what type of node it is, which can give us the color
	ids = set()			#ids of tweets so that they can be saved
	edges = {}
	
	#constructor
	#id, name, type - see above
	def __init__(self, id, name, type, favorites, retweets, self_retweets, initial_importance = 1, followers = [], friends = []):
		#set the necessary data for the node
		self.id = id
		self.name = name
		self.type = type
		
		if favorites == None:
			self.favorites = 0
		else:
			self.favorites = favorites
			
		if retweets == None:
			self.retweets = 0
		else:
			self.retweets = retweets
			
		self.self_retweets = self_retweets
		self.followers = followers
		self.friends = friends
		
		self.initial_importance = initial_importance
		if self.initial_importance <= 0:
			self.initial_importance = 1
			
		self.edges = {}
		
	#returns the outward facing label for the node
	#return - node's label
	def get_label(self):
		if (self.type == Type.TW_HASHTAG):
			return "#" + self.name
		else:
			return self.name
	
	#key - key for other half of the edge
	def add_edge(self, key, type, count=1):
		if not (key in self.edges):
			self.edges[key] = Edge(key)
		self.edges[key].add_edge_count(type, count)
		
	#id - id of post the node was in (for twitter - tweet id
	def add_post_id(self, id):
		self.ids.add(id)
	
	#return - json representation of node
	def get_json(self):
		return {"id":self.id,"name":self.name,"type":self.type.value,"favorites":self.favorites, "retweets":self.retweets, "self_retweets":self.self_retweets, "pst_id":list(self.ids),"edges":self.get_edge_json()}
		
	#tw_count - total tweet count
	#fav_count - total favorite count
	#ret_count - total retweet count
	#return - importance 'ranking' number for gathering the top nodes
	def get_importance(self, tw_count, fav_count, ret_count, edge_count, fol_count):
		importance = self.initial_importance
		
		fav_count = fav_count + 1
		ret_count = ret_count + 1
		fol_count = fol_count + 1
		
		num_favs = self.favorites + 1		#number of favs for related posts
		num_edges = len(self.edges) + 1		#number of individual edges (not necessarily the count)
		num_retw = self.retweets + 1		#number of times posts they're related to are retweeted
		num_s_retw = self.self_retweets + 1	#number of times they are involved with a retweet
		num_tw = len(self.ids)				#number of tweets the node is involved in
		num_ed = self.edge_count()			#number of edges attached to tweet
		num_followers = len(self.followers) #number of followers
		
		
		#importance factors based off of tweet/post information
		importance = importance * (num_favs/fav_count)					#more favorites = better
		importance = importance * (num_tw/tw_count)						#connected to more tweets = better
		importance = importance * (num_retw/(ret_count*num_s_retw))		#more times retweeted = better, more times a retweeter (not original) = worse
		importance = importance * (num_ed/edge_count)					#more edges = better
		importance = importance * (num_followers/fol_count)				#more followers = betters
		
		
		self.importance = importance
		return importance
		
	#return - all edge keys for graphing edges
	def get_edge_keys(self):
		keys = set()
		
		for ed in self.edges:
			keys.add(self.edges[ed].node_id)
			
		return keys
		
	def get_edge_tuples(self):
		edges = set()
		
		for ed in self.edges:
			temp = sorted([self.id, self.edges[ed].node_id])
			edges.add((temp[0],temp[1]))
			
		return edges
	
	#return - json that represents edges
	def get_edge_json(self):
		edge_json = []
		for key in self.edges:
			edge_json.append(self.edges[key].get_json())
		return edge_json
		
	#deletes an unnecessary edge from node
	#key - node key for connected node
	#return - none
	def del_edge(self, key):
		if key in self.edges:
			del self.edges[key]
			
	def add_favs(self, favorites):
		if (favorites == None):
			favorites = 0
			
		self.favorites = self.favorites + favorites
		
	def add_retw(self, retweets):
		if (retweets == None):
			retweets = 0
		
		self.retweets = self.retweets + retweets
		
	def add_retw_self(self, is_retweet):
		if (is_retweet == True):
			self.self_retweets = self.self_retweets + 1
			
	def add_follower(self, follower_lst):
		self.followers = follower_lst
			
	def add_friend(self, friend_lst):
		self.friends = friend_lst
		
	def edge_count(self):
		ed_count = 0
		
		for ed in self.edges:
			ed_count = ed_count + self.edges[ed].edge_count()
			
		return ed_count
		

#class for edges
class Edge:

	node_id = ""
	type_counts = {}
	
	#constructor
	def __init__(self, node_id):
		self.node_id = node_id
		self.type_counts = {}
		
	#type - type of edge
	#count - number ot times edge appears
	#return - none
	def add_edge_count(self, type, count=1):
		if not (type in self.type_counts):
			self.type_counts[type] = 0
		self.type_counts[type] = self.type_counts[type] + count
		
	#return - json representation of edge instance
	def get_json(self):
		edge_json = {"node_id":self.node_id,"details":[]}
		
		for tp in self.type_counts:
			edge_json["details"].append({"type":tp.value, "count":self.type_counts[tp]})
			
		return edge_json
		
	def edge_count(self):
		ed_count = 0
		
		for tp in self.type_counts:
			ed_count = ed_count + self.type_counts[tp]
		
		return ed_count