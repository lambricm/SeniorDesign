#general data model - for creating networkx graphs from collected data
#should be used to create specialized models for different data collection

from abc import ABC,abstractmethod
import networkx as nx
import pickle
from math import ceil
from numpy import mean
from copy import deepcopy
from networkx import closeness_centrality,betweenness_centrality,degree_centrality,eigenvector_centrality,pagerank, DiGraph, has_path

#data library class
class DataLib():
	
	#contructor
	def __init__(self):
		self.data_set = {}
		
	#checks if id is new
	def is_new(self, id):
		return not (id in self.data_set)
		
	#adds id and data to class library
	def add(self,id,data = None):
		if (not (data == None)) and self.is_new(id):
			self.data_set[id] = self.parse_data(data)
			
	#parses given data to possibly store in different format
	def parse_data(self, data):
		return data

	#obtain keys for class data set
	def get_keys(self):
		return keys(self.data_set)
		
	#obtain a value given a key 'id'
	def get_data(self, id):
		if id in self.data_set:
			return self.data_set[id]
		else:
			return None
		
	#obtain length of data set
	def length(self):
		return len(self.data_set)
			
class Graph(ABC):
	
	#constructor
	def __init__(self, config_data = {"max_node_size":600, "min_node_size":200, "colors":{}}):
		self.node_list = {}
		
		self.max_node_size = config_data["max_node_size"]
		self.min_node_size = config_data["min_node_size"]
		self.colors = config_data["colors"]
		self.data_count = 0
		
		self.exclude = []
		
	#add a node to the grpah
	@abstractmethod
	def add_node(self,id,node_data = {}):
		pass
		
	#add and edge to the graph
	def add_edge(self, id1, id2, type, count=1):
		if not (id == id2):
			self.node_list[id1].add_edge(id2, type, count)
			self.node_list[id2].add_edge(id1, type, count)
		
	#return node keys
	def get_nodes(self):
		return self.node_list.keys()
	
	#export graph object to networkx
	def export_to_networkx(self, exclude_keys=[]):
		G = nx.Graph()
	
		node_keys = self.get_nodes()
		
		for node in node_keys:
			node_data = self.node_list[node].networkx_node()
			G.add_node(node_data["id"])
			G.nodes[node_data["id"]]["attributes"] = node_data["attributes"]
			
			for attr in node_data["attributes"]:
				G.nodes[node_data["id"]]["attributes"][attr] = node_data["attributes"][attr]
				
			edges = self.node_list[node].networkx_edges(self.get_edge_weight_modifiers())
		
			for edge in edges:
				if not (edge["id"] in G.edges):
					#add entire node
					G.add_edges_from([edge["id"]])
					
					for attr in edge["attributes"]:
						G.edges[edge["id"]][attr] = edge["attributes"][attr]
				else:
					#just add weights
					if "weight1" in edge["attributes"]:
						G.edges[edge["id"]]["weight1"] = edge["attributes"]["weight1"]
					if "weight2" in edge["attributes"]:
						G.edges[edge["id"]]["weight2"] = edge["attributes"]["weight2"]

		
		for key in exclude_keys:
			if key in G.nodes:
				G.remove_node(key)
		
		return G

	#for determining final edge importance
	#for edge weights, we use the formula:
	#	w = sum((1-((# times edge type is seen)/(total # edges))) * ((# times edge type is present - specific node)/(average # times edge type is present))) from type_0 to type_n
	#so, for determining the edge modifiers, I've simplified the formula into:
	#	a = # times edge type is seen
	#	b = total # edges
	#	c = # times edge type is present - specific node
	#	d = average # times edge type is present
	#meaning the equation is:
	#	w = sum((1-(a/b)) * (c/d)) from type_0 to type_n
	#for the inner part, we want a formula where we can determine most variables with one sweep:
	#	(1-(a/b)) * (c/d) = c/d - ac/bd = c(1/d - a/bd)
	#	where c is based on the edge itself and not data from all the edges, which is why it has to wait to be determined
	def get_edge_weight_modifiers(self):
		type_sums = {} 		#used for determining d
		type_avg = {} 		#d
		type_counts = {}	#a
		edge_set = set() 	#used to determine b
		edge_count = 0		#b

		for node in self.get_nodes():
			for edge in self.node_list[node].edges:
				edge_set.add(self.node_list[node].edges[edge].get_key(node))
				for type in self.node_list[node].edges[edge].type_counts:

					if not type in type_sums:
						type_sums[type] = 0
					if not type in type_counts:
						type_counts[type] = 0

					type_sums[type] = type_sums[type] + self.node_list[node].edges[edge].type_counts[type]
					type_counts[type] = type_counts[type] + 1
					
		for type in type_sums:
			type_avg[type] = type_sums[type]/type_counts[type]

		edge_count = len(edge_set)

		#return (1/d - a/bd) values so that we can calculate the total weight during our networkx export
		type_modifiers = {}
		for type in type_avg:
			type_modifiers[type] = (1/type_avg[type]) * (type_counts[type]/(edge_count * type_avg[type]))

		return type_modifiers
		
	#add any links that couldn't be added before
	def get_user_links(self):
		pass
		
	#check the number of nodes
	def check_num(num):
		#num should an integer > 0
		if num < 1:
			num = 1
		num = ceil(num)
		
		return num
		
	#retrieve a networkx graph with only the top nodes
	def get_top_nodes(self, num, data_count=0):
		exclude = self.exclude
		
		num = Graph.check_num(num)
		self.get_user_links()
		
		self.get_node_importances(data_count)

		G = self.export_to_networkx(exclude)
		sub_graphs = list(nx.connected_component_subgraphs(G))
		
		largest_sub_graph = sub_graphs[0]
		for sg in sub_graphs:
			if len(sg.nodes) > len(largest_sub_graph.nodes):
				largest_sub_graph = sg
				
		G = largest_sub_graph
		
		try:
			cc = closeness_centrality(G)
		except:
			cc = None
		try:
			dc = degree_centrality(G)
		except:
			dc = None
		try:
			bc = betweenness_centrality(G)
		except:
			bc = None
		try:
			ec = eigenvector_centrality(G)
		except:
			ec = None

		mean_arr = []
		weightmap = {}
		
		for node in G.nodes:	
			if not cc == None:
				G.nodes[node]["cc"] = cc[node]
				mean_arr.append(cc[node])
			if not bc == None:
				G.nodes[node]["bc"] = bc[node]
				mean_arr.append(bc[node])
			if not dc == None:
				G.nodes[node]["dc"] = dc[node]
				mean_arr.append(dc[node])
			if not ec == None:
				G.nodes[node]["ec"] = ec[node]
				mean_arr.append(ec[node])
			
			G.nodes[node]["weight"] = mean([self.node_list[node].importance,mean(mean_arr)])
			weightmap[node] = G.nodes[node]["weight"]
		
		GD_temp = DiGraph()
		GD_temp.add_nodes_from(G.nodes)
		
		for edge in G.edges:
			w1 = 1
			w2 = 1

			if "weight1" in G.edges[edge]:
				w1 = G.edges[edge]["weight1"]
			if "weight2" in G.edges[edge]:
				w2 = G.edges[edge]["weight2"]

			GD_temp.add_edge(edge[0],edge[1])
			GD_temp.edges[(edge[0],edge[1])]["importance"] = w1
			GD_temp.add_edge(edge[1],edge[0])
			GD_temp.edges[(edge[1],edge[0])]["importance"] = w2

		#looked up default parameters for alpha=0.85, personalization=None, max_iter=100, and tol=1e-08
		#pg = pagerank(GD_temp, 0.85, None, 100, 1e-08, weightmap, edgeweightmap)
		pg = pagerank(GD_temp, 0.85, None, 100, 1e-08, weightmap, "importance")
		
		total_nodes = len(G.nodes)
		inv_pg = {}
		
		#reverse map because we care more about the importance values determined from pagerank
		for key in pg:
			if pg[key] not in inv_pg:
				inv_pg[pg[key]] = []
			inv_pg[pg[key]].append(key)
			
		#while we still have too many nodes, remove the ones with the smallest importance
		vals = (sorted(inv_pg.keys())[::-1])
		
		nodes_keep = []
			
		while (len(vals) > 0) and (len(nodes_keep) < num):
			nodes_keep = nodes_keep + inv_pg[vals[0]]
			vals.pop(0)
			
		#determine which nodes were connected
		conn = {}
		for node in nodes_keep:
			conn[node] = []
			for node2 in nodes_keep:
				if not node == node2 and has_path(G, node, node2):
					conn[node].append(node2)
		
		#remove nodes we don't want
		temp_nodes = list(G.nodes)
		for nd in temp_nodes:
			if not (nd in nodes_keep):
				G = self.node_removal_check(G,deepcopy(G),nd,conn)
			else:
				G.nodes[nd]["rank"] = (nodes_keep.index(nd)+ 1)
				print(G.nodes[nd]["rank"])

		return G
		
	#makes sure that nodes that should be connected are connected in the end by removing middle nodes,
	# but keeping theh overall connections between the important nodes
	#G = original graph (used for finding shortest path when we remove node in G2)
	#G2 = graph we will actually remove the node from and return
	#node_remove = node id for the node we want to remove
	#node_conns = node connections in dictionary format - can be used for uni- or bi-directional graphs
	#	but loses some time efficiency by checking for connections both ways
	def node_removal_check(self,G,G2,node_remove,node_conns):
		G2.remove_node(node_remove)
		
		#get links that used to be there but no longer are (only for important nodes)
		#check all important nodes
		
		for node in node_conns:
			#check all other important nodes they're supposed to be connected to
			for node2 in node_conns[node]:
				#if the path is gone
				if not  has_path(G2, node, node2):
					
					#find shortest path from G
					sh_path = nx.shortest_path(G,node,node2)
					#find where the node we want to remove is in the path
					ind = sh_path.index(node_remove)
					#add an edge between surrounding nodes to keep the graph connected in similar way
					G2.add_edge(sh_path[ind-1],sh_path[ind+1])
				
		return G2

		
	def get_node_importances(self, data_count = 0):
		pass
		
