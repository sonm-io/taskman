# sonm-taskman

SONM Task manager (taskman) is a bot for customer. It's main goal is to automate deal and task managing, and make it as easy as possible.

Written with Python 3.7. Open-sourced and available for changes without any limitations.

Concept:
- describe hardware needs for your task(s), including preferred price and number of instances;
- describe your task(s);
- run the bot (in user session or in background);
- relax and watch how the bot will take deals, start your task and perform task tracking.

---

## Preparations

  `git clone git://github.com/sonm-io/taskman.git`
  
  `pip3.7 install -r requirements.txt`

## Configuration

- Describe hardware requirements (see *claymore_config.yaml* for example);
- Describe specification of your task you want to run in SONM (see *claymore_task.yaml* for example);
- Edit config.yaml to describe keystore settings and list of tasks for managing.

You may use this bot to manage multiple different tasks. Task configs must have differemt tags.
You may change configs and you don't need to interrupt bot for this (add/remove tasks, increase or reduce number of instances for each task). Configs are reloaded once per minute.

## Usage

`./taskman.py` (or `nohup ./taskman.py &` to run bot in background).

Bot will create orders and wait for deals.
When deal appears, it will start task and will track it.

You may see bot stats at http://localhost:8081 (you may change default port in config).

Bot logs are in *./out/logs/monitor.log*.

Bot retrieve task logs on task fail or successfull finish. Logs are in *./out* folder.

If you want to change order price or hardware requirements, you may change config and run `sonmcli order purge`.

Bot will close deals if task has failed to start (and add worker to blacklist).
Run command `sonmcli blacklist purge` to clear blacklist.

---

Visit https://docs.sonm.com/guides/sonm-taskman for additional info.
