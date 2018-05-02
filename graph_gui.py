#graph_gui
#Will display json data from networkx
#can actually display any json data if not using the function 'load_graph_visualization_order'

from tkinter import *
from tkinter.ttk import *
import json
import argparse
import pickle
from re import sub

#gui to display json data via a tree format
class Graph_GUI:
	#error if parsing problem
	#notably - will trigger if character encoding exceeds the tkinter display range
	DEF_ERR_STR = "Could not parse"

	#constructor
	def __init__(self, master):
		self.parser_error_number = 1				#cannot display same error message
		self.file_name = "No file name specified"
	
		self.master = master						#top level display window
		self.master.minsize(width=200, height=300)	#set minimum window size
		self.master.geometry("300x500")				#set default window size
		master.title("Network Visualization")
		
		#add treeview
		self.tr = Treeview(master, selectmode='browse')
		self.tr.heading("#0",text=self.file_name)
		self.tr.pack(side='left', fill=BOTH, expand=1)
		
		#add scrollbar
		self.vsb = Scrollbar(master, orient='vertical', command=self.tr.yview)
		self.vsb.pack(side='right', fill='y')
		self.tr.configure(yscrollcommand=self.vsb.set)
		
	#function to add data to the treeview
	#json_data - data to display
	#parent - parent entry to display under - start with 'None' to get top-level
	def add_data(self, json_data, parent=None):
		id = parent
		if id == None:
			id = ""
		
		if (type(json_data) == type({})):
			for key in json_data:
				if (type(json_data[key]) == type({})) or (type(json_data[key]) == type([])):
					new_id = self.insert_tree(self.tr, id, key)
					self.add_data(json_data[key], new_id)
				else:
					new_id = self.insert_tree(self.tr, id, str(key) + " = " + str(json_data[key]))
		elif (type(json_data) == type([])):
			ind = 0
			for key in json_data:
				ind = ind + 1
				if (type(key) == type({})) or (type(key) == type([])):
					new_id = self.insert_tree(self.tr, id, ind)
					self.add_data(key, new_id)
				else:
					self.insert_tree(self.tr, id, key)
		else:
			self.insert_tree(self.tr, id, json_data)
			
	#inserts data into the tree
	#tree - tree object of format
	#id - id of parent entry in tree
	#text_in - text we are adding to the tree under the parent id
	#used instead of default because there were lots of error with character ranges
	def insert_tree(self, tree, id, text_in):
		ret = id
		try:
			ret = tree.insert(id, "end", text=text_in)
		except:
			ret = tree.insert(id, "end", self.DEF_ERR_STR + " " + str(self.parser_error_number))
			self.parser_error_number = self.parser_error_number + 1
			
		return ret
		
	#sets the main column header the same as the input file name
	#return - file name without extension
	def set_filename(self, args_in):
		self.tr.heading("#0",text=args_in.input_file[0])
		self.tr.pack(side='left', fill=BOTH, expand=1)
		
#takes data gotten from other scripts for exporting visual networkx data from social networks and
# adjusts the data for optimal display
#json_data - node data for networkx graph
#return - adjusted json data
def load_graph_visualization_order(json_data):
	prev = json_data["nodes"]
	
	temp_dict = {}
	temp = []
	
	for node in prev:
		if not node["importance"] in temp_dict:
			temp_dict[node["importance"]] = []
		temp_dict[node["importance"]].append(node)
		
	key_order = sorted(temp_dict.keys())[::-1]
	
	for key in key_order:
		temp = temp + temp_dict[key]
		
	json_data["nodes"] = temp
	
	return json_data
		
#gets command line input from argparse
#return - argparse object
def get_input():
	parser=argparse.ArgumentParser(description="graph_gui.py arguments")
	parser.add_argument("-i", nargs=1, required=True, help="JSON input file.", metavar="input_file_path", dest="input_file")
	parser.add_argument("-b", required=False, help="Allows one to pull in a file using the pickle module's reader - useful for irregular characters", action="store_true")
	args_in = parser.parse_args()

	return args_in
	
#loads a json file
#input_file - file path to load
#return - json data
#can only be used for pure json files without strange characters
#use load_bytes and output via bytes with 'pickle' library for more robust loading
def load_json(input_file):
	file_in_r = open(input_file, "r")
	json_data = json.load(file_in_r)
	file_in_r.close()
	
	return json_data
	
#loads a json byte file
#input_file - file path to load
#return - json data
def load_bytes(input_file):
	ifile = open(input_file,'rb')
	indata = pickle.load(ifile)
	ifile.close()
	
	return indata
	
#loads the json file
#exits if problem with file
def load_file():
	args_in = get_input()
	
	if hasattr(args_in, "input_file") and (not (args_in.input_file == None)):
		if ((hasattr(args_in, "b")) and (args_in.b == True)):
			return load_bytes(args_in.input_file[0])
		else:
			return load_json(args_in.input_file[0])
	else:
		print("ERROR: could not open '" + args_in.input_file + "'")
		exit()
		
root = Tk()
my_gui = Graph_GUI(root)
my_gui.set_filename(get_input())
my_gui.add_data(load_graph_visualization_order(load_file()))
root.mainloop()