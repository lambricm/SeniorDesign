#getGraphData
#Purpose: Displays networkx graph object in desired format

import argparse
import os
import json
import networkx as nx
import matplotlib.pyplot as plt
import pickle
import copy as cp

from dataModel import Nodes
from dataModel import Type

#import methods
	
#retrieves command line arguments
#return - argparse command line arguments
def get_inputs():
	parser=argparse.ArgumentParser(description="getGraphData.py arguments")
	#parser.add_argument("help", required=False, help="displays help guide for program")
	parser.add_argument("-i", nargs=1, required=True, help="File with byte data for networkx graph", metavar="json_input_file_path", dest="in_data")
	parser.add_argument("-c", nargs=1, required=False, help="Config. file for graph settings", metavar="config_file", dest="config_file")
	#parser.add_argument("-g_mc", action="store_true", required=False, help="Outputs graph with minimal crossing visualization")
	parser.add_argument("-g_nx", action="store_true", required=False, help="Outputs graph with generic networkx visualization")
	parser.add_argument("-g_ml", action="store_true", required=False, help="Outputs graph with matplot visualization")
	args_in = parser.parse_args()
	
	return args_in
	
#ensures path is a file
#file_in - string path to check_path
#return - True if path is good
def check_path(file_in):
	if not (os.path.exists(file_in)):
		print(file_in + " is not a file")
		return False
	return True

#sets configuration data
#args_in - command line arguments (argparse)
#graph_data - Nodes object
#return - modified Nodes object)
def set_config(args_in, graph_data):
	if not (args_in.config_file == None):
		filename = args_in.config_file[0]
		
		if check_path(filename):
			inFile = open(filename)
			config = json.load(inFile)["graph_config"]
			inFile.close()
			
			graph_data.config_from_json(config)
			
	return graph_data

#reads the networkx byte code file
#file_name - file we need to load from
#return - networkx graph
def read_networkx(file_name):
	if not check_path(file_name):
		print("ERROR: could not read file '" + file_name + "'")
	
	ifile = open(file_name,'rb')
	G = pickle.load(ifile)
	ifile.close()

	return G
		
#gets the rankings for each of the nodes in G2
#G - networkx graph
#return - list of nodes in order from most important to least important
def get_rank(G):
	
	temp_dict = {}
	temp = []
	
	for node in G.nodes:
		if not G.nodes[node]["attributes"]["importance"] in temp_dict:
			temp_dict[G.nodes[node]["attributes"]["importance"]] = []
		temp_dict[G.nodes[node]["attributes"]["importance"]].append(node)
		
	key_order = sorted(temp_dict.keys())[::-1]
	
	for key in key_order:
		temp = temp + temp_dict[key]
		
	return temp
		
#creates graph from data
#graph_data - Nodes object
def create_graph():         
	args_in = get_inputs()
	
	G = read_networkx(args_in.in_data[0])
	
	temp_order_holder = {}
	for node in G:
		G.nodes[node]["original"] = "yes"
		
		#print(G.nodes[node]["rank"])
	
	rn = get_rank(G)
	
	G2 = nx.Graph()
	
	for node in G.nodes:
		if node in rn:
			G2.add_node((rn.index(node)+1))
			G2.nodes[(rn.index(node)+1)]["original"] = "yes"
		
	for edge in G.edges:
		if not edge[0] == edge[1]:
			G2.add_edge((rn.index(edge[0])+1), (rn.index(edge[1])+1))	
			
	if hasattr(args_in, "g_ml") and (args_in.g_ml == True):
		nx.draw(G2, with_labels=False)
		nx.draw_networkx_labels(G2, nx.spring_layout(G2))
		plt.show()
	if hasattr(args_in, "g_nx") and (args_in.g_nx == True):
		plt.figure(figsize=(20, 12))
		nx.draw(G2, with_labels=True)
		plt.show()
	"""
	if hasattr(args_in, "g_mc") and (args_in.g_mc == True):
		min_crossing = 10000000
		minG = 0

		for i in range(10):
			Gx = cp.deepcopy(G2)
			crossing = methods.reduceCrossing(Gx, 3, 1, toPrint=False, toPlot=False)
			if crossing < min_crossing:
				min_crossing = crossing
				minG = cp.deepcopy(Gx)

		print("Final crossing: ", min_crossing)
		methods.plotFinal(minG)
	"""
#----------------------------------------------------------------
create_graph() #OUTPUT A GRAPH