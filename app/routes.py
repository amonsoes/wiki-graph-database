from app import app
from flask import render_template, request
from .forms import SearchForm
from .parse_wikidumps import *

# ===== num of search results ====

NUM_RESULTS = 5

# ================================

app.config["SECRET_KEY"] = "1"
result = ""

@app.route('/')
@app.route('/index', methods=["GET", "POST"])
def index():
    form = SearchForm()
    if request.method == "POST":
        srch = request.form["search"] # request will be saved in this variable
        search_result = se.search(srch, NUM_RESULTS)
        result = process_search_result(search_result)
        return render_template("index.html", result=result, form=form)
    return render_template("index.html", form=form)

