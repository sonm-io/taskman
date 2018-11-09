#!/usr/bin/env python3.7
import concurrent
import logging
import os
import time
from logging.config import dictConfig
from os.path import join

from apscheduler.schedulers.background import BackgroundScheduler

from source.http_server import run_http_server, SonmHttpServer
from source.utils import Nodes, print_state, create_dir
from source.config import Config
from source.init import init_nodes_state, reload_config, init_sonm_api, check_balance


def setup_logging(default_config='logging.yaml', default_level=logging.INFO):
    if os.path.exists(join(Config.config_folder, default_config)):
        config = Config.load_cfg(default_config)
        dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


def watch(executor, futures):
    for node in Nodes.get_nodes_arr():
        futures[node.node_tag] = executor.submit(node.watch_node)
        time.sleep(1)
    while len(futures) > 0:
        # Clear finished futures
        for item in [{"tag": node_tag, "future": future} for node_tag, future in futures.items()]:
            if item["future"].done():
                exception_ = item["future"].exception()
                logger.info("Removing Node {} from execution list.".format(item["tag"]))
                del futures[item["tag"]]
                if exception_:
                    logger.exception("Node {} failed with exception".format(item["tag"]), exception_)
                    Nodes.get_node(item["tag"]).RUNNING = False
        for node_tag in Nodes.get_nodes_keys():
            # Destroy nodes, if they aren't exist in reloaded config
            if node_tag not in Config.node_configs.keys():
                logger.info("Stopping Node {}. It doesn't exist in configuration".format(node_tag))
                Nodes.get_node(node_tag).finish_work()
                logger.info("Removing Node {} from active nodes list.".format(node_tag))
                Nodes.remove_node(node_tag)
        for node_tag in Nodes.get_nodes_keys():
            # Add new nodes to executor:
            if not Nodes.get_node(node_tag).is_running:
                logger.info("Adding Node {} to executor".format(node_tag))
                futures[node_tag] = executor.submit(Nodes.get_node(node_tag).watch_node)
        time.sleep(1)


def main():
    Config.load_config()
    sonm_api = init_sonm_api()
    check_balance(sonm_api)
    Config.load_prices(sonm_api)
    init_nodes_state(sonm_api)
    scheduler = BackgroundScheduler()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=100)
    futures_ = dict()
    try:
        scheduler.start()
        scheduler.add_job(print_state, 'interval', seconds=60, id='print_state')
        scheduler.add_job(reload_config, 'interval', kwargs={"sonm_api": sonm_api}, seconds=60, id='reload_config')
        scheduler.add_job(check_balance, 'interval', kwargs={"sonm_api": sonm_api}, seconds=600, id='check_balance')
        executor.submit(run_http_server)
        watch(executor, futures_)
        print_state()
        logger.info("Work completed")
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt, script exiting")
    except SystemExit as e:
        logger.exception("System Exit", e)
    finally:
        logger.info("Script exiting. Sonm node will continue work")
        for n in Nodes.get_nodes_arr():
            n.stop_work()
        SonmHttpServer.KEEP_RUNNING = False
        executor.shutdown(wait=False)
        scheduler.shutdown(wait=False)


create_dir("out/logs", "out/orders", "out/tasks")
setup_logging()
logging.getLogger('apscheduler').setLevel(logging.FATAL)
logger = logging.getLogger('monitor')

if __name__ == "__main__":
    print('Press Ctrl+{0} to interrupt script'.format('Break' if os.name == 'nt' else 'C'))
    main()
