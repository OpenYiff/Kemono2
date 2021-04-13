import re
import random
import string
import json
import pytz
from feedgen.feed import FeedGenerator
from urllib.parse import urlencode
from datetime import datetime, timedelta
from os import getenv, stat, rename, makedirs
from os.path import join, dirname, isfile, splitext
from shutil import move

from PIL import Image
from python_resumable import UploaderFlask
from flask import Flask, jsonify, render_template, render_template_string, request, redirect, url_for, send_from_directory, make_response, g, abort, session, Blueprint
from werkzeug.utils import secure_filename
from slugify import slugify_filename
import requests
from markupsafe import Markup
from bleach.sanitizer import Cleaner
from hashlib import sha256

from ..internals.database.database import get_cursor
from ..internals.cache.flask_cache import cache
from ..utils.utils import make_cache_key, relative_time, delta_key, allowed_file, limit_int

legacy = Blueprint('legacy', __name__)

@legacy.route('/thumbnail/<path:path>')
def thumbnail(path):
    try:
        image = Image.open(join(getenv('DB_ROOT'), path))
        image = image.convert('RGB')
        image.thumbnail((800, 800))
        makedirs(dirname(join(getenv('DB_ROOT'), 'thumbnail', path)), exist_ok=True)
        image.save(join(getenv('DB_ROOT'), 'thumbnail', path), 'JPEG', quality=60)
        return redirect(join('/', 'thumbnail', path), code=302)
    except Exception as e:
        return f"The file you requested could not be converted. Error: {e}", 404

@legacy.route('/artists/updated')
@cache.cached(key_prefix=make_cache_key)
def updated_artists():
    cursor = get_cursor()
    props = {
        'currentPage': 'artists'
    }
    query = 'WITH "posts" as (select "user", "service", max("added") from "posts" group by "user", "service" order by max(added) desc limit 50) '\
        'select "user", "posts"."service" as service, "lookup"."name" as name, "max" from "posts" inner join "lookup" on "posts"."user" = "lookup"."id"'
    cursor.execute(query)
    results = cursor.fetchall()
    response = make_response(render_template(
        'updated.html',
        props = props,
        results = results
    ), 200)
    response.headers['Cache-Control'] = 'max-age=60, public, stale-while-revalidate=2592000'
    return response

@legacy.route('/artists/blocked')
def blocked():
    props = {
        'currentPage': 'artists'
    }

    results = []
    if session.get('blocked'):
        for user in session['blocked']:
            service = user.split(':')[0]
            user_id = user.split(':')[1]
            
            cursor2 = get_cursor()
            query2 = "SELECT * FROM lookup WHERE id = %s AND service = %s"
            params2 = (user_id, service)
            cursor2.execute(query2, params2)
            results2 = cursor2.fetchone()
            
            results.append({
                "name": results2['name'] if results2 else "",
                "service": service,
                "user": user_id
            })
    
    response = make_response(render_template(
        'blocked.html',
        props = props,
        results = results,
        session = session
    ), 200)
    response.headers['Cache-Control'] = 'no-store, max-age=0'
    return response

