from app import app
from flask import render_template, request
from .forms import SearchForm
from .parse_wikidumps import *
from .SearchEngine import SearchEngine

# ===== num of search results ====

NUM_RESULTS = 5

# ================================

app.config["SECRET_KEY"] = "1"
result = ""

se = SearchEngine()
print("reading...")
DumpObject.link_dict = import_aggregated_relations()
print("finished")


@app.route('/')
@app.route('/index', methods=["GET", "POST"])
def index():
    form = SearchForm()
    if request.method == "POST":
        query = request.form["search"] # request will be saved in this variable
        result = se.disambiguate(query, DumpObject.link_dict, NUM_RESULTS)
        return render_template("index.html", result=result, form=form)
    return render_template("index.html", form=form)

