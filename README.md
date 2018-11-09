# sonm-taskman

## Preparations

  `git clone git://github.com/sonm-io/taskman.git`
  
**Mac OS X:**  
  
  `pip3.7 install -r requirements.txt`

**Linux:**
  
  `pip3.7 install -r requirements.txt`

## Configuration

- Describe hardware requirements (see *config_task_claymore.yaml* for example);
- Describe specification of your task you want to run in SONM (see *claymore.yaml* for example);
- Edit config.yaml to describe keystore settings and list of tasks for managing.

You may use this bot to manage multiple different tasks. Task configs must have differemt tags.
You may change configs and you don't need to interrupt bot for this (add/remove tasks, increase or reduce number of instances for each task). Configs are reloaded once per minute.

## Usage

`./taskman.py` (or `nohup ./taskman.py &` to run bot in background).

Bot will create orders and wait for deals.
When deal appears, it will start task and will track it.

You may see bot stats at http://localhost:8081 (you may change default port in config).

Bot logs are in *monitor.log*.

If you want to change order price, you may change config and run `sonmcli order purge`.

Bot will close deals if task has failed to start.
Run command `sonmcli blacklist purge` to clear blacklist.
