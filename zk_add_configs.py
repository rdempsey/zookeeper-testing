import yaml
from scutils.log_factory import LogFactory
from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import NoNodeError

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

# Read the yaml config
logger.info("Loading the yaml config")
with open('twitter_creds.yml') as f:
    creds = yaml.load(f)

# Create Zookeeper configs for each traptor in the yaml file. Assumes that the base config already exists
for traptor, config in creds['traptors'].items():

    # Get the configs
    traptor_name = traptor
    traptor_type = config['traptor_type']
    traptor_id = str(config['traptor_id'])
    status = config['status']
    consumer_key = config['consumer_key']
    consumer_secret = config['consumer_secret']
    access_token = config['access_token']
    access_token_secret = config['access_token_secret']

    fields = [
        'traptor_name',
        'traptor_type',
        'traptor_id',
        'status',
        'consumer_key',
        'consumer_secret',
        'access_token',
        'access_token_secret'
    ]

    # Delete all the fields for this Traptor if they exist
    logger.info("Deleting the current config for {} from Zookeeper".format(traptor))
    for field in fields:
        try:
            zk.delete("/zktesting/traptor/{}/{}".format(traptor_name, field))
        except NoNodeError as nne:
            logger.error("Unable to delete field: {}. Error: {}".format(field, nne))
            pass

    # Delete the base traptor config for this Traptor
    try:
        # /zktesting/traptor/<traptor-name>/<key>:<value>
        zk.delete("/zktesting/traptor/{}".format(traptor_name))
    except NoNodeError as nne:
        logger.error("Error when deleting a config: {}".format(nne))
        pass

    # Create a new znode for this traptor
    logger.info("Adding the config for {} to Zookeeper".format(traptor))
    try:
        # /zktesting/traptor/<traptor-name>/<key>:<value>
        zk.create("/zktesting/traptor/{}".format(traptor_name))
    except Exception as e:
        logger.error("Unable to add the base config for: {}".format(traptor_name))

    # Add the data to the znode
    try:
        zk.create("/zktesting/traptor/{}/traptor_type".format(traptor_name), bytes(traptor_type, 'utf-8'))
        zk.create("/zktesting/traptor/{}/traptor_id".format(traptor_name), bytes(traptor_id, 'utf-8'))
        zk.create("/zktesting/traptor/{}/status".format(traptor_name), bytes(status, 'utf-8'))
        zk.create("/zktesting/traptor/{}/consumer_key".format(traptor_name), bytes(consumer_key, 'utf-8'))
        zk.create("/zktesting/traptor/{}/consumer_secret".format(traptor_name), bytes(consumer_secret, 'utf-8'))
        zk.create("/zktesting/traptor/{}/access_token".format(traptor_name), bytes(access_token, 'utf-8'))
        zk.create("/zktesting/traptor/{}/access_token_secret".format(traptor_name), bytes(access_token_secret, 'utf-8'))
    except Exception as e:
        logger.error("Unable to add node(s) to Zookeeper: {}".format(e))
        pass

    # Let's see what we've got
    try:
        logger.info("Child information for {}".format(zk.get_children("/zktesting/traptor/{}".format(traptor_name))))
    except Exception as e:
        pass

    for field in fields:
        try:
            logger.info(zk.get("/zktesting/traptor/{}/{}".format(traptor_name, field)))
        except Exception as e:
            logger.error("Unable to retrieve information for: {}. Error: {}".format(field, e))
            pass

zk.stop()