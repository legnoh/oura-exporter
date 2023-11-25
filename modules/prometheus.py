from prometheus_client import Gauge, Counter, Info, CollectorRegistry
from dataclasses import dataclass
from dacite import from_dict
import yaml

@dataclass
class OuraMetricsConfig:
    name: str
    desc: str
    type: str 
    unit: str | None
    labels: list[str]
    iterator: str | None

@dataclass
class OuraCategoryConfig:
    name: str
    prefix: str
    labels: list[str]
    metrics: list[OuraMetricsConfig]

@dataclass
class OuraRootConfig:
    categories: list[OuraCategoryConfig]

def load_oura_metrics_configs(file:str):
    with open(file, 'r') as f:
        metrics_definitions_dict = yaml.load(f, Loader=yaml.FullLoader)
        return from_dict(data_class=OuraRootConfig, data=metrics_definitions_dict)

def create_metric_instance(definition:OuraMetricsConfig, registry:CollectorRegistry, prefix:str):
    if definition.type == 'gauge':
        m = Gauge( prefix + definition.name, definition.desc, definition.labels, registry=registry )
    elif definition.type == 'counter':
        m = Counter( prefix + definition.name, definition.desc, definition.labels, registry=registry )
    elif definition.type == 'summary':
        m = Counter( prefix + definition.name, definition.desc, definition.labels, registry=registry )
    elif definition.type == 'info':
        m = Info( prefix + definition.name, definition.desc, definition.labels, registry=registry )
    else:
        return None
    return m

def set_metrics(m, labels:list, value):
    if value == None:
        pass
    elif m._type == 'gauge':
        m.labels(*labels).set(value)
    elif m._type == 'info':
        m.labels(*labels).info({'val': value})
    elif m._type == 'counter':
        m.labels(*labels).inc(value)
    else:
        pass
