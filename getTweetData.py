#File:get_tweet_data
#Creator: Cicely Lambright
#Desc:collect twitter data

import tweepy
import argparse
import os
import json
import pickle

from twitterDataCollection import Twitter_Graph,Twitter_Type,TweetLib
from keywords import KeyWords

import networkx as nx
import matplotlib.pyplot as plt
import re

## TOKENS - CHANGE IF DIFFERENT USER ##
access_token = "960290092282728450-WTADVXDL4cQa3YogxjsCE33mc0DyFcg"
access_token_secret = "pwsDtwqwh3m7n3GR3MmrLMFeSU5ratq2tne9qVNYpkzRJ"
consumer_key = "alDs89SFYVKZS38WnD9cMloaZ"
consumer_secret = "vX1SC84OouKePJIlrqFoVbVJuniz8uo2rTtnvEWmFePDyMRBOQ"
	
#retrieves api object
#return - twitter api object
def get_api():	
	#sets up connection
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)
	api = tweepy.API(auth)
		
	return api

#changes list of keywords into a search string
#lst_in - list of keywords
#ret - search string
def search_string(lst_in):
	max_len = 500

	ret = ""
	if (len(lst_in) > 0):
		ret = '"' + lst_in[0] + '"'
	else:
		return ret
	
	for kword in lst_in:
		if not kword == lst_in[0]:
			if (len(ret) + len(kword)) > max_len:
				return ret
			ret = ret +  ' OR "' + kword + '"'

	ret = re.sub(r'#',r'%23',ret)

	return ret
	
#obtains some information about users
#id - user id
#return - user information about friends & followers	
def get_user_info(id):
	ret = {}
	
	try:
		api = get_api()
		ret['friends'] = api.friends_ids(id)
		ret['followers'] = api.followers_ids(id)
	except tweepy.TweepError as e:
		ret['friends'] = []
		ret['followers'] = []
	
	return ret
	
#retrieves tweets from twitter server
#keywords - keywords we want ot search one
#num_tweets - initial number of tweets
#tweetLib - a TweetLib object to ensure no multiple tweets
#num_times - tweet  multiplier - the higher the number, the more we will have that we can sift through
#return - retrieved tweets
def get_tweets(keywords, num_tweets, tweetLib, num_times=100):

	if not isinstance(num_tweets, int):
		num_tweets = 15
	num_tweets = num_tweets*num_times
	
	api = get_api()
	search = keywords			#list of keywords	
	tweets = []					#where found tweet are put
	last_id = -1				#make sure we don't get same tweets

	searched_tweets = get_tweet_batch(api, search_string(keywords), last_id, num_tweets, tweetLib, tweets)
	searched_tweets2 = get_tweet_batch(api, search_string(get_research_kwords(searched_tweets, keywords)), last_id, num_tweets, tweetLib, tweets)
	return [searched_tweets, searched_tweets2]

#retrieves keywords from first batch of tweets obtained
#searched_tweets - first batch of tweets
#orig_kwords - original search terms to avoid duplication
#return - array of top keywords	
def get_research_kwords(searched_tweets, orig_kwords):
	filters = []#['^#.*', '^@.*']
	kw = KeyWords(orig_kwords, filters)
	id_lst = set()
	
	for tw in searched_tweets:
		if not tw.id_str in id_lst:
			id_lst.add(tw.id_str)
			kw.add_source(tw.text)
		if hasattr(tw, 'retweeted_status'):
			if not tw.retweeted_status.id_str in id_lst:
				id_lst.add(tw.retweeted_status.id_str)
				kw.add_source(tw.retweeted_status.text)
				
	return kw.calc_top()
		
#grabs a 'batch' of tweets and keeps grabbing recursively until either ti cannot fetch more tweets or has reached the desired twet count
#api - api object for retrieveing items from tweetpy
#search_str - search string to submit to twitter
#last_id - previous id we have gatherded up to so we don't continuously obtain the same tweets
#num_tweets_left - a count of the remaining tweets we want to collect
#tweetLib - a TweetLib object to ensure no multiple tweets
#tweeets - collected tweet list
#return - collected tweets
def get_tweet_batch(api, search_str, last_id, num_tweets_left, tweetLib, tweets):

	if (num_tweets_left > 0):
	
		try:
			ct = 100
			if (num_tweets_left <= 0):
				return tweets
			if (num_tweets_left < 100):
				ct = num_tweets_left
				
			#get tweets
			new_tweets = api.search(q=search_str, max_id=str(last_id - 1), include_rts=True, count=ct)
			
			if not (len(new_tweets) < 1):
				#get ID of last tweet so that we don't get the same tweets
				last_id = new_tweets[-1].id
			
				for tw in new_tweets:
					if tweetLib.is_new(tw.id):
						tweetLib.add(tw.id,tw)
						tweets.append(tw)
						num_tweets_left = num_tweets_left - 1
						
				return get_tweet_batch(api, search_str, last_id, num_tweets_left, tweetLib, tweets)
		except tweepy.TweepError as e:
			print("TWEEPY ERROR")
			print(e.reason)
			return tweets
	else:
			return tweets
	