@legacy.route('/posts')
def posts():
    cursor = get_cursor()
    props = {
        'currentPage': 'posts'
    }
    base = request.args.to_dict()
    base.pop('o', None)

    limit = limit_int(request.args.get('limit') or 25, 50)
    offset = int(request.args.get('o') or 0)

    props['limit'] = limit

    if not request.args.get('q'):
        query = "SELECT * FROM posts "
        params = ()

        query += "ORDER BY added desc "
        query += "OFFSET %s "
        params += (offset,)
        query += "LIMIT %s"
        params += (limit,)
    else:
        query = "SET LOCAL enable_indexscan = off; "
        query += "SELECT * FROM posts WHERE to_tsvector('english', content || ' ' || title) @@ websearch_to_tsquery(%s) "
        params = (request.args.get('q'),)

        query += "ORDER BY added desc "
        offset = request.args.get('o') if request.args.get('o') else 0
        query += "OFFSET %s "
        params += (offset,)
        limit = request.args.get('limit') if request.args.get('limit') and request.args.get('limit') <= 50 else 25
        query += "LIMIT %s"
        params += (limit,)
    
    cursor.execute(query, params)
    results = cursor.fetchall()

    cursor2 = get_cursor()
    query2 = "SELECT COUNT(*) FROM posts "
    params2 = ()
    if request.args.get('q'):
        query2 += "WHERE to_tsvector('english', content || ' ' || title) @@ websearch_to_tsquery(%s)"
        params2 += (request.args.get('q'),)
    cursor2.execute(query2, params2)
    results2 = cursor2.fetchall()
    props["count"] = int(results2[0]["count"])

    result_previews = []
    result_attachments = []
    result_flagged = []
    result_after_kitsune = []
    result_is_image = []
    for post in results:
        if post['added'] > datetime(2020, 12, 22, 0, 0, 0, 0):
            result_after_kitsune.append(True)
        else:
            result_after_kitsune.append(False)
        previews = []
        attachments = []
        if len(post['file']):
            if re.search("\.(gif|jpe?g|jpe|png|webp)$", post['file']['path'], re.IGNORECASE):
                result_is_image.append(True)
                previews.append({
                    'type': 'thumbnail',
                    'path': post['file']['path'].replace('https://kemono.party','')
                })
            else:
                result_is_image.append(False)
                attachments.append({
                    'path': post['file']['path'],
                    'name': post['file'].get('name')
                })
        else:
            result_is_image.append(False)
        
        if len(post['embed']):
            previews.append({
                'type': 'embed',
                'url': post['embed']['url'],
                'subject': post['embed']['subject'],
                'description': post['embed']['description']
            })
        for attachment in post['attachments']:
            if re.search("\.(gif|jpe?g|jpe|png|webp)$", attachment['path'], re.IGNORECASE):
                previews.append({
                    'type': 'thumbnail',
                    'path': attachment['path'].replace('https://kemono.party','')
                })
            else:
                attachments.append({
                    'path': attachment['path'],
                    'name': attachment['name']
                })

        cursor4 = get_cursor()
        query4 = "SELECT * FROM booru_flags WHERE id = %s AND \"user\" = %s AND service = %s"
        params4 = (post['id'], post['user'], post['service'])
        cursor4.execute(query4, params4)
        results4 = cursor4.fetchall()

        result_flagged.append(True if len(results4) > 0 else False)
        result_previews.append(previews)
        result_attachments.append(attachments)
    
    response = make_response(render_template(
        'posts.html',
        props = props,
        results = results,
        base = base,
        result_previews = result_previews,
        result_attachments = result_attachments,
        result_flagged = result_flagged,
        result_after_kitsune = result_after_kitsune,
        result_is_image = result_is_image
    ), 200)
    response.headers['Cache-Control'] = 'no-store, max-age=0'
    return response

@legacy.route('/posts/upload')
def upload_post():
    props = {
        'currentPage': 'posts'
    }
    response = make_response(render_template(
        'upload.html',
        props=props
    ), 200)
    response.headers['Cache-Control'] = 's-maxage=60'
    return response

# TODO: /:service/user/:id/rss

