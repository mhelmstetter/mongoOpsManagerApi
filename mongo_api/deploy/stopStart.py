import requests
from requests.auth import HTTPDigestAuth
import json
import argparse
import logging
import pprint
import sys
import time
import copy
from pymongo import MongoClient
from bson.json_util import dumps
import fcntl
import errno
import time
sys.path.append('../lib')
from automation_api_base import AutomationApiBase


logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

# LaSpina - added file locking mechanism to prevent multiple scripts from running
class FileLock:
    def __init__(self, filename=None):
        self.filename = './MONGODB_AUTOMATION_LOCK_FILE' if filename is None else filename
        self.lock_file = open(self.filename, 'w+')

    def unlock(self):
        fcntl.flock(self.lock_file, fcntl.LOCK_UN)

    def lock(self, maximum_wait=10):
        waited = 0
        while True:
            try:
                fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                print ("file locked")
                return True
            except IOError as e:
                if e.errno != errno.EAGAIN:
                    raise e
                else:
                    time.sleep(1)
                    waited += 1
                    if waited >= maximum_wait:
                        return False


class StopStart(AutomationApiBase):

    def __init__(self, host, group_id, api_user, api_key):
        AutomationApiBase.__init__(self, host, group_id, api_user, api_key)

    #
    # Wait for a given member to become either
    # PRIMARY', 'SECONDARY',  or 'ARBITER' before exiting the script
    #
    def waitForSecondary(self):
        client = MongoClient(host=host, port=int(port))
        db = client.admin
        db.authenticate(args.rsUser, args.rsPassword)

        print "Wait for secondary"
        # LaSpina - Changed from dictionary {} to list [] for 2.5 compatibility.
        okStatus = ['PRIMARY', 'SECONDARY', 'ARBITER']
        while True:
            status = db.command("replSetGetStatus")
            for member in status['members']:
                print member['name']
                if member['name'] == args.hostPort:
                    stateStr = member['stateStr']
                    print 'stateStr: ' + stateStr
                    if stateStr in okStatus:
                        return


    def __startStopHost(self, disabledState):
        config = auto.get_automation_config()
        new_config = copy.deepcopy(config)

        modifiedCount = 0
        for item in list(new_config['processes']):
            if item.get('hostname') == host and item.get('args2_6', {}).get('net', {}).get('port') == int(port):
                modifiedCount += 1
                processName = item.get('name')
                if disabledState:
                    print 'Asked to stop process ' + processName
                    item['disabled'] = disabledState
                else:
                    print 'Asked to start process ' + processName
                    if item.get('disabled'):
                        del item['disabled']

        if modifiedCount > 0:
            self.__post_automation_config(new_config)

    # TODO - improve this logic to handle waiting for the connection
    #        if not disabledState:
    #            waitForSecondary()
        else:
            print "WARNING No matching host(s) %s found in automation config" % (args.hostPort)
            fl.unlock()
            sys.exit(1)



    def stopHost(self):
        self.__startStopHost(True)


    def startHost(self):
        self.__startStopHost(False)

    def __post_automation_config(self, automation_config):
        response = requests.put(automationConfigEndpoint,
                    auth=HTTPDigestAuth(args.username,args.apiKey),
                    data=json.dumps(automation_config),
                    headers=headers,
                    verify=False)

        print "Result %s %s" % (response.status_code,response.reason)

        if (response.status_code != requests.codes.created):
            print "ERROR %s %s" % (response.status_code,response.reason)
            print(response.headers)
            print(response.content)
        else:
            response.raise_for_status()


if __name__ == '__main__':

    headers = { "Content-Type" : "application/json" }
    disabled = { "enabled" : "false" }
    enabled = { "enabled" : "true" }

    requests.packages.urllib3.disable_warnings()

    parser = argparse.ArgumentParser(description="Manage users from MongoDB Ops/Cloud Manager")

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
    actionsParser.add_argument("--stopHost",dest='action', action='store_const'
            ,const=test.stopHost
            ,help='Stop monogd on specified host')
    actionsParser.add_argument("--startHost",dest='action', action='store_const'
            ,const=test.startHost
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


    args = parser.parse_args()
    test = StopStart(
        args.host,
        args.group,
        args.api_user,
        args.apiKey
    )

    if args.action is None:
        parser.parse_args(['-h'])

    fl = FileLock()
    if not fl.lock(int(args.waitForLock) if args.waitForLock is not None else 10):
        print ("Could not obtain process lock - exiting")
        sys.exit(1)

    automationConfigEndpoint = args.host +"/api/public/v1.0/groups/" + args.group +"/automationConfig"

    hostPort = args.hostPort.split(':')
    if len(hostPort) != 2:
        print "ERROR Invalid hostPort %s, should be of the form mongohost1.foo.com:27017" % (hostPort)
        sys.exit(2)

    host = hostPort[0]
    port = hostPort[1]

    # based on the argument passed, this will call the "const" function from the parser config
    # e.g. --disableAlertConfigs argument will call disableAlerts()
    args.action()
    time.sleep(30)

    fl.unlock()
