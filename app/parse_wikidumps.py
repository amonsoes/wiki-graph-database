import xml.etree.ElementTree as et
import py2neo
import os
import pickle

from app import app
from py2neo import Graph
from py2neo.data import Node, Relationship
from .DumpObject import DumpObject
from .SearchEngine import DocCollection



# ========== build option macros ============


BUILD_DATABASE = False
RUN_DUMP_EXTRACTION = False


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
    #graph.delete_all() # enter danger zone by uncommenting


# ======= process link counts and search results ======


def process_search_result(result):
    unranked_list = []
    for page_name, _ in result:
        total = 0
        for key in DumpObject.link_dict:
            if key == page_name:
                total += DumpObject.link_dict[key]
        unranked_list.append((page_name,total))
    return ["PAGE: {}, LINKS: {}".format(x,y) for x,y in sorted(unranked_list, key=lambda x: x[1], reverse=True)]


# ======== load xml =========


def process_file(file):
    print(" START EXTRACTION FOR FILE " ,file)
    root = et.parse("./files/"+file).getroot()
    print("ROOT PARSED...")
    objs = make_dump_object(zip_attributes(root, TITLE_TAG, TEXT_TAG, PAGE_TAG)) # slice to reduce testing time # list
    print("BUILDING OBJS FINISHED...")
    del root
    collection = DocCollection.from_dumpobj(objs)
    print("COLLECTION BUILT...")
    collection.to_file()
    del collection
    if BUILD_DATABASE:
        nodes = make_node(objs)
    else:
        make_all_relations(DumpObject.link_dict)
    del objs


def xml_to_collections(path):
    """load file to database extension of the search engine
    """
    for _, _, files in os.walk(path):
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
    print("ROOT ITER FINISHED")
    return [i for i in zip(titles,texts,ids)]


# ========= link counts file I/O =======


if BUILD_DATABASE:

    def rel_to_file(origin_text, target, path="./links.txt"):
        DumpObject.link_dict[(origin_text,target["name"], target["id"])] += 1
        with open(path, "a", encoding="utf-8") as f:
            f.write("{}\t{}\t{}\n".format(origin_text, target["name"], target["id"]))
        return None

else:

    def rel_to_file(origin_text, target, path="./links.txt"):
        with open(path, "a", encoding="utf-8") as f:
            f.write("{}\t{}\t{}\n".format(origin_text, target, DumpObject.id_dict.get(target, None)))
        return None


def output_aggregated_relations(dic, path="./bin/links_aggregated"):
    with open(path, "wb") as b:
        pickle.dump(dic, b)


def import_aggregated_relations(path="./bin/links_aggregated"):
    with open(path, "rb") as b:
        d = pickle.load(b)
    return d


# ========= make dump objects ==========


def make_dump_object(ls):
    """ turn an 2dim list of attributes into a list of dumpObjects
    """
    return list(filter(lambda x: x != None, [DumpObject.make_instance(i) for i in ls if i[0].count(":") == 0]))


# ======== turn to nodes, make relations =======


def make_all_relations(dic):
    print("START BUILDING RELATIONS")
    for key, val in dic.items():
        for n in range(val):
            rel_to_file(key[0], key[1])
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


# ========= main ===========


if __name__ == '__main__':

    if RUN_DUMP_EXTRACTION:

        xml_to_collections(DUMP_DIR)
        output_aggregated_relations(DumpObject.link_dict)

    else:
        print("reading...")
        DumpObject.link_dict = import_aggregated_relations()
        print("finished reading")