@legacy.route('/<service>/user/<id>/rss')
def user_rss(service, id):
    cursor = get_cursor()
    query = "SELECT * FROM posts WHERE \"user\" = %s AND service = %s "
    params = (id, service)

    query += "ORDER BY added desc "
    query += "LIMIT 10"

    cursor.execute(query, params)
    results = cursor.fetchall()

    cursor3 = get_cursor()
    query3 = "SELECT * FROM lookup WHERE id = %s AND service = %s"
    params3 = (id, service)
    cursor3.execute(query3, params3)
    results3 = cursor.fetchall()
    name = results3[0]['name'] if len(results3) > 0 else ''

    fg = FeedGenerator()
    fg.title(name)
    fg.description('Feed for posts from ' + name + '.')
    fg.id(f'http://{request.headers.get("host")}/{service}/user/{id}')
    fg.link(href=f'http://{request.headers.get("host")}/{service}/user/{id}')
    fg.generator(generator='Kemono')
    fg.ttl(ttl=40)

    for post in results:
        fe = fg.add_entry()
        fe.title(post['title'])
        fe.id(f'http://{request.headers.get("host")}/{service}/user/{id}/post/{post["id"]}')       
        fe.link(href=f'http://{request.headers.get("host")}/{service}/user/{id}/post/{post["id"]}')
        fe.content(content=post["content"])
        fe.pubDate(pytz.utc.localize(post["added"]))

    response = make_response(fg.atom_str(pretty=True), 200)
    response.headers['Content-Type'] = 'application/rss+xml'
    return response

@legacy.route('/discord/server/<id>')
def discord_server(id):
    response = make_response(render_template(
        'discord.html'
    ), 200)
    response.headers['Cache-Control'] = 's-maxage=60'
    return response

@legacy.route('/board')
def board():
    props = {
        'currentPage': 'board'
    }
    response = make_response(render_template(
        'board_list.html',
        props = props
    ), 200)
    response.headers['Cache-Control'] = 'max-age=60, public, stale-while-revalidate=2592000'
    return response

@legacy.route('/requests')
def requests_list():
    props = {
        'currentPage': 'requests'
    }
    base = request.args.to_dict()
    base.pop('o', None)

    if not request.args.get('commit'):
        query = "SELECT * FROM requests "
        query += "WHERE status = 'open' "
        query += "ORDER BY votes desc "
        query += "OFFSET %s "
        offset = request.args.get('o') if request.args.get('o') else 0
        params = (offset,)
        query += "LIMIT 25"
    else:
        query = "SELECT * FROM requests "
        query += "WHERE title ILIKE %s "
        params = ('%' + request.args.get('q') + '%',)
        if request.args.get('service'):
            query += "AND service = %s "
            params += (request.args.get('service'),)
        query += "AND service != 'discord' "
        if request.args.get('max_price'):
            query += "AND price <= %s "
            params += (request.args.get('max_price'),)
        query += "AND status = %s "
        params += (request.args.get('status'),)
        query += "ORDER BY " + {
            'votes': 'votes',
            'created': 'created',
            'price': 'price'
        }.get(request.args.get('sort_by'), 'votes')
        query += {
            'asc': ' asc ',
            'desc': ' desc '
        }.get(request.args.get('order'), 'desc')
        query += "OFFSET %s "
        offset = request.args.get('o') if request.args.get('o') else 0
        params += (offset,)
        query += "LIMIT 25"

    cursor = get_cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()

    response = make_response(render_template(
        'requests_list.html',
        props = props,
        results = results,
        base = base
    ), 200)
    return response

@legacy.route('/requests/<id>/vote_up', methods=['POST'])
def vote_up(id):
    ip = request.headers.getlist("X-Forwarded-For")[0].rpartition(' ')[-1] if 'X-Forwarded-For' in request.headers else request.remote_addr
    query = "SELECT * FROM requests WHERE id = %s"
    params = (id,)

    cursor = get_cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()

    props = {
        'currentPage': 'requests',
        'redirect': request.args.get('Referer') if request.args.get('Referer') else '/requests'
    }

    if not len(result):
        abort(404)
    hash = sha256(ip.encode()).hexdigest()
    if hash in result.get('ips'):
        props['message'] = 'You already voted on this request.'
        return make_response(render_template(
            'error.html',
            props = props
        ), 401)
    else:
        record = result.get('ips')
        record.append(hash)
        query = "UPDATE requests SET votes = votes + 1,"
        query += "ips = %s "
        params = (record,)
        query += "WHERE id = %s"
        params += (id,)
        cursor.execute(query, params)

        return make_response(render_template(
            'success.html',
            props = props
        ), 200)

