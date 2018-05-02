import dataCollection
from enum import Enum
from numpy import mean
from sys import maxsize
import praw

class Reddit_Type(Enum):
	NONE = 0
	
	#node types
	USER = 1
	SUBREDDIT = 2
	
	#edge_types
	#bi-directional edge types
	USR_COMMENT = 3
	USR_SUBMISSION = 4
	POST_COMMENT = 5
	SUBR_COMMENT = 6
	PARENT_CHILD = 7
	SUPER_COMMENT = 8
	SUB_COMMENT = 9
	
	def toString(type):
		if type == Reddit_Type.USER:
			return "User"
		elif type == Reddit_Type.SUBREDDIT:
			return "Subreddit"
		return ""
	
class Data_Type(Enum):
	USER = 0
	POST_COMMENT = 1
	
#library to hold comments
class CommentLib(dataCollection.DataLib):

	def parse_data(self, data):
		temp = {}
		
		if not (data.author == None):
			temp["author"] = data.author.name
		else:
			temp["author"] = "[deleted]"
		temp["submission"] = data.submission.id
		#temp["body"] = data.body
		
		return temp
		
#library to hold posts
class PostLib(dataCollection.DataLib):

	def parse_data(self, data):
		temp = {}
		
		if not (data.author == None):
			temp["author"] = data.author.name
		else:
			temp["author"] = "[deleted]"
		temp["subreddit"] = data.subreddit.display_name
		#temp["body"]
		
		return temp
		
#library to hold subreddits
class SubredditLib(dataCollection.DataLib):
	
	def parse_data(self, data):
		super().parse_data(data)

#library to hold users
class UserLib(dataCollection.DataLib):
	
	def parse_data(self, data):
		super().parse_data(data)

