#!/usr/bin/env python3
"""
Fireworks AI Status Monitor - Teste tous les modeles utilises sur le serveur
"""

import os
import json
import requests
from datetime import datetime

FIREWORKS_API_KEY = os.getenv('FIREWORKS_API_KEY', 'fw_CbsGnsaL5NSi4wgasWhjtQ')
FIREWORKS_URL = 'https://api.fireworks.ai/inference/v1/chat/completions'

MODELS = {
    'qwen3-vl-235b': {
        'id': 'accounts/fireworks/models/qwen3-vl-235b-a22b-instruct',
        'usage': 'Extraction AI documents (facturation)',
        'critical': True
    },
    'qwen3-235b': {
        'id': 'accounts/fireworks/models/qwen3-235b-a22b-instruct-2507',
        'usage': 'Text generation general',
        'critical': True
    },
    'deepseek-v3': {
        'id': 'accounts/fireworks/models/deepseek-v3p2',
        'usage': 'SEO analysis, content generation',
        'critical': True
    },
}

def test_model(model_name, model_info):
    try:
        response = requests.post(
            FIREWORKS_URL,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {FIREWORKS_API_KEY}'
            },
            json={
                'model': model_info['id'],
                'messages': [{'role': 'user', 'content': '1'}],
                'max_tokens': 1
            },
            timeout=20
        )
        if response.status_code == 200:
            return {'status': 'ok', 'response_time_ms': int(response.elapsed.total_seconds() * 1000)}
        else:
            return {'status': 'error', 'code': response.status_code}
    except requests.exceptions.Timeout:
        return {'status': 'timeout'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)[:50]}

def check_all_models():
    results = {
        'timestamp': datetime.now().isoformat(),
        'overall_status': 'ok',
        'models': {}
    }
    
    critical_failed = False
    for name, info in MODELS.items():
        result = test_model(name, info)
        result['usage'] = info['usage']
        result['critical'] = info['critical']
        results['models'][name] = result
        if result['status'] != 'ok' and info['critical']:
            critical_failed = True
    
    if critical_failed:
        results['overall_status'] = 'critical_failure'
    elif any(r['status'] != 'ok' for r in results['models'].values()):
        results['overall_status'] = 'degraded'
    
    return results

if __name__ == '__main__':
    status = check_all_models()
    print(json.dumps(status, indent=2))
    with open('/opt/seo-agent/security/fireworks-status.json', 'w') as f:
        json.dump(status, f, indent=2)
