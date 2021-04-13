from flask import Blueprint, request, make_response, render_template, session, redirect, url_for

import re

from ..utils.utils import sort_dict_list_by, offset, take, limit_int, parse_int
from ..internals.cache.flask_cache import cache
from ..internals.database.database import get_cursor
from ..lib.artist import get_all_non_discord_artists, get_artist, get_artist_post_count, get_artists_by_service, get_top_artists_by_faves, get_count_of_artists_faved
from ..lib.post import get_artist_posts, get_all_posts_by_artist, is_post_flagged, get_render_data_for_posts
from ..lib.favorites import is_artist_favorited
from ..lib.account import load_account

artists = Blueprint('artists', __name__)

@artists.route('/artists')
def list():
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
    offset = parse_int(request.args.get('o'), 0)
    limit = 25

    (results, total_count) = ([], 0)
    if commit is not None:
        (results, total_count) = get_artist_search_results(q, service, sort_by, order, offset, limit)
        props['display'] = 'search results'
    else:
        results = get_top_artists_by_faves(offset, limit)
        total_count = get_count_of_artists_faved()
        props['display'] = 'most popular artists'

    props['count'] = total_count
    props['limit'] = limit

    response = make_response(render_template(
        'artists.html',
        props = props,
        results = results,
        base = base
    ), 200)
    response.headers['Cache-Control'] = 's-maxage=60'
    return response

@artists.route('/<service>/user/<artist_id>')
def get(service, artist_id):
    cursor = get_cursor()
    props = {
        'currentPage': 'posts',
        'id': artist_id,
        'service': service,
        'session': session
    }
    base = request.args.to_dict()
    base.pop('o', None)
    base["service"] = service
    base["artist_id"] = artist_id

    offset = int(request.args.get('o') or 0)
    query = request.args.get('q')
    limit = limit_int(int(request.args.get('limit') or 25), 50)

    favorited = False
    account = load_account()
    if account is not None:
        favorited = is_artist_favorited(account['id'], service, artist_id)

    (posts, total_count) = ([], 0)
    if query is None:
        (posts, total_count) = get_artist_post_page(artist_id, service, offset, limit)
    else:
        (posts, total_count) = do_artist_post_search(artist_id, service, query, offset, limit)

    artist = get_artist(service, artist_id)
    if artist is None:
        return redirect(url_for('artists.list'))

    props['name'] = artist['name']
    props['count'] = total_count
    props['limit'] = limit
    props['favorited'] = favorited
    props['artist'] = artist
    props['display_data'] = make_artist_display_data(artist)

    (result_previews, result_attachments, result_flagged, result_after_kitsune, result_is_image) = get_render_data_for_posts(posts)
    
    response = make_response(render_template(
        'user.html',
        props = props,
        results = posts,
        base = base,
        result_previews = result_previews,
        result_attachments = result_attachments,
        result_flagged = result_flagged,
        result_after_kitsune = result_after_kitsune,
        result_is_image = result_is_image
    ), 200)
    response.headers['Cache-Control'] = 's-maxage=60'
    return response

def get_artist_search_results(q, service, sort_by, order, o, limit):
    if service:
        artists = get_artists_by_service(service)
    else:
        artists = get_all_non_discord_artists()

    page = []
    matches = []
    q_lower = q.lower()
    for artist in artists:
        if q_lower in artist['name'].lower():
            matches.append(artist)

    matches = sort_dict_list_by(matches, sort_by, order=='desc')

    return (take(limit, offset(o, matches)), len(matches))

def do_artist_post_search(id, service, search, o, limit):
    posts = get_all_posts_by_artist(id, service)

    matches = []
    for post in posts:
        if search in post['content'].lower() or search in post['title'].lower():
            matches.append(post)

    matches = sort_dict_list_by(matches, 'published', True)

    return (take(limit, offset(o, matches)), len(matches))

def get_artist_post_page(artist_id, service, offset, limit):
    posts = get_artist_posts(artist_id, service, offset, limit, 'published desc')
    total_count = get_artist_post_count(artist_id, service)
    return (posts, total_count)

def make_artist_display_data(artist):
    data = {}
    if artist['service'] == 'patreon':
        data['service'] = 'Patreon';
        data['proxy'] = '/proxy/patreon/user/' + str(artist['id']);
        data['href'] = 'https://www.patreon.com/user?u=' + str(artist['id']);
    elif artist['service'] == 'fanbox':
        data['service'] = 'Fanbox';
        data['href'] = 'https://www.pixiv.net/fanbox/creator/' + str(artist['id']);
    elif artist['service'] == 'gumroad':
        data['service'] = 'Gumroad';
        data['href'] = 'https://gumroad.com/' + str(artist['id']);
    elif artist['service'] == 'subscribestar':
        data['service'] = 'SubscribeStar';
        data['href'] = 'https://subscribestar.adult/' + str(artist['id']);
    elif artist['service'] == 'dlsite':
        data['service'] = 'DLsite';
        data['href'] = 'https://www.dlsite.com/eng/circle/profile/=/maker_id/' + str(artist['id']);

    return data