class Reddit_Graph(dataCollection.Graph):

	def __init__(self, config_data = {"max_node_size":600, "min_node_size":200, "colors":{Reddit_Type.NONE:"#FFFFFF",Reddit_Type.USER:"#01DF01", Reddit_Type.SUBREDDIT:"#8904B1"}}):
		super().__init__(config_data)
		
		self.ul = UserLib()
		self.cl = CommentLib()
		self.pl = PostLib()
		self.sl = SubredditLib()
		
		self.add_node("[deleted]", Reddit_Type.USER)
		
		self.total_gold = 0
		self.comment_karma = 0
		self.post_karma = 0
		
		self.data_count = 0
		
		self.exclude = ["[deleted]"]
	
	def add_node(self, id, type):
		self.data_count = self.data_count - 1
		self.node_list[id] = Reddit_Node(id, type)
		
	def add_edge(self, id1, id2, type, count=1):
		super().add_edge(id1, id2, type, count)
		
		if not id1 == id2:
			if (type == Reddit_Type.PARENT_CHILD):
				self.node_list[id1].add_edge(id2, Reddit_Type.SUPER_COMMENT)
				self.node_list[id2].add_edge(id1, Reddit_Type.SUB_COMMENT)
			
	
	def add_data(self, reddit, data, type):
		if type == Data_Type.USER:
			self.add_user(data)
		if type == Data_Type.POST_COMMENT:
			self.add_comment(reddit, data)
			
	#adds reddit user to the data
	#data - user data
	#return - user's name
	def add_user(self, data):
		try:
			if not (data == None):
					name = data.name
			else:
				#if no name, author is assumed to be deleted
				name = "[deleted]"
					
			if self.data_count > 0:			
				if self.ul.is_new(name):
					self.ul.add(name,data)
				if not (name in self.node_list):
					self.add_node(name, Reddit_Type.USER)
					
			return name
		except:
			pass

	#adds subreddit to the data
	#reddit - reddit api
	#data - subreddit data
	#delve - used to determine whether we want to go deeper or not
	def add_subreddit(self, reddit, data, delve=False):
		try:
			if self.data_count > 0:
				name = data.display_name
				self.add_node(name, Reddit_Type.SUBREDDIT)
				
				if self.sl.is_new(name):
					self.sl.add(name,data)
					
					if (delve):
						#grab a bunch of submissions from top
						for submission in data.top(limit=None):
							self.add_submission(reddit, submission)
		except:
			pass
		
	#adds comment to the data
	#reddit - reddit api
	#data - comment data
	#type - type of edge we want
	#delve - whether we want to go deeper into the data
	#children/parents - child/parent commen usernames so we can connect users to eachother
	def add_comment(self, reddit, data, edge_type = Reddit_Type.USR_COMMENT, delve=True, children=[], parents=[]):
		try:
			if self.data_count > 0:
				score = data.score
				author = data.author
				subr = data.subreddit
				id = data.name
				submission = data.submission
				
				if self.cl.is_new(id) and ((len(children) <= 10) and (len(parents) <= 10)):
					
					if author == None:
						auth_name = "[deleted]"
					else:
						self.add_user(author)
						auth_name = author.name
						
					self.cl.add(id,data)
					
					self.add_subreddit(reddit, subr)
					self.add_submission(reddit, submission, True)
					
					self.add_edge(auth_name, subr.display_name, Reddit_Type.USR_COMMENT)
					
					
					separation = len(children)
					for child in children:
						self.node_list[child].add_parent(auth_name,separation)
						separation = separation - 1
					
					separation = len(parents)
					for parent in parents:
						self.node_list[auth_name].add_parent(parent,separation)
						separation = separation - 1
					if delve:
						
						if not (data.is_root):
							parent = data.parent()
							children.append(auth_name)
							self.add_comment(reddit, parent, Reddit_Type.USR_COMMENT, True, children, parents)
						
						try:
							data.refresh()
							childr = data.replies#.replace_more(limit=0)

							for child in childr:
								if child.author == None:
									ch_auth_name = "[deleted]"
								else:
									ch_author_name = child.author.name
									self.add_user(author)
									
								parents.append(auth_name)
								self.add_comment(reddit, child, Reddit_Type.USR_COMMENT, True, children, parents)
						except:
							pass #just continue - we don't care that much
						
					self.add_karma(auth_name, subr.display_name, data.score, Reddit_Type.USR_COMMENT)
		except:
			pass
					
	#adds a submission/post to the data
	#reddit - reddit api
	#data - submission data
	#from_comment - whether we got the submission from a comment or not
	#edge_type - edge type to use by default
	def add_submission(self, reddit, data, from_comment=False, edge_type = Reddit_Type.USR_SUBMISSION):
		try:
			if self.data_count > 0:
				id = data.id
				
				if self.pl.is_new(id):
					self.pl.add(id, data)
					
					post_subr = data.subreddit.display_name
					if not (data.author == None):
						post_author = data.author.name
					else:
						post_author = "[deleted]"
					
					self.add_user(data.author)
					self.add_subreddit(reddit, data.subreddit)
					
					self.add_edge(post_author, post_subr, Reddit_Type.USR_SUBMISSION)
					
					comments = data.comments.list()
					
					for comment in comments:
						if (not (comment == None)) and hasattr(comment, "author"):
				
							self.add_user(comment.author)
							
							if self.cl.is_new(comment.name):
								self.cl.add(comment.name, comment)
						
							author = self.cl.get_data(comment.name)["author"]

							self.add_edge(author, post_author, Reddit_Type.POST_COMMENT)
							self.add_edge(author, post_subr, Reddit_Type.SUBR_COMMENT)
							
					self.add_karma(post_author, post_subr, data.score, Reddit_Type.USR_SUBMISSION)
		except:
			pass
		
	#links users, use for connections coming from node data sets
	def get_user_links(self):
		for node in self.node_list:
			for parent in self.node_list[node].parents:
				self.add_edge(parent, node, Reddit_Type.PARENT_CHILD)
		
	def get_node_importances(self, data_count=0):
		min_sr = maxsize
		max_sr = 0
		min_us = maxsize
		max_us = 0
	
		for key in self.node_list:
			val = self.node_list[key].get_importance(self.comment_karma, self.post_karma, self.total_gold)
			
			if (self.node_list[key].type == Reddit_Type.USER):
				if (val < min_us):
					min_us = val
				elif (val > max_us):
					max_us = val
			elif (self.node_list[key].type == Reddit_Type.SUBREDDIT):
				if (val < min_sr):
					min_sr = val
				elif (val > max_sr):
					max_sr = val
					
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
			if (self.node_list[key].type == Reddit_Type.SUBREDDIT):
				add_dif = (min_us - min_sr)
				new_range = max_us - min_us
				old_range = max_sr - min_sr
				
				if(new_range == 0):
					new_range = 1
				if(old_range == 0):
					old_range = 1
				
				self.node_list[key].importance = (self.node_list[key].importance + add_dif) * (new_range/old_range)
		
	#add reddit gold counts
	#user - user who was golded
	#num_gilded - number of golds to add
	def add_gold(self, user, num_gilded):
		user_name = self.add_user(user)
		self.node_list[user_name].add_gold(num_gilded)
		
	#add reddit karma
	#usr - user or submission
	#subr - subreddit
	#num_karma - karma to add
	#type - type of entity - user or submission
	def add_karma(self, usr, subr, num_karma, type = Reddit_Type.NONE):
		if (type == Reddit_Type.USR_COMMENT):
			self.comment_karma = self.comment_karma + num_karma
			self.node_list[usr].add_karma(type, num_karma)
			self.node_list[subr].add_karma(type, num_karma)
		elif (type == Reddit_Type.USR_SUBMISSION):
			self.post_karma = self.post_karma + num_karma
			self.node_list[usr].add_karma(type, num_karma)
			self.node_list[subr].add_karma(type, num_karma)

	def export_to_networkx(self, exclude_keys=["[delete]"]):
		return super().export_to_networkx(exclude_keys)
	
