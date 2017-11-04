import requests
from requests.auth import HTTPDigestAuth
import json
import argparse
import sys
import copy
from pymongo import MongoClient
from bson.json_util import dumps

def fixNoTablescan(config):
    for process in config.get('processes', None):
        notable_opt = process.get("args2_6", {}).get("setParameter", {}).get("notablescan")
        if notable_opt != None and (notable_opt == "false" or notable_opt == "true") :
            if notable_opt == "false":
               process['args2_6']['setParameter']['notablescan'] = False
            else:
                process['args2_6']['setParameter']['notablescan'] = True

def getAutomationConfig():
    response = requests.get(automationConfigEndpoint
            ,auth=HTTPDigestAuth(args.username,args.apiKey), verify=False)
    response.raise_for_status()
    new_config = copy.deepcopy(response.json())
    fixNoTablescan(new_config)
    return new_config

def printAutomationConfig():
    config = getAutomationConfig()
    configStr = json.dumps(config, indent=4)
    print(configStr)

def changeKey():

    config = getAutomationConfig()
    new_config = copy.deepcopy(config)
    new_config['auth']['key'] = args.key
    __post_automation_config(new_config)


def __post_automation_config(automation_config):
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


#
# main
#

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
actionsParser.add_argument("--changeKey",dest='action', action='store_const'
        ,const=changeKey
        ,help='Stop monogd on specified host')


optionsParser = parser.add_argument_group('options')
optionsParser.add_argument("--key"
        ,help='Keyfile string'
        ,required=True)




args = parser.parse_args()

if args.action is None:
    parser.parse_args(['-h'])

automationConfigEndpoint = args.host +"/api/public/v1.0/groups/" + args.group +"/automationConfig"



# based on the argument passed, this will call the "const" function from the parser config
# e.g. --disableAlertConfigs argument will call disableAlerts()
args.action()