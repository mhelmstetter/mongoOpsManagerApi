import argparse
import logging
from lib.stopstart_lib import StopStart

logging.basicConfig(
    level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)

def stopHost():
    target = StopStart(args.base_url, args.group_id, args.api_user, args.api_key,
                       args.hostPort, args.rsUser, args.rsPassword, args.lock_mongo_uri)
    target.stopHost()


def startHost():
    target = StopStart(args.base_url, args.group_id, args.api_user, args.api_key,
                       args.hostPort, args.rsUser, args.rsPassword, args.lock_mongo_uri)
    target.startHost()

parser = argparse.ArgumentParser(description="Manage users from MongoDB Ops/Cloud Manager")

requiredNamed = parser.add_argument_group('required arguments')
requiredNamed.add_argument("--base_url"
        ,help='the OpsMgr host with protocol and port, e.g. http://server.com:8080'
        ,required=True)
requiredNamed.add_argument("--group_id"
        ,help='the OpsMgr group id'
        ,required=True)
requiredNamed.add_argument("--api_user"
        ,help='OpsMgr user name'
        ,required=True)
requiredNamed.add_argument("--api_key"
        ,help='OpsMgr api key for the user'
        ,required=True)

actionsParser = parser.add_argument_group('actions')
actionsParser.add_argument("--stopHost",dest='action', action='store_const'
        ,const=stopHost
        ,help='Stop monogd on specified host')
actionsParser.add_argument("--startHost",dest='action', action='store_const'
        ,const=startHost
        ,help='Start monogd on specified host')


optionsParser = parser.add_argument_group('options')
optionsParser.add_argument("--hostPort"
        ,help='host:port of process to be stopped/started'
        ,required=False)
optionsParser.add_argument("--rsUser"
        ,help='MongoDB username to connect to replica set'
        ,required=False)
optionsParser.add_argument("--rsPassword"
        ,help='MongoDB password to connect to replica set'
        ,required=False)
optionsParser.add_argument("--waitForLock"
        ,help='Number of seconds to wait for a process lock - default 10 '
        ,required=False)
optionsParser.add_argument("--lock_mongo_uri"
        ,help='Mongo URI for where to store lock document'
        ,required=False)



args = parser.parse_args()

if args.action is None:
    parser.parse_args(['-h'])

args.action()

