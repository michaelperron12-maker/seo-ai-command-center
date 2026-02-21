#!/usr/bin/env python3
"""
SeoAI Google Full Setup — Run after OAuth authorization
Usage: python3 setup_google_full.py <AUTH_CODE>

This script:
1. Exchanges the auth code for tokens with full scopes
2. Creates a Google Maps API key
3. Enables Places API
4. Adds all client sites to Search Console
5. Finds Place IDs for all GBP profiles
6. Syncs Google reviews
"""
import sys
import json
import requests
import sqlite3
import os
from datetime import datetime

DB_PATH = '/opt/seo-agent/db/seo_agent.db'
TOKEN_PATH = '/opt/seo-agent/google_tokens.json'
CREDS_PATH = '/opt/seo-agent/google_credentials.json'
ENV_PATH = '/opt/seo-agent/.env'

def log(msg):
    print(f'[{datetime.now().strftime("%H:%M:%S")}] {msg}')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def step1_exchange_code(auth_code):
    """Exchange authorization code for access + refresh tokens"""
    log('STEP 1: Exchanging auth code for tokens...')
    
    with open(CREDS_PATH) as f:
        creds = json.load(f)
    
    installed = creds.get('installed', {})
    
    resp = requests.post('https://oauth2.googleapis.com/token', data={
        'code': auth_code,
        'client_id': installed['client_id'],
        'client_secret': installed['client_secret'],
        'redirect_uri': 'http://localhost',
        'grant_type': 'authorization_code'
    })
    
    if resp.status_code != 200:
        log(f'ERROR: Token exchange failed: {resp.text[:300]}')
        return None
    
    data = resp.json()
    tokens = {
        'access_token': data['access_token'],
        'refresh_token': data.get('refresh_token', ''),
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': installed['client_id'],
        'client_secret': installed['client_secret'],
        'expiry': datetime.utcnow().isoformat()
    }
    
    with open(TOKEN_PATH, 'w') as f:
        json.dump(tokens, f, indent=2)
    os.chmod(TOKEN_PATH, 0o600)
    
    log(f'OK: Tokens saved ({len(data.get("scope","").split())} scopes)')
    return data['access_token']

def step2_create_api_key(token):
    """Create a Google Maps API key"""
    log('STEP 2: Creating Google Maps API key...')
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    with open(CREDS_PATH) as f:
        project = json.load(f).get('installed', {}).get('project_id', '')
    
    # First enable Places API
    log('  Enabling Places API (New)...')
    enable_url = f'https://serviceusage.googleapis.com/v1/projects/{project}/services/places-backend.googleapis.com:enable'
    resp = requests.post(enable_url, headers=headers, timeout=30)
    log(f'  Places API enable: {resp.status_code}')
    
    # Create API key
    log('  Creating API key...')
    resp = requests.post(
        f'https://apikeys.googleapis.com/v2/projects/{project}/locations/global/keys',
        headers=headers,
        json={
            'displayName': 'SeoAI-Places-Reviews',
            'restrictions': {
                'apiTargets': [{'service': 'places-backend.googleapis.com'}]
            }
        },
        timeout=30
    )
    
    if resp.status_code in (200, 201):
        data = resp.json()
        # The key creation is async, get the key string
        if 'name' in data:
            # Poll for completion
            import time
            op_name = data['name']
            for _ in range(10):
                time.sleep(2)
                op_resp = requests.get(f'https://apikeys.googleapis.com/v2/{op_name}', headers=headers, timeout=15)
                if op_resp.status_code == 200:
                    op_data = op_resp.json()
                    if op_data.get('done'):
                        key_data = op_data.get('response', {})
                        api_key = key_data.get('keyString', '')
                        if api_key:
                            _save_api_key(api_key)
                            log(f'OK: API key created: {api_key[:10]}...')
                            return api_key
                        break
        log(f'  Response: {resp.text[:300]}')
    else:
        log(f'  ERROR: {resp.status_code} - {resp.text[:300]}')
    
    return None

def _save_api_key(api_key):
    """Save API key to .env file"""
    env_content = ''
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            env_content = f.read()
    
    if 'GOOGLE_MAPS_API_KEY' in env_content:
        lines = env_content.split('\n')
        lines = [l if not l.startswith('GOOGLE_MAPS_API_KEY') else f'GOOGLE_MAPS_API_KEY={api_key}' for l in lines]
        env_content = '\n'.join(lines)
    else:
        env_content += f'\nGOOGLE_MAPS_API_KEY={api_key}\n'
    
    with open(ENV_PATH, 'w') as f:
        f.write(env_content)
    os.chmod(ENV_PATH, 0o600)

