from flask import Blueprint, jsonify

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return jsonify({'message': 'Insurance Policy Parser API', 'status': 'running'})

from . import policy_processing_routes
from . import api_adapter_routes 