import requests
from requests.auth import HTTPDigestAuth
import json
import argparse

def getAlertConfigs():
    response = requests.get(alertConfigsEndpoint
            ,auth=HTTPDigestAuth(args.username,args.apiKey), verify=False)
    response.raise_for_status()
    return response.json()

def printAlertConfigs():
    configs = getAlertConfigs()
    configsStr = json.dumps(configs, indent=4)
    print(configsStr)

def setAlertsEnabled(enabledFlagJson):
    configs = getAlertConfigs()
    for alert in configs['results']:
        #print alert['id']
        for matcher in alert.get("matchers", None):
            #print matcher
            #print alert['id'] + " " + alert.get("typeName", "")
            if matcher['fieldName'] == 'HOSTNAME' and matcher['value'] == args.alertHostname:
                #print "got match on hostname"
                response = requests.patch(alertConfigsEndpoint + "/" + alert['id'],
                    auth=HTTPDigestAuth(args.username,args.apiKey),
                    verify=False,
                    data=json.dumps(enabledFlagJson),
                    headers=headers)
                response.raise_for_status()
                #print json.dumps(response.json(), indent=4)
                print "Setting alert " + response.json()['id'] + ", enabled:" + str(response.json()['enabled'])

def disableAlerts():
    setAlertsEnabled(disabled)

def enableAlerts():
    setAlertsEnabled(enabled)

#
# main
#

headers = { "Content-Type" : "application/json" }
disabled = { "enabled" : "false" }
enabled = { "enabled" : "true" }

requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser(description="Manage alerts from MongoDB Ops/Cloud Manager")

requiredNamed = parser.add_argument_group('required named arguments')
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

disableAlertArgs = parser.add_argument_group('disable alert arguments')

disableAlertArgs.add_argument("--disableAlertConfigs",dest='action', action='store_const'
        ,const=disableAlerts
        ,help='Disable alert configurations')
parser.add_argument("--enableAlertConfigs",dest='action', action='store_const'
        ,const=enableAlerts
        ,help='Enable alert configurations')
parser.add_argument("--alertHostname"
        ,help='Hostname to use for enableAlerts/disableAlerts'
        ,required=False)
parser.add_argument("--printAlertConfigs",dest='action', action='store_const'
        ,const=printAlertConfigs
        ,help='Print alert configurations')

args = parser.parse_args()

if args.action is None:
    parser.parse_args(['-h'])

alertConfigsEndpoint = args.host +"/api/public/v1.0/groups/" + args.group +"/alertConfigs"

# based on the argument passed, this will call the "const" function from the parser config
# e.g. --disableAlertConfigs argument will call disableAlerts()
args.action()




