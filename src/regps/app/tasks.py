# regps/app/tasks.py

import celery
import falcon
import os
import requests
from time import sleep

dbrok = "redis://redis:6379/0"
dback = "redis://redis:6379/0"

CELERY_BROKER = os.environ.get('CELERY_BROKER')
if CELERY_BROKER is None:
    print(f"CELERY_BROKER is not set. Using default {dbrok}")
    CELERY_BROKER = dbrok
CELERY_BACKEND = os.environ.get('CELERY_BACKEND')
if CELERY_BACKEND is None:
    print(f"CELERY_BACKEND is not set. Using default {dback}")
    CELERY_BACKEND = dback
    
app = celery.Celery('tasks', broker=CELERY_BROKER, backend=CELERY_BACKEND)

purl = "http://localhost:7676/presentations/"
aurl = "http://localhost:7676/authorizations/"

@app.task
def check_login(aid) -> falcon.Response:
    print("checking login: aid {}".format(aid))
    gres = requests.get(aurl+f"{aid}", headers={"Content-Type": "application/json"})
    print("login status: {}".format(gres))
    return gres

@app.task
def verify(aid,said,vlei) -> falcon.Response:
    # first check to see if we're already logged in
    gres = check_login(aid)
    if gres.status_code == falcon.http_status_to_code(falcon.HTTP_ACCEPTED):
        print("already logged in")
        return gres
    else:
        print("putting to {}".format(purl+f"{said}"))
        pres = requests.put(purl+f"{said}", headers={"Content-Type": "application/json+cesr"}, data=vlei)
        print("put response {}".format(pres.text))
        if pres.status_code == falcon.http_status_to_code(falcon.HTTP_ACCEPTED):
            gres = None
            while(gres == None or gres.status_code == falcon.http_status_to_code(falcon.HTTP_404)):
                gres = check_login(aid)
                print("polling result {}".format(gres.text))
                sleep (1)
            return gres
        else:
            return pres
        
    