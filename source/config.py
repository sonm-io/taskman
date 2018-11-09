import json
import os
from os.path import join

from pathlib2 import Path
from ruamel.yaml import YAML

from source.utils import logger, validate_eth_addr, template_bid


class Config(object):
    base_config = {}
    node_configs = {}
    config_folder = "conf/"

    bids = {}
    prices = {}
    balance = {}

    @staticmethod
    def price_for_tag(tag):
        if tag in Config.prices.keys():
            return Config.prices[tag]
        else:
            return None

    @staticmethod
    def formatted_price_for_tag(tag):
        if tag in Config.prices.keys() and Config.prices[tag] and "perHourUSD" in Config.prices[tag]:
            return "{:.4f} USD/h".format(Config.prices[tag]["perHourUSD"])
        else:
            return ""

    @staticmethod
    def load_bid_configs(bids_):
        if len(Config.bids) == 0:
            Config.bids = bids_
        else:
            for tag in bids_.keys():
                if tag in Config.bids and Config.bids[tag] == bids_[tag]:
                    continue
                Config.bids[tag] = bids_[tag]

    @staticmethod
    def load_prices(sonm_api):
        for tag, bid in Config.bids.items():
            Config.prices[tag] = sonm_api.predict_bid(bid["resources"])

    @staticmethod
    def get_node_config(node_tag):
        return Config.node_configs.get(node_tag)

    @staticmethod
    def load_config():
        Config.load_base_config()
        Config.load_task_configs()

    @staticmethod
    def load_task_configs():
        temp_node_configs = {}
        temp_bids = {}
        logger.debug("Try to parse configs:")
        if not Config.base_config["tasks"]:
            raise Exception("Configuration must have at least one task")
        else:
            loaded_tasks = [Config.load_cfg(task) for task in Config.base_config["tasks"]]
            tags = [task["tag"] for task in loaded_tasks if "tag" in task]
            if len(tags) != len(set(tags)):
                raise Exception("Config has tasks with same tag")

        for task_config in loaded_tasks:
            Config.validate_config_keys(["numberofnodes", "tag", "price_coefficient", "max_price", "ets",
                                         "task_start_timeout", "template_file", "duration", "counterparty",
                                         "identity", "ramsize", "storagesize", "cpucores", "sysbenchsingle",
                                         "sysbenchmulti", "netdownload", "netupload", "overlay", "incoming",
                                         "gpucount", "gpumem", "ethhashrate"], task_config)
            temp_bids[task_config["tag"]] = template_bid(task_config)
            for num in range(1, task_config["numberofnodes"] + 1):
                task_config["counterparty"] = validate_eth_addr(task_config["counterparty"])
                ntag = "{}_{}".format(task_config["tag"], num)
                temp_node_configs[ntag] = task_config
                logger.debug("Config for node {} was created successfully".format(ntag))
                logger.debug("Config: {}".format(json.dumps(task_config, sort_keys=True, indent=4)))
        Config.node_configs = temp_node_configs
        Config.load_bid_configs(temp_bids)

    @staticmethod
    def load_base_config():
        logger.debug("Loading base config")
        temp_config = Config.load_cfg()
        Config.validate_config_keys(["node_address", "ethereum", "tasks"], temp_config)
        Config.base_config = temp_config
        logger.debug("Base config loaded")

    @staticmethod
    def validate_config_keys(config_keys, temp_config):
        missed_keys = [key for key in config_keys if key not in temp_config]
        if len(missed_keys) > 0:
            raise Exception("Missed keys: '{}'".format("', '".join(missed_keys)))

    @staticmethod
    def reload_node_config(node_tag):
        Config.base_config = Config.load_cfg()
        for task in Config.base_config["tasks"]:
            task_config = Config.load_cfg(task)
            if node_tag.startswith(task_config["tag"] + "_"):
                Config.node_configs[node_tag] = task_config

    @staticmethod
    def load_cfg(filename='config.yaml', folder=config_folder):
        path = join(folder, filename)
        if os.path.exists(path):
            p = Path(path)
            yaml_ = YAML(typ='safe')
            return yaml_.load(p)
        else:
            raise Exception("File {} not found".format(filename))
