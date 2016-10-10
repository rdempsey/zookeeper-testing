# Zookeeper Testing: Prototype

Prototype (dockerized) application to demonstrate dynamically configuring an application based on configs obtained from Apache Zookeeper. Currently it's a test of how to dynamically configure [Traptors](https://github.com/istresearch/traptor) as they are scaled.

## Requirements

* Python 3.5.2
* [Docker](https://www.docker.com)
* [Docker-Compose](https://docs.docker.com/compose/)

## Running It

Get the code:

* `git clone git@github.com:rdempsey/zookeeper-testing.git`
* `cd zookeeper-testing`

Create a new Python virtual environment and then install all of the requirements so you can run the Zookeeper scripts:

```
pip install -r requirements.txt
```


Next fire up all things Docker:

* `docker login` if you aren't already logged into docker hub.
* `docker-compose down` if you have any previous containers running.
* `docker-compose up --build -d` to build everything
* `docker ps` to check if everything is running. Give it about 10-15 seconds and then...

## First Time Configuration

Once all of the Docker containers are operational, add the base configuration to Zookeeper by running the following:

```
python zk_add_base_config.py
```

**Note**: if you ever need to recreate the base config you'll need to remove all existing configs first.

## Load the Twitter Configs into Zookeeper

First rename `twitter_creds_example.yml` to `twitter_creds.yml` and add your configs to the file.

Next, load the Traptor configs into Zookeeper by running the following:

```
python zk_add_configs.py
```

**Note**: running `zk_add_configs.py` multiple times will overwrite the current settings although the base configuration will remain untouched.

## Verifying Everything Works

Visit Kibana at the following url:

```
http://localhost:5601/app/kibana#/discover
```

You will need to create an index pattern. Use `logs-*` for that and `timestamp` for the timestamp field. Once that is created click on the Discover tab and turn on auto-refresh.

## To Do

* Add tests