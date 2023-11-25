import datetime
from dataclasses import dataclass

@dataclass
class OuraDailyActivityContributors:
    meet_daily_targets: int
    move_every_hour: int
    recovery_time: int
    stay_active: int
    training_frequency: int
    training_volume: int

@dataclass
class OuraDailyActivityMet:
    interval: float
    items: list[float]
    timestamp: datetime.datetime

@dataclass
class OuraDailyActivity:
    id: str
    class_5_min: str
    score: int
    active_calories: int
    average_met_minutes: float
    contributors: OuraDailyActivityContributors
    equivalent_walking_distance: int
    high_activity_met_minutes: int
    high_activity_time: int
    inactivity_alerts: int
    low_activity_met_minutes: int
    low_activity_time: int
    medium_activity_met_minutes: int
    medium_activity_time: int
    met: OuraDailyActivityMet
    meters_to_target: int
    non_wear_time: int
    resting_time: int
    sedentary_met_minutes: int
    sedentary_time: int
    steps: int
    target_calories: int
    target_meters: int
    total_calories: int
    day: datetime.date
    timestamp: datetime.datetime

@dataclass
class OuraDailyActivities:
    data: list[OuraDailyActivity]
    next_token: str | None

@dataclass
class OuraDailyReadinessContributors:
    activity_balance: int
    body_temperature: int
    hrv_balance: int | None
    previous_day_activity: int
    previous_night: int
    recovery_index: int
    resting_heart_rate: int
    sleep_balance: int

@dataclass
class OuraDailyReadiness:
    id: str
    contributors: OuraDailyReadinessContributors
    day: datetime.date
    score: int
    temperature_deviation: float
    temperature_trend_deviation: float
    timestamp: datetime.datetime

@dataclass
class OuraDailyReadinesses:
    data: list[OuraDailyReadiness]
    next_token: str | None

@dataclass
class OuraDailySleepContributors:
    deep_sleep: int
    efficiency: int
    latency: int
    rem_sleep: int
    restfulness: int
    timing: int
    total_sleep: int

@dataclass
class OuraDailySleep:
    id: str
    contributors: OuraDailySleepContributors
    day: datetime.date
    score: int
    timestamp: datetime.datetime

@dataclass
class OuraDailySleeps:
    data: list[OuraDailySleep]
    next_token: str | None

@dataclass
class OuraDailySpo2Spo2Percentage:
    average: float

@dataclass
class OuraDailySpo2:
    id: str
    day: datetime.date
    spo2_percentage: OuraDailySpo2Spo2Percentage

@dataclass
class OuraDailySpo2s:
    data: list[OuraDailySpo2]
    next_token: str | None

@dataclass
class OuraHeartRate:
    bpm: int
    source: str
    timestamp: datetime.datetime

@dataclass
class OuraHeartRates:
    data: list[OuraHeartRate]
    next_token: str | None

@dataclass
class OuraPersonalInfo:
    id: str
    age: int
    weight: float
    height: float
    biological_sex: str
    email: str