@legacy.route('/requests/new')
def request_form():
    props = {
        'currentPage': 'requests'
    }

    response = make_response(render_template(
        'requests_new.html',
        props = props
    ), 200)
    response.headers['Cache-Control'] = 'max-age=60, public, stale-while-revalidate=2592000'
    return response

@legacy.route('/requests/new', methods=['POST'])
def request_submit():
    props = {
        'currentPage': 'requests',
        'redirect': request.args.get('Referer') if request.args.get('Referer') else '/requests'
    }

    ip = request.headers.getlist("X-Forwarded-For")[0].rpartition(' ')[-1] if 'X-Forwarded-For' in request.headers else request.remote_addr

    if not request.form.get('user_id'):
        props['message'] = 'You didn\'t enter a user ID.'
        return make_response(render_template(
            'error.html',
            props = props
        ), 400)

    if getenv('TELEGRAMTOKEN'):
        snippet = ''
        with open('views/requests_new.html', 'r') as file:
            snippet = file.read()

        requests.post(
            'https://api.telegram.org/bot' + getenv('TELEGRAMTOKEN') + '/sendMessage',
            params = {
                'chat_id': '-' + getenv('TELEGRAMCHANNEL'),
                'parse_mode': 'HTML',
                'text': render_template_string(snippet)
            }
        )

    filename = ''
    try:
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename and allowed_file(image.content_type, ['png', 'jpeg', 'gif']):
                filename = original = slugify_filename(secure_filename(image.filename))
                tmp = join('/tmp', filename)
                image.save(tmp)
                limit = int(getenv('REQUESTS_IMAGES')) if getenv('REQUESTS_IMAGES') else 1048576
                if stat(tmp).st_size > limit:
                    abort(413)
                makedirs(join(getenv('DB_ROOT'), 'requests', 'images'), exist_ok=True)
                store = join(getenv('DB_ROOT'), 'requests', 'images', filename)
                copy = 1
                while isfile(store):
                    filename = splitext(original)[0] + '-' + str(copy) + splitext(original)[1]
                    store = join(getenv('DB_ROOT'), 'requests', 'images', filename)
                    copy += 1
                move(tmp, store)
    except Exception as error:
        props['message'] = 'Failed to upload image. Error: {}'.format(error)
        return make_response(render_template(
            'error.html',
            props = props
        ), 500)

    scrub = Cleaner(tags = [])
    text = Cleaner(tags = ['br'])

    columns = ['service','"user"','title','description','price','ips']
    description = request.form.get('description').strip().replace('\n', '<br>\n')
    params = (
        scrub.clean(request.form.get('service')),
        scrub.clean(request.form.get('user_id').strip()),
        scrub.clean(request.form.get('title').strip()),
        text.clean(description),
        scrub.clean(request.form.get('price').strip()),
        [sha256(ip.encode()).hexdigest()]
    )
    if request.form.get('specific_id'):
        columns.append('post_id')
        params += (scrub.clean(request.form.get('specific_id').strip()),)
    if filename:
        columns.append('image')
        params += (join('/requests', 'images', filename),)
    data = ['%s'] * len(params)

    query = "INSERT INTO requests ({fields}) VALUES ({values})".format(
        fields = ','.join(columns),
        values = ','.join(data)
    )

    cursor = get_cursor()
    cursor.execute(query, params)

    return make_response(render_template(
        'success.html',
        props = props
    ), 200)

@legacy.route('/importer')
def importer():
    props = {
        'currentPage': 'import'
    }

    response = make_response(render_template(
        'importer_list.html',
        props = props
    ), 200)
    response.headers['Cache-Control'] = 'max-age=60, public, stale-while-revalidate=2592000'
    return response

