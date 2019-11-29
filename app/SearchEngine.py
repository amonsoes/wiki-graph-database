import nltk
import math
import pickle

from collections import defaultdict

def dot (dictA, dictB):
    return sum([dictA.get(tok) * dictB.get(tok,0) for tok in dictA])

def normalized_tokens(text):
    return [tok.lower() for tok in nltk.word_tokenize(text)]

class DocCollection:

    def __init__(self, term_df, term_id, obj_doc):
        self.term_df = term_df
        self.term_id = term_id
        self.obj_doc = obj_doc

    @classmethod
    def from_dumpobj(cls, dumpobjs):
        term_df = defaultdict(int)
        term_id = defaultdict(set)
        obj_doc = {}
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

    def to_file(self):
        with open("./documentCollection", "wb") as p:
            pickle.dump(self, p)
        return "Done"


class SearchEngine:

    def __init__(self, doc_collection):
        self.doc_collection = doc_collection

    @classmethod
    def from_file(cls, path="./documentCollection"):
        with open(path, "rb") as p:
            doc_collection = pickle.load(p)
        return cls(doc_collection)

    def search(self, query, n=10):
        q_tokens = nltk.FreqDist(normalized_tokens(query))
        docs = self.doc_collection.docs_with_all_tokens(q_tokens.keys())
        doc_sims = [(name, self.doc_collection.cosine(q_tokens,doc)) for name, doc in docs]
        return sorted(doc_sims, key= lambda x: -x[1])[:n]

    def to_file(self):
        with open("./searchEngine", "wb") as p:
            pickle.dump(self, p)
        return "Done"

