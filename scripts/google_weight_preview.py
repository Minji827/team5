"""Live Google Places weighting preview. Store only place IDs and match decisions.

Google ratings, counts, names and addresses are not written to files.
"""
import math
import os
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher

import requests
from dotenv import load_dotenv

from weight_experiment import ROOT, OUT, WEIGHTS, read, write, score


def normalized(value):
    return re.sub(r'[^a-z0-9가-힣]', '', unicodedata.normalize('NFKC', value).lower())


def distance_m(row, place):
    location = place.get('location', {})
    lat1, lon1 = math.radians(float(row['lat'])), math.radians(float(row['lon']))
    lat2, lon2 = math.radians(location['latitude']), math.radians(location['longitude'])
    a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 6371000 * 2 * math.asin(min(1., math.sqrt(a)))


def match(row, places):
    candidates = []
    for p in places:
        try:
            distance = distance_m(row, p)
            similarity = SequenceMatcher(None, normalized(row['name']),
                                         normalized(p.get('displayName', {}).get('text', ''))).ratio()
            if distance <= 200 and similarity >= .9:
                candidates.append(p)
        except (KeyError, TypeError, ValueError):
            continue
    return candidates[0] if len(candidates) == 1 else None


def main():
    load_dotenv(ROOT / '.env')
    key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not key:
        raise SystemExit('Google Places key is not configured.')
    rows = read(OUT / 'sample.csv')
    previous_path = OUT / 'google_place_matches.csv'
    previous = {r['id']: r for r in read(previous_path)} if previous_path.exists() else {}
    decisions, live = [], []
    for row in rows:
        saved = previous.get(row['id'], {})
        headers = {'X-Goog-Api-Key': key}
        try:
            if saved.get('google_place_id') and saved.get('match_status') == 'matched':
                headers['X-Goog-FieldMask'] = 'id,rating,userRatingCount'
                response = requests.get('https://places.googleapis.com/v1/places/' + saved['google_place_id'],
                                        headers=headers, timeout=20)
                places = None
            else:
                headers['X-Goog-FieldMask'] = ('places.id,places.displayName,places.formattedAddress,'
                                              'places.location,places.rating,places.userRatingCount')
                response = requests.post('https://places.googleapis.com/v1/places:searchText',
                                         headers=headers,
                                         json={'textQuery': row['name'] + ' ' + row['address'],
                                               'languageCode': 'ko', 'regionCode': 'KR', 'pageSize': 5}, timeout=20)
                places = True
            if not response.ok:
                raise SystemExit(f'Google API stopped at HTTP {response.status_code}; no upstream secrets logged.')
            data = response.json()
        except requests.RequestException:
            raise SystemExit('Google network request failed; no upstream secrets logged.') from None
        place = match(row, data.get('places', [])) if places else data
        status = 'matched' if place else ('review_needed' if data.get('places') else 'no_result')
        decisions.append({'id': row['id'], 'name': row['name'], 'category': row['category'],
                          'google_place_id': place['id'] if place else '', 'match_status': status})
        if place:
            rating, count = place.get('rating'), place.get('userRatingCount', 0)
            if isinstance(rating, (int, float)) and 1 <= rating <= 5 and isinstance(count, int) and count > 0:
                live.append((row, float(rating), float(count)))
        print(f'{len(decisions)}/{len(rows)} {row["id"]}: {status}', flush=True)
    duplicates = Counter(d['google_place_id'] for d in decisions if d['google_place_id'])
    for d in decisions:
        if d['google_place_id'] and duplicates[d['google_place_id']] > 1:
            d.update(google_place_id='', match_status='duplicate_review')
    valid = {d['id'] for d in decisions if d['match_status'] == 'matched'}
    live = [item for item in live if item[0]['id'] in valid]
    write(previous_path, decisions)
    print('MATCH_SUMMARY', dict(Counter(d['match_status'] for d in decisions)))
    means = defaultdict(list)
    for row, rating, count in live:
        means[row['category']].append(rating)
    ranked = defaultdict(list)
    for row, rating, count in live:
        if not row['walk_minutes']:
            continue
        category = row['category']
        mean = sum(means[category]) / len(means[category])
        adjusted, distance, total = score(rating, count, mean, float(row['walk_minutes']), WEIGHTS[category])
        if total is not None:
            ranked[category].append((total, row['name'], rating, int(count), adjusted))
    print('LIVE_RATING_COUNT', len(live))
    print('LIVE_ELIGIBLE_COUNT', sum(map(len, ranked.values())))
    print('Google Maps: live preview; ratings/counts are not saved. Category means are provisional sample means.')
    for category in WEIGHTS:
        print(category, 'rated:', len(means[category]), 'eligible:', len(ranked[category]))
        for total, name, rating, count, adjusted in sorted(ranked[category], reverse=True)[:3]:
            print(f'  {name}: rating={rating}, reviews={count}, adjusted={adjusted:.3f}, score={total:.4f}')


if __name__ == '__main__':
    assert normalized('폼 (FORM)') == normalized('폼form')
    row = {'name': '테스트', 'lat': '35.1', 'lon': '129.03'}
    good = {'id': 'test', 'displayName': {'text': '테스트'},
            'location': {'latitude': 35.1, 'longitude': 129.03}}
    assert match(row, [good]) == good
    assert match(row, [good, good]) is None
    assert match(row, [dict(good, displayName={'text': '다른가게'})]) is None
    main()