@legacy.route('/importer/tutorial')
def importer_tutorial():
    props = {
        'currentPage': 'import'
    }

    response = make_response(render_template(
        'importer_tutorial.html',
        props = props
    ), 200)
    response.headers['Cache-Control'] = 'max-age=60, public, stale-while-revalidate=2592000'
    return response

@legacy.route('/importer/ok')
def importer_ok():
    props = {
        'currentPage': 'import'
    }

    response = make_response(render_template(
        'importer_ok.html',
        props = props
    ), 200)
    response.headers['Cache-Control'] = 'max-age=60, public, stale-while-revalidate=2592000'
    return response

@legacy.route('/importer/status/<lgid>')
def importer_status(lgid):
    props = {
        'currentPage': 'import',
        'id': lgid
    }

    try:
        with open(join(getenv('DB_ROOT'), 'logs', lgid + '.log')) as f:
            response = make_response(render_template(
                'importer_status.html',
                props = props,
                log = f.read()
            ), 200)
    except IOError:
        props['message'] = 'That log doesn\'t exist.'
        response = make_response(render_template(
            'error.html',
            props = props
        ), 401)

    response.headers['Cache-Control'] = 'max-age=0, private, must-revalidate'
    return response

### API ###
@legacy.route('/api/import', methods=['POST'])
def importer_submit():
    host = getenv('ARCHIVERHOST')
    port = getenv('ARCHIVERPORT') if getenv('ARCHIVERPORT') else '8000'

    try:
        r = requests.post(
            f'http://{host}:{port}/api/import',
            json = {
                'service': request.form.get("service"),
                'session_key': request.form.get("session_key"),
                'channel_ids': request.form.get("channel_ids")
            },
            params = {
                'service': request.form.get("service"),
                'session_key': request.form.get("session_key"),
                'channel_ids': request.form.get("channel_ids")
            }
        )
        r.raise_for_status()
        # in new importer, return just the id instead of a whole page
        props = {
            'currentPage': 'import',
            'redirect': f'/importer/status/{r.text}'
        }
        return make_response(render_template(
            'success.html',
            props = props
        ), 200)
    except Exception as e:
        return f'Error while connecting to archiver. Is it running? Error: {e}', 500

@legacy.route('/api/upload', methods=['POST'])
def upload():
    resumable_dict = {
        'resumableIdentifier': request.form.get('resumableIdentifier'),
        'resumableFilename': request.form.get('resumableFilename'),
        'resumableTotalSize': request.form.get('resumableTotalSize'),
        'resumableTotalChunks': request.form.get('resumableTotalChunks'),
        'resumableChunkNumber': request.form.get('resumableChunkNumber')
    }

    if int(request.form.get('resumableTotalSize')) > int(getenv('UPLOAD_LIMIT')):
        return "File too large.", 415

    makedirs(join(getenv('DB_ROOT'), 'uploads'), exist_ok=True)
    makedirs(join(getenv('DB_ROOT'), 'uploads', 'temp'), exist_ok=True)

    resumable = UploaderFlask(
        resumable_dict,
        join(getenv('DB_ROOT'), 'uploads'),
        join(getenv('DB_ROOT'), 'uploads', 'temp'),
        request.files['file']
    )

    resumable.upload_chunk()

    if resumable.check_status() is True:
        resumable.assemble_chunks()
        try:
            resumable.cleanup()
        except:
            pass

        post_model = {
            'id': ''.join(random.choice(string.ascii_letters) for x in range(8)),
            '"user"': request.form.get('user'),
            'service': request.form.get('service'),
            'title': request.form.get('title'),
            'content': request.form.get('content') or "",
            'embed': {},
            'shared_file': True,
            'added': datetime.now(),
            'published': datetime.now(),
            'edited': None,
            'file': {
                "name": request.form.get('resumableFilename'),
                "path": f"/uploads/{request.form.get('resumableFilename')}"
            },
            'attachments': []
        }

        post_model['embed'] = json.dumps(post_model['embed'])
        post_model['file'] = json.dumps(post_model['file'])
        
        columns = post_model.keys()
        data = ['%s'] * len(post_model.values())
        data[-1] = '%s::jsonb[]' # attachments
        query = "INSERT INTO posts ({fields}) VALUES ({values})".format(
            fields = ','.join(columns),
            values = ','.join(data)
        )
        cursor = get_cursor()
        cursor.execute(query, list(post_model.values()))
        
        return jsonify({
            "fileUploadStatus": True,
            "resumableIdentifier": resumable.repo.file_id
        })

    return jsonify({
        "chunkUploadStatus": True,
        "resumableIdentifier": resumable.repo.file_id
    })


