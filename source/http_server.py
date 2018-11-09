import logging
import threading
import time
from collections import defaultdict
from functools import wraps

from flask_table import Table, Col
from flask import Flask, render_template, request, Response
from flask_appconfig import AppConfig
from flask_bootstrap import Bootstrap

from source.utils import Nodes
from source.config import Config

logger = logging.getLogger("monitor")


class SonmHttpServer:
    KEEP_RUNNING = True


def check_auth(username, password):
    return username == Config.base_config["http_server"]["user"] and \
           password == Config.base_config["http_server"]["password"]


def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


class NodesTable(Table):
    def sort_url(self, col_id, reverse=False):
        pass

    def get_tr_attrs(self, item):
        return {'class': item.css_class}

    node = Col('Node')
    order_id = Col('Order id')
    order_price = Col('Order Price')
    deal_id = Col('Deal id')
    task_id = Col('Task id')
    task_uptime = Col('Task uptime')
    node_status = Col('Node status')
    since_hb = Col('HB')


def create_app(configfile=None):
    app = Flask(__name__)
    AppConfig(app, configfile)
    Bootstrap(app)

    @app.route('/', methods=('GET', 'POST'))
    @requires_auth
    def index():
        nodes_content = []
        groups = defaultdict(list)
        for obj in Nodes.get_nodes_arr():
            groups[obj.tag].append(obj)

            nodes_content = [{
                'node_tag': tag,
                'predicted_price': Config.formatted_price_for_tag(tag),
                'nodes_table': NodesTable([node.as_table_item for node in nodes],
                                          classes=['table', 'table-striped', 'table-bordered'])
            }
                for tag, nodes in groups.items()]

        return render_template('index.html', nodes=nodes_content, token_balance=Config.balance)

    return app


def run_http_server():
    if "http_server" in Config.base_config and "run" in Config.base_config["http_server"]:
        if not Config.base_config["http_server"]["run"]:
            return
        if not ("password" in Config.base_config["http_server"] and "user" in Config.base_config["http_server"]):
            logger.error("Login and password are mandatory parameters for http server.")
            logger.error("Http server stopped")
            return
        logger.info('Starting HTTP server...')

        thread = get_http_thread(create_app())
        logger.info("Agent started on port: {}".format(Config.base_config["http_server"]["port"]))

        while SonmHttpServer.KEEP_RUNNING:
            if not thread.is_alive():
                thread = get_http_thread(create_app())
            time.sleep(1)
        logger.info("Http server stopped")


def get_http_thread(app, host='0.0.0.0', port=8081):
    thread = threading.Thread(target=app.run, kwargs={'host': host, 'port': port})
    thread.daemon = True
    thread.start()
    return thread
