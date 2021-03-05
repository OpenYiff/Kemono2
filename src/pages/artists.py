from flask import Blueprint, request, make_response, render_template

from ..utils.utils import make_cache_key
from ..internals.cache.flask_cache import cache
from ..internals.database.database import get_cursor

artists = Blueprint('artists', __name__)

@artists.route('/artists')
@cache.cached(key_prefix=make_cache_key)
def get_artists():
    props = {
        'currentPage': 'artists'
    }
    base = request.args.to_dict()
    base.pop('o', None)

    q = request.args.get('q')
    commit = request.args.get('commit')
    service = request.args.get('service')
    sort_by = request.args.get('sort_by')
    order = request.args.get('order')
    offset = request.args.get('o')

    if not commit:
        results = {}
    else:
        query = "SELECT * FROM lookup "
        query += "WHERE name ILIKE %s "
        params = ('%' + q + '%',)
        if service:
            query += "AND service = %s "
            params += (service,)
        query += "AND service != 'discord-channel' "
        query += "ORDER BY " + {
            'indexed': 'indexed',
            'name': 'name',
            'service': 'service'
        }.get(sort_by, 'indexed')
        query += {
            'asc': ' asc ',
            'desc': ' desc '
        }.get(order, 'asc')
        query += "OFFSET %s "
        offset = offset if offset else 0
        params += (offset,)
        query += "LIMIT 25"

        cursor = get_cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()

        query2 = "SELECT COUNT(*) FROM lookup "
        query2 += "WHERE name ILIKE %s "
        params2 = ('%' + q + '%',)
        if service:
            query2 += "AND service = %s "
            params2 += (service,)
        query2 += "AND service != 'discord-channel'"
        cursor2 = get_cursor()
        cursor2.execute(query2, params2)
        results2 = cursor.fetchall()
        props["count"] = int(results2[0]["count"])
        
    response = make_response(render_template(
        'artists.html',
        props = props,
        results = results,
        base = base
    ), 200)
    response.headers['Cache-Control'] = 's-maxage=60'
    return response
