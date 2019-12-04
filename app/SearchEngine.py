import nltk
import math
import pickle
import os

from collections import defaultdict

def dot (dictA, dictB):
    return sum([dictA.get(tok) * dictB.get(tok,0) for tok in dictA])

def normalized_tokens(text):
    return [tok.lower() for tok in nltk.word_tokenize(text)]

def open_collection(path):
    with open(path, "rb") as p:
        doc_collection = pickle.load(p)
    return doc_collection


class DocCollection:

    id = 0

    def __init__(self, term_df, term_id, obj_doc):
        self.term_df = term_df # defdict(int)
        self.term_id = term_id # defdict(set)
        self.obj_doc = obj_doc # dict
        self.id = DocCollection.id
        DocCollection.id += 1

    @classmethod
    def from_dumpobj(cls, dumpobjs):
        term_df = defaultdict(int)
        term_id = defaultdict(set)
        obj_doc = {}
        if dumpobjs:
            for obj in dumpobjs:
                obj_doc[obj] = nltk.FreqDist(normalized_tokens(obj.description))
                for tok in normalized_tokens(obj.description):
                    term_df[tok] += 1
                    term_id[tok].add(obj)
        return cls(term_df,term_id,obj_doc)

    def docs_with_all_tokens(self, tokens):
        obj_for_each_token = [self.term_id[tok] for tok in tokens]
        docids = set.intersection(*obj_for_each_token)
        return [(obj.name, self.obj_doc[obj]) for obj in docids]

    def tfidf(self, counts):
        N = len(self.obj_doc.keys())
        return {tok: tf * math.log(N / self.term_df[tok]) for tok, tf in counts.items() if tok in self.term_df}

    def cosine(self, dictA, dictB):
        weightedA = self.tfidf(dictA)
        weightedB = self.tfidf(dictB)
        dotAB = dot(weightedA, weightedB)
        valA = math.sqrt(dot(weightedA, weightedA))
        valB = math.sqrt(dot(weightedB, weightedB))
        return dotAB / (valA *valB) if valA *valB != 0 else 0
    
    def extend(self,dumpobjs):
        for obj in dumpobjs:
            self.obj_doc[obj] = nltk.FreqDist(normalized_tokens(obj.description))
            for tok in normalized_tokens(obj.description):
                self.term_df[tok] += 1
                self.term_id[tok].add(obj)

    def to_file(self):
        with open("./bin/collections/documentCollection" + str(self.id), "wb") as p:
            pickle.dump(self, p)
        return "Done"


class SearchEngine:

    def __init__(self, doc_collection=None):
        self.doc_collection = doc_collection

    @classmethod
    def from_file(cls, path):
        return cls(open_collection(path))

    def search(self, query, n=10):
        q_tokens = nltk.FreqDist(normalized_tokens(query))
        all_doc_sims = []
        for _,_,files in os.walk("./bin/collections"):
            for file in files:
                self.doc_collection = open_collection("./bin/collections/"+file)
                docs = self.doc_collection.docs_with_all_tokens(q_tokens.keys())
                doc_sims = [(name, self.doc_collection.cosine(q_tokens,doc)) for name, doc in docs]
                all_doc_sims.extend(doc_sims)
                self.doc_collection = None
        return sorted(all_doc_sims, key=lambda x: -x[1])[:n]


