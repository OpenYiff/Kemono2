from ..internals.cache.redis import get_conn
from ..internals.database.database import get_cursor
import ujson
import dateutil

def get_non_discord_artist_ids(reload = False):
    redis = get_conn()
    key = 'non_discord_artist_ids'
    artist_ids = redis.get(key)
    if artist_ids is None or reload:
        cursor = get_cursor()
        query = "SELECT id FROM lookup WHERE service != 'discord-channel'"
        cursor.execute(query)
        artist_ids = cursor.fetchall()
        artist_ids = list(map(lambda row: row['id'], artist_ids))
        redis.set(key, ujson.dumps(artist_ids), ex = 600)
    else:
        artist_ids = ujson.loads(artist_ids)
    return artist_ids

def get_artist(artist_id, reload = False):
    redis = get_conn()
    key = 'artist:' + str(artist_id)
    artist = redis.get(key)
    if artist is None or reload:
        cursor = get_cursor()
        query = 'SELECT * FROM lookup WHERE id = %s'
        cursor.execute(query, (artist_id,))
        artist = cursor.fetchone()
        redis.set(key, serialize_artist(artist), ex = 600)
    else:
        artist = deserialize_artist(artist)
    return artist

def serialize_artist(artist):
    artist['indexed'] = artist['indexed'].isoformat()
    return ujson.dumps(artist)

def deserialize_artist(artist_str):
    artist = ujson.loads(artist_str)
    artist['indexed'] = dateutil.parser.parse(artist['indexed'])
    return artist
