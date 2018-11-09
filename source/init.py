import logging
from genericpath import isfile
from os import listdir
from os.path import join

from source.sonmapi import SonmApi
from source.utils import Nodes
from source.config import Config
from source.worknode import WorkNode, State

logger = logging.getLogger("monitor")


def reload_config(sonm_api: SonmApi):
    Config.load_config()
    Config.load_prices(sonm_api)
    append_missed_nodes(sonm_api, Config.node_configs)


def check_balance(sonm_api: SonmApi):
    Config.balance = sonm_api.token_balance()


def append_missed_nodes(sonm_api, node_configs):
    for node_tag, node_config in node_configs.items():
        if node_tag not in Nodes.get_nodes_keys():
            Nodes.add_node(WorkNode.create_empty(sonm_api, node_tag))


def init_nodes_state(sonm_api):
    nodes_num_ = len(Config.node_configs)
    # get deals
    deals_ = sonm_api.deal_list(nodes_num_)
    if deals_:
        for deal in deals_:
            status = State.DEAL_OPENED
            deal_status = sonm_api.deal_status(deal["id"])
            order_ = sonm_api.order_status(deal_status["bid_id"])
            for node_tag, node_config in Config.node_configs.items():
                if node_tag == order_["tag"]:
                    task_id = ""
                    if deal_status["worker_offline"]:
                        logger.info(
                            "Seems like worker is offline: no respond for the resources and tasks request."
                            " Deal will be closed")
                        status = State.TASK_FAILED
                    if deal_status["running"]:
                        task_id = deal_status["running"][0]
                        status = State.TASK_RUNNING
                    bid_id_ = deal_status["bid_id"]
                    price = deal_status["price"]
                    node_ = WorkNode(status, sonm_api, order_["tag"], deal["id"], task_id, bid_id_, price)
                    logger.info("Found deal, id {} (Node {})".format(deal["id"], order_["tag"]))
                    Nodes.add_node(node_)

    # get orders
    orders_ = sonm_api.order_list(nodes_num_)
    if orders_ and orders_["orders"]:
        for order_ in list(orders_["orders"]):
            status = State.AWAITING_DEAL
            for node_tag, node_config in Config.node_configs.items():
                if node_tag == order_["tag"]:
                    price = order_["price"]
                    node_ = WorkNode(status, sonm_api, order_["tag"], "", "", order_["id"], price)
                    logger.info("Found order, id {} (Node {})".format(order_["id"], order_["tag"]))
                    Nodes.add_node(node_)
    append_missed_nodes(sonm_api, Config.node_configs)


def init_sonm_api():
    timeout = int(Config.base_config["timeout"]) if "timeout" in Config.base_config else 60

    key_file_path = Config.base_config["ethereum"]["key_path"]
    keys = [f for f in listdir(key_file_path) if isfile(join(key_file_path, f))]
    if len(keys) == 0:
        raise Exception("Key storage doesn't contain any files")
    key_password = Config.base_config["ethereum"]["password"]
    node_addr = Config.base_config["node_address"]
    sonm_api = SonmApi(join(key_file_path, keys[0]), key_password, node_addr, timeout)
    return sonm_api
