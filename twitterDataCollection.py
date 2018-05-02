#twitter data collection class - a subclass of the data collection class primarity dealing with collecting twitter data

import dataCollection
from enum import Enum
from sys import maxsize
from numpy import mean


class Twitter_Type(Enum):
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

	#specialty edge types - only for edge weights
	TW_RETWEETER = 9
	TW_RETWEETEE = 10
	TW_MENTIONER = 11
	TW_MENTIONEE = 12
	TW_FOLLOWER = 13
	TW_FOLLOWED = 14	

	#only care about changing node types into strings
	def toString(type):
		if type == Twitter_Type.TW_USER:
			return "User"
		elif type == Twitter_Type.TW_HASHTAG:
			return "Hashtag"
		return ""
	
#library to collect tweets
class TweetLib(dataCollection.DataLib):
		
	def parse_data(self, tweet):
		dt = {}
		
		dt["poster"] = tweet.user.name
		dt["favorite_count"] = tweet.favorite_count
		dt["retweet_count"] = tweet.retweet_count

		dt["is_retweet"] = hasattr(tweet, 'retweeted_status')
		if dt["is_retweet"]:
			dt["original_poster"] = tweet.retweeted_status.id

		dt["hashtags"] = []
		for ht in tweet.entities["hashtags"]:
			if ht["text"].lower() not in dt["hashtags"]:
				dt["hashtags"].append(ht["text"].lower())

		dt["user_mentions"] = []
		for um in tweet.entities['user_mentions']:
			if um["id_str"] not in dt["user_mentions"]:
				dt["user_mentions"].append(um["id_str"])
				
		return dt
				
	def output_json(self, G):
		final_json = {"status_id":{}}
		
		for node in G.nodes:
			ids = G.nodes[node]["libs"]["status_id"]
			for id in ids:
				if (not (id in final_json["status_id"])) and (id in self.data_set):
					final_json["status_id"][id] = self.data_set[id]
			

class Twitter_Graph(dataCollection.Graph):
	
	def __init__(self, config_data = {"max_node_size":600, "min_node_size":200, "colors":{Twitter_Type.NONE:"#FFFFFF",Twitter_Type.TW_USER:"#01DF01", Twitter_Type.TW_HASHTAG:"#8904B1"}}):
		super().__init__(config_data)
		
		self.favorites = 0
		self.retweets = 0
		self.total_edges = 0
		self.total_followers = 0
		self.importance = 0
		
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
			self.node_list[id] = Twitter_Node(id, name, type, favorites, retweets, 0, init_importance)
			new_add = True
			
		if not (pst_id == None):
			self.node_list[id].add_post_id(id)
		
		self.node_list[id].add_retw_self(is_retweet)	
		self.node_list[id].add_favs(favorites)
		self.node_list[id].add_retw(retweets)
		self.favorites = self.favorites + favorites
		self.retweets = self.retweets + retweets
		
		return new_add
		
	#adds followers to node
	#id - node id
	#follower_list - list of follower ids
	def add_follower(id, follower_lst):
		if id in self.node_list:
			self.node_list[id].add_follower(follower_lst)
			self.total_followers = self.total_followers + len(follower_lst)
		
	#adds friends to node
	#id - node id
	#friend_list - list of friend ids
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
		super().add_edge(id1, id2, type, count)

		if (type is Twitter_Type.TW_USR_MENTION):
			self.node_list[id1].add_edge(id2, Twitter_Type.TW_MENTIONER)
			self.node_list[id2].add_edge(id1, Twitter_Type.TW_MENTIONEE)
		elif (type == Twitter_Type.TW_RETWEET):
			self.node_list[id1].add_edge(id2, Twitter_Type.TW_RETWEETER)
			self.node_list[id2].add_edge(id1, Twitter_Type.TW_RETWEETEE)
		elif (type == Twitter_Type.TW_FOLLOW):
			self.node_list[id1].add_edge(id2, Twitter_Type.TW_FOLLOWED)
			self.node_list[id2].add_edge(id1, Twitter_Type.TW_FOLLOWER)
		
		self.total_edges = self.total_edges + 1
		
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
			self.node_list[id] = Twitter_Node(id, name, type, favorites, retweets, 0, init_importance)
			new_add = True
			
		if not (pst_id == None):
			self.node_list[id].add_post_id(id)
		
		self.node_list[id].add_retw_self(is_retweet)	
		self.node_list[id].add_favs(favorites)
		self.node_list[id].add_retw(retweets)
		self.favorites = self.favorites + favorites
		self.retweets = self.retweets + retweets
		
		return new_add
				
	#adds an edge to the list of edges
	#id1 - a node id
	#id2 - a node id
	#type - see type class for options
	#count - used if there is already a count on connections between two nodes, starts as 1
	#def add_edge(self, id1, id2, type, count=1):
	#	self.node_list[id1].add_edge(id2, type, count)
	#	self.node_list[id2].add_edge(id1, type, count)
		
	#	self.total_edges = self.total_edges + 1
		
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
			self.add_node(nd["id"],nd["name"],Twitter_Type(nd["type"]),nd["favorites"],nd["retweets"],nd["self_retweets"])
			
			for pst_id in nd["pst_id"]:
				self.node_list[nd["id"]].add_post_id(pst_id)
				
			for ed in nd["edges"]:
				for ty_set in ed["details"]:
					self.node_list[nd["id"]].add_edge(ed["node_id"], Twitter_Type(ty_set["type"]), ty_set["count"])
			
	#configures the graph's general colors from a config file
	#config - input json
	def config_from_json(self, config):
		#set the values based on input
		if 'none_color' in config:
			self.colors[Twitter_Type.NONE] = config['none_color']
		if 'tw_user_color' in config:
			self.colors[Twitter_Type.TW_USER] = config['tw_user_color']
		if 'tw_hashtag_color' in config:
			self.colors[Twitter_Type.TW_HASHTAG] = config['tw_hashtag_color']
		if 'max_node_size' in config:
			self.max_node_size = config['max_node_size']
		if 'min_node_size' in config:
			self.min_node_size = config['min_node_size']
	
	def get_node_importances(self, data_count):
		min_ht = maxsize
		max_ht = 0
		min_us = maxsize
		max_us = 0
	
		for key in self.node_list:
			val = self.node_list[key].get_importance(data_count, self.favorites, self.retweets, self.total_followers)
			
			if (self.node_list[key].type == Twitter_Type.TW_USER):
				if (val < min_us):
					min_us = val
				elif (val > max_us):
					max_us = val
			elif (self.node_list[key].type == Twitter_Type.TW_HASHTAG):
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
			if (self.node_list[key].type == Twitter_Type.TW_HASHTAG):
				add_dif = (min_us - min_ht)
				new_range = max_us - min_us
				old_range = max_ht - min_ht
				
				if(new_range == 0):
					new_range = 1
				if(old_range == 0):
					old_range = 1
				
				self.node_list[key].importance = ((self.node_list[key].importance * (new_range/old_range)) + add_dif)
					