@legacy.route('/api/bans')
def bans():
    cursor = get_cursor()
    query = "SELECT * FROM dnp"
    cursor.execute(query)
    results = cursor.fetchall()
    return make_response(jsonify(results), 200)

@legacy.route('/api/recent')
def recent():
    cursor = get_cursor()
    query = "SELECT * FROM posts ORDER BY added desc "
    params = ()

    offset = request.args.get('o') if request.args.get('o') else 0
    query += "OFFSET %s "
    params += (offset,)
    limit = request.args.get('limit') if request.args.get('limit') and int(request.args.get('limit')) <= 50 else 25
    query += "LIMIT %s"
    params += (limit,)

    cursor.execute(query, params)
    results = cursor.fetchall()

    response = make_response(jsonify(results), 200)
    response.headers['Cache-Control'] = 'max-age=60, public, stale-while-revalidate=2592000'
    return response

@legacy.route('/api/lookup')
def lookup():
    if (request.args.get('q') is None):
        return make_response('Bad request', 400)
    cursor = get_cursor()
    query = "SELECT * FROM lookup "
    params = ()
    query += "WHERE name ILIKE %s "
    params += ('%' + request.args.get('q') + '%',)
    if (request.args.get('service')):
        query += "AND service = %s "
        params += (request.args.get('service'),)
    limit = request.args.get('limit') if request.args.get('limit') and int(request.args.get('limit')) <= 150 else 50
    query += "LIMIT %s"
    params += (limit,)

    cursor.execute(query, params)
    results = cursor.fetchall()
    response = make_response(jsonify(list(map(lambda x: x['id'], results))), 200)
    return response

@legacy.route('/api/discord/channels/lookup')
def discord_lookup():
    cursor = get_cursor()
    query = "SELECT channel FROM discord_posts WHERE server = %s GROUP BY channel"
    params = (request.args.get('q'),)
    cursor.execute(query, params)
    channels = cursor.fetchall()
    lookup = []
    for x in channels:
        cursor = get_cursor()
        cursor.execute("SELECT * FROM lookup WHERE service = 'discord-channel' AND id = %s", (x['channel'],))
        lookup_result = cursor.fetchall()
        lookup.append({ 'id': x['channel'], 'name': lookup_result[0]['name'] if len(lookup_result) else '' })
    response = make_response(jsonify(lookup))
    return response

@legacy.route('/api/discord/channel/<id>')
def discord_channel(id):
    cursor = get_cursor()
    query = "SELECT * FROM discord_posts WHERE channel = %s ORDER BY published desc "
    params = (id,)

    offset = request.args.get('skip') if request.args.get('skip') else 0
    query += "OFFSET %s "
    params += (offset,)
    limit = request.args.get('limit') if request.args.get('limit') and int(request.args.get('limit')) <= 150 else 25
    query += "LIMIT %s"
    params += (limit,)

    cursor.execute(query, params)
    results = cursor.fetchall()
    return jsonify(results)

