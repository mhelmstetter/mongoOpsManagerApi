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

def get_automation_status():
    response = requests.get(automationStatusEndpoint
            ,auth=HTTPDigestAuth(args.username,args.apiKey), verify=False)
    response.raise_for_status()
    return response.json()

def wait_for_goal_state():
    count = 0
    while True:
        continue_to_wait = False
        status = get_automation_status()
        goal_version = status['goalVersion']

        for process in status['processes']:
            logging.info("Round: %s GoalVersion: %s Process: %s (%s) LastVersionAchieved: %s Plan: %s "
                 % (count, goal_version, process['name'], process['hostname'], process['lastGoalVersionAchieved'], process['plan']))

            if process['lastGoalVersionAchieved'] < goal_version:
                continue_to_wait = True

        if continue_to_wait:
            time.sleep(5)
        else:
            logging.info("All processes in Goal State. GoalVersionAchieved: %s" % goal_version)
            break
        count += 1

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
    wait_for_goal_state()

def addReplicaMember():
    config = getAutomationConfig()
    new_config = copy.deepcopy(config)

    data = open( args.rsTemplate, 'r').read()
    rsTemplate = json.loads(data)

    hostPort = args.hostPort.split(':')
    if len(hostPort) != 2:
        print "ERROR Invalid hostPort %s, should be of the form mongohost1.foo.com:27017" % (hostPort)
        sys.exit(2)

    host = hostPort[0]
    port = hostPort[1]

    modifiedCount = 0
    for item in list(new_config['processes']):
        if item.get('hostname') == host and item.get('args2_6', {}).get('net', {}).get('port') == int(port):
            modifiedCount += 1
            processName = item.get('name')
            print processName
            break

    if modifiedCount > 0:
        print "ERROR Host %s already exists in automation config" % (args.hostPort)
        sys.exit(1)


    rsName = args.rsName
    rsIds = []
    rsCount = 0

    for replicaSet in list(new_config['replicaSets']):
        if replicaSet.get('_id') == rsName:
            for member in list(replicaSet['members']):
                rsIds.append(member.get('_id'))

    print "Existing rsIds %s" % str(rsIds)

    process_id = max(rsIds) + 1
    rsMemberIndex = len(rsIds)
    rsConfig = copy.deepcopy(rsTemplate)
    rsConfig['_id'] = args.rsName

    #TODO make this a function
    process = copy.deepcopy(processTemplate)
    process['hostname'] = host
    process['name'] = args.rsName + "_" + str(process_id)
    process['args2_6']['replication']['replSetName'] = args.rsName
    new_config['processes'].append(process)

    # TODO assumes template members are all the same,
    # need to know template/details for the member we're adding
    rsConfig['members'][rsMemberIndex]['_id'] = process_id
    rsConfig['members'][rsMemberIndex]['host'] = args.rsName + "_" + str(process_id)

    for replicaSet in list(new_config['replicaSets']):
        if replicaSet.get('_id') == rsName:
            replicaSet['members'].append(rsConfig['members'][rsMemberIndex])
            print str(rsConfig['members'][rsMemberIndex])

    configStr = json.dumps(new_config, indent=4)
    print(configStr)
    __post_automation_config(new_config)
    wait_for_goal_state()



def removeReplicaMember():
    config = getAutomationConfig()
    new_config = copy.deepcopy(config)

    hostPort = args.hostPort.split(':')
    if len(hostPort) != 2:
        print "ERROR Invalid hostPort %s, should be of the form mongohost1.foo.com:27017" % (hostPort)
        sys.exit(2)

    host = hostPort[0]
    port = hostPort[1]

    modifiedCount = 0
    procsList = list(new_config['processes'])
    for idx,item in enumerate(procsList):
        if item.get('hostname') == host and item.get('args2_6', {}).get('net', {}).get('port') == int(port):
            modifiedCount += 1
            processName = item.get('name')
            print processName
            procsList.pop(idx)
            break
    new_config['processes'] = procsList

    rsNameId = processName.split('_')
    rsName = rsNameId[0];
    print rsName
    rsMemberId = int(rsNameId[1]);

    for replicaSet in list(new_config['replicaSets']):
        if replicaSet.get('_id') == rsName:
            rsList = list(replicaSet['members'])
            for idx,member in enumerate(rsList):
                if member.get('_id') == rsMemberId:
                    modifiedCount += 1
                    print str(member.get('_id')) + " --> " +  str(idx)
                    rsList.pop(idx)
            replicaSet['members'] = rsList

    print str(rsList)

    if modifiedCount >= 2:
        print processName

        configStr = json.dumps(new_config, indent=4)
        print(configStr)
        __post_automation_config(new_config)
        wait_for_goal_state()
    else:
        print "WARNING No matching host(s) %s found in automation config" % (args.hostPort)
        sys.exit(1)


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
actionsParser.add_argument("--removeReplicaMember",dest='action', action='store_const'
        ,const=removeReplicaMember
        ,help='Remove member from existing replica set')
actionsParser.add_argument("--addReplicaMember",dest='action', action='store_const'
        ,const=addReplicaMember
        ,help='Add member to existing replica set')


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
optionsParser.add_argument("--hostPort"
        ,help='host:port of the replica member to remove'
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