#node class
class Node(ABC):
	
	@abstractmethod
	def __init__(self, id):
		self.id = id
		self.edges = {}
		self.ids = set()

	#add an edge connection for the node
	@abstractmethod
	def add_edge(self, key, type, count=1):
		pass
	
	#retreive node's importance
	@abstractmethod
	def get_importance(self, additional_info = {}):
		pass
		
	#get node data for networkx
	@abstractmethod
	def networkx_node(self):
		return {"id":self.id, "attributes":{}}
		
	#retrieve edge data for networkx
	def networkx_edges(self, weight_mods = {}):
		edges = []
		
		for edge in self.edges:
			temp_edge = {"id":self.edges[edge].get_key(self.id), "attributes":self.edges[edge].networkx_edge(self.id,weight_mods)}

			edges.append(temp_edge)
			
		return edges
			
class Edge(ABC):
	
	def __init__(self, id):
		self.id = id
		self.type_counts = {}
		
	#add a count for the type of edge
	#allows one edge to have multiple types of edges and the counts of each one
	def add_edge_count(self, type, count=1):
		if not (type in self.type_counts):
			self.type_counts[type] = 0
		self.type_counts[type] = self.type_counts[type] + count
		
	#retreive networkx edge
	@abstractmethod
	def networkx_edge(self, id, weight_mods):
		ret = {}

		#determine edge weight
		weight = 1

		for type in self.type_counts:
			weight = weight + (self.type_counts[type] * weight_mods[type])

		#determine whether weight 1 (id1 -> id2) or weight 2 (id1 <- id2)
		key = self.get_key(id)
		if (self.id == key[0]):
			ret['weight1'] = weight
		elif (self.id == key[1]):
			ret['weight2'] = weight

		return ret
	
	#get key for adding to networkx
	def get_key(self, id2):
		temp = sorted([self.id,id2])
		return (temp[0],temp[1])