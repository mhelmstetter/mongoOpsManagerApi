import requests
from requests.auth import HTTPDigestAuth
import json
import argparse
import sys
import copy

# get all hosts in group as a dict
def getHosts():
    response = requests.get(hostsEndpoint
            ,auth=HTTPDigestAuth(args.username,args.apiKey), verify=False)
    response.raise_for_status()
    return response.json()

def printHosts():
    hosts = getHosts()
    hostsStr = json.dumps(hosts, indent=4)
    print(hostsStr)

# get alert configs as a dict
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
            if matcher['fieldName'] == 'HOSTNAME_AND_PORT' and matcher['value'] == args.alertHostnamePort:
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

def exportAlertConfigs():
    alertConfigs = getAlertConfigs()

    with open(args.alertConfigsOutput, 'w') as outfile:
        json.dump(alertConfigs, outfile, indent=4, sort_keys=True, separators=(',', ':'))

def importAlertConfigs():
    if ( args.alertConfigsInput == "-" ):
        data = sys.stdin.read()
    else:
        data = open( args.alertConfigsInput, 'r').read()
    #print data
    alert_configs = json.loads(data)
    __post_alert_configs(args,alert_configs)


# loop through all alerts from the input file
# for all HOST alerts loop through all hosts and duplicate
# that alert for every host.
# for all other alerts, duplicate the alert
def importAlertConfigsEveryHost():
    if ( args.alertConfigsInput == "-" ):
        data = sys.stdin.read()
    else:
        data = open( args.alertConfigsInput, 'r').read()

    alert_configs = json.loads(data)
    hosts = getHosts()

    new_alert_configs = {}
    new_alert_configs['results']=[]

    for alert in alert_configs['results']:

        if alert.get('typeName', None) in ['HOST', 'HOST_METRIC']:
            for host in hosts['results']:
                hostnamePort = host['hostname'] + ":" + str(host['port'])
                new_alert = copy.deepcopy(alert)
                for matcher in new_alert.get("matchers", None):
                    # replace the hostname of the cloned alert with the new hostname
                    if matcher['fieldName'] == 'HOSTNAME_AND_PORT':
                        matcher['value'] = hostnamePort
                new_alert_configs['results'].append(new_alert)
        else:
            new_alert = copy.deepcopy(alert)
            new_alert_configs['results'].append(new_alert)

    # all done now create all of the new alerts
    __post_alert_configs(args,new_alert_configs)

def __post_alert_configs(args,alert_configs):
    migrated_alerts = 0
    failed_migrations = 0
    for alert in alert_configs['results']:

        __delete_node(alert, 'links')
        __delete_node(alert, 'id')
        __delete_node(alert, 'created')
        __delete_node(alert, 'updated')

        #print(json.dumps(alert, indent=4))

        response = requests.post(alertConfigsEndpoint,
                    auth=HTTPDigestAuth(args.username,args.apiKey),
                    data=json.dumps(alert),
                    headers=headers,
                    verify=False)

        print "Result %s %s" % (response.status_code,response.reason)

        if args.continueOnError and (response.status_code != requests.codes.created):
            print "ERROR %s %s" % (response.status_code,response.reason)
            print( "Failed migration alert JSON:" )
            print json.dumps(alert)
            failed_migrations += 1
        else:
            response.raise_for_status()
            migrated_alerts += 1
    print "Migrated %d alerts (%d failures)" % (migrated_alerts,failed_migrations)

def __delete_node(myDict, key):
    if (myDict.get(key, None)):
        del myDict[key]


def deleteAlertConfigs():
    deleted_alerts = 0
    failed_deletions = 0

    alert_configs = getAlertConfigs()

    for alert in alert_configs["results"]:
        response = requests.delete(alertConfigsEndpoint + "/" + alert['id'],
                    auth=HTTPDigestAuth(args.username,args.apiKey),
                    verify=False)
        if args.continueOnError and (response.status_code != requests.codes.ok):
            print "ERROR %s %s" % (response.status_code,response.reason)
            print( "Failed migration alert JSON:" )
            print json.dumps(alert)
            failed_deletions += 1
        else:
            response.raise_for_status()
            deleted_alerts += 1
    print "Deleted %d alerts (%d failures)" % (deleted_alerts,failed_deletions)

#
# main
#

headers = { "Content-Type" : "application/json" }
disabled = { "enabled" : "false" }
enabled = { "enabled" : "true" }

requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser(description="Manage alerts from MongoDB Ops/Cloud Manager")

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
actionsParser.add_argument("--disableAlertConfigs",dest='action', action='store_const'
        ,const=disableAlerts
        ,help='Disable alert configurations')
actionsParser.add_argument("--enableAlertConfigs",dest='action', action='store_const'
        ,const=enableAlerts
        ,help='Enable alert configurations')
actionsParser.add_argument("--printAlertConfigs",dest='action', action='store_const'
        ,const=printAlertConfigs
        ,help='Print alert configurations')
actionsParser.add_argument("--printHosts",dest='action', action='store_const'
        ,const=printHosts
        ,help='Print all hosts in group')
actionsParser.add_argument("--importAlertConfigs",dest='action', action='store_const'
        ,const=importAlertConfigs
        ,help='import alert configs from file')
actionsParser.add_argument("--importAlertConfigsEveryHost",dest='action', action='store_const'
        ,const=importAlertConfigsEveryHost
        ,help='for every host in the group, create alert configs from the specified template file')
actionsParser.add_argument("--exportAlertConfigs",dest='action', action='store_const'
        ,const=exportAlertConfigs
        ,help='export alert configs to file')

actionsParser.add_argument("--deleteAlertConfigs",dest='action', action='store_const'
        ,const=deleteAlertConfigs
        ,help='delete ALL alert configs from host')

optionsParser = parser.add_argument_group('options')
optionsParser.add_argument("--alertHostnamePort"
        ,help='Hostname:port to use for enableAlerts/disableAlerts'
        ,required=False)
optionsParser.add_argument("--alertConfigsInput"
        ,help='Input file containing JSON alert configs or "-" for STDIN (default: export.json)'
        ,default="export.json")
optionsParser.add_argument("--alertConfigsOutput"
        ,help='Output file containing JSON alert configs (default: export.json)'
        ,default="export.json")
optionsParser.add_argument("--continueOnError", action='store_true', default=False
        ,help='for operations that issue multiple API calls, continue processing even if errors occur')

args = parser.parse_args()

if args.action is None:
    parser.parse_args(['-h'])

alertConfigsEndpoint = args.host +"/api/public/v1.0/groups/" + args.group +"/alertConfigs"
hostsEndpoint = args.host +"/api/public/v1.0/groups/" + args.group +"/hosts"

# based on the argument passed, this will call the "const" function from the parser config
# e.g. --disableAlertConfigs argument will call disableAlerts()
args.action()




