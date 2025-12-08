
from flask import Blueprint

# Create blueprint for robot feature
learning_bp = Blueprint(
    'learning',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/learning/static'
)

# Import routes
from . import routes