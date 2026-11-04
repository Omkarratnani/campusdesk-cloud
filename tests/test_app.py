"""Isolated smoke tests for CampusDesk Cloud."""
import os, re, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(script):
    with tempfile.TemporaryDirectory() as directory:
        env={**os.environ,"DATABASE_URL":"sqlite:///"+directory+"/test.db","SECRET_KEY":"isolated-test-secret"}
        result=subprocess.run([sys.executable,"-c",script],cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
        assert result.returncode==0,result.stderr
def test_registration_ticket_and_access():
    run("""
import re
from fastapi.testclient import TestClient
from app import app
with TestClient(app) as c:
    assert c.get('/health').json()['database']=='connected'
    assert 'One clear solution' in c.get('/').text
    csrf=re.search(r'name="_csrf" value="([^"]+)',c.get('/register').text).group(1)
    r=c.post('/register',data={'name':'Test Student','email':'test@example.edu','password':'Passphrase123!','_csrf':csrf},follow_redirects=True)
    assert 'My support dashboard' in r.text
    csrf=re.search(r'name="_csrf" value="([^"]+)',r.text).group(1)
    r=c.post('/tickets/new',data={'title':'Campus Wi-Fi issue','description':'The campus network is disconnecting.','category':'Network','priority':'High','_csrf':csrf},follow_redirects=True)
    assert 'Campus Wi-Fi issue' in r.text
    assert c.get('/admin',follow_redirects=False).status_code==403
    assert c.get('/api/summary',follow_redirects=False).status_code==403
    assert c.post('/tickets/new',data={'_csrf':'bad'}).status_code==403
""")
def test_admin_update_and_api():
    run("""
import re
from fastapi.testclient import TestClient
from app import app
from seed_demo import *
with TestClient(app) as c:
    csrf=re.search(r'name="_csrf" value="([^"]+)',c.get('/login').text).group(1)
    r=c.post('/login',data={'email':'admin@demo.edu','password':'AdminDemo123!','_csrf':csrf},follow_redirects=True)
    assert 'Admin overview' in r.text
    assert c.get('/api/summary').json()['total']==5
    csrf=re.search(r'name="_csrf" value="([^"]+)',r.text).group(1)
    r=c.post('/tickets/1/update',data={'state':'Resolved','priority':'Low','note':'Fixed','_csrf':csrf},follow_redirects=True)
    assert r.status_code==200
""")
