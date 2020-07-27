#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""


import os
import logging
import subprocess

from celery import Celery
from celery.schedules import crontab

import rm_functions as rf


app = Celery('periodic', broker=os.environ.get('CELERY_BROKER_URL'),
						  backend=os.environ.get('CELERY_RESULT_BACKEND'))


@app.task(queue='periodic_queue')
def periodic_compressor():
	"""
	"""

	result = subprocess.check_output(['python',
    	'schema_compressor.py',
    	'-m', 'global',
    	'--g', os.environ.get('DEFAULTHGRAPH'),
    	'--s', os.environ.get('LOCAL_SPARQL'),
    	'--b', os.environ.get('BASE_URL')])


@app.task(queue='periodic_queue')
def periodic_remover():
	"""
	"""

	result = rf.periodic_remover(48,
		                         os.environ.get('DEFAULTHGRAPH'),
		                         os.environ.get('LOCAL_SPARQL'),
		                         os.environ.get('BASE_URL'),
		                         os.environ.get('VIRTUOSO_USER'),
		                         os.environ.get('VIRTUOSO_PASS'))


# add periodic tasks to the beat schedule
app.conf.beat_schedule = {
    "remover-task": {
    	"task": "periodic_jobs.periodic_remover",
    	"schedule": crontab(minute=0, hour='*')
    }
}
