import requests
from requests.auth import HTTPDigestAuth
import json
import argparse
import sys
import copy
from pymongo import MongoClient

processTemplate = {
    "authSchemaVersion": 5,
    "disabled": False,
    "hostname": "",
    "logRotate": {
        "maxUncompressed": 5,
        "numUncompressed": 5,
        "percentOfDiskspace": 0.9,
        "sizeThresholdMB": 1536,
        "timeThresholdHrs": 24
    },
    "manualMode": False,
    "name": "",
    "numCores": 0,
    "processType": "mongod",
    "featureCompatibilityVersion": "3.4",
    "version": "3.4.14",
    "args2_6": {
        "net": {
            "port": 27017
        },
        "storage": {
            "dbPath": "/data"
        },
        "systemLog": {
            "destination": "file",
            "path": "/data/mongodb.log"
        },
        "replication": {
            "replSetName": ""
        }
    }
}

monitoringUser = {
    "initPwd" : "cf2ac21046052a0f61215dd86d94b708",
    "db": "admin",
    "user": "mms-monitoring-agent",
    "roles": [
        {
            "role": "clusterMonitor",
            "db": "admin"
        }
    ]
}

backupUser =  {
    "initPwd": "b386182320b2c23a7adcbcee7840b1d1",
    "db": "admin",
    "user": "mms-backup-agent",
    "roles": [
        {
            "role": "clusterAdmin",
            "db": "admin"
        },
        {
            "role": "readAnyDatabase",
            "db": "admin"
        },
        {
            "role": "userAdminAnyDatabase",
            "db": "admin"
        },
        {
            "role": "readWrite",
            "db": "local"
        },
        {
            "role": "readWrite",
            "db": "admin"
        }
    ]
}

# TODO - how do we get the matching version of the monitoring agent to Ops Manager?
monitoringVersion = {
            "directoryUrl": None,
            "hostname": "",
            "baseUrl": None,
            "name": "5.4.3.361"
        }


def getAutomationConfig():
    response = requests.get(automationConfigEndpoint
            ,auth=HTTPDigestAuth(args.username,args.apiKey), verify=False)
    response.raise_for_status()
    #print "Result %s %s" % (response.status_code,response.reason)
    #print(response.headers)
    #print(response.content)
    return response.json()

def printAutomationConfig():
    config = getAutomationConfig()
    configStr = json.dumps(config, indent=4)
    print(configStr)





def addReplicaSet():
    config = getAutomationConfig()
    new_config = copy.deepcopy(config)
    hosts = args.rsHosts.split(",")
    process_id = 0; # TODO might need something more unique

    data = open( args.rsTemplate, 'r').read()
    rsTemplate = json.loads(data)

    rsConfig = copy.deepcopy(rsTemplate)
    rsConfig['_id'] = args.rsName

    for host in hosts:
        process = copy.deepcopy(processTemplate)
        process['hostname'] = host
        process['name'] = args.rsName + "_" + str(process_id)
        process['args2_6']['replication']['replSetName'] = args.rsName
        new_config['processes'].append(process)
        rsConfig['members'][process_id]['_id'] = process_id
        rsConfig['members'][process_id]['host'] = args.rsName + "_" + str(process_id)
        process_id += 1

    new_config['replicaSets'].append(rsConfig)

    configStr = json.dumps(new_config, indent=4)
    print(configStr)

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
actionsParser.add_argument("--printAutomationConfig",dest='action', action='store_const'
        ,const=printAutomationConfig
        ,help='Get Automation Config')
actionsParser.add_argument("--addReplicaSet",dest='action', action='store_const'
        ,const=addReplicaSet
        ,help='Add new replica set')


optionsParser = parser.add_argument_group('options')
optionsParser.add_argument("--rsName"
        ,help='Replica Set Name'
        ,required=False)
optionsParser.add_argument("--rsHosts"
        ,help='Comma separated list of replica set hosts'
        ,required=False)
optionsParser.add_argument("--rsTemplate"
        ,help='Input file containing JSON template for replica set config'
        ,required=False)


args = parser.parse_args()

if args.action is None:
    parser.parse_args(['-h'])

alertConfigsEndpoint = args.host +"/api/public/v1.0/groups/" + args.group +"/alertConfigs"
hostsEndpoint = args.host +"/api/public/v1.0/groups/" + args.group +"/hosts"
automationConfigEndpoint = args.host +"/api/public/v1.0/groups/" + args.group +"/automationConfig"

# based on the argument passed, this will call the "const" function from the parser config
# e.g. --disableAlertConfigs argument will call disableAlerts()
args.action()




