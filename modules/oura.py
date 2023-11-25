import logging, requests, datetime
from modules.oura_dataclasses import *
from dacite import from_dict, Config

logger = logging.getLogger(__name__)

class Oura:

    def __init__(self, personal_access_token:str):
        self.url = "https://api.ouraring.com/v2"
        self.token = personal_access_token
        self.cast_config = Config({
            datetime.datetime: datetime.datetime.fromisoformat,
            datetime.date: datetime.date.fromisoformat,
        })
    
    def __call__(self, hook, **kwargs):
        getattr(self, f'get_{hook}')(**kwargs)

    def get_usercollection(self, path:str, **params) -> dict | None:
        try:
            response = requests.get(
                url="{u}/usercollection/{p}".format(u=self.url,p=path),
                headers={
                    "Authorization": "Bearer {t}".format(t=self.token),
                },
                params=params
            )
            if response.status_code != 200:
                logging.error("{u} return {s}: {t}".format(u=response.url, s=response.status_code, t=response.text))
                return None
            return response.json()
        except requests.exceptions.RequestException as err:
            logging.error("HTTP Request failed: {e}".format(e=err))
            return None

    def get_daily_activity(self, start_date:datetime.date, end_date:datetime.date) -> OuraDailyActivities:
        res_dict = self.get_usercollection("daily_activity", start_date=start_date, end_date=end_date)
        if res_dict != None:
            return from_dict(data_class=OuraDailyActivities, data=res_dict, config=self.cast_config)
        return None

    def get_daily_readiness(self, start_date:datetime.date, end_date:datetime.date) -> OuraDailyReadinesses:
        res_dict = self.get_usercollection("daily_readiness", start_date=start_date, end_date=end_date)
        if res_dict != None:
            return from_dict(data_class=OuraDailyReadinesses, data=res_dict, config=self.cast_config)
        return None

    def get_daily_sleep(self, start_date:datetime.date, end_date:datetime.date) -> OuraDailySleeps:
        res_dict = self.get_usercollection("daily_sleep", start_date=start_date, end_date=end_date)
        if res_dict != None:
            return from_dict(data_class=OuraDailySleeps, data=res_dict, config=self.cast_config)
        return None

    def get_daily_spo2(self, start_date:datetime.date, end_date:datetime.date) -> OuraDailySpo2s:
        res_dict = self.get_usercollection("daily_spo2", start_date=start_date, end_date=end_date)
        if res_dict != None:
            return from_dict(data_class=OuraDailySpo2s, data=res_dict, config=self.cast_config)
        return None

    def get_heartrate(self, start_datetime:datetime.datetime, end_datetime:datetime.datetime) -> OuraHeartRates:
        res_dict = self.get_usercollection("heartrate", start_datetime=start_datetime, end_datetime=end_datetime)
        if res_dict != None:
            return from_dict(data_class=OuraHeartRates, data=res_dict, config=self.cast_config)
        return None

    def get_personal_info(self) -> OuraPersonalInfo:
        res_dict = self.get_usercollection("personal_info")
        if res_dict != None:
            return from_dict(data_class=OuraPersonalInfo, data=res_dict, config=self.cast_config)
        return None
