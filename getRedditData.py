import praw
import argparse
import os
import json
import pickle

import networkx as nx

from redditDataCollection import Reddit_Graph, UserLib, SubredditLib, Data_Type

#retrieves api object
#return - reddit api object
def get_api():
	return praw.Reddit(\
		client_id="oNPOQPebbHoQoA", \
		client_secret="501Vxy6BmPG6welfUK0P67GZaE8", \
		password="1x35ge1wd2dfh998a1", \
		user_agent="Social Network Data Gathering script by /u/data_collection_bot1", \
		username="data_collection_bot1")
		
#retrieve command line inputs
#return - argparse object
def get_inputs():
	parser=argparse.ArgumentParser(description="getRedditData.py arguments")
	parser.add_argument("-k", nargs=1, required=True, help="File with keywords/search terms/user/subreddits", metavar="keyword_file_path", dest="keywords_input")
	parser.add_argument("-o", nargs=1, required=False, help="File that will hold reddit data output later used for graph creation & processing", metavar="output_file_path", dest="output_file")
	parser.add_argument("-o_rd", action="store_true", required=False, help="Will output in data format returned by reddit api. Useful for outputting multiple files and concatenating them later")
	parser.add_argument("-o_nx", action="store_true", required=False, help="Will output in networkx format. Note that this format goes through the process of gathering the most important nodes before exporting")
	parser.add_argument("-i", nargs=1, required=False, help="Raw Reddit API data input file.", metavar="input_file_path", dest="input_file")
	parser.add_argument("-num_nodes", nargs=1, required=False, help="Number of nodes we want to collect and graph", metavar="num_nodes", dest="num_nodes")
	#parser.add_argument("-sr", required=False, help="Allows subreddits to be collected as nodes")
	args_in = parser.parse_args()
	
	if not (args_in.num_nodes == None):
		try:
			args_in.num_nodes = int(args_in.num_nodes[0])
		except ValueError:
			print("ERROR: cannot set number of nodes to '" + args_in.num_nodes[0] + "' because it is not an integer and cannot be converted to one. exiting")
			exit()
		if (args_in.num_nodes < 1):
			print("ERROR: could not set number nodes to '" + args_in.num_nodes[0] + "' because the number of nodes cannot be less than 1")
			exit()
	
	return args_in
	
#obtains data from reddit
#num_nodes = approx. number of nodes we want at the end (only more when there are ties for importance)
#kwords - search keywords, namely users and/or subreddits
def gather_data(num_nodes, kwords):
	reddit = get_api()
	
	mult = 100
	rg = Reddit_Graph()
	
	#get user data
	if "users" in kwords:
		for user_name in kwords["users"]:
			rg.data_count = num_nodes*100
			
			user = reddit.redditor(user_name)
			
			rg.add_data(reddit, user, Data_Type.USER)
			
			#go through the user's top comments
			for comment in user.comments.top(limit=None):
				if rg.data_count < num_nodes*10:
					rg.data_count = num_nodes*10
				rg.add_data(reddit, comment, Data_Type.POST_COMMENT)
			
			#go through user's top submissions
			for submission in user.submissions.top():
				if rg.data_count < num_nodes*10:
					rg.data_count = num_nodes*10
				rg.add_submission(reddit, submission)
			
			#add golds if they have them
			gilds = 0
			for gild in user.gilded():
				gilds = gilds + 1
			rg.add_gold(user, gilds)
				
	#go through subreddits
	if "subreddits" in kwords:
		rg.data_count = num_nodes*100
		for subreddit in kwords["subreddits"]:
			if rg.data_count < num_nodes*10:
					rg.data_count = num_nodes*10
			subr = reddit.subreddit(subreddit)
			rg.add_subreddit(reddit, subr, True)
		
	return rg
	
#make sure the file can be read
#file_in - path to be checked
#return - True if can be read
def check_file_read(file_in):
	if os.path.exists(file_in):
		if os.access(os.path.dirname(file_in), os.R_OK):
			return True
		else:
			print("ERROR: File '" + file_in + "' is not available for reading")
	else:
		print("ERROR: Path '" + file_in + "' could not be found")
		
	return False
	
#retrieve keywords from file
#args_in - arparse object
#return - desired keyword(s)
def get_keywords(args_in):
	kwords = {"users":[],"subreddits":[]}

	if hasattr(args_in, 'keywords_input') and not (args_in.keywords_input == None):
		if check_file_read(args_in.keywords_input[0]):
			keywords_input = args_in.keywords_input[0]
			
			file_in_r = open(keywords_input, "r")
			kwords = json.load(file_in_r)
			file_in_r.close()

			for ind in range(len(kwords["keywords"])):
				kwords["keywords"][ind] = kwords["keywords"][ind].lower()
		else:
			print("ERROR: Keyword file '" + args_in.keywords_input[0] + "' could not be used. Exiting")
			exit()
			
	return kwords
	
#get the output file
#args_in - argparse object
#return - output filename
def get_file_out(args_in):
	output_file = "./twitter_data.txt"

	if hasattr(args_in, 'output_file') and not (args_in.output_file == None):
		output_file = args_in.output_file[0]
	
	return output_file

#writes networkx format to file
#G - networkx graph
#file_name - output file path
def write_networkx(G, file_name):
	ofile = open(file_name,'wb')
	pickle.dump(G, ofile)
	ofile.close()
	
#retreives a json to allow easy viewing of the node
#G - networkx graph
#return - node json ready for output
def get_node_json(G):
	node_json = {"nodes":[]}
	for node in G.nodes:
		node_json["nodes"].append(G.nodes[node]["attributes"])
		
	return node_json
	
#writes the viewable data file for viewing data about the ndoes via grpah_gui script
#G - networkx grpah
#file_name - output file path
def write_data_file(G, orig_file_name):
	node_json = get_node_json(G)
	write_networkx(node_json, "viewable_data_" + orig_file_name)

#main actions for entire script	
def get_reddit_data():
	args_in = get_inputs()
	
	num_nodes = 15
	if not args_in.num_nodes == None:
		num_nodes = args_in.num_nodes
		
	kwords = get_keywords(args_in)

	rg = gather_data(num_nodes, kwords)
	G = rg.get_top_nodes(num_nodes)
	write_networkx(G, get_file_out(args_in))
	write_data_file(G, get_file_out(args_in))
	
get_reddit_data()