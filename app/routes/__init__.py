from flask import Blueprint

main = Blueprint('main', __name__)

from . import policy_processing_routes 