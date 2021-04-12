from flask import Blueprint, request, make_response, render_template, session, redirect, flash, url_for, current_app
from babel import dates

from ..utils.utils import make_cache_key, get_value, restrict_value, sort_dict_list_by, take, offset, parse_int
from ..lib.account import load_account
from ..lib.favorites import get_favorite_artists, get_favorite_posts, add_favorite_post, add_favorite_artist, remove_favorite_post, remove_favorite_artist
from ..lib.security import is_password_compromised
from ..internals.cache.flask_cache import cache

favorites = Blueprint('favorites', __name__)

@favorites.route('/favorites', methods=['GET'])
def list():
    account = load_account()
    if account is None:
        flash('We now support accounts! Register for an account and your current favorites will automatically be added to your account.')
        return redirect(url_for('account.get_login'))

    props = {
        'currentPage': 'favorites'
    }
    base = request.args.to_dict()
    base.pop('o', None)

    favorites = []
    fave_type = get_value(request.args, 'type', 'artist')
    if fave_type == 'post':
        favorites = get_favorite_posts(account['id'])
        sort_field = restrict_value(get_value(request.args, 'sort'), ['faved_seq', 'published'], 'faved_seq')
    else:
        favorites = get_favorite_artists(account['id'])
        sort_field = restrict_value(get_value(request.args, 'sort'), ['faved_seq', 'updated'], 'updated')

    offset = parse_int(request.args.get('o'), 0)
    sort_asc = True if get_value(request.args, 'order') == 'asc' else False
    results = sort_and_filter_favorites(favorites, offset, sort_field, sort_asc)

    props['fave_type'] = fave_type
    props['sort_field'] = sort_field
    props['sort_asc'] = sort_asc

    response = make_response(render_template(
        'favorites.html',
        props = props,
        base = base,
        source = 'account',
        results = results,
        format_date = dates.format_date
    ), 200)
    response.headers['Cache-Control'] = 's-maxage=60'
    return response

@favorites.route('/favorites/post/<service>/<artist_id>/<post_id>', methods=['POST'])
def post_favorite_post(service, artist_id, post_id):
    account = load_account()
    if account is None:
        return redirect(url_for('account.get_login'))
    add_favorite_post(account['id'], service, artist_id, post_id)
    return '', 200

@favorites.route('/favorites/artist/<service>/<artist_id>', methods=['POST'])
def post_favorite_artist(service, artist_id):
    account = load_account()
    if account is None:
        return redirect(url_for('account.get_login'))
    add_favorite_artist(account['id'], service, artist_id)
    return '', 200

@favorites.route('/favorites/post/<service>/<artist_id>/<post_id>', methods=['DELETE'])
def delete_favorite_post(service, artist_id, post_id):
    account = load_account()
    if account is None:
        return redirect(url_for('account.get_login'))
    remove_favorite_post(account['id'], service, artist_id, post_id)
    return '', 200

@favorites.route('/favorites/artist/<service>/<artist_id>', methods=['DELETE'])
def delete_favorite_artist(service, artist_id):
    account = load_account()
    if account is None:
        return redirect(url_for('account.get_login'))
    remove_favorite_artist(account['id'], service, artist_id)
    return '', 200

def sort_and_filter_favorites(favorites, o, field, asc):
    favorites = sort_dict_list_by(favorites, field, not asc)
    return take(25, offset(o, favorites))
