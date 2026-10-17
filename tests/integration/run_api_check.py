"""Start/stop an isolated API process using generated local settings."""
import os
import subprocess
import sys
import time
from pathlib import Path
import httpx
from dotenv import dotenv_values

root=Path(__file__).resolve().parents[2]
environment={**dotenv_values(root/'.env'), **os.environ}
with (root/'api-integration.log').open('w') as log:
    process=subprocess.Popen([sys.executable,'-m','uvicorn','main:app','--host','127.0.0.1','--port','8082'],
                             cwd=root/'back',env=environment,stdout=log,stderr=log)
    try:
        for attempt in range(60):
            if process.poll() is not None: raise RuntimeError('API startup failed; inspect api-integration.log')
            try:
                if httpx.get('http://127.0.0.1:8082/',timeout=1).status_code==200: break
            except httpx.RequestError: pass
            time.sleep(.5)
        else: raise RuntimeError('API readiness timed out')
        subprocess.run([sys.executable,str(root/'tests/integration/check_api.py')],env=environment,check=True)
    finally:
        process.terminate()
        process.wait(timeout=10)
