import yaml
from scutils.log_factory import LogFactory
from kazoo.client import KazooClient, KazooState

# Set up logging
logger = LogFactory.get_instance(json=True,
                                 stdout=True,
                                 name="zksetup",
                                 level='INFO',
                                 dir='logs',
                                 file='zksetup.log')

# Create a zookeeper listener
def _my_listener(state):
    if state == KazooState.LOST:
        # Register somewhere that the session was lost
        logger.warning("Zookeeper session lost: {}".format(state))
    elif state == KazooState.SUSPENDED:
        # Handle being disconnected from Zookeeper
        logger.warning("Zookeeper session suspended: {}".format(state))
    else:
        # Handle being connected/reconnected to Zookeeper
        logger.info("Connected to zookeeper: {}".format(state))

# Connect to Zookeeper
try:
    logger.info("Connecting to zookeeper")
    zk = KazooClient(hosts='localhost:2181')
    zk.add_listener(_my_listener)
    zk.start()
except Exception as e:
    logger.error("Unable to start the connection to Zookeeper".format(e))

# Create the base config in Zookeeper
try:
    zk.create("/zktesting")
    zk.create("/zktesting/traptor")
except Exception as e:
    logger.error("Unable to create the base Traptor config")

zk.stop()