import functools
import json

import requests
from django.contrib.gis.geoip2 import GeoIP2
from ipware import get_client_ip

from researchhub.settings import AMPLITUDE_API_KEY
from user.models import User
from utils.parsers import json_serial
from utils.sentry import log_info

geo = GeoIP2()


class Amplitude:
    api_key = AMPLITUDE_API_KEY
    api_url = "https://api.amplitude.com/2/httpapi"

    def _build_event_properties(self, view):
        data = view.__dict__
        event_type = f"{data['basename']}_{data['action']}"
        return event_type

    def _build_user_properties(self, user):
        if user.is_anonymous:
            user_properties = {
                "email": "",
                "first_name": "Anonymous",
                "last_name": "Anonymous",
                "reputation": 0,
                "is_suspended": False,
                "probable_spammer": False,
                "invited_by_id": 0,
                "is_hub_editor": False,
            }
            user_id = "_Anonymous_"
        else:
            invited_by = user.invited_by
            if invited_by:
                invited_by = invited_by.id
            user_properties = {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "reputation": user.reputation,
                "is_suspended": user.is_suspended,
                "probable_spammer": user.probable_spammer,
                "invited_by_id": invited_by,
                "is_hub_editor": user.is_hub_editor(),
            }
            user_id = f"user: {user.email}_{user.id}"
        return user_id, user_properties

    def _build_geo_properties(self, request):
        ip, is_routable = get_client_ip(request)
        data = {}
        try:
            geo_info = geo.city(ip)
            data["ip"] = ip
            data["country"] = geo_info["country_name"]
            data["city"] = geo_info["city"]
            data["region"] = geo_info["region"]
            data["dma"] = geo_info["dma_code"]
            data["location_lat"] = geo_info["latitude"]
            data["location_lng"] = geo_info["longitude"]
        except Exception as e:
            log_info(e)
            return {}
        return data

    def build_hit(self, res, view, request, *args, **kwargs):
        user = request.user
        user_id, user_properties = self._build_user_properties(user)
        event_type = self._build_event_properties(view)
        geo_properties = self._build_geo_properties(request)
        data = {
            "user_id": user_id,
            "event_type": event_type,
            "event_properties": res.data,
            "user_properties": user_properties,
            "insert_id": f"{event_type}_{res.data['id']}",
            **geo_properties,
        }
        hit = {
            "api_key": self.api_key,
            "events": [data],
        }
        self.hit = json.dumps(hit, default=json_serial)
        self.forward_event()

    def old_build_hit(self, request, data):
        hit = {}
        event_data = data.copy()

        user_id = data.get("user_id", request.user.id)
        ip, is_routable = get_client_ip(request)

        hit["api_key"] = self.api_key

        if user_id:
            user = User.objects.get(id=user_id)
            user_email = user.email

            invited_by = user.invited_by
            if invited_by:
                invited_by_id = invited_by.id
            else:
                invited_by_id = None

            user_properties = {
                "email": user_email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "reputation": user.reputation,
                "is_suspended": user.is_suspended,
                "probable_spammer": user.probable_spammer,
                "invited_by_id": invited_by_id,
                "is_hub_editor": user.is_hub_editor(),
            }
            user_id = f"{user_email}_{user_id}"

            if len(user_id) < 5:
                user_id += "_____"
            event_data["user_id"] = user_id
        else:
            user_properties = {
                "email": "",
                "first_name": "Anonymous",
                "reputation": 0,
                "is_suspended": False,
                "probable_spammer": False,
            }
            event_data["user_id"] = "_Anonymous_"

        event_data["user_properties"] = user_properties

        if ip is not None:
            try:
                geo_info = geo.city(ip)
                event_data["ip"] = ip
                event_data["country"] = geo_info["country_name"]
                event_data["city"] = geo_info["city"]
                event_data["region"] = geo_info["region"]
                event_data["dma"] = geo_info["dma_code"]
                event_data["location_lat"] = geo_info["latitude"]
                event_data["location_lng"] = geo_info["longitude"]
            except Exception as e:
                log_info(e)

        hit["events"] = [event_data]
        self.hit = json.dumps(hit, default=json_serial)

    def forward_event(self):
        headers = {"Content-Type": "application/json", "Accept": "*/*"}
        request = requests.post(self.api_url, data=self.hit, headers=headers)
        res = request.json()
        if request.status_code != 200:
            log_info(res)
        return res


def track_event(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        res = func(*args, **kwargs)
        try:
            if res.status_code >= 200 and res.status_code <= 299:
                amp = Amplitude()
                amp.build_hit(res, *args, **kwargs)
        except Exception as e:
            log_info(e, getattr(amp, "hit", None))
        return res

    return inner
