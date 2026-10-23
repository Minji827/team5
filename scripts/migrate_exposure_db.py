"""Apply the additive server-only exposure schema using the local .env. Never print credentials."""
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    load_dotenv(ROOT / '.env')
    url = os.getenv('EXPOSURE_DATABASE_URL')
    if not url:
        raise SystemExit('EXPOSURE_DATABASE_URL is not configured.')
    try:
        with psycopg.connect(url, sslmode='require', connect_timeout=10) as db:
            before = db.execute('SELECT count(*) FROM app_private.exposure_lists').fetchone()[0]
            db.execute((ROOT / 'supabase/exposure.sql').read_text(encoding='utf-8'))
            after = db.execute('SELECT count(*) FROM app_private.exposure_lists').fetchone()[0]
        print('Exposure schema migration committed. Existing requests retained:', before == after)
    except psycopg.Error as error:
        raise SystemExit('Exposure schema migration failed: ' + type(error).__name__) from None
