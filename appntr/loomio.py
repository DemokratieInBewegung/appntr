from django.conf import settings
import requests
from requests_oauthlib import OAuth2Session
from .models import CfgOption
import json

import requests
import logging

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



BASE_URI = "https://www.loomio.org/api/v1/"
CREATE_DISCUSSION_URI = BASE_URI + "discussions.json"
# DISCUSSION_URI = BASE_URI + "discussion/{}.json"
CREATE_PROPOSAL_URI = BASE_URI + "proposals.json"
PROPOSAL_URI = BASE_URI + "proposals/{}.json"


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

	return OAuth2Session(settings.LOOMIO_CLIENT_ID, 
			token=json.loads(model.value),
			auto_refresh_url="https://www.loomio.org/oauth/token",
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


def create_discussion(title, content):
	return _make_request("post", CREATE_DISCUSSION_URI, {
		"discussion": {
			"title": title,
			"description": content,
			"group_id":  settings.LOOMIO_GROUP,
			"attachments_ids": [],
			"uses_markdown": True,
			"private": True,
			"make_announcement": False,
		}})['discussions'][0]


def update_discussion(title, content):
	return _make_request("put", CREATE_DISCUSSION_URI, {
		"discussion": {
			"title": title,
			"description": content,
			"group_id":  settings.LOOMIO_GROUP,
			"attachments_ids": [],
			"uses_markdown": True,
			"private": True,
			"make_announcement": False,
		}})['discussions'][0]


def create_proposal(discussion_id, title, datetime, description=""):
	return _make_request("post", CREATE_PROPOSAL_URI, {
		"motion": {
			"name": title,
			"description": description,
			"discussion_id": discussion_id,
			"attachments_ids": [],
			"closing_time": datetime.isoformat(),
			"outcome": ""
		}})['proposals'][0]


def calc_result(proposal):
	vc = proposal["vote_counts"]
	no = vc["block"] + vc["no"]
	abstain = vc["abstain"]
	yes = vc["yes"]

	if (yes + no) < abstain:
		return "abstain"
	if yes >= no:
		return "yes"
	return "no"


def get_proposal(proposal_id):
	return _make_request("get", PROPOSAL_URI.format(proposal_id)
			)["proposals"][0]