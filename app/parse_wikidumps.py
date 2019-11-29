import xml.etree.ElementTree as et
import py2neo
import os
import pickle

from app import app
from py2neo import Graph
from py2neo.data import Node, Relationship
from collections import defaultdict
from DumpObject import DumpObject
from .SearchEngine import DocCollection, SearchEngine


# ========== build option macros ============

BUILD_DATABASE = False
RUN_DUMP_EXTRACTION = False


# ========== macros for xml-file specific vars ==========
# TODO: make file-invariant

DUMP_FILE = "./enwiki-latest-pages-articles-multistream1.xml-p10p30302"

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


link_pair_cntr = defaultdict(int)


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


def all_xml_trees(path,ls):
    """load and parse all xml files TODO: deal with xml files without the suffix -> mime type test?
    """
    return [et.parse(file) for file in files for _,_,files in os.walk(path) if file.endswith(".xml")]

def single_xml_tree(path):
    return et.parse(path)


# ========= xml tree operations =========


def zip_attributes(root, title, text, id):
    """ get attributes of an undefined list of tags
    """
    titles = [x.text for x in root.iter(title)]
    texts = [x.text for x in root.iter(text)]
    ids = [x.find(ID_TAG).text for x in root.iter(id)]
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
    return [DumpObject.make_instance(i) for i in ls]

def remove_redirects(objects):
    """ if dump obj only redirects to a page, remove that obj and increase the link count of it's target by 1
    """
    filterlist = []
    for obj in objects:
        if obj.description == "REDIRECT":
            if obj.links:
                target = obj.links[0][0]
                for subobj in objects:
                    if subobj.name == target:
                        subobj.link_count += 1
            filterlist.append(obj)
    return filter(lambda x: x not in filterlist, objects)

def to_file(list_of_objects, path="./dumpObjects"):
    with open(path, "wb") as p:
        pickle.dump(list_of_objects,p)
    return "Done"

def from_file(path="./dumpObjects"):
    with open(path, "rb") as p:
        list_of_objects = pickle.load(p)
    return list_of_objects


# ======== turn to nodes, make relations =======


def make_all_relations(nodes):
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

    tree = single_xml_tree(DUMP_FILE)
    tree_root = tree.getroot()
    matrix = zip_attributes(tree_root,TITLE_TAG, TEXT_TAG, PAGE_TAG)
    objs = list(remove_redirects(make_dump_object(matrix))) # slice matrix to reduce testing time
    to_file(objs)
    collection = DocCollection.from_dumpobj(objs)
    collection.to_file()
    se = SearchEngine(collection)

else:

    objs = from_file()
    se = SearchEngine.from_file()


if BUILD_DATABASE:

    nodes = make_node(objs)
    make_all_relations(nodes)

else:

    make_all_relations(objs)

output_aggregated_relations(link_pair_cntr)




