import base64
import errno
import logging
import os
import platform
import re
from enum import Enum

import ruamel.yaml
from jinja2 import Template

from ruamel import yaml
from tabulate import tabulate

logger = logging.getLogger("monitor")


class Identity(Enum):
    unknown = 0
    anonymous = 1
    registered = 2
    identified = 3
    professional = 4


class TaskStatus(Enum):
    unknown = 0
    spooling = 1
    spawning = 2
    running = 3
    finished = 4
    broken = 5


class Nodes(object):
    nodes_ = dict()

    @staticmethod
    def add_node(node):
        Nodes.nodes_[node.node_tag] = node

    @staticmethod
    def get_node(node_tag):
        return Nodes.nodes_[node_tag]

    @staticmethod
    def remove_node(node_tag):
        del Nodes.nodes_[node_tag]

    @staticmethod
    def get_nodes_keys():
        return list(Nodes.nodes_.keys())

    @staticmethod
    def get_nodes_arr():
        temp = list(Nodes.nodes_.values())
        temp.sort(key=lambda x: natural_keys(x.node_tag))
        return temp


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [atoi(c) for c in re.split("(\d+)", text)]


def parse_tag(order_):
    return base64.b64decode(order_).decode().strip("\0")


def create_dir(*dirs_):
    for dir_ in dirs_:
        if not os.path.exists(dir_):
            try:
                os.makedirs(dir_)
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise


def convert_price(price_):
    return int(price_) / 1e18 * 3600


def parse_price(price_: str):
    if price_.endswith("USD/h") or price_.endswith("USD/s"):
        return int(float(price_[:-5]) * 1e18 / 3600)
    else:
        raise Exception("Cannot parse price {}".format(price_))


def get_sonmcli():
    if platform.system() == "Darwin":
        return "sonmcli_darwin_x86_64"
    else:
        return "sonmcli"


def validate_eth_addr(eth_addr):
    pattern = re.compile("^0x[a-fA-F0-9]{40}$")
    if eth_addr and pattern.match(eth_addr):
        logger.debug("Eth address was parsed successfully: " + eth_addr)
        return eth_addr
    else:
        logger.debug("Incorrect eth address or not specified")
        return None


def print_state():
    tabul_nodes = [[n.node_tag, n.bid_id, n.price, n.deal_id, n.task_id, n.task_uptime, n.status.name] for n in
                   Nodes.get_nodes_arr()]
    logger.info("Nodes:\n" +
                tabulate(tabul_nodes,
                         ["Node", "Order id", "Order price", "Deal id", "Task id", "Task uptime", "Node status"],
                         tablefmt="grid"))


def template_bid(config, tag="", counterparty=None):
    gpumem = config["gpumem"]
    ethhashrate = config["ethhashrate"]
    if config["gpucount"] == 0:
        gpumem = 0
        ethhashrate = 0
    bid_template = {
        "duration": config["duration"],
        "price": "0USD/h",
        "identity": config["identity"],
        "tag": tag,
        "resources": {
            "network": {
                "overlay": config["overlay"],
                "outbound": True,
                "incoming": config["incoming"]
            },
            "benchmarks": {
                "ram-size": config["ramsize"] * 1024 * 1024,
                "storage-size": config["storagesize"] * 1024 * 1024 * 1024,
                "cpu-cores": config["cpucores"],
                "cpu-sysbench-single": config["sysbenchsingle"],
                "cpu-sysbench-multi": config["sysbenchmulti"],
                "net-download": config["netdownload"] * 1024 * 1024,
                "net-upload": config["netupload"] * 1024 * 1024,
                "gpu-count": config["gpucount"],
                "gpu-mem": gpumem * 1024 * 1024,
                "gpu-eth-hashrate": ethhashrate * 1000000
            }
        }
    }
    if counterparty:
        bid_template["counterparty"] = counterparty
    return bid_template


def dump_file(data, filename):
    with open(filename, 'w+') as file:
        yaml.dump(data, file, Dumper=yaml.RoundTripDumper)


def template_task(file_, kwargs=None):
    if not kwargs:
        kwargs = {}
    with open(file_, 'r') as fp:
        t = Template(fp.read())
        data = t.render(**kwargs)
        return ruamel.yaml.round_trip_load(data, preserve_quotes=True)
