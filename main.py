import os,time,yaml, logging, sys, datetime, zoneinfo
from modules.oura import Oura
from operator import attrgetter
from prometheus_client import CollectorRegistry, start_http_server
import modules.prometheus as prom

ORIGIN_TZ = zoneinfo.ZoneInfo(os.environ.get("TZ"))
OURA_ACCESS_TOKEN = os.environ.get("OURA_ACCESS_TOKEN", None)
HTTP_PORT = os.environ.get('PORT', 8000)
LOGLEVEL = os.environ.get('LOGLEVEL', logging.INFO)
CONF_FILE = 'config/metrics.yml'

if __name__ == "__main__":

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=LOGLEVEL, format='%(asctime)s - %(levelname)s : %(message)s', datefmt="%Y-%m-%dT%H:%M:%S%z")

    metrics_definitions = prom.load_oura_metrics_configs(CONF_FILE)

    registry = CollectorRegistry()
    start_http_server(int(HTTP_PORT), registry=registry)

    if OURA_ACCESS_TOKEN == None:
        logging.fatal("OURA_ACCESS_TOKEN env is not defined. Please set it!")
        sys.exit(1)

    oura = Oura(personal_access_token=OURA_ACCESS_TOKEN)

    personal_info = oura.get_personal_info()

    if personal_info == None:
        logging.fatal("OURA_ACCESS_TOKEN is not usable. Please check it!")
        sys.exit(1)
    
    labels = [ personal_info.email ]

    root_metrics = {}

    while True:
        now = datetime.datetime.now(ORIGIN_TZ)
        today = now.date()
        onedaybefore = now - datetime.timedelta(days=1)
        yesterday = onedaybefore.date()

        for category in metrics_definitions.categories:
            logging.debug("gathering {cat} data...".format(cat=category.name))

            if not category.name in root_metrics:
                root_metrics[category.name] = {}

            if category.name == 'daily_activity':
                metrics = oura.get_daily_activity(yesterday, today)
            elif category.name == 'daily_readiness':
                metrics = oura.get_daily_readiness(today, today)
            elif category.name == 'daily_sleep':
                metrics = oura.get_daily_sleep(today, today)
            elif category.name == 'daily_spo2':
                metrics = oura.get_daily_spo2(today, today)
            elif category.name == 'heartrate':
                metrics = oura.get_heartrate(onedaybefore, now)
            elif category.name == 'personal_info':
                metrics = oura.get_personal_info()

            if metrics == None:
                logging.warn("getting {cat} process was failed.".format(cat=category.name))
                continue
            elif category.name != 'personal_info' and len(metrics.data) == 0:
                logging.warn("{cat} data was not found.".format(cat=category.name))
                continue
            
            if category.name != 'personal_info':
                latest_metrics = metrics.data[-1]
            else:
                latest_metrics = metrics

            for m in category.metrics:
                iterator = m.iterator if m.iterator != None else m.name
                extractor = attrgetter(iterator)
                value = extractor(latest_metrics)
                logging.debug("{prefix}{key}: {value}".format(prefix=category.prefix, key=m.name, value=value))
                if not m.name in root_metrics[category.name]:
                    root_metrics[category.name][m.name] = prom.create_metric_instance(m, registry, category.prefix)
                prom.set_metrics(root_metrics[category.name][m.name], labels, value)
            logging.info("gathering {cat} metrics successful.".format(cat=category.name))

        logging.info("gathering all metrics successful.")
        time.sleep(60)
