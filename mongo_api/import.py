import argparse
import logging
from lib.stopstart_lib import StopStart

logging.basicConfig(
    level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)


parser = argparse.ArgumentParser(description="Import existing MongoDB clusters into Ops/Cloud Manager")

requiredNamed = parser.add_argument_group('required arguments')
requiredNamed.add_argument("--host"
        ,help='the OpsMgr host with protocol and port, e.g. http://server.com:8080'
        ,required=True)
requiredNamed.add_argument("--group"
        ,help='the OpsMgr group id'
        ,required=True)
requiredNamed.add_argument("--username"
        ,help='OpsMgr user name'
        ,required=True)
requiredNamed.add_argument("--apiKey"
        ,help='OpsMgr api key for the user'
        ,required=True)

actionsParser = parser.add_argument_group('actions')
actionsParser.add_argument("--printAutomationConfig",dest='action', action='store_const'
        ,const=printAutomationConfig
        ,help='Get Automation Config')
actionsParser.add_argument("--importReplicaSet",dest='action', action='store_const'
        ,const=importReplicaSet
        ,help='Import an existing replica set')
actionsParser.add_argument("--removeReplicaSet",dest='action', action='store_const'
        ,const=removeReplicaSet
        ,help='Remove an existing replica set')


optionsParser = parser.add_argument_group('options')
optionsParser.add_argument("--rsName"
        ,help='Replica Set Name'
        ,required=False)
optionsParser.add_argument("--rsHost"
        ,help='Hostname of one replica member used as the import "seed"'
        ,required=False)
optionsParser.add_argument("--rsPort"
        ,help='MongoDB port number'
        ,required=False
        ,default=27017)
optionsParser.add_argument("--rsUser"
        ,help='MongoDB username to connect to replica set'
        ,required=False)
optionsParser.add_argument("--rsPassword"
        ,help='MongoDB password to connect to replica set'
        ,required=False)
optionsParser.add_argument("--autoPassword"
        ,help='MongoDB password for mms-automation user'
        ,required=False)
optionsParser.add_argument("--waitForLock"
        ,help='Number of seconds to wait for a process lock - default 10 '
        ,required=False)


args = parser.parse_args()

if args.action is None:
    parser.parse_args(['-h'])

args.action()