class Twitter_Node(dataCollection.Node):
		
	def __init__(self, id, name, type, favorites, retweets, self_retweets, initial_importance = 1, followers = [], friends = []):
		super().__init__(id)
	
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
		
	#returns the outward facing label for the node
	#return - node's label
	def get_label(self):
		if (self.type == Twitter_Type.TW_HASHTAG):
			return "#" + self.name
		else:
			return self.name
	
	#key - key for other half of the edge
	def add_edge(self, key, type, count=1):
		if not (key in self.edges):
			self.edges[key] = Twitter_Edge(key)
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
	def get_importance(self, tw_count, fav_count, ret_count, fol_count):
		importance = self.initial_importance
		
		fav_count = fav_count + 1
		tw_count = tw_count + 1
		ret_count = ret_count + 1
		fol_count = fol_count + 1
		
		num_favs = self.favorites + 1			#number of favs for related posts
		num_edges = len(self.edges) + 1			#number of individual edges (not necessarily the count)
		num_retw = self.retweets + 1			#number of times posts they're related to are retweeted
		num_s_retw = self.self_retweets + 1		#number of times they are involved with a retweet
		num_tw = len(self.ids) + 1				#number of tweets the node is involved in
		num_followers = len(self.followers) + 1	#number of followers
		
		
		#importance factors based off of tweet/post information
		importance = importance * (num_favs/fav_count)					#more favorites = better
		importance = importance * (num_tw/tw_count)						#connected to more tweets = better
		importance = importance * (num_retw/(ret_count*num_s_retw))		#more times retweeted = better, more times a retweeter (not original) = worse
		importance = importance * (num_followers/fol_count)				#more followers = betters
		
		self.importance = importance
		return importance
		
	#return - all edge keys for graphing edges
	def get_edge_keys(self):
		keys = set()
		
		for ed in self.edges:
			keys.add(self.edges[ed].node_id)
			
		return keys
		
	#return - edge tuples
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
			
	#adds favorites to node favorite count
	def add_favs(self, favorites):
		if (favorites == None):
			favorites = 0
			
		self.favorites = self.favorites + favorites
		
	#adds retweets to node retweet count
	def add_retw(self, retweets):
		if (retweets == None):
			retweets = 0
		
		self.retweets = self.retweets + retweets
		
	#adds number or retweets that others have done to user to count
	def add_retw_self(self, is_retweet):
		if (is_retweet == True):
			self.self_retweets = self.self_retweets + 1
			
	#adds follower list to node
	def add_follower(self, follower_lst):
		self.followers = follower_lst
			
	#adds friend list to node
	def add_friend(self, friend_lst):
		self.friends = friend_lst

	#counts edges
	def edge_count(self):
		ed_count = 0
		
		for ed in self.edges:
			ed_count = ed_count + self.edges[ed].edge_count()
			
		return ed_count
		
	def networkx_node(self):
		ret = super().networkx_node()
		
		ret["attributes"]["id"] = self.id
		ret["attributes"]["label"] = self.name
		ret["attributes"]["type"] = Twitter_Type.toString(self.type)
		ret["attributes"]["importance"] = self.importance
		ret["attributes"]["favorites"] = self.favorites
		ret["attributes"]["retweets"] = self.retweets
		ret["attributes"]["downloaded_tweet_count"] = str(len(self.ids))
		
		return ret
		
class Twitter_Edge(dataCollection.Edge):
	
	node_id = ""
	type_counts = {}
	
	#constructor
	def __init__(self, node_id):
		super().__init__(node_id)
		
	#return - json representation of edge instance
	def get_json(self):
		edge_json = {"node_id":self.node_id,"details":[]}
		
		for tp in self.type_counts:
			edge_json["details"].append({"type":tp.value, "count":self.type_counts[tp]})
			
		return edge_json
		
	#counts occurence of this edge
	def edge_count(self):
		ed_count = 0
		
		for tp in self.type_counts:
			ed_count = ed_count + self.type_counts[tp]
		
		return ed_count
	
	def networkx_edge(self, id, weight_mods):
		ret = super().networkx_edge(id, weight_mods)
		return ret