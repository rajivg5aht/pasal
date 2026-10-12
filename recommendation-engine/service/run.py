"""Start local API, loading only its service token from the ignored root .env."""
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'recommendation-engine'))

if __name__=='__main__':
    path=ROOT/'.env'
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith('RECOMMENDATION_SERVICE_TOKEN='):
                key,value=line.split('=',1)
                os.environ.setdefault(key,value.strip())
    import uvicorn
    uvicorn.run('service.app:create_app',factory=True,host='127.0.0.1',port=8000,
                workers=1,access_log=False)
