import datetime
import logging
from typing import Any

import requests
from dacite import Config, from_dict

from modules.oura_dataclasses import *

logger = logging.getLogger(__name__)

class Oura:

    def __init__(self, token_provider: Any):
        self.url = "https://api.ouraring.com/v2"
        self.token_provider = token_provider
        self.cast_config = Config({
            datetime.datetime: datetime.datetime.fromisoformat,
            datetime.date: datetime.date.fromisoformat,
        })
    
    def __call__(self, hook, **kwargs):
        getattr(self, f'get_{hook}')(**kwargs)

    def get_usercollection(self, path:str, **params) -> dict | None:
        try:
            response = self._authorized_get(path, params)
            if response is None:
                return None
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"HTTP Request failed: {e}")
            return None

    def get_daily_activity(self, start_date:datetime.date, end_date:datetime.date) -> OuraDailyActivities:
        res_dict = self.get_usercollection("daily_activity", start_date=start_date.isoformat(), end_date=end_date.isoformat())
        if res_dict != None:
            return from_dict(data_class=OuraDailyActivities, data=res_dict, config=self.cast_config)
        return None

    def get_daily_readiness(self, start_date:datetime.date, end_date:datetime.date) -> OuraDailyReadinesses:
        res_dict = self.get_usercollection("daily_readiness", start_date=start_date.isoformat(), end_date=end_date.isoformat())
        if res_dict != None:
            return from_dict(data_class=OuraDailyReadinesses, data=res_dict, config=self.cast_config)
        return None

    def get_daily_resilience(self, start_date:datetime.date, end_date:datetime.date) -> OuraDailyResiliences:
        res_dict = self.get_usercollection("daily_resilience", start_date=start_date.isoformat(), end_date=end_date.isoformat())
        if res_dict != None:
            return from_dict(data_class=OuraDailyResiliences, data=res_dict, config=self.cast_config)
        return None

    def get_daily_sleep(self, start_date:datetime.date, end_date:datetime.date) -> OuraDailySleeps:
        res_dict = self.get_usercollection("daily_sleep", start_date=start_date.isoformat(), end_date=end_date.isoformat())
        if res_dict != None:
            return from_dict(data_class=OuraDailySleeps, data=res_dict, config=self.cast_config)
        return None

    def get_daily_spo2(self, start_date:datetime.date, end_date:datetime.date) -> OuraDailySpo2s:
        res_dict = self.get_usercollection("daily_spo2", start_date=start_date.isoformat(), end_date=end_date.isoformat())
        if res_dict != None:
            return from_dict(data_class=OuraDailySpo2s, data=res_dict, config=self.cast_config)
        return None

    def get_daily_stress(self, start_date:datetime.date, end_date:datetime.date) -> OuraDailyStresses:
        res_dict = self.get_usercollection("daily_stress", start_date=start_date.isoformat(), end_date=end_date.isoformat())
        if res_dict != None:
            return from_dict(data_class=OuraDailyStresses, data=res_dict, config=self.cast_config)
        return None

    def get_heartrate(self, start_datetime:datetime.datetime, end_datetime:datetime.datetime) -> OuraHeartRates:
        res_dict = self.get_usercollection("heartrate", start_datetime=start_datetime.isoformat(), end_datetime=end_datetime.isoformat())
        if res_dict != None:
            return from_dict(data_class=OuraHeartRates, data=res_dict, config=self.cast_config)
        return None

    def get_personal_info(self) -> OuraPersonalInfo:
        res_dict = self.get_usercollection("personal_info")
        if res_dict != None:
            return from_dict(data_class=OuraPersonalInfo, data=res_dict, config=self.cast_config)
        return None

    def _authorized_get(self, path: str, params: dict) -> requests.Response | None:
        token = self.token_provider.get_access_token()
        response = requests.get(
            url=f"{self.url}/usercollection/{path}",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params=params,
            timeout=15,
        )

        if response.status_code == 401 and hasattr(self.token_provider, "refresh_access_token"):
            logging.warning("Access token rejected; attempting refresh.")
            if self.token_provider.refresh_access_token():
                token = self.token_provider.get_access_token()
                response = requests.get(
                    url=f"{self.url}/usercollection/{path}",
                    headers={
                        "Authorization": f"Bearer {token}",
                    },
                    params=params,
                    timeout=15,
                )

        if response.status_code != 200:
            logging.error(f"{response.url} return {response.status_code}: {response.text}")
            return None

        return response