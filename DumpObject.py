import re
import nltk

# for link extraction and content filtering
link_regex = re.compile(r"\[\[(.+?\|?.*?)\]\]")
filter_regex1 = re.compile(r"\{\{.*?\}\}")


def get_description(name, content):
    """ extracts a concise description from article. "steps" represent the clean-up process with regex string operations
    """
    des_start = nltk.sent_tokenize(content)[0]
    step_1 = re.sub(filter_regex1, "", des_start[des_start.find(name):])
    inserts = [i[:i.find("|")] if "|" in i else i for i in re.findall(link_regex, step_1)]
    try:
        step_2  = re.sub(link_regex, "%s", step_1) % tuple(inserts)
    except:
        step_2 = step_1
    step_3 = re.sub(r"\'{3}","",step_2)
    return step_3 if len(step_3) > 2 else "REDIRECT"

class DumpObject:

    def __init__(self, name, instance_id, description, links, category=None):
        self.name = name
        self.id = instance_id
        self.description = description
        self.links = links
        self.link_count = 0


    @classmethod
    def make_instance(cls, input):
        """cleans up the links for better further processing and then creates an instance"""
        links = [(i[:i.find("|")], i[i.find("|")+1:]) if "|" in i else (i, i) for i in re.findall(link_regex, input[1])]
        description = get_description(input[0], input[1]) if len(links) > 1 else "REDIRECT"
        instance_id = input[2]
        return cls(input[0], instance_id, description, links)