@legacy.route('/api/lookup/cache/<id>')
def lookup_cache(id):
    if (request.args.get('service') is None):
        return make_response('Bad request', 400)
    cursor = get_cursor()
    query = "SELECT * FROM lookup WHERE id = %s AND service = %s"
    params = (id, request.args.get('service'))
    cursor.execute(query, params)
    results = cursor.fetchall()
    response = make_response(jsonify({ "name": results[0]['name'] if len(results) > 0 else '' }))
    return response

@legacy.route('/api/<service>/user/<user>/lookup')
def user_search(service, user):
    if (request.args.get('q') and len(request.args.get('q')) > 35):
        return make_response('Bad request', 400)
    cursor = get_cursor()
    query = "SELECT * FROM posts WHERE \"user\" = %s AND service = %s "
    params = (user, service)
    query += "AND to_tsvector(content || ' ' || title) @@ websearch_to_tsquery(%s) "
    params += (request.args.get('q'),)
    query += "ORDER BY published desc "

    offset = request.args.get('o') if request.args.get('o') else 0
    query += "OFFSET %s "
    params += (offset,)
    limit = request.args.get('limit') if request.args.get('limit') and int(request.args.get('limit')) <= 150 else 25
    query += "LIMIT %s"
    params += (limit,)

    cursor.execute(query, params)
    results = cursor.fetchall()
    return jsonify(results)

@legacy.route('/api/<service>/user/<user>/post/<post>')
def post_api(service, user, post):
    cursor = get_cursor()
    query = "SELECT * FROM posts WHERE id = %s AND \"user\" = %s AND service = %s ORDER BY added asc"
    params = (post, user, service)
    cursor.execute(query, params)
    results = cursor.fetchall()
    return jsonify(results)

@legacy.route('/api/<service>/user/<user>/post/<post>/flag')
def flag_api(service, user, post):
    cursor = get_cursor()
    query = "SELECT * FROM booru_flags WHERE id = %s AND \"user\" = %s AND service = %s"
    params = (post, user, service)
    cursor.execute(query, params)
    results = cursor.fetchall()
    return "", 200 if len(results) else 404

@legacy.route('/api/<service>/user/<user>/post/<post>/flag', methods=["POST"])
def new_flag_api(service, user, post):
    cursor = get_cursor()
    query = "SELECT * FROM posts WHERE id = %s AND \"user\" = %s AND service = %s"
    params = (post, user, service)
    cursor.execute(query, params)
    results = cursor.fetchall()
    if len(results) == 0:
        return "", 404

    cursor2 = get_cursor()
    query2 = "SELECT * FROM booru_flags WHERE id = %s AND \"user\" = %s AND service = %s"
    params2 = (post, user, service)
    cursor2.execute(query2, params2)
    results2 = cursor.fetchall()
    if len(results2) > 0:
        # conflict; flag already exists
        return "", 409

    scrub = Cleaner(tags = [])
    columns = ['id','"user"','service']
    params = (
        scrub.clean(post),
        scrub.clean(user),
        scrub.clean(service)
    )
    data = ['%s'] * len(params)
    query = "INSERT INTO booru_flags ({fields}) VALUES ({values})".format(
        fields = ','.join(columns),
        values = ','.join(data)
    )
    cursor3 = get_cursor()
    cursor3.execute(query, params)

    return "", 200

@legacy.route('/api/<service>/user/<id>')
@cache.cached(key_prefix=make_cache_key)
def user_api(service, id):
    cursor = get_cursor()
    query = "SELECT * FROM posts WHERE \"user\" = %s AND service = %s ORDER BY published desc "
    params = (id, service)

    offset = request.args.get('o') if request.args.get('o') else 0
    query += "OFFSET %s "
    params += (offset,)
    limit = request.args.get('limit') if request.args.get('limit') and int(request.args.get('limit')) <= 50 else 25
    query += "LIMIT %s"
    params += (limit,)

    cursor.execute(query, params)
    results = cursor.fetchall()

    return jsonify(results)