import xml.etree.ElementTree as et
import py2neo
import os
import pickle

#from app import app
from py2neo import Graph
from py2neo.data import Node, Relationship
from collections import defaultdict
from DumpObject import DumpObject
from SearchEngine import DocCollection, SearchEngine
from scipy.sparse import lil_matrix



# ========== build option macros ============

BUILD_DATABASE = False
RUN_DUMP_EXTRACTION = True


# ========== macros for xml-file specific vars ==========
# TODO: make file-invariant

DUMP_DIR = "./files"

TITLE_TAG = "{http://www.mediawiki.org/xml/export-0.10/}title"
TEXT_TAG = "{http://www.mediawiki.org/xml/export-0.10/}text"
PAGE_TAG = "{http://www.mediawiki.org/xml/export-0.10/}page"
ID_TAG = "{http://www.mediawiki.org/xml/export-0.10/}id"


# =========== connection set up ============

if BUILD_DATABASE:

    GRAPH_ADDRESS = "http://localhost:7474/" # replace to access remote database
    GRAPH_AUTH = ("neo4j", "test") # replace with remote database authetification

    graph = Graph(GRAPH_ADDRESS, user=GRAPH_AUTH[0], password=GRAPH_AUTH[1])
    graph.delete_all()


# ======= process link counts and search results ======


def process_search_result(result):
    dct = import_aggregated_relations()
    unranked_list = []
    for page_name, _ in result:
        total = 0
        for key, val in  dct.items():
            if key[1] == page_name:
                total += val
        unranked_list.append((page_name,total))
    return ["PAGE: {}, LINKS: {}".format(x,y) for x,y in sorted(unranked_list, key=lambda x: x[1], reverse=True)]



# ======== load xml =========

def fast_iter(root):
    """ TODO
    """
    pass

def process_file(file):
    print(" START EXTRACTION FOR FILE " ,file)
    root = et.parse("./files/"+file).getroot()
    print("ROOT PARSED...")
    objs = make_dump_object(zip_attributes(root, TITLE_TAG, TEXT_TAG, PAGE_TAG)[:30]) # slice to reduce testing time # list
    print("BUILDING OBJS FINISHED...")
    print(DumpObject.mat)
    del root
    collection = DocCollection.from_dumpobj(objs)
    print("COLLECTION BUILT...")
    collection.to_file()
    del collection
    if BUILD_DATABASE:
        nodes = make_node(objs)
        make_all_relations(nodes)
    else:
        make_all_relations(objs)
    del objs



def xml_to_collections(path):
    """load file to database extension of the search engine
    """
    for _,_,files in os.walk(path):
        for file in files:
            process_file(file)
    


def single_xml_tree(path):
    return et.parse(path)


# ========= xml tree operations =========


def zip_attributes(root, title, text, id):
    """ get attributes of an undefined list of tags
    """
    print("ENTERED ROOT ITERATION...")
    titles = [x.text for x in root.iter(title)]
    texts = [x.text for x in root.iter(text)]
    ids = [x.find(ID_TAG).text for x in root.iter(id)]
    DumpObject.mat = lil_matrix(len(titles),len(titles))
    print("ROOT ITER FINISHED")
    return [i for i in zip(titles,texts,ids)]


# ========= link counts file I/O =======

if BUILD_DATABASE:

    def rel_to_file(origin_text, target, path="./links.txt"):
        link_pair_cntr[(origin_text,target["name"],target["id"])] += 1
        with open(path, "a", encoding="utf-8") as f:
            f.write("{}\t{}\t{}\n".format(origin_text, target["name"], target["id"]))
        return None

else:

    def rel_to_file(origin_text, target, path="./links.txt"):
        link_pair_cntr[(origin_text,target.name,target.id)] += 1
        with open(path, "a", encoding="utf-8") as f:
            f.write("{}\t{}\t{}\n".format(origin_text, target.name, target.id))
        return None

def output_aggregated_relations(dict, path="./links_aggregated.txt"):
    with open(path, "a", encoding="utf-8") as f:
        for key,val in dict.items():
            f.write("{}\t{}\t{}\t{}\n".format(key[0], key[1], key[2], val))

def import_aggregated_relations(path="./links_aggregated.txt"):
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.split("\t") for line in f.readlines()]
    return {tuple(i[:2]):int(i[-1]) for i in lines}


# ========= make dump objects ==========


def make_dump_object(ls):
    """ turn an 2dim list of attributes into a list of dumpObjects
    """
    return list(filter(lambda x: x != None, [DumpObject.make_instance(i) for i in ls if i[0].count(":") == 0]))


# TODO: TEST IF YOU ACTUALLY NEED TO EXPORT THE OBJS

counter = 0
def to_file(list_of_objects, path="./bin/objs/dumpObjects"+str(counter)):
    global counter
    with open(path, "wb") as p:
        pickle.dump(list_of_objects,p)
    counter += 1
    return "Done"

def from_file(file):
    with open(file, "rb") as p:
        list_of_objects = pickle.load(p)
    return list_of_objects

def from_dir(path="./bin/objs"):
    objs = []
    for _,_,files in os.walk(path):
        for file in files:
            objs.extend(from_file(file))
    return objs



# ======== turn to nodes, make relations =======


def make_all_relations(nodes):
    print("START BUILDING RELATIONS")
    for n in nodes:
        for x in nodes:
            make_relation(n, x)
    print("RELATIONS ESTABLISHED")
    return None

if BUILD_DATABASE:

    def make_node(objects):
        """ integrate objects into graph
        """
        object_list = [Node("Article", name=obj.name, id=obj.id, description=obj.description, links=[i[0] for i in obj.links], link_text=[i[1] for i in obj.links], link_count=obj.link_count) for obj in objects]
        for i in object_list:
            graph.create(i)
        return object_list

    def make_relation(origin, target):
        """ iterates through links of origin to find link to target TODO: find method to make lookup time constant
        """
        for ind, link in enumerate(origin["links"]):
            if link == target["name"]:
                target["link_count"] += 1
                rel_to_file(origin["link_text"][ind],target)
                return graph.create(Relationship(origin, "HAS_LINK", target))
        return None

else:

    def make_relation(origin, target):
        """ iterates through links of origin to find link to target TODO: find method to make lookup time constant
        """
        for ind, link in enumerate([i[0] for i in origin.links]):
            if link == target.name:
                target.link_count += 1
                rel_to_file(origin.links[ind][1],target)
        return None


# ========= main ===========


if RUN_DUMP_EXTRACTION:

    link_pair_cntr = defaultdict(int)
    xml_to_collections(DUMP_DIR)
    output_aggregated_relations(link_pair_cntr)


else:

    link_pair_cntr = import_aggregated_relations()


if BUILD_DATABASE:

    nodes = make_node(objs)
    make_all_relations(nodes)