#collects desired values from twitter data and returns a 'Nodes' object
#twitter_data - collection of tweets
#return - Nodes object
def collect_vals(tweet_collections):
	data = Twitter_Graph()
	
	importance_diff = 0
	
	for twitter_data in tweet_collections:
		if (len(twitter_data)) > 0:
			importance_diff = importance_diff + (1/len(twitter_data))
		
		importance = 1 - importance_diff
	
		#go through each tweet
		for tweet in twitter_data:

			#add user as node
			data.add_node(tweet.user.id_str,tweet.user.name,Twitter_Type.TW_USER,tweet.favorite_count,tweet.retweet_count,hasattr(tweet, 'retweeted_status'), importance, tweet.id)
			usr_info = get_user_info(tweet.user.id_str)
			data.node_list[tweet.user.id_str].add_follower(usr_info['followers'])
			data.node_list[tweet.user.id_str].add_friend(usr_info['friends'])
			
			#check all hashtags
			for ht in tweet.entities['hashtags']:
			
				#add hashtab as node
				data.add_node(ht['text'].lower(), ht['text'], Twitter_Type.TW_HASHTAG,tweet.favorite_count, tweet.retweet_count, hasattr(tweet, 'retweeted_status'), importance, tweet.id)
				
				#add edge between hashtag and user
				data.add_edge(tweet.user.id_str,ht['text'].lower(), Twitter_Type.TW_STATUSHT)
				
			temp_set = set()
			for ht in tweet.entities['hashtags']:
				temp_set.add(ht['text'].lower())
				for ht_s in tweet.entities['hashtags']:
					if (not (ht_s['text'].lower() in temp_set)):
						#make edge between hashtags in same tweet
						data.add_edge(ht['text'].lower(), ht_s['text'].lower(), Twitter_Type.TW_HTHT)
						
			#check user mentions in tweet
			for um in tweet.entities['user_mentions']:
			
				#add mentioned user as node
				data.add_node(um['id_str'], um['screen_name'], Twitter_Type.TW_USER, tweet.favorite_count, tweet.retweet_count, hasattr(tweet, 'retweeted_status'), importance, tweet.id)
				
				#add connection between user and mentioned user
				data.add_edge(tweet.user.id_str, um['id_str'], Twitter_Type.TW_USR_MENTION)
			
			#check if retweet
			if hasattr(tweet, 'retweeted_status'):
				
				#add retweeted user as node
				data.add_node(tweet.retweeted_status.user.id_str, tweet.retweeted_status.user.name, Twitter_Type.TW_USER, tweet.retweeted_status.favorite_count, tweet.retweeted_status.retweet_count, hasattr(tweet.retweeted_status, 'retweeted_status'), importance, tweet.id)
				data.add_node(tweet.retweeted_status.user.id_str, tweet.retweeted_status.user.name, Twitter_Type.TW_USER, tweet.retweeted_status.favorite_count, tweet.retweeted_status.retweet_count, hasattr(tweet.retweeted_status, 'retweeted_status'), importance, tweet.retweeted_status.id)
					
				#add edge between users
				data.add_edge(tweet.user.id_str,tweet.retweeted_status.user.id_str, Twitter_Type.TW_RETWEET)
					
				#check hashtags in retweet
				for ht in tweet.retweeted_status.entities['hashtags']:
					
					#add hashtag as node
					data.add_node(ht['text'].lower(), ht['text'], Twitter_Type.TW_HASHTAG, tweet.retweeted_status.favorite_count, tweet.retweeted_status.retweet_count, hasattr(tweet.retweeted_status, 'retweeted_status'), importance, tweet.retweeted_status.id)
							
					#add edge between retweeted user and the hashtags they've used
					data.add_edge(tweet.retweeted_status.user.id_str, ht['text'].lower(), Twitter_Type.TW_STATUSHT)
						
				temp_set = set()
				for ht in tweet.retweeted_status.entities['hashtags']:
					temp_set.add(ht['text'].lower())
					for ht_s in tweet.retweeted_status.entities['hashtags']:
						if (not (ht_s['text'].lower() in temp_set)):
						
							#make edge between hashtags in same tweet
							data.add_edge(ht['text'].lower(), ht_s['text'].lower(), Twitter_Type.TW_HTHT)
					
				#check user mentions in retweet
				for um in tweet.retweeted_status.entities['user_mentions']:
					#add mentioned user as node
					data.add_node(um['id_str'], um['screen_name'], Twitter_Type.TW_USER, tweet.retweeted_status.favorite_count, tweet.retweeted_status.retweet_count, hasattr(tweet.retweeted_status, 'retweeted_status'), importance, tweet.retweeted_status.id)
					
					#add connection between user and mentioned user
					data.add_edge(tweet.retweeted_status.user.id_str, um['id_str'], Twitter_Type.TW_USR_MENTION)
				
	return data
	
