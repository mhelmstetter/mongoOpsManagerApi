import requests
from requests.auth import HTTPDigestAuth
import json
import argparse
import sys
import copy



def getAutomationConfig():
    response = requests.get(automationConfigEndpoint
            ,auth=HTTPDigestAuth(args.username,args.apiKey), verify=False)
    response.raise_for_status()
    return response.json()

def printAutomationConfig():
    config = getAutomationConfig()
    configStr = json.dumps(config, indent=4)
    print(configStr)

def __setVersion(item):
    item['version'] = args.version
    if args.version.startswith("3.4"):
        item['featureCompatibilityVersion'] = args.featureCompatibilityVersion
        print(str(item))

def __upgradeRs(new_config, rsNameToUpgade):

    for item in list(new_config['processes']):
        rsName = item.get('args2_6', {}).get('replication', {}).get('replSetName')
        if rsName == rsNameToUpgade:
            print(str(rsName))
            __setVersion(item)
    return new_config

def upgradeRs():

    config = getAutomationConfig()
    new_config = copy.deepcopy(config)

    __upgradeRs(new_config, args.rsName)

    configStr = json.dumps(new_config, indent=4)
    print(configStr)

    __post_automation_config(new_config)

def upgradeCluster():

    config = getAutomationConfig()
    new_config = copy.deepcopy(config)

    for cluster in list(new_config['sharding']):

        if cluster.get('name') == args.clusterName:

            for shard in cluster.get('shards'):
                rsName = shard['rs']
                #print "upgrade cluster " + rsName
                new_config = __upgradeRs(new_config, rsName)
            csrs = cluster.get('configServerReplica')
            new_config = __upgradeRs(new_config, csrs)

    for item in list(new_config['processes']):
        cluster = item.get('cluster', {})
        if (cluster == args.clusterName):
            __setVersion(item)

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
actionsParser.add_argument("--upgradeRs",dest='action', action='store_const'
        ,const=upgradeRs
        ,help='Upgrade the MongoDB version for a replica set')
actionsParser.add_argument("--upgradeCluster",dest='action', action='store_const'
        ,const=upgradeCluster
        ,help='Upgrade the MongoDB version for a sharded cluster')


optionsParser = parser.add_argument_group('options')
optionsParser.add_argument("--rsName"
        ,help='Replica Set Name to be upgraded'
        ,required=False)
optionsParser.add_argument("--clusterName"
        ,help='Cluster Name to be upgraded'
        ,required=False)
optionsParser.add_argument("--version"
        ,help='MongoDB version to upgrade to'
        ,required=True)
optionsParser.add_argument("--featureCompatibilityVersion"
        ,help='MongoDB featureCompatibilityVersion (e.g. 3.2 or 3.4) only required for MongoDB versions 3.4+'
        ,required=False
        ,default="3.2")



args = parser.parse_args()

if args.action is None:
    parser.parse_args(['-h'])

automationConfigEndpoint = args.host +"/api/public/v1.0/groups/" + args.group +"/automationConfig"

# based on the argument passed, this will call the "const" function from the parser config
# e.g. --disableAlertConfigs argument will call disableAlerts()
args.action()




