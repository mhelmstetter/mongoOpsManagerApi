import requests
from requests.auth import HTTPDigestAuth
import json
import argparse
import sys
import copy
import random
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
    "version": "",
    "args2_6": {
    }
}

monitoringUser = {
    "initPwd" : ''.join(random.choice('0123456789abcdef') for n in xrange(30)),
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
    "initPwd": ''.join(random.choice('0123456789abcdef') for n in xrange(30)),
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
            "hostname": ""
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

def importReplicaSet():
    config = getAutomationConfig()
    new_config = copy.deepcopy(config)

    # Somehow we end up with empty roles for monitoring and backup users
    for index, user in enumerate(new_config['auth']['usersWanted']):
        if user['user'] == "mms-monitoring-agent" and not user['roles']:
            user['roles'] = monitoringUser['roles']
        elif user['user'] == "mms-backup-agent" and not user['roles']:
            user['roles'] = backupUser['roles']

    # if the monitoring user does not exist, add it
    if not any(x['user'] == "mms-monitoring-agent" for x in new_config['auth']['usersWanted']):
        print "*** adding monitoring user"
        new_config['auth']['usersWanted'].append(monitoringUser)

    # if the backup user does not exist, add it
    if not any(x['user'] == "mms-backup-agent" for x in new_config['auth']['usersWanted']):
        print "*** adding backup user"
        new_config['auth']['usersWanted'].append(backupUser)

    new_config['auth']['disabled'] = False
    new_config['auth']['authoritativeSet'] = False
    new_config['auth']['autoUser'] = "mms-automation"
    #new_config['auth']['autoPwd'] = ''.join(random.choice('0123456789abcdef') for n in xrange(30))

    new_config['auth']['deploymentAuthMechanisms'] =  ["MONGODB-CR"]

    hosts = args.rsHost.split(",")

    if not new_config['monitoringVersions']:
        print "*** adding monitoring version"
        monitoringVersion['hostname'] = hosts[0]
        new_config['monitoringVersions'].append(monitoringVersion)

    client = MongoClient(host=hosts, port=int(args.rsPort))
    db = client.admin
    db.authenticate(args.rsUser, args.rsPassword)
    conf = db.command("replSetGetConfig").get("config", None)
    cmdLine = db.command("getCmdLineOpts").get("parsed", None)
    params = db.command({"getParameter":"*"})

    keyFile = cmdLine['security']['keyFile']

    new_config['auth']['keyfile'] = keyFile
    #new_config['auth']['key'] = args.rsKey

    with open(keyFile, 'r') as myfile:
        data = myfile.read().replace('\n', '')
        new_config['auth']['key'] = data

    #
    if not any(x['user'] == args.rsUser for x in new_config['auth']['usersWanted']):
        admin = db.system.users.find_one({"user":args.rsUser})
        #print(admin)
        creds = admin['credentials']['SCRAM-SHA-1']
        del admin['credentials']
        del admin['_id']
        admin['scramSha1Creds'] = creds
        new_config['auth']['usersWanted'].append(admin)


    if not any(x['_id'] == args.rsName for x in new_config['replicaSets']):
        process_id = 0;
        rsConfig = copy.deepcopy(conf)
        del rsConfig['settings']
        del rsConfig['version']
        del rsConfig['protocolVersion']
        for member in rsConfig['members']:
            print(member)
            hostPort = member['host'].split(':')
            host = hostPort[0]
            port = hostPort[1]

            client = MongoClient(host=host, port=int(port))
            db = client.admin
            if not member['arbiterOnly']:
                db.authenticate(args.rsUser, args.rsPassword)
                cmdLine = db.command("getCmdLineOpts").get("parsed", None)
                buildInfo = db.command("buildinfo")

            del member['tags']
            del member['buildIndexes']
            process = copy.deepcopy(processTemplate)
            process['hostname'] = host


            if params.get("featureCompatibilityVersion"):
                process['featureCompatibilityVersion'] = params.get("featureCompatibilityVersion")

            if "enterprise" in buildInfo['modules']:
                process['version'] = buildInfo['version'] + '-ent'
            else:
                process['version'] = buildInfo['version']

            process['name'] = args.rsName + "_" + str(process_id)

            process['args2_6'] = cmdLine
            #replSet = cmdLine['replication']['replSet']
            replSet = rsConfig['_id']
            if process.get('args2_6').get('replication').get('replSet'):
                del process['args2_6']['replication']['replSet']
            process['args2_6']['replication']['replSetName'] = replSet


            new_config['processes'].append(process)
            rsConfig['members'][process_id]['_id'] = process_id
            rsConfig['members'][process_id]['host'] = args.rsName + "_" + str(process_id)
            process_id += 1

        #print(rsConfig)
        new_config['replicaSets'].append(rsConfig)

    #configStr = json.dumps(new_config, indent=4)
    #print(configStr)

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

args = parser.parse_args()

if args.action is None:
    parser.parse_args(['-h'])

alertConfigsEndpoint = args.host +"/api/public/v1.0/groups/" + args.group +"/alertConfigs"
hostsEndpoint = args.host +"/api/public/v1.0/groups/" + args.group +"/hosts"
automationConfigEndpoint = args.host +"/api/public/v1.0/groups/" + args.group +"/automationConfig"

# based on the argument passed, this will call the "const" function from the parser config
# e.g. --disableAlertConfigs argument will call disableAlerts()
args.action()




