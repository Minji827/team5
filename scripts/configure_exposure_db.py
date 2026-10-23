"""Prompt locally for the existing DB password; never print the connection URL."""
from getpass import getpass
from pathlib import Path
from urllib.parse import quote

from dotenv import set_key

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    password = getpass('Supabase database password (hidden): ')
    if not password:
        raise SystemExit('No password entered; .env unchanged.')
    url = ('postgresql://postgres.zidcslicgrjgceszlxfz:' + quote(password, safe='')
           + '@aws-0-ap-southeast-2.pooler.supabase.com:5432/postgres?sslmode=require')
    set_key(str(ROOT / '.env'), 'EXPOSURE_DATABASE_URL', url)
    print('Saved EXPOSURE_DATABASE_URL to local .env; password and URL were not printed.')
