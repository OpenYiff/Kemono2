from flask import Blueprint, request, make_response, render_template

import requests
from os import getenv

importer_page = Blueprint('importer_page', __name__)

@importer_page.route('/importer')
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

@importer_page.route('/importer/tutorial')
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

@importer_page.route('/importer/ok')
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

@importer_page.route('/importer/status/<log_id>')
def importer_status(log_id):
    props = {
        'currentPage': 'import',
    }

    response = make_response(render_template(
        'importer_status.html',
        props = props,
        log_id = log_id
    ), 200)

    response.headers['Cache-Control'] = 'max-age=0, private, must-revalidate'
    return response

@importer_page.route('/api/logs/<log_id>')
def get_importer_logs(log_id):
    host = getenv('ARCHIVERHOST')
    port = getenv('ARCHIVERPORT') if getenv('ARCHIVERPORT') else '8000'

    try:
        r = requests.get(
            f'http://{host}:{port}/api/logs/{log_id}'
        )
        r.raise_for_status()
        return r.text, r.status_code
    except Exception:
        return f'Error while connecting to archiver.', 500

### API ###
@importer_page.route('/api/import', methods=['POST'])
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
        log_id = r.text
        props = {
            'currentPage': 'import',
            'redirect': f'/importer/status/{log_id}'
        }
        return make_response(render_template(
            'success.html',
            props = props
        ), 200)
    except Exception as e:
        return f'Error while connecting to archiver. Is it running? Error: {e}', 500