def step3_add_search_console_sites(token):
    """Add all client sites to Google Search Console"""
    log('STEP 3: Adding sites to Search Console...')
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    sites = [
        'https://jcpeintre.com/',
        'https://paysagiste-excellence.ca/',
        'https://deneigement-excellence.ca/',
        'https://seoparai.com/'
    ]
    
    for site_url in sites:
        encoded = requests.utils.quote(site_url, safe='')
        resp = requests.put(
            f'https://www.googleapis.com/webmasters/v3/sites/{encoded}',
            headers=headers, timeout=15
        )
        status = 'OK' if resp.status_code in (200, 204) else f'ERROR {resp.status_code}'
        log(f'  {site_url}: {status}')

def step4_find_place_ids(token, api_key=None):
    """Find Place IDs for GBP profiles using Places API"""
    log('STEP 4: Finding Place IDs...')
    
    conn = get_db()
    profiles = conn.execute('SELECT id, client_id, business_name, address, city, phone, place_id FROM google_business_profiles').fetchall()
    
    for profile in profiles:
        if profile['place_id']:
            log(f'  {profile["business_name"]}: already has place_id {profile["place_id"]}')
            continue
        
        query = f'{profile["business_name"]} {profile["address"]} {profile["city"]} QC'
        log(f'  Searching: {query}')
        
        if api_key:
            # Use Places API (New) with API key
            resp = requests.post(
                'https://places.googleapis.com/v1/places:searchText',
                headers={
                    'X-Goog-Api-Key': api_key,
                    'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount',
                    'Content-Type': 'application/json'
                },
                json={'textQuery': query, 'languageCode': 'fr'},
                timeout=15
            )
        else:
            # Use OAuth token
            resp = requests.post(
                'https://places.googleapis.com/v1/places:searchText',
                headers={
                    'Authorization': f'Bearer {token}',
                    'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount',
                    'Content-Type': 'application/json'
                },
                json={'textQuery': query, 'languageCode': 'fr'},
                timeout=15
            )
        
        if resp.status_code == 200:
            places = resp.json().get('places', [])
            if places:
                place = places[0]
                place_id = place.get('id', '')
                name = place.get('displayName', {}).get('text', '')
                rating = place.get('rating', 0)
                reviews = place.get('userRatingCount', 0)
                
                # Update DB
                conn.execute(
                    'UPDATE google_business_profiles SET place_id = ?, updated_at = datetime("now") WHERE id = ?',
                    (place_id, profile['id'])
                )
                conn.commit()
                
                log(f'  FOUND: {name} — place_id: {place_id}, {rating} stars, {reviews} reviews')
            else:
                log(f'  NOT FOUND for: {query}')
        else:
            log(f'  API error {resp.status_code}: {resp.text[:200]}')
    
    conn.close()

def step5_sync_reviews(api_key):
    """Sync Google reviews using Places API"""
    log('STEP 5: Syncing Google reviews...')
    
    if not api_key:
        log('  Skipping: no API key available')
        return
    
    sys.path.insert(0, '/opt/seo-agent/agents')
    from google_reviews_fetcher import sync_all_reviews
    result = sync_all_reviews()
    log(f'  Result: {json.dumps(result, indent=2)}')

def main():
    if len(sys.argv) < 2:
        print('Usage: python3 setup_google_full.py <AUTH_CODE>')
        print()
        print('Get the auth code from this URL:')
        with open(CREDS_PATH) as f:
            creds = json.load(f)
        client_id = creds.get('installed', {}).get('client_id', '')
        scopes = 'https://www.googleapis.com/auth/business.manage https://www.googleapis.com/auth/webmasters https://www.googleapis.com/auth/analytics.readonly https://www.googleapis.com/auth/indexing https://www.googleapis.com/auth/cloud-platform https://www.googleapis.com/auth/siteverification'
        from urllib.parse import urlencode
        params = {
            'client_id': client_id,
            'redirect_uri': 'http://localhost',
            'response_type': 'code',
            'scope': scopes,
            'access_type': 'offline',
            'prompt': 'consent'
        }
        print(f'https://accounts.google.com/o/oauth2/auth?{urlencode(params)}')
        sys.exit(1)
    
    auth_code = sys.argv[1]
    
    # Step 1: Exchange code for tokens
    token = step1_exchange_code(auth_code)
    if not token:
        log('FATAL: Could not get access token')
        sys.exit(1)
    
    # Step 2: Create API key
    api_key = step2_create_api_key(token)
    
    # Step 3: Add Search Console sites
    step3_add_search_console_sites(token)
    
    # Step 4: Find Place IDs
    step4_find_place_ids(token, api_key)
    
    # Step 5: Sync reviews
    step5_sync_reviews(api_key)
    
    log('=== SETUP COMPLETE ===')

if __name__ == '__main__':
    main()
