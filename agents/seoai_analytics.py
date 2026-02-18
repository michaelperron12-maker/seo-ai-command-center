#!/usr/bin/env python3
"""
SeoAI Analytics Module — Zero-cookie server-side analytics
Adds Flask routes for: tracker endpoint, JS serve, dashboard data, gclid tracking
Import and call register_analytics_routes(app) from api_server.py
"""
import sqlite3
import json
import hashlib
import hmac
import secrets
import threading
import time
from datetime import datetime, date, timedelta
from collections import deque
from urllib.parse import urlparse
from flask import request, Response, jsonify

ANALYTICS_DB = '/opt/seo-agent/db/seo_analytics.db'
VALID_SITES = {'seoparai', 'jcpeintre', 'deneigement', 'paysagiste'}
VALID_EVENTS = {'pageview', 'heartbeat', 'exit', 'conversion'}

# ============================================================
# IN-MEMORY EVENT QUEUE + BACKGROUND FLUSH
# ============================================================
_event_queue = deque(maxlen=10000)
_flush_lock = threading.Lock()
_flush_thread = None


def _get_db():
    conn = sqlite3.connect(ANALYTICS_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _get_daily_salt():
    """Get or create today's fingerprint salt"""
    today = date.today().isoformat()
    conn = _get_db()
    row = conn.execute('SELECT salt FROM analytics_salt WHERE date=?', (today,)).fetchone()
    if row:
        salt = row['salt']
    else:
        salt = secrets.token_hex(16)
        conn.execute('INSERT OR IGNORE INTO analytics_salt (date, salt) VALUES (?, ?)', (today, salt))
        conn.commit()
    conn.close()
    return salt


def _make_fingerprint(ip, user_agent):
    """Create privacy-safe session fingerprint (rotates daily)"""
    salt = _get_daily_salt()
    data = f"{ip}|{user_agent}".encode()
    return hmac.new(salt.encode(), data, hashlib.sha256).hexdigest()[:16]


def _get_referrer_domain(referrer):
    """Extract domain from referrer URL"""
    if not referrer:
        return ''
    try:
        parsed = urlparse(referrer)
        return parsed.hostname or ''
    except Exception:
        return ''


def _detect_device(screen_width):
    """Simple device detection from screen width"""
    if screen_width < 768:
        return 'mobile'
    elif screen_width < 1024:
        return 'tablet'
    return 'desktop'


def _flush_events():
    """Background thread: flush event queue to SQLite every 2 seconds"""
    while True:
        time.sleep(2)
        if not _event_queue:
            continue
        events = []
        with _flush_lock:
            while _event_queue:
                events.append(_event_queue.popleft())
        if not events:
            continue
        try:
            conn = _get_db()
            conn.executemany('''
                INSERT INTO analytics_events
                (site_id, event_type, fingerprint, page_path, referrer, referrer_domain,
                 user_agent, device_type, screen_width, screen_height, language, country,
                 gclid, utm_source, utm_medium, utm_campaign)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', events)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f'[Analytics] Flush error: {e}')


def _start_flush_thread():
    """Start the background flush thread (daemon)"""
    global _flush_thread
    if _flush_thread is None or not _flush_thread.is_alive():
        _flush_thread = threading.Thread(target=_flush_events, daemon=True)
        _flush_thread.start()


# ============================================================
# TRACKER JAVASCRIPT
# ============================================================
TRACKER_JS = '''(function(){
var E='https://seoparai.com/api/t';
var S=document.currentScript?document.currentScript.getAttribute('data-site'):'';
if(window.__sat)return;window.__sat=1;
function gp(n){var m=location.search.match(new RegExp('[?&]'+n+'=([^&]*)'));return m?decodeURIComponent(m[1]):'';}
function gd(){var w=screen.width;return w<768?'mobile':w<1024?'tablet':'desktop';}
function rd(){try{if(!document.referrer)return'';var a=new URL(document.referrer);return a.hostname===location.hostname?'':a.hostname;}catch(e){return'';}}
var g=gp('gclid')||'';
if(g){try{sessionStorage.setItem('_sg',g);}catch(e){}}else{try{g=sessionStorage.getItem('_sg')||'';}catch(e){}}
function bp(t){return JSON.stringify({s:S,t:t,p:location.pathname+location.search,r:rd(),rf:document.referrer||'',sw:screen.width,sh:screen.height,l:navigator.language||'',d:gd(),g:g,us:gp('utm_source'),um:gp('utm_medium'),uc:gp('utm_campaign')});}
function sn(t){var d=bp(t);if(navigator.sendBeacon){navigator.sendBeacon(E,d);}else{var x=new XMLHttpRequest();x.open('POST',E,true);x.setRequestHeader('Content-Type','text/plain');x.send(d);}}
sn('pageview');
var hi=null;
function sh(){if(!hi)hi=setInterval(function(){sn('heartbeat');},15000);}
function ph(){if(hi){clearInterval(hi);hi=null;}}
sh();
document.addEventListener('visibilitychange',function(){if(document.hidden){ph();sn('exit');}else{sh();}});
window.addEventListener('pagehide',function(){sn('exit');});
document.addEventListener('click',function(e){var a=e.target.closest('a');if(!a)return;var h=a.getAttribute('href')||'';if(h.startsWith('tel:')||h.startsWith('mailto:')){var cd=JSON.stringify({s:S,t:'conversion',p:location.pathname,ct:h.startsWith('tel:')?'phone':'email',g:g});if(navigator.sendBeacon)navigator.sendBeacon(E,cd);else{var x=new XMLHttpRequest();x.open('POST',E,true);x.setRequestHeader('Content-Type','text/plain');x.send(cd);}}});
})();'''


# ============================================================
# FLASK ROUTES
# ============================================================
def register_analytics_routes(app):
    """Register all analytics routes on the Flask app"""
    _start_flush_thread()

    # --- Tracker endpoint (high volume, must be fast) ---
    @app.route('/api/t', methods=['POST', 'OPTIONS'])
    def track_event():
        if request.method == 'OPTIONS':
            resp = Response('', 204)
            resp.headers['Access-Control-Allow-Origin'] = '*'
            resp.headers['Access-Control-Allow-Methods'] = 'POST'
            resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return resp

        try:
            data = json.loads(request.get_data(as_text=True))
        except Exception:
            return Response('', 204)

        site_id = data.get('s', '')
        event_type = data.get('t', '')
        if site_id not in VALID_SITES or event_type not in VALID_EVENTS:
            return Response('', 204)

        ip = request.headers.get('X-Real-IP', request.remote_addr)
        ua = request.headers.get('User-Agent', '')
        fingerprint = _make_fingerprint(ip, ua)

        page_path = (data.get('p', '/') or '/')[:500]
        referrer = (data.get('rf', '') or '')[:500]
        referrer_domain = _get_referrer_domain(referrer)
        sw = int(data.get('sw', 0) or 0)
        sh = int(data.get('sh', 0) or 0)
        device = data.get('d', '') or _detect_device(sw)
        language = (data.get('l', '') or '')[:10]
        gclid = (data.get('g', '') or '')[:200]
        utm_source = (data.get('us', '') or '')[:100]
        utm_medium = (data.get('um', '') or '')[:100]
        utm_campaign = (data.get('uc', '') or '')[:100]

        # Handle conversion events from tel/mailto clicks
        if event_type == 'conversion' and gclid:
            conv_type = (data.get('ct', '') or '')[:50]
            try:
                conn = _get_db()
                conn.execute('''
                    UPDATE analytics_gclid SET converted=1, conversion_type=?, conversion_at=datetime('now')
                    WHERE gclid=? AND converted=0
                ''', (conv_type, gclid))
                conn.commit()
                conn.close()
            except Exception:
                pass

        # Queue event for batch insert
        event_tuple = (
            site_id, event_type, fingerprint, page_path, referrer, referrer_domain,
            ua[:500], device, sw, sh, language, '',  # country placeholder
            gclid, utm_source, utm_medium, utm_campaign
        )
        _event_queue.append(event_tuple)

        # Store gclid if present
        if gclid and event_type == 'pageview':
            try:
                conn = _get_db()
                conn.execute('''
                    INSERT OR IGNORE INTO analytics_gclid (gclid, site_id, fingerprint, landing_page)
                    VALUES (?, ?, ?, ?)
                ''', (gclid, site_id, fingerprint, page_path))
                conn.commit()
                conn.close()
            except Exception:
                pass

        # Update realtime
        if event_type in ('pageview', 'heartbeat'):
            try:
                conn = _get_db()
                now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
                conn.execute('''
                    INSERT INTO analytics_realtime (fingerprint, site_id, page_path, last_seen, session_start, page_count)
                    VALUES (?, ?, ?, ?, ?, 1)
                    ON CONFLICT(fingerprint, site_id) DO UPDATE SET
                        page_path=excluded.page_path,
                        last_seen=excluded.last_seen,
                        page_count=page_count+CASE WHEN excluded.page_path!=analytics_realtime.page_path THEN 1 ELSE 0 END
                ''', (fingerprint, site_id, page_path, now, now))
                conn.commit()
                conn.close()
            except Exception:
                pass

        resp = Response('', 204)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    # --- Serve tracker JS ---
    @app.route('/api/t.js', methods=['GET'])
    def serve_tracker_js():
        resp = Response(TRACKER_JS, mimetype='application/javascript')
        resp.headers['Cache-Control'] = 'public, max-age=3600'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    # --- Analytics overview ---
    @app.route('/api/analytics/overview', methods=['GET'])
    def analytics_overview():
        site_id = request.args.get('site_id', 'all')
        period = request.args.get('period', '7d')
        days = int(period.replace('d', '')) if period.endswith('d') else 7

        conn = _get_db()
        start_date = (date.today() - timedelta(days=days)).isoformat()
        today = date.today().isoformat()

        where = "created_date >= ?"
        params = [start_date]
        if site_id != 'all':
            where += " AND site_id = ?"
            params.append(site_id)

        # Pageviews
        pv = conn.execute(f"SELECT COUNT(*) FROM analytics_events WHERE event_type='pageview' AND {where}", params).fetchone()[0]
        # Unique visitors
        uv = conn.execute(f"SELECT COUNT(DISTINCT fingerprint) FROM analytics_events WHERE event_type='pageview' AND {where}", params).fetchone()[0]

        # Today's stats
        today_params = [today] + ([site_id] if site_id != 'all' else [])
        today_where = "created_date = ?" + (" AND site_id = ?" if site_id != 'all' else "")
        today_pv = conn.execute(f"SELECT COUNT(*) FROM analytics_events WHERE event_type='pageview' AND {today_where}", today_params).fetchone()[0]
        today_uv = conn.execute(f"SELECT COUNT(DISTINCT fingerprint) FROM analytics_events WHERE event_type='pageview' AND {today_where}", today_params).fetchone()[0]

        # Per-site breakdown
        sites = {}
        for sid in VALID_SITES:
            s_pv = conn.execute("SELECT COUNT(*) FROM analytics_events WHERE event_type='pageview' AND site_id=? AND created_date >= ?", (sid, start_date)).fetchone()[0]
            s_uv = conn.execute("SELECT COUNT(DISTINCT fingerprint) FROM analytics_events WHERE event_type='pageview' AND site_id=? AND created_date >= ?", (sid, start_date)).fetchone()[0]
            sites[sid] = {'pageviews': s_pv, 'visitors': s_uv}

        conn.close()
        return jsonify({
            'period': period,
            'total_pageviews': pv,
            'unique_visitors': uv,
            'today_pageviews': today_pv,
            'today_visitors': today_uv,
            'sites': sites
        })

    # --- Realtime ---
    @app.route('/api/analytics/realtime', methods=['GET'])
    def analytics_realtime():
        conn = _get_db()
        cutoff = (datetime.utcnow() - timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%S')
        # Clean old
        conn.execute("DELETE FROM analytics_realtime WHERE last_seen < ?", (cutoff,))
        conn.commit()

        rows = conn.execute("SELECT site_id, page_path, COUNT(*) as cnt FROM analytics_realtime GROUP BY site_id, page_path ORDER BY cnt DESC").fetchall()
        total = conn.execute("SELECT COUNT(DISTINCT fingerprint) FROM analytics_realtime").fetchone()[0]

        by_site = {}
        active_pages = []
        for row in rows:
            sid = row['site_id']
            by_site[sid] = by_site.get(sid, 0) + row['cnt']
            active_pages.append({'site': sid, 'path': row['page_path'], 'visitors': row['cnt']})

        conn.close()
        return jsonify({
            'active_now': total,
            'by_site': by_site,
            'active_pages': active_pages[:20]
        })

    # --- Charts: Visitors per day ---
    @app.route('/api/charts/analytics-visitors', methods=['GET'])
    def chart_visitors():
        days = int(request.args.get('days', 30))
        site_id = request.args.get('site_id', 'all')
        conn = _get_db()
        start_date = (date.today() - timedelta(days=days)).isoformat()

        dates = []
        d = date.today() - timedelta(days=days)
        for i in range(days + 1):
            dates.append((d + timedelta(days=i)).isoformat())

        sites_data = {}
        for sid in VALID_SITES:
            if site_id != 'all' and sid != site_id:
                continue
            rows = conn.execute('''
                SELECT created_date, COUNT(DISTINCT fingerprint) as visitors
                FROM analytics_events
                WHERE event_type='pageview' AND site_id=? AND created_date >= ?
                GROUP BY created_date
            ''', (sid, start_date)).fetchall()
            day_map = {r['created_date']: r['visitors'] for r in rows}
            sites_data[sid] = [day_map.get(d, 0) for d in dates]

        conn.close()
        return jsonify({'dates': dates, 'sites': sites_data})

    # --- Charts: Top pages ---
    @app.route('/api/charts/analytics-pages', methods=['GET'])
    def chart_pages():
        days = int(request.args.get('days', 7))
        site_id = request.args.get('site_id', 'all')
        conn = _get_db()
        start_date = (date.today() - timedelta(days=days)).isoformat()

        where = "event_type='pageview' AND created_date >= ?"
        params = [start_date]
        if site_id != 'all':
            where += " AND site_id = ?"
            params.append(site_id)

        rows = conn.execute(f'''
            SELECT page_path, COUNT(*) as views
            FROM analytics_events WHERE {where}
            GROUP BY page_path ORDER BY views DESC LIMIT 20
        ''', params).fetchall()

        conn.close()
        return jsonify({'pages': [{'path': r['page_path'], 'views': r['views']} for r in rows]})

    # --- Charts: Referrers ---
    @app.route('/api/charts/analytics-referrers', methods=['GET'])
    def chart_referrers():
        days = int(request.args.get('days', 7))
        site_id = request.args.get('site_id', 'all')
        conn = _get_db()
        start_date = (date.today() - timedelta(days=days)).isoformat()

        where = "event_type='pageview' AND created_date >= ?"
        params = [start_date]
        if site_id != 'all':
            where += " AND site_id = ?"
            params.append(site_id)

        rows = conn.execute(f'''
            SELECT CASE WHEN referrer_domain='' THEN 'direct' ELSE referrer_domain END as domain,
                   COUNT(*) as cnt
            FROM analytics_events WHERE {where}
            GROUP BY domain ORDER BY cnt DESC LIMIT 10
        ''', params).fetchall()

        conn.close()
        return jsonify({'referrers': [{'domain': r['domain'], 'count': r['cnt']} for r in rows]})

    # --- Charts: Devices ---
    @app.route('/api/charts/analytics-devices', methods=['GET'])
    def chart_devices():
        days = int(request.args.get('days', 7))
        site_id = request.args.get('site_id', 'all')
        conn = _get_db()
        start_date = (date.today() - timedelta(days=days)).isoformat()

        where = "event_type='pageview' AND created_date >= ?"
        params = [start_date]
        if site_id != 'all':
            where += " AND site_id = ?"
            params.append(site_id)

        rows = conn.execute(f'''
            SELECT device_type, COUNT(*) as cnt
            FROM analytics_events WHERE {where}
            GROUP BY device_type
        ''', params).fetchall()

        result = {'desktop': 0, 'mobile': 0, 'tablet': 0}
        for r in rows:
            if r['device_type'] in result:
                result[r['device_type']] = r['cnt']

        conn.close()
        return jsonify(result)

    # --- Charts: Bounce rate trend ---
    @app.route('/api/charts/analytics-bounce', methods=['GET'])
    def chart_bounce():
        days = int(request.args.get('days', 30))
        conn = _get_db()
        start_date = (date.today() - timedelta(days=days)).isoformat()

        rows = conn.execute('''
            SELECT date, bounce_rate FROM analytics_daily
            WHERE date >= ? ORDER BY date
        ''', (start_date,)).fetchall()

        conn.close()
        return jsonify({
            'dates': [r['date'] for r in rows],
            'rates': [r['bounce_rate'] for r in rows]
        })

    # --- Google Ads: List gclids ---
    @app.route('/api/analytics/gclid', methods=['GET'])
    def list_gclids():
        days = int(request.args.get('days', 30))
        conn = _get_db()
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%S')

        rows = conn.execute('''
            SELECT * FROM analytics_gclid WHERE first_seen >= ? ORDER BY first_seen DESC
        ''', (start_date,)).fetchall()

        total = len(rows)
        converted = sum(1 for r in rows if r['converted'])
        pending = sum(1 for r in rows if r['converted'] and not r['sent_to_google'])

        conn.close()
        return jsonify({
            'total_clicks': total,
            'converted': converted,
            'pending_upload': pending,
            'clicks': [dict(r) for r in rows]
        })

    # --- Google Ads: Mark conversion ---
    @app.route('/api/analytics/gclid/convert', methods=['POST'])
    def convert_gclid():
        data = request.json or {}
        gclid = data.get('gclid', '')
        conv_type = data.get('conversion_type', 'manual')
        if not gclid:
            return jsonify({'error': 'gclid required'}), 400

        conn = _get_db()
        conn.execute('''
            UPDATE analytics_gclid SET converted=1, conversion_type=?, conversion_at=datetime('now')
            WHERE gclid=? AND converted=0
        ''', (conv_type, gclid))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

    # --- Aggregation ---
    @app.route('/api/analytics/aggregate', methods=['POST'])
    def aggregate_analytics():
        conn = _get_db()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        target_date = request.args.get('date', yesterday)

        for sid in VALID_SITES:
            # Pageviews
            pv = conn.execute(
                "SELECT COUNT(*) FROM analytics_events WHERE event_type='pageview' AND site_id=? AND created_date=?",
                (sid, target_date)).fetchone()[0]
            uv = conn.execute(
                "SELECT COUNT(DISTINCT fingerprint) FROM analytics_events WHERE event_type='pageview' AND site_id=? AND created_date=?",
                (sid, target_date)).fetchone()[0]

            # Top pages
            pages = conn.execute('''
                SELECT page_path, COUNT(*) as v FROM analytics_events
                WHERE event_type='pageview' AND site_id=? AND created_date=?
                GROUP BY page_path ORDER BY v DESC LIMIT 20
            ''', (sid, target_date)).fetchall()
            top_pages = json.dumps([{'path': r[0], 'views': r[1]} for r in pages])

            # Top referrers
            refs = conn.execute('''
                SELECT CASE WHEN referrer_domain='' THEN 'direct' ELSE referrer_domain END as d, COUNT(*) as c
                FROM analytics_events WHERE event_type='pageview' AND site_id=? AND created_date=?
                GROUP BY d ORDER BY c DESC LIMIT 20
            ''', (sid, target_date)).fetchall()
            top_refs = json.dumps([{'domain': r[0], 'count': r[1]} for r in refs])

            # Devices
            devs = conn.execute('''
                SELECT device_type, COUNT(*) FROM analytics_events
                WHERE event_type='pageview' AND site_id=? AND created_date=?
                GROUP BY device_type
            ''', (sid, target_date)).fetchall()
            devices = json.dumps({r[0]: r[1] for r in devs})

            # Languages
            langs = conn.execute('''
                SELECT language, COUNT(*) FROM analytics_events
                WHERE event_type='pageview' AND site_id=? AND created_date=? AND language!=''
                GROUP BY language ORDER BY 2 DESC LIMIT 10
            ''', (sid, target_date)).fetchall()
            languages = json.dumps({r[0]: r[1] for r in langs})

            # Bounce: fingerprints with only 1 pageview
            fps = conn.execute('''
                SELECT fingerprint, COUNT(*) as pv FROM analytics_events
                WHERE event_type='pageview' AND site_id=? AND created_date=?
                GROUP BY fingerprint
            ''', (sid, target_date)).fetchall()
            total_sessions = len(fps)
            bounced = sum(1 for r in fps if r[1] == 1)
            bounce_rate = (bounced / total_sessions * 100) if total_sessions > 0 else 0

            conn.execute('''
                INSERT INTO analytics_daily (site_id, date, total_pageviews, unique_visitors, total_sessions,
                    bounced_sessions, bounce_rate, top_pages, top_referrers, devices, languages)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(site_id, date) DO UPDATE SET
                    total_pageviews=excluded.total_pageviews, unique_visitors=excluded.unique_visitors,
                    total_sessions=excluded.total_sessions, bounced_sessions=excluded.bounced_sessions,
                    bounce_rate=excluded.bounce_rate, top_pages=excluded.top_pages,
                    top_referrers=excluded.top_referrers, devices=excluded.devices,
                    languages=excluded.languages, aggregated_at=datetime('now')
            ''', (sid, target_date, pv, uv, total_sessions, bounced, round(bounce_rate, 1),
                  top_pages, top_refs, devices, languages))

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'date': target_date})

    # --- Purge old events ---
    @app.route('/api/analytics/purge', methods=['POST'])
    def purge_analytics():
        conn = _get_db()
        cutoff = (date.today() - timedelta(days=90)).isoformat()
        deleted = conn.execute("DELETE FROM analytics_events WHERE created_date < ?", (cutoff,)).rowcount
        # Clean old salts
        conn.execute("DELETE FROM analytics_salt WHERE date < ?", (cutoff,))
        conn.commit()
        conn.execute("VACUUM")
        conn.close()
        return jsonify({'success': True, 'deleted_events': deleted})

    print('[Analytics] Routes registered, flush thread started')