#retrieve command line inputs
#return - argparse object
def get_inputs():
	parser=argparse.ArgumentParser(description="getTweetData.py arguments")
	parser.add_argument("-k", nargs=1, required=False, help="File with keywords/search terms for tweet", metavar="keyword_file_path", dest="keywords_input")
	parser.add_argument("-o", nargs=1, required=False, help="File that will hold tweet data output later used for graph creation & processing", metavar="output_file_path", dest="output_file")
	parser.add_argument("-o_tw", action="store_true", required=False, help="Will output in tweepy format. Useful for outputting multiple files and concatenating them")
	parser.add_argument("-o_nx", action="store_true", required=False, help="Will output in networkx format. Note that this format goes through the process of gathering the most important nodes before exporting")
	parser.add_argument("-i", nargs=1, required=False, help="Tweepy input file.", metavar="input_file_path", dest="input_file")
	parser.add_argument("-num_tw", nargs=1, required=False, help="Number of tweets we want to collect and graph", metavar="num_tweets", dest="num_tweets")
	args_in = parser.parse_args()
	
	if not (args_in.num_tweets == None):
		try:
			args_in.num_tweets = int(args_in.num_tweets[0])
		except ValueError:
			print("ERROR: cannot set number of tweets to '" + args_in.num_tweets[0] + "' because it is not an integer and cannot be converted to one. exiting")
			exit()
	
	return args_in

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
	kwords = {"key":"none","keywords":[]}

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

#retreives a json to allow easy viewing of the node
#G - networkx graph
#return - node json ready for output
def get_node_json(G):
	node_json = {"nodes":[]}
	for node in G.nodes:
		node_json["nodes"].append(G.nodes[node]["attributes"])
		
	return node_json
	
#write json data to file
#args_in - arparse object
#json_out - json object to output
def write_json_to_file(args_in, json_out):
	output_file = "./twitter_data.txt"

	if hasattr(args_in, 'output_file') and not (args_in.output_file == None):
		output_file = args_in.output_file[0]
	
	out_file = open(output_file, 'w')
	json.dump(json_out, out_file)
	out_file.close()

#get the output file
#args_in - argparse object
#return - output filename
def get_file_out(args_in):
	output_file = "./twitter_data.txt"

	if hasattr(args_in, 'output_file') and not (args_in.output_file == None):
		output_file = args_in.output_file[0]
	
	return output_file

#exports in tweepy format - good for concatenating data over time
#twitter_data - retreived data
#args_in - argparse object
def export_tweepy(twitter_data, args_in):
	output_file = get_file_out(args_in)
	ofile = open(output_file,'wb')
	pickle.dump(twitter_data, ofile)
	ofile.close()

#imports tweepy format - good for easy re-use without re-querying (as well as concatenation)
#file_name - import file path
#tweetLib - a TweetLib object to be certain no repreat tweets are absorbed
def import_tweepy(file_name,tweetLib):
	ifile = open(file_name,'rb')
	indata = pickle.load(ifile)
	ifile.close()
	
	for tw_large in indata:
		for tw in tw_large:
			if tweetLib.is_new(tw.id):
				tweetLib.add(tw.id, tw)

	return indata

#writes networkx format to file
#G - networkx graph
#file_name - output file path
def write_networkx(G, file_name):
	ofile = open(file_name,'wb')
	pickle.dump(G, ofile)
	ofile.close()

#reads networkx grpah from file
#file_name = input file path
#return - netowrkx graph
def read_networkx(file_name):
	ifile = open(file_name,'rb')
	G = pickle.load(ifile)
	ifile.close()

	return G
	
#writes the viewable data file for viewing data about the ndoes via grpah_gui script
#G - networkx grpah
#file_name - output file path
def write_data_file(G, orig_file_name):
	node_json = get_node_json(G)
	write_networkx(node_json, "viewable_data_" + orig_file_name)
	
#complete operations for entire script
def get_tweet_data():

	args_in = get_inputs()
	
	#check for input
	tweets_in = []
	tweetLib = TweetLib()
	
	num_tweets = args_in.num_tweets
	
	if num_tweets is None:
		num_tweets = 15
		
	if hasattr(args_in, "input_file") and (not (args_in.input_file == None)):
		tweets_in = import_tweepy(args_in.input_file[0], tweetLib)
	else:
		keywords = get_keywords(args_in)
		tweets_in = get_tweets(keywords['keywords'], num_tweets, tweetLib, 10)
		
	if hasattr(args_in, "o_tw") and (args_in.o_tw == True):
		export_tweepy(tweets_in, args_in)
	else:
		tweets_data = collect_vals(tweets_in)
		G = tweets_data.get_top_nodes(num_tweets,tweetLib.length())
		
		if hasattr(args_in, "o_nx") and (args_in.o_nx == True):
			write_networkx(G, get_file_out(args_in))
			write_data_file(G, get_file_out(args_in))
	
get_tweet_data()