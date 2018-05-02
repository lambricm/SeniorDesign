## Contents
* General requirements
* Collecting Twitter Data
* Collecting Reddit Data
* Creating graph from data
* Viewing node data
* Using the plot function
* FAQ

## General Requirements

* Python
* Python Modules Used (Note: These modules might not initially be installed)
     * Pickle
     * Numpy
     * NetworkX
     * NLTK
     * praw
     * Tweepy
     * Matplotlib
     * tkinter

As a note, this program uses Python (We're using 3.6, find it [here](https://www.python.org/downloads/). If you don't know what python version you have installed, find your version by simply typing "Python" into a terminal.

For installing the python packages it is recommended to use pip. See [this link](https://packaging.python.org/tutorials/installing-packages/) for more information.

## Collecting Twitter Data

To collect twitter data, use the file 'getTweetData.py'.

### Things you will need

* Access data for twitter - an access token, access token secret, consumer key, and consumer secret. This has to be obtained through twitter (Find info on how to get these [here](https://www.slickremix.com/docs/how-to-get-api-keys-and-tokens-for-twitter/). After obtaining the data, the variables in the file (access_tokens, access_token_secret, consumer_key, and consumer_secret) should be replaced with these. While our access keys are currently in the file, their validity in the future will NOT be guaranteed.
* Either
     * A Keyword file - a file with keyword data used to obtain tweets (See below for formatting).
     * OR a tweepy input file path retrieved from a different run
* an output file path. This will default to './twitter_data.txt'
* [Optional] - Number of tweets to retain for graphing. Defaults to 15

### Keyword File Format

The keyword file format is in a simple json format.
Format:

```
{
 "key":"desired_descriptor",
 "keywords":["keyword_1","keyword_2","keyword_3"...]
}
```

NOTE: For the best results, Keywords should be hashtags, user tags, or a single keyword. Many keywords often results in disjointed subsets that cannot be properly graphed with our algorithm.

### Running the Program

The program can be run via this format:

```
./getTweetData.py [-k <keyword_path.txt>] [-o <output_path.txt>] [-o_tw] [-o_nx] [-i <input file path> ] [-num_tw <num_nodes>] 

-k -> file where the keyword(s) (formatted as in the section above)
-o -> output file path - either for tweepy or networkx file
-o_tw -> flag to indicate tweepy output
-o_nx -> flag to indicate networkx output
-i -> input file path (tweepy files ONLY)
-num_tw -> number of nodes to output for the networkx file
```

### Output

Either a tweepy or networkx binary file.

## Collecting Reddit Data

To collect Reddit data, use the file 'getRedditData.py'.

### Things you will need

* Access data for Reddit - a client id, client secret, password, user agent description, and username. This has to be obtained through Reddit. Find info on these [here](https://praw.readthedocs.io/en/latest/getting_started/authentication.html) and check out the Reddit application page (must be logged in) [here](https://www.reddit.com/prefs/apps/). After obtaining the data, the variables in the file (client_id, client_secret, password, user_+agent, username) should be replaced with these. While our access data (for a throwaway acccount) is currently in the file, their validity in the future will NOT be guaranteed.
* A Keyword file - a file with keyword data used to obtain tweets (See below for formatting).
* an output file path. This will default to './reddit_data.txt'
* [Optional] - Number of nodes to retain for graphing. Defaults to 15

### Keyword File Format

The keyword file format is in a simple json format.
Format:

```
{
 "users":["user_1","user_2","user_3"...],
 "subreddits":["subreddit_1","subreddit_2","subreddit_3"...]
}
```

NOTE: For the best results, use less subreddits/users. Many keywords often results in disjointed subsets that cannot be properly graphed with our algorithm.

### Running the Program

The program can be run via this format:

```
./getRedditData.py [-k <keyword_path.txt>] [-o <output_path.txt>] [-o_nx] [-num_tw <num_nodes>] 

-k -> file where the keyword(s) (formatted as in the section above)
-o -> output file path
-o_nx -> flag to indicate networkx output
-num_tw -> number of nodes to output for the networkx file
```

### Output

A networkx binary file.

## Graphing the Networkx File

If you have already retrieved data an it is residing in a file, all you need to do is run it through the 'getGraphData.py' script.

### Running the Program - Graph

The program can be run via this format:

```
./getGraphData.py [-i <input_file_path>] [-g_nx] [-g_ml]

-i -> binary networkx graph file
-g_nx -> flag to output data via generic networkx graphing formula
-g_ml -> flag to output data via matplotlib default graphing

Note: If you do not give it an option, it will not graph. -g_nx is reccommended - it is the most clean. Other graphing methods can be added
```

### Running the Program - Node Data

If you output a networkx binary file, a JSON file describing the nodes should have also been output as:

```
your_path/viewable_data_<original_file_name>.txt'
```

You will need this file to view the node data. The labels in the graph will match the node numbers in the json file.

The program can be run via this format:

```
./graph_gui.py [-i <input_file_path>] -b

-i -> networkx graph file
-b -> uses 'pickle' to interpret as binary file

Note: ALL of our output files from the Reddit/Twitter data collections should be in the binary format so be sure to use -b. This program can be used to view non-binary JSON files, but we use binary because there are a lot of characters that can't be easily output/input by python unless they are in binary form.

## FAQ

Q: Why do I have to collect the twitter/reddit data using my own keys? Can't I use yours?

A: Twitter & reddit has each application connected to an account. Overusing the same key(s) may reduce the amount of data one can collect. Using your own keys is for the best. Our keys are currently in the code because it's easy for our team to share but the twitter/reddit account attached to the program currently will be removed in the future.