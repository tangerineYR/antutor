"""Create private, disposable local service settings. Never overwrites a file."""
import argparse
import os
import secrets
import time
from pathlib import Path
import jwt


def create(path: Path):
    signing_key = secrets.token_urlsafe(48)
    values = {
        'SECRET_KEY': secrets.token_urlsafe(48),
        'LOCAL_DB_PASSWORD': secrets.token_urlsafe(32),
        'LOCAL_NEO4J_PASSWORD': secrets.token_urlsafe(32),
        'LOCAL_SUPABASE_JWT_SECRET': signing_key,
        'SUPABASE_URL': 'http://localhost:54321',
        'SUPABASE_KEY': jwt.encode({'role': 'service_role', 'iss': 'antutor-local',
                                   'iat': int(time.time()), 'exp': int(time.time()) + 86400*30}, signing_key, algorithm='HS256'),
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USER': 'neo4j',
        'ENABLE_BENCHMARK_ENDPOINT': 'false',
        'ENABLE_KOREAN_TRANSLATION': 'false',
    }
    values['NEO4J_PASSWORD'] = values['LOCAL_NEO4J_PASSWORD']
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as stream:
        stream.write('# Generated local-only credentials. Do not publish or commit.\n')
        stream.write('\n'.join(f'{key}={value}' for key,value in values.items()) + '\n')
    print('Created local settings; credential values were not printed. Token expires in 30 days.')

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1]/'.env')
    create(parser.parse_args().output)
