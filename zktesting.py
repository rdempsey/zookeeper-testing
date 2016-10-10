import time
import sys
import os
from scutils.log_factory import LogFactory
from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import NoNodeError

# dc up --build --force-recreate -d

class ZkTest(object):
    def __init__(self,
                 zk_hosts,
                 traptor_type=None,
                 traptor_id=None,
                 traptor_api_keys=None,
                 log_level='INFO',
                 log_dir='/var/log/zktesting',
                 log_file='zktesting.log'):

        self.zk_hosts = zk_hosts
        self.traptor_type = traptor_type
        self.traptor_id = traptor_id
        self.traptor_api_keys = traptor_api_keys
        self.log_level = log_level
        self.log_dir = log_dir
        self.log_file = log_file


    def _my_listener(self, state):
        if state == KazooState.LOST:
            # Register somewhere that the session was lost
            self.logger.warning("Zookeeper session lost: {}".format(state))
        elif state == KazooState.SUSPENDED:
            # Handle being disconnected from Zookeeper
            self.logger.warning("Zookeeper session suspended: {}".format(state))
        else:
            # Handle being connected/reconnected to Zookeeper
            self.logger.info("Connected to zookeeper and obtaining configuration info: {}".format(state))

    def _get_configs_from_zookeeper(self):
        """Get the configs from Zookeeper"""
        # Config format: /zktesting/traptor/<traptor-name>/<key>:<value>
        self.logger.info("Checking zookeeper for configs")
        try:
            configs = self.zk.get_children("/zktesting/traptor")
        except NoNodeError as nne:
            self.logger.warning("No base configs found.")
            return

        self.logger.debug("App configs: {}".format(configs))
        self.logger.debug("Config count: {}".format(len(configs)))

        # If there are Traptor configs, process them.
        if len(configs) > 0:
            # Get all the config statuses
            available_configs = []

            try:
                for config in configs:
                    self.logger.debug("Checking config: {}".format(config))
                    config_status = self.zk.get("/zktesting/traptor/{}/status".format(config))[0].decode('utf-8')
                    self.logger.debug("Config status: {}".format(config_status))
                    if config_status == 'available':
                        available_configs.append(config)
            except NoNodeError as nne:
                self.logger.error("Unable to get config status: {}".format(nne))

            # If a config is available, assign the first one to self
            if len(available_configs) > 0:
                self.logger.info("Available configs found: {}".format(available_configs))
                config = available_configs[0]
                self.logger.info("Updating from config: {}".format(config))
                self.traptor_type = self.zk.get("/zktesting/traptor/{}/traptor_type".format(config))[0].decode('utf-8')
                self.traptor_id = self.zk.get("/zktesting/traptor/{}/traptor_id".format(config))[0].decode('utf-8')
                self.traptor_api_keys = {
                    "consumer_key": self.zk.get("/zktesting/traptor/{}/consumer_key".format(config))[0].decode('utf-8'),
                    "consumer_secret": self.zk.get("/zktesting/traptor/{}/consumer_secret".format(config))[0].decode('utf-8'),
                    "access_token": self.zk.get("/zktesting/traptor/{}/access_token".format(config))[0].decode('utf-8'),
                    "access_token_secret": self.zk.get("/zktesting/traptor/{}/access_token_secret".format(config))[0].decode('utf-8')
                }
                # Set the status of this Traptor config as unavailable
                self.zk.set("/zktesting/traptor/{}/status".format(config), b"assigned")
                # Kill the connection to Zookeeper
                self.zk.stop()

    def _wait_for_config(self):
        """Check Zookeeper for available Traptor configs until one is available"""
        self._get_configs_from_zookeeper()

        while self.traptor_type is None:
            self.logger.info("No app configs available. Sleeping for 15 seconds.")
            time.sleep(15)
            self._get_configs_from_zookeeper()

    def _do_your_thang(self):
        self.logger.info("I'm doing my streaming thang!")
        self.logger.info("My info: Type: {}, ID: {}".format(self.traptor_type,
                                                            self.traptor_id))
        # This is where you would be streaming data. For now just exit.
        # Note: this will cause your Docker container to continuously restart
        sys.exit()

    def run(self):
        """Do your thang!"""
        time.sleep(30)
        # Set up a logger
        self.logger = LogFactory.get_instance(json=True,
                                              stdout=False,
                                              name="zktesting",
                                              level=self.log_level,
                                              dir=self.log_dir,
                                              file=self.log_file)

        # Connect to Zookeeper
        self.logger.info("Connecting to zookeeper and obtaining configuration info")
        self.zk = KazooClient(hosts=self.zk_hosts)
        self.zk.add_listener(self._my_listener)
        self.zk.start()

        # Wait until there is a config available, then grab the first one and start "processing"
        while True:
            self._wait_for_config()
            # Act like we're in business
            self.logger.info("Configuration complete. Starting main loop.")
            self._do_your_thang()

def main():
    # Defaults below are for running on your local computer. Defaults in the class are for the Dockerized version.

    # Zookeeper
    zk_hosts = os.getenv('ZK_HOSTS', 'localhost:2181')

    # Log info
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_dir = os.getenv('LOG_DIR', './logs')
    log_file = os.getenv('LOG_FILE', 'zktesting.log')

    # Create a ZkTest object and run it
    zktest = ZkTest(zk_hosts=zk_hosts,
                    log_level=log_level,
                    log_dir=log_dir,
                    log_file=log_file)
    zktest.run()


if __name__ == '__main__':
    sys.exit(main())