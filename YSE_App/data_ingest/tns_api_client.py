"""
Minimal TNS HTTP API helpers (no astro_prost / antares / django_cron imports).

Used by management commands and tooling that must not import all of TNS_uploads.py.
"""

from __future__ import annotations

import json
from collections import OrderedDict

import requests


def format_to_json(source):
    return json.loads(source, object_pairs_hook=OrderedDict)


def search(url, json_list, api_key, tns_bot_id, tns_bot_name):
    try:
        search_url = url + "/search"
        headers = {
            "User-Agent": (
                'tns_marker{"tns_id":'
                + str(tns_bot_id)
                + ', "type":"bot", "name":"'
                + tns_bot_name
                + '"}'
            )
        }
        json_file = OrderedDict(json_list)
        search_data = {"api_key": api_key, "data": json.dumps(json_file)}
        return requests.post(search_url, headers=headers, data=search_data)
    except Exception as exc:
        raise RuntimeError(f"TNS search failed: {exc}") from exc


def get(url, json_list, api_key, tns_bot_id, tns_bot_name):
    try:
        get_url = url + "/object"
        headers = {
            "User-Agent": (
                'tns_marker{"tns_id":'
                + str(tns_bot_id)
                + ', "type":"bot", "name":"'
                + tns_bot_name
                + '"}'
            )
        }
        json_file = OrderedDict(json_list)
        get_data = {"api_key": api_key, "data": json.dumps(json_file)}
        return requests.post(get_url, headers=headers, data=get_data)
    except Exception as exc:
        raise RuntimeError(f"TNS get failed: {exc}") from exc