class Reddit_Node(dataCollection.Node):

	def __init__(self, id, type, init_importance = 1):
		super().__init__(id)
		
		self.parents = {}
		
		self.subreddits = set()
		self.comments = set()
		self.posts = set()
		
		self.type = type
		self.importance = init_importance
		self.comment_karma = 0
		self.post_karma = 0
		self.gold = 0
	
	#add comment parents to node
	#id - parent id
	#separationn - how far apart the comment were
	def add_parent(self, id, separation):
		if not (id in self.parents):
			self.parents[id] = separation
		self.parents[id] = mean([self.parents[id], separation])
		
	#add gold count
	#num_gilded - gold to add
	def add_gold(self, num_gilded):
		self.gold = self.gold + num_gilded
		
	#add karma
	#type - post or comment?
	#num_karma - amount of karma to add
	def add_karma(self, type, num_karma):
		if (type == Reddit_Type.USR_COMMENT):
			self.comment_karma = self.comment_karma + num_karma 
		elif (type == Reddit_Type.USR_SUBMISSION):
			self.post_karma = self.post_karma + num_karma
		
	def add_edge(self, key, type, count=1):
		if not (key in self.edges):
			self.edges[key] = Reddit_Edge(key)
		self.edges[key].add_edge_count(type, count)
		
	def get_importance(self, total_comment_karma, total_post_karma, total_gold):
		importance = self.importance
		
		#using absolute value because even if a user has a high negative karma score he impacted the 
		# community and is therefore still 'important', even in a negative light
		gold = self.gold + 1
		c_karma = self.comment_karma + 1
		p_karma = self.post_karma + 1
		
		total_comment_karma = total_comment_karma + 1
		total_post_karma = total_post_karma + 1
		total_gold = total_gold + 1
		
		importance = importance * abs(c_karma/total_comment_karma) #more karma (less polarized) = better
		importance = importance * abs(p_karma/total_post_karma) #more karma (less polarized) = better
		importance = importance * abs(gold/total_gold) #more gold = better
		self.importance = importance
		return importance
		
	def networkx_node(self):
		ret = super().networkx_node()
		
		type = Reddit_Type.toString(self.type)
		ret["attributes"]["type"] = type
		
		ret["attributes"]["name"] = self.id
		ret["attributes"]["importance"] = self.importance
		ret["attributes"]["comment_karma"] = self.comment_karma
		ret["attributes"]["post_karma"] = self.post_karma
		ret["attributes"]["gold_count"] = self.gold
		
		#ret["libs"]["comment"] = self.comments
		#ret["libs"]["post"] = self.posts
		
		#if type == Reddit_Type.USER:
		#	ret["libs"]["subreddit"] = self.subreddits
		return ret
			
		
class Reddit_Edge(dataCollection.Edge):
	
	#constructor
	def __init__(self, node_id):
		super().__init__(node_id)
	
	def networkx_edge(self, id, weight_mods):
		return super().networkx_edge(id, weight_mods)