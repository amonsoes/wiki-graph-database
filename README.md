HOW TO RUN THE APP

1.) in command line: set env variable $ FLASK_APP=parse_wikidumps.py

2.) (OPTIONAL) in command line: activate graph database with docker if dockerized

3.) in ./app/parse_wikidumps.py:
	
	-> configure build options for a graph database by changing the macros in the sector "build option macros"
	-> configure build options for a construction of a document collection by changing the macros in the sector "build option macros"
	-> if macros are set to FALSE, app will import existing pickle files to create the necessary objects to run the app

4.) in command line: enter $ flask run to run application. will be available on a local address


APP STRUCTURE

1.) Main script is "parse_wikidumps.py". 
2.) Script uses a DumpObject-class to extract meaningful parts of the wikipedia dump
3.) (OPTIONAL) use dump objects to build database
4.) (OPTIONAL) use dump objects to build a new document collection instead of importing the existing one
5.) Script uses a SearchEngine algorithm to look for relevant documents
6.) (OPTIONAL) change Macro in "routes.py" to include more/less search results
7.) Flask API is build and sends request to search engine, serach engine sends it back to the front end 


