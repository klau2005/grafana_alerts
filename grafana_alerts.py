from flask import Flask, request, Response
import json, time, os, sys, ast
import logging
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode, ParseResult
import pymysql.cursors

__author__ = "Claudiu Tomescu"
__version__ = "0.3"
__date__ = "August 2018"
__maintainer__ = "Claudiu Tomescu"
__email__ = "klau2005@gmail.com"
__status__ = "Development"

app = Flask(__name__)

alerts_dict = {"ok": 0, "paused": 1, "pending": 2, "no_data": 3, "alerting": 4}
log_levels = {"CRITICAL": 50, "ERROR": 40, "WARNING": 30, "INFO": 20, "DEBUG": 10, "NOTSET": 0}

log_level_name = os.environ.get("LOG_LEVEL", "INFO")
log_level = log_levels[log_level_name]
log_fmt = "[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s"
grafana_domain = os.environ.get("GRAFANA_DOMAIN", "localhost")
cwd = os.getcwd()
db_conf_file = "configs/db.conf"

logging.basicConfig(level = log_level, datefmt = "%Y-%m-%d %H:%M:%S %z", format = log_fmt)

logging.info("Using log level {0}".format(log_level_name))

def validate_key(data, key):
    try:
        value = data[key]
    except KeyError:
        logging.debug("Received alert with missing field \"{0}\"".format(key))
        logging.debug("Complete JSON body received below")
        logging.debug(data)
        value = "None"
    return value

try:
    with open(db_conf_file, "r") as f:
        db_conf = f.read()
except FileNotFoundError:
    logging.critical("{0} file could not be found in {1}/configs directory, exiting...".format(db_conf_file, cwd))
    sys.exit(4)
except PermissionError:
    logging.critical("No permission to read {0}/configs/{1} file, exiting...".format(cwd, db_conf_file))
    sys.exit(4)

db_conf_dict = ast.literal_eval(db_conf)

@app.route('/alerts', methods=['POST'])
def parse_response():
    data = request.get_json()
    if data is None:
        logging.warning("Incorrect data type provided, expecting JSON")
        return Response(status=400)
    else:
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        title = validate_key(data, "title")
        message = validate_key(data, "message")
        state = data["state"]
        state = alerts_dict[state]
        ruleId = data["ruleId"]
        try:
            url = data["ruleUrl"]
        except KeyError:
            logging.error("Data received contains no alert URL, data body below")
            logging.error(data)
            url = "http://localhost/inexistent"
        finally:
            url = urlparse(url)
            dashboard = url.path
            dashboard = dashboard.split("/")[-1]
            dashboard = dashboard.upper()
            query_params = url.query
            query_params_dict = parse_qs(query_params)
            try:
                del query_params_dict['edit']
            except KeyError:
                pass
            new_query_params = urlencode(query_params_dict, doseq=True)
            new_parsed_url = ParseResult(
            url.scheme, url.netloc, url.path, url.params, new_query_params, url.fragment)
            url = new_parsed_url._replace(scheme = "https")
            url = url._replace(netloc = grafana_domain)
            url = urlunparse(url)
            url = '<a href="{0}">{1}<a/>'.format(url, dashboard)
        if len(data["evalMatches"]) > 0:
            value = str(data["evalMatches"][0]["value"])
            metric = data["evalMatches"][0]["metric"]
        else:
            value = None
            metric = None
        connection = pymysql.connect(host=db_conf_dict["host"],
                                    user=db_conf_dict["user"],
                                    password=db_conf_dict["password"],
                                    db=db_conf_dict["db"],
                                    cursorclass=pymysql.cursors.DictCursor)
        try:
            with connection.cursor() as cursor:
                # Create a new record
                sql = "INSERT INTO `alerts` \
                (`title`, `message`, `state`, `time`, `dashboardName`, `alertLink`, `value`, `metric`, `ruleId`) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                logging.debug("About to perform following DB insert")
                logging.debug(sql % (title, message, state, current_time, dashboard, url, value, metric, ruleId))
                cursor.execute(sql, (title, message, state, current_time, dashboard, \
                url, value, metric, ruleId))
            # connection is not autocommit by default. So you must commit to save
            # your changes.
            connection.commit()
        except Exception as e:
            logging.error("Error encountered while trying to insert data in DB, below details")
            logging.error(e)
        except pymysql.err.InternalError:
            logging.error("Error encountered while trying to insert data in DB, skipping...")
            pass
        finally:
            logging.debug("Closing DB connection")
            connection.close()
        return("200")
