import os,time,yaml, logging, sys, datetime, zoneinfo
from operator import attrgetter

from prometheus_client import CollectorRegistry, start_http_server

import modules.prometheus as prom
from modules.oauth import OAuthTokenManager, StaticTokenProvider
from modules.oura import Oura

ORIGIN_TZ = zoneinfo.ZoneInfo(os.environ.get("TZ"))
OURA_ACCESS_TOKEN = os.environ.get("OURA_ACCESS_TOKEN", None)
OURA_CLIENT_ID = os.environ.get("OURA_CLIENT_ID")
OURA_CLIENT_SECRET = os.environ.get("OURA_CLIENT_SECRET")
OURA_REDIRECT_URI = os.environ.get("OURA_REDIRECT_URI", "http://localhost:8000/callback")
OURA_SCOPES = os.environ.get("OURA_SCOPES")
OURA_TOKEN_PATH = os.environ.get("OURA_TOKEN_PATH", os.path.expanduser("~/.config/oura-exporter/oauth_token.json"))
OURA_AUTH_CODE = os.environ.get("OURA_AUTH_CODE")
OURA_AUTH_CODE_FILE = os.environ.get("OURA_AUTH_CODE_FILE")
HTTP_PORT = os.environ.get('PORT', 8000)
LOGLEVEL = os.environ.get('LOGLEVEL', logging.INFO)
CONF_FILE = 'config/metrics.yml'

if __name__ == "__main__":

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=LOGLEVEL, format='%(asctime)s - %(levelname)s : %(message)s', datefmt="%Y-%m-%dT%H:%M:%S%z")

    metrics_definitions = prom.load_oura_metrics_configs(CONF_FILE)

    registry = CollectorRegistry()
    start_http_server(int(HTTP_PORT), registry=registry)

    if OURA_ACCESS_TOKEN:
        logger.warning("Using legacy OURA_ACCESS_TOKEN (PAT). Oura recommends OAuth; PATs are being removed.")
        token_provider = StaticTokenProvider(OURA_ACCESS_TOKEN)
    else:
        if OURA_CLIENT_ID is None:
            logging.fatal("Missing Oura OAuth config. Set OURA_CLIENT_ID (and optionally OURA_CLIENT_SECRET) or keep OURA_ACCESS_TOKEN for legacy use.")
            sys.exit(1)

        scopes = OURA_SCOPES.split() if OURA_SCOPES else None
        initial_auth_code = OURA_AUTH_CODE
        if not initial_auth_code and OURA_AUTH_CODE_FILE:
            try:
                with open(OURA_AUTH_CODE_FILE, encoding="utf-8") as fp:
                    initial_auth_code = fp.read().strip()
            except OSError as exc:
                logging.error(f"Failed to read OURA_AUTH_CODE_FILE: {exc}")

        token_provider = OAuthTokenManager(
            client_id=OURA_CLIENT_ID,
            client_secret=OURA_CLIENT_SECRET,
            redirect_uri=OURA_REDIRECT_URI,
            scopes=scopes,
            token_path=OURA_TOKEN_PATH,
            initial_auth_code=initial_auth_code,
        )

    # Trigger OAuth consent early so the server can start only after auth is ready.
    try:
        token_provider.get_access_token()
    except Exception as exc:
        logging.fatal(f"Failed to prepare Oura authentication: {exc}")
        sys.exit(1)

    oura = Oura(token_provider=token_provider)

    personal_info = oura.get_personal_info()

    if personal_info == None:
        logging.fatal("Oura authentication failed. Refresh credentials or re-run OAuth consent.")
        sys.exit(1)
    
    labels = [ personal_info.email ]

    root_metrics = {}

    while True:
        now = datetime.datetime.now(ORIGIN_TZ)
        today = now.date()     
        days_ago = now - datetime.timedelta(days=7)
        start_date = days_ago.date()
        
        for category in metrics_definitions.categories:
            logging.debug(f"gathering {category.name} data...")

            if not category.name in root_metrics:
                root_metrics[category.name] = {}

            if category.name == 'daily_activity':
                metrics = oura.get_daily_activity(start_date, today)
            elif category.name == 'daily_readiness':
                metrics = oura.get_daily_readiness(start_date, today)
            elif category.name == 'daily_resilience':
                metrics = oura.get_daily_resilience(start_date, today)
            elif category.name == 'daily_sleep':
                metrics = oura.get_daily_sleep(start_date, today)
            elif category.name == 'daily_spo2':
                metrics = oura.get_daily_spo2(start_date, today)
            elif category.name == 'daily_stress':
                metrics = oura.get_daily_stress(start_date, today)
            elif category.name == 'heartrate':
                # For heart rate, use a 24-hour window
                metrics = oura.get_heartrate(now - datetime.timedelta(days=1), now)
            elif category.name == 'personal_info':
                metrics = oura.get_personal_info()

            if metrics == None:
                logging.warning(f"getting {category.name} process was failed.")
                continue
            elif category.name != 'personal_info' and len(metrics.data) == 0:
                logging.warning(f"{category.name} data was not found for date range {start_date} to {today}.")
                continue
            
            if category.name != 'personal_info':
                latest_metrics = metrics.data[-1]
                if category.name == 'heartrate':
                    logging.info(f"Found {len(metrics.data)} {category.name} entries, using latest from {latest_metrics.timestamp}")
                else:
                    logging.info(f"Found {len(metrics.data)} {category.name} entries, using latest from {latest_metrics.day}")
            else:
                latest_metrics = metrics

            for m in category.metrics:
                iterator = m.iterator if m.iterator != None else m.name
                try:
                    extractor = attrgetter(iterator)
                    value = extractor(latest_metrics)
                    logging.debug(f"{category.prefix}{m.name}: {value}")
                    if not m.name in root_metrics[category.name]:
                        root_metrics[category.name][m.name] = prom.create_metric_instance(m, registry, category.prefix)
                    prom.set_metrics(root_metrics[category.name][m.name], labels, value)
                except Exception as e:
                    logging.error(f"Error processing metric {m.name}: {e}")
                    continue
            logging.info(f"gathering {category.name} metrics successful.")

        logging.info("gathering all metrics successful.")
        time.sleep(60)