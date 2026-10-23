"""Anonymous list impressions, acknowledged once after rendering."""
import json
import os
import re
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

WINDOW_SECONDS = 7 * 86400
MAX_EXTRA_SECONDS = 120


class ExposureStorageError(RuntimeError):
    pass


class PostgresConnection:
    """Keep the small SQLite query set compatible with server-only PostgreSQL."""
    def __init__(self, connection):
        self.connection = connection

    def execute(self, sql, parameters=()):
        return self.connection.execute(re.sub(r'\blists\b', 'app_private.exposure_lists', sql).replace('?', '%s'), parameters)


@contextmanager
def database():
    url = os.getenv('EXPOSURE_DATABASE_URL')
    if url:
        try:
            import psycopg
        except ImportError:
            raise ExposureStorageError('PostgreSQL 드라이버가 설치되지 않았습니다.') from None
        try:
            with psycopg.connect(url, sslmode='require', connect_timeout=10) as connection:
                yield PostgresConnection(connection)
        except psycopg.Error:
            # Connection exceptions can contain credentials: never forward them.
            raise ExposureStorageError('추천 기록 DB에 연결하지 못했습니다.') from None
        return
    if os.getenv('RENDER') == 'true':
        raise ExposureStorageError('영속 추천 기록 DB 설정이 필요합니다.')
    path = Path(os.getenv('EXPOSURE_DB_PATH', str(Path(__file__).resolve().parents[2] / 'var/exposure.sqlite3')))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    try:
        with db:
            db.execute('CREATE TABLE IF NOT EXISTS lists (id TEXT PRIMARY KEY, created REAL NOT NULL, shown REAL, places TEXT NOT NULL)')
            db.execute('CREATE INDEX IF NOT EXISTS lists_shown ON lists(shown)')
            yield db
    finally:
        db.close()


def counts():
    result = {}
    with database() as db:
        for (places,) in db.execute('SELECT places FROM lists WHERE shown >= ?', (time.time()-WINDOW_SECONDS,)):
            for rank, place_id in enumerate(json.loads(places)):
                top, total = result.get(place_id, (0, 0))
                result[place_id] = (top + (rank == 0), total + 1)
    return result


def rotate(candidates):
    if not candidates:
        return []
    seconds = lambda p: p.get('leg_seconds', p['leg_minutes'] * 60)
    nearest = sorted(candidates, key=lambda p: (seconds(p), p['id']))
    cutoff = seconds(nearest[0]) + MAX_EXTRA_SECONDS
    history = counts()
    similar = [p for p in nearest if seconds(p) <= cutoff]
    similar.sort(key=lambda p: (*history.get(p['id'], (0, 0)), seconds(p), p['id']))
    fallback = [p for p in nearest if seconds(p) > cutoff]
    return (similar + fallback)[:3]


def issue(places):
    token = str(uuid4())
    now = time.time()
    with database() as db:
        # Keep acknowledged history for the dashboard; only discard unused lists.
        db.execute('DELETE FROM lists WHERE shown IS NULL AND created < ?', (now-3600,))
        db.execute('INSERT INTO lists(id,created,places) VALUES (?,?,?)',
                   (token, now, json.dumps([p['id'] for p in places])))
    return token


def acknowledge(token):
    now = time.time()
    with database() as db:
        cursor = db.execute('UPDATE lists SET shown=? WHERE id=? AND shown IS NULL AND created>=?',
                            (now, str(token), now-3600))
        if cursor.rowcount:
            return True
        if db.execute('SELECT 1 FROM lists WHERE id=? AND shown IS NOT NULL', (str(token),)).fetchone():
            return False
    raise ValueError('Unknown or expired list')
