from flask import Blueprint, request, make_response, render_template

from ..utils.utils import make_cache_key
from ..internals.cache.flask_cache import cache

home = Blueprint('home', __name__)

@home.route('/')
@cache.cached(key_prefix=make_cache_key)
def get_home():
    props = {}
    base = request.args.to_dict()
    base.pop('o', None)
    response = make_response(render_template(
        'home.html',
        props = props,
        base = base
    ), 200)
    response.headers['Cache-Control'] = 's-maxage=60'
    return response
