from django.conf import settings
import requests
from requests_oauthlib import OAuth2Session
from .models import CfgOption
from django.utils.dateparse import parse_datetime
import json

import requests
import logging
import time

# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True



BASE_URI = "https://loomio.bewegung.jetzt/api/v1/"
DISCUSSIONS_URI = BASE_URI + "discussions.json"
DISCUSSION_URI = BASE_URI + "discussions/{}.json"
PROPOSALS_URI = BASE_URI + "polls.json"
PROPOSAL_URI = BASE_URI + "polls/{}.json"
MOVE_DISCUSSION_URI = BASE_URI + "discussions/{}/move"
PROPOSAL_URI = BASE_URI + "polls/{}.json"


class LoomioError(Exception):

	def __init__(self, code, message):
		self.code = code
		self.message = message

	def __str__(self):
		return "Loomio Response Error({}): {}".format(self.code, self.message)


def check_error(resp):
	if resp.status_code >= 300:
		raise LoomioError(resp.status_code, resp.text)

def get_client():

	model = CfgOption.objects.get(pk="LOOMIO_TOKEN")
	def update_token(token):
		model.value = json.dumps(token)
		model.save()

	token = json.loads(model.value)
	token['expires_in'] = int(token['created_at']) + int(token['expires_in']) - time.time()

	print(token)

	return OAuth2Session(settings.LOOMIO_CLIENT_ID, 
			token=token,
			auto_refresh_url="https://loomio.bewegung.jetzt/oauth/token",
			auto_refresh_kwargs={
				"client_id": settings.LOOMIO_CLIENT_ID,
				"client_secret": settings.LOOMIO_CLIENT_SECRET
			},
			token_updater=update_token)


def _make_request(method, uri, data=dict()):
	resp = getattr(get_client(), method)(uri, 
			# +'?access_token=' + settings.LOOMIO_ACCESS_TOKEN ,
			headers={'Content-Type': 'application/json; charset=utf-8'},
			json=data,
			allow_redirects=False)

	check_error(resp)
	return resp.json()


def get_discussion(discussion_id): 
	return _make_request("get", DISCUSSION_URI.format(discussion_id), {})['discussions'][0]


def create_discussion(title, content):
	return _make_request("post", DISCUSSIONS_URI, {
		"discussion": {
			"title": title,
			"description": content,
			"group_id":  settings.LOOMIO_INCOMING_GROUP,
			"attachments_ids": [],
			"uses_markdown": True,
			"private": True,
			"make_announcement": False,
		}})['discussions'][0]


def update_discussion(discussion_id, title, content):
	return _make_request("put", DISCUSSION_URI.format(discussion_id), {
		"discussion": {
			"title": title,
			"description": content
		}})['discussions'][0]

def postpone_proposal(proposal_id, datetime):
	return _make_request('patch', PROPOSAL_URI.format(proposal_id), {
		"poll": {
			"closing_at": datetime.replace(minute=0, second=0, microsecond=0).isoformat() + "Z",
			}
		})


def create_proposal(discussion_id, title, datetime, description=""):
	return _make_request("post", PROPOSALS_URI, {
		"poll": {
			"title": title,
			"details": description,
			"discussion_id": discussion_id,
			"poll_type": "proposal",
			"attachments_ids": [],
			"closing_at": datetime.replace(minute=0, second=0, microsecond=0).isoformat() + "Z",
			"poll_option_names": ["agree", "abstain", "disagree"]
		}})['polls'][0]


def get_vote_ended():
	return filter(lambda x: not x['active_proposal_id'],
			_make_request("get", DISCUSSIONS_URI + "?group_id={}&per=1000".format(settings.LOOMIO_INCOMING_GROUP)
		)['discussions'])


def get_votes_need_postponing(max_end_time):
	resp = _make_request("get", DISCUSSIONS_URI + "?group_id={}&per=1000".format(settings.LOOMIO_INCOMING_GROUP))
	props = { x['id'] : x for x in resp['polls'] }
	for dc in resp['discussions']:
		for pid in dc['active_poll_ids']:

			prop = props[pid]

			if int(prop['stances_count']) >= settings.MIN_VOTERS:
				continue # enough votes

			if parse_datetime(prop['closing_at']).replace(tzinfo=None) <= max_end_time:
				yield (dc, prop)


def move_discussion(discussion_id, target_group_id):
	return _make_request("patch", MOVE_DISCUSSION_URI.format(discussion_id), 
						{"group_id": target_group_id})



def calc_result(proposal):
	vc = proposal["stance_data"]
	no = vc["disagree"]
	abstain = vc["abstain"]
	yes = vc["agree"]

	if yes >= no:
		if abstain >= yes:
			return "abstain"
		return "yes"
	if abstain >= no:
		return "abstain"
	return "no"


def get_proposal(proposal_id):
	return _make_request("get", PROPOSAL_URI.format(proposal_id)
			)["polls"][0]

