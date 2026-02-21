#!/usr/bin/env python3
"""
Google Reviews Fetcher — Uses Places API (New) to fetch reviews
Requires GOOGLE_MAPS_API_KEY in .env
"""
import os
import json
import sqlite3
import requests
from datetime import datetime

DB_PATH = '/opt/seo-agent/db/seo_agent.db'
LOG_PATH = '/opt/seo-agent/logs/reviews_fetcher.log'

def log(msg, level='INFO'):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] [{level}] {msg}'
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, 'a') as f:
            f.write(line + '\n')
    except:
        pass

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_api_key():
    """Get Google Maps API Key from .env"""
    env_path = '/opt/seo-agent/.env'
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip().startswith('GOOGLE_MAPS_API_KEY='):
                    return line.strip().split('=', 1)[1].strip()
    return os.environ.get('GOOGLE_MAPS_API_KEY')

def fetch_reviews_places_api(place_id, api_key):
    """Fetch reviews using Google Places API (New) — returns up to 5 reviews"""
    url = f'https://places.googleapis.com/v1/places/{place_id}'
    headers = {
        'X-Goog-Api-Key': api_key,
        'X-Goog-FieldMask': 'id,displayName,rating,userRatingCount,reviews'
    }
    
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        log(f'Places API error for {place_id}: {resp.status_code} - {resp.text[:200]}', 'ERROR')
        return None
    
    return resp.json()

def fetch_place_id_from_text(query, api_key):
    """Search for a place by text and return its Place ID"""
    url = 'https://places.googleapis.com/v1/places:searchText'
    headers = {
        'X-Goog-Api-Key': api_key,
        'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount',
        'Content-Type': 'application/json'
    }
    
    resp = requests.post(url, headers=headers, json={'textQuery': query}, timeout=15)
    if resp.status_code != 200:
        log(f'Text search error: {resp.status_code} - {resp.text[:200]}', 'ERROR')
        return None
    
    data = resp.json()
    places = data.get('places', [])
    if places:
        return places[0]
    return None

def save_reviews_to_db(reviews_data, site_id):
    """Save fetched reviews to google_reviews table"""
    conn = get_db()
    cursor = conn.cursor()
    saved = 0
    
    reviews = reviews_data.get('reviews', [])
    for review in reviews:
        review_id = review.get('name', '').split('/')[-1] or f'rev_{datetime.now().timestamp()}'
        author = review.get('authorAttribution', {}).get('displayName', 'Anonyme')
        rating = review.get('rating', 5)
        text = review.get('text', {}).get('text', '') if isinstance(review.get('text'), dict) else review.get('text', '')
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO google_reviews (site_id, review_id, author, rating, text, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            ''', (site_id, review_id, author, rating, text))
            if cursor.rowcount > 0:
                saved += 1
        except Exception as e:
            log(f'Error saving review: {e}', 'ERROR')
    
    conn.commit()
    conn.close()
    return saved

def sync_all_reviews():
    """Main function: fetch and save reviews for all GBP profiles with place_id"""
    api_key = get_api_key()
    if not api_key:
        log('GOOGLE_MAPS_API_KEY not configured in .env', 'ERROR')
        return {'error': 'No API key configured'}
    
    conn = get_db()
    profiles = conn.execute(
        'SELECT id, client_id, business_name, place_id FROM google_business_profiles WHERE place_id IS NOT NULL AND place_id != ""'
    ).fetchall()
    conn.close()
    
    if not profiles:
        log('No GBP profiles with place_id found', 'WARNING')
        return {'error': 'No profiles with place_id'}
    
    results = {}
    total_new = 0
    
    for profile in profiles:
        name = profile['business_name']
        place_id = profile['place_id']
        site_id = profile['client_id']
        
        log(f'Fetching reviews for {name} (place_id: {place_id})')
        
        data = fetch_reviews_places_api(place_id, api_key)
        if data:
            rating = data.get('rating', 0)
            count = data.get('userRatingCount', 0)
            reviews = data.get('reviews', [])
            
            saved = save_reviews_to_db(data, site_id)
            total_new += saved
            
            results[name] = {
                'rating': rating,
                'total_reviews': count,
                'fetched': len(reviews),
                'new_saved': saved
            }
            
            log(f'  {name}: {rating} stars, {count} total reviews, {len(reviews)} fetched, {saved} new saved')
        else:
            results[name] = {'error': 'API call failed'}
    
    log(f'Sync complete: {total_new} new reviews saved across {len(profiles)} profiles')
    return {'profiles_synced': len(profiles), 'total_new_reviews': total_new, 'details': results}

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'find':
        # Find Place ID mode
        api_key = get_api_key()
        if not api_key:
            print('Error: GOOGLE_MAPS_API_KEY not set')
            sys.exit(1)
        query = ' '.join(sys.argv[2:])
        result = fetch_place_id_from_text(query, api_key)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print('No results found')
    else:
        # Sync mode
        result = sync_all_reviews()
        print(json.dumps(result, indent=2))
