#!/usr/bin/env python3
from flask import Flask, jsonify
import subprocess, json, requests, smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)

ALERT_EMAIL = 'michaelperron12@gmail.com'
FIREWORKS_API_KEY = 'fw_CbsGnsaL5NSi4wgasWhjtQ'

def run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except:
        return ''

def send_alert(subject, message):
    try:
        msg = MIMEText(message)
        msg['Subject'] = f'[ALERTE SERVEUR] {subject}'
        msg['From'] = 'alert@seoparai.com'
        msg['To'] = ALERT_EMAIL
        with smtplib.SMTP('localhost', 25) as server:
            server.send_message(msg)
        return True
    except Exception as e:
        print(f'Email error: {e}')
        return False

def check_fireworks():
    result = {'status': 'ok', 'models': {}, 'checked_at': datetime.now().isoformat()}
    models = {
        'qwen3-vl-235b': 'accounts/fireworks/models/qwen3-vl-235b-a22b-instruct',
        'deepseek-v3': 'accounts/fireworks/models/deepseek-v3p2'
    }
    all_ok = True
    for name, model_id in models.items():
        try:
            resp = requests.post(
                'https://api.fireworks.ai/inference/v1/chat/completions',
                headers={'Authorization': f'Bearer {FIREWORKS_API_KEY}', 'Content-Type': 'application/json'},
                json={'model': model_id, 'messages': [{'role': 'user', 'content': '1'}], 'max_tokens': 1},
                timeout=20
            )
            ok = resp.status_code == 200
            result['models'][name] = {'ok': ok, 'ms': int(resp.elapsed.total_seconds() * 1000)}
            if not ok: all_ok = False
        except Exception as e:
            result['models'][name] = {'ok': False, 'error': str(e)[:50]}
            all_ok = False
    result['status'] = 'ok' if all_ok else 'error'
    return result

def check_facturation():
    try:
        resp = requests.get('http://localhost:8001/api/health', timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {'status': data.get('status', 'unknown'), 'db_ok': data.get('checks', {}).get('database', {}).get('status') == 'ok'}
        return {'status': 'error', 'code': resp.status_code}
    except Exception as e:
        return {'status': 'down', 'error': str(e)[:50]}

@app.route('/api/security-status')
def security_status():
    data = {}
    alerts_to_send = []
    
    svc = {}
    for name in ['fail2ban','crowdsec','netdata','nginx','postfix','facturation']:
        svc[name] = run(f'systemctl is-active {name}') == 'active'
        if not svc[name] and name in ['facturation', 'nginx']:
            alerts_to_send.append(f'Service {name} est DOWN!')
    data['services'] = svc

    containers = {}
    for c in ['uptime-kuma','n8n']:
        out = run('docker inspect -f "{{.State.Running}}" ' + c + ' 2>/dev/null')
        containers[c] = out == 'true'
    data['containers'] = containers

    f2b = {'jails': 0, 'total_banned': 0, 'jail_names': []}
    f2b_out = run('sudo fail2ban-client status')
    if 'Jail list' in f2b_out:
        jails = [j.strip() for j in f2b_out.split('Jail list:')[1].strip().split(',') if j.strip()]
        f2b['jails'] = len(jails)
        f2b['jail_names'] = jails
        total = 0
        for jail in jails:
            j_out = run('sudo fail2ban-client status ' + jail)
            if 'Currently banned' in j_out:
                try: total += int(j_out.split('Currently banned:')[1].split('\n')[0].strip())
                except: pass
        f2b['total_banned'] = total
    data['fail2ban'] = f2b

    cs = {'active_decisions': 0, 'version': ''}
    cs_out = run('sudo cscli decisions list -o json 2>/dev/null')
    try:
        d = json.loads(cs_out) if cs_out and cs_out != 'null' else []
        cs['active_decisions'] = len(d) if d else 0
    except: pass
    v = run('cscli version 2>&1 | head -1')
    cs['version'] = v.split('version:')[1].strip() if 'version:' in v else ''
    data['crowdsec'] = cs

    lynis = {'score': 'N/A', 'date': 'N/A'}
    try:
        with open('/opt/seo-agent/security/last-audit.json') as f:
            a = json.load(f)
            lynis['score'] = a.get('score', 'N/A') or 'N/A'
            lynis['date'] = a.get('date', 'N/A')
    except: pass
    data['lynis'] = lynis

    backup = {'date': 'N/A', 'size': 'N/A'}
    try:
        with open('/opt/seo-agent/security/last-backup.json') as f:
            b = json.load(f)
            backup['date'] = b.get('date', 'N/A')
            backup['size'] = b.get('size', 'N/A')
    except: pass
    data['backup'] = backup

    data['ufw'] = {'active': 'Status: active' in run('sudo ufw status')}

    certs = {}
    for d in ['seoparai.com','jcpeintre.com','deneigement-excellence.ca','paysagiste-excellence.ca','facturation.deneigement-excellence.ca']:
        exp = run(f'echo | openssl s_client -servername {d} -connect {d}:443 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null')
        certs[d] = exp.replace('notAfter=', '') if 'notAfter=' in exp else 'OK'
    data['ssl'] = certs

    kuma = {'monitors': []}
    try:
        sql = "SELECT m.name, (SELECT h.status FROM heartbeat h WHERE h.monitor_id=m.id ORDER BY h.time DESC LIMIT 1), (SELECT h.ping FROM heartbeat h WHERE h.monitor_id=m.id ORDER BY h.time DESC LIMIT 1) FROM monitor m WHERE m.active=1"
        out = run(f'docker exec uptime-kuma sqlite3 /app/data/kuma.db "{sql}"')
        for line in out.split('\n'):
            p = line.split('|')
            if len(p) >= 3:
                kuma['monitors'].append({'name': p[0], 'up': p[1] == '1', 'ping': int(p[2]) if p[2].isdigit() else 0})
    except: pass
    data['uptime_kuma'] = kuma

    try:
        df_out = run('df -h /').split('\n')
        disk_pct = df_out[1].split()[4] if len(df_out) >= 2 else 'N/A'
    except: disk_pct = 'N/A'
    
    ram_total, ram_used, ram_pct = 0, 0, 'N/A'
    try:
        for line in run('free -m').split('\n'):
            if line.startswith('Mem:'):
                parts = line.split()
                ram_total, ram_used = int(parts[1]), int(parts[2])
                ram_pct = f'{round(ram_used / ram_total * 100)}%'
                break
    except: pass
    data['resources'] = {'disk_pct': disk_pct, 'ram_pct': ram_pct, 'ram_used': f'{ram_used}M', 'ram_total': f'{ram_total}M'}

    fireworks = check_fireworks()
    data['fireworks'] = fireworks
    if fireworks['status'] != 'ok':
        failed = [k for k, v in fireworks['models'].items() if not v.get('ok')]
        alerts_to_send.append(f'Fireworks AI ERREUR! Modeles: {", ".join(failed)}')

    facturation = check_facturation()
    data['facturation'] = facturation
    if facturation.get('status') not in ['ok', 'degraded']:
        alerts_to_send.append(f'Systeme soumission DOWN! Status: {facturation.get("status")}')

    if alerts_to_send:
        msg = f"ALERTES SERVEUR - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n" + '\n'.join(f'- {a}' for a in alerts_to_send) + "\n\nVerifiez: https://seoparai.com/dashboard"
        send_alert('Probleme detecte', msg)
        data['alerts_sent'] = alerts_to_send

    return jsonify(data)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8919, debug=False)
