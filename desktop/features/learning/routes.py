from flask import render_template
from . import learning_bp


@learning_bp.route("/learning")
def learning():
    return render_template("learning.html")