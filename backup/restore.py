import requests
import logging
import pprint
from requests.auth import HTTPDigestAuth
import json
import argparse
import sys
import copy
import time

logging.basicConfig(
    level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)

def get(url):
    logging.debug("Executing GET: %s" % url)
    r = requests.get(url, auth=HTTPDigestAuth(args.username,args.apiKey))
    check_response(r)
    logging.debug("%s" % pprint.pformat(r.json()))
    return r.json()

def post(url, json_body):
    logging.debug("Executing POST: %s" % url)
    headers = {'content-type': 'application/json'}
    r = requests.post(
        url,
        auth=HTTPDigestAuth(args.username, args.apiKey),
        data=json.dumps(json_body),
        headers=headers
    )
    check_response(r)
    logging.debug("%s" % pprint.pformat(r.json()))
    return r.json()

def put(url, json_body):
    logging.debug("Executing PUT: %s" % url)
    headers = {'content-type': 'application/json'}
    r = requests.put(
        url,
        auth=HTTPDigestAuth(args.username, args.apiKey),
        data=json.dumps(json_body),
        headers=headers
    )
    check_response(r)
    logging.debug("%s" % pprint.pformat(r.json()))
    return r.json()

def check_response(r):
    if r.status_code not in [requests.codes.ok, 202]:
        logging.error("Response Error Code: %s Detail: %s" % (r.status_code, r.json()['detail']))
        raise ValueError(r.json()['detail'])

def getAutomationConfig(group_id):
    automationConfigEndpoint = args.host +"/api/public/v1.0/groups/" + group_id +"/automationConfig"
    return get(automationConfigEndpoint)

def __post_automation_config(group_id, automation_config):
    automationConfigEndpoint = args.host +"/api/public/v1.0/groups/" + group_id +"/automationConfig"
    return put(automationConfigEndpoint, automation_config)

def get_automation_status(group_id):
    url = "%s/api/public/v1.0/groups/%s/automationStatus" % (args.host, group_id)
    return get(url)

def printAutomationConfig(group_id):
    config = getAutomationConfig(group_id)
    configStr = json.dumps(config, indent=4)
    print(configStr)

def get_snapshots_replica_set(replica_set_name):
    cluster_id = _get_cluster_id_from_replica_set(replica_set_name)
    return _get_snapshots(cluster_id)

#def get_snapshots_cluster(cluster_name):
#    cluster_id = _get_cluster_id_from_cluster_name(cluster_name)
#    return _get_snapshots(cluster_id)

def _get_snapshots(group_id, cluster_id):
    url = "%s/api/public/v1.0/groups/%s/clusters/%s/snapshots" % (args.host, group_id, cluster_id)
    response = get(url)
    return response['results']

def _get_cluster_id_from_replica_set(group_id, cluster_name):
    url = "%s/api/public/v1.0/groups/%s/clusters" % (args.host, group_id)
    response = get(url)
    #print(response)
    for cluster in response['results']:
        #print cluster
        if cluster.get('replicaSetName', {}) == cluster_name:
            return cluster['id']
        elif cluster['clusterName'] == cluster_name and cluster['typeName'] == 'SHARDED_REPLICA_SET':
            return cluster['id']

    return None

def get_replica_set_from_cluster_id(group_id, cluster_id):
    url = "%s/api/public/v1.0/groups/%s/clusters" % (args.host, group_id)
    response = get(url)

    for cluster in response['results']:
        if cluster['id'] == cluster_id and cluster.get('replicaSetName'):
            return cluster['replicaSetName']

    return None

def _get_restore_job_result(group_id, cluster_id, job_id=None, batch_id=None):
    url = "%s/api/public/v1.0/groups/%s/clusters/%s/restoreJobs" % (args.host, group_id, cluster_id)

    if job_id:
        url = "%s/%s" % (url, job_id)

    if batch_id:
        url = "%s?batchId=%s" % (url, batch_id)

    #print "_get_restore_job_result: " + url
    response = get(url)
    return response

def _request_restore(group_id, cluster_id, snapshot_id, max_downloads, expiration_hours):
    url = "%s/api/public/v1.0/groups/%s/clusters/%s/restoreJobs" % (args.host, group_id, cluster_id)

    json_body = {
        'snapshotId': snapshot_id,
        'delivery': {
            'methodName': 'HTTP',
            'maxDownloads': max_downloads,
            'expirationHours': expiration_hours
        }
    }

    return post(url, json_body)

def request_restore_http_replica_set(group_id, cluster_id, snapshot_id, max_downloads, expiration_hours):
    return _request_restore(group_id, cluster_id, snapshot_id, max_downloads, expiration_hours)

def printSnapshots():
    cluster_id = _get_cluster_id_from_replica_set(args.group, args.clusterName)
    print "cluster_id " + cluster_id
    url = "%s/api/public/v1.0/groups/%s/clusters/%s/snapshots" % (args.host, args.group, cluster_id)
    response = get(url)
    print("Snapshot                  Date")
    print("------------------------  ---------------")
    for snapshot in response['results']:
        print "%s  %s" % (snapshot['id'], snapshot['created']['date'])

def get_cluster_info(group_id, cluster_name):
    cluster_info = {}
    sets = []
    csrs = None
    url = "%s/api/public/v1.0/groups/%s/clusters" % (args.host, group_id)
    response = get(url)
    for cluster in response['results']:
        if cluster['clusterName'] == cluster_name and cluster['typeName'] == 'REPLICA_SET':
            sets.append(cluster['replicaSetName'])
        elif cluster['clusterName'] == cluster_name and cluster['typeName'] == 'CONFIG_SERVER_REPLICA_SET':
            csrs = cluster['replicaSetName']
    cluster_info['sets'] = sets
    cluster_info['configRsName'] = csrs
    return cluster_info


def restore():

    cluster_id = _get_cluster_id_from_replica_set(args.group, args.clusterName)
    logging.info("cluster_id " + cluster_id)

    source_cluster_info =  get_cluster_info(args.group, args.clusterName)


    print(source_cluster_info)


    snapshot_id = args.snapshotId
    restore_job_response = request_restore_http_replica_set(args.group, cluster_id, snapshot_id, 6, 1)

    restore_job = restore_job_response['results'][0]

    batch_id = restore_job['batchId']
    batch_count = restore_job_response['totalCount']
    logging.debug("batchId " + batch_id)
    restore_links = {}


    while True:
        restore_job_statuses = _get_restore_job_result(args.group, cluster_id, batch_id=batch_id)

        # And then wait for the deliveryUrls to be complete for both components
        for restore_job_status in restore_job_statuses['results']:
            delivery_status = restore_job_status['delivery']['statusName']
            restore_cluster_id = restore_job_status['clusterId']
            #print "cluster_id " + restore_cluster_id + " status " + delivery_status
            if delivery_status == 'READY':
                restore_link = restore_job_status['delivery']['url']
                restore_rs_name = get_replica_set_from_cluster_id(args.group, restore_cluster_id)
                #cluster_id = restore_job_status['clusterId']

                # Keep a dictionary of the restore links for each component in the cluster
                # Identify the component by it's replica set id
                restore_links[restore_rs_name] = restore_link

        if len(restore_links) == batch_count:
            logging.info("Restore jobs ready")
            break

        sys.stdout.write('.')
        time.sleep(1)

    gid = None
    if (args.destGroup):
        gid = args.destGroup
        dest_cluster_info =  get_cluster_info(args.destGroup, args.destCluster)
        print(dest_cluster_info)
    else:
        gid = args.group

    config = getAutomationConfig(gid)
    automation_config = copy.deepcopy(config)

    for process in automation_config['processes']:
        if process['processType'] == 'mongod':
            rName = process['args2_6']['replication']['replSetName']
            mappedName = None
            if rName in dest_cluster_info['sets']:
                i = dest_cluster_info['sets'].index(rName)
                mappedName = source_cluster_info['sets'][i]
                print(rName + " -> " + mappedName)
            elif rName == dest_cluster_info['configRsName']:
                mappedName = source_cluster_info['configRsName']
                print(rName + " -> " + mappedName)
            else:
                print "**** rName" + rName + " not found"
            link = restore_links[mappedName]
            process['backupRestoreUrl'] = link

    logging.info("Initializing restore")
    __post_automation_config(gid, automation_config)
    logging.info("Waiting for goal state")
    wait_for_goal_state(gid)

    config = getAutomationConfig(gid)
    automation_config = copy.deepcopy(config)

    logging.info("Cleaning up")
    for process in automation_config['processes']:
        if process['processType'] == 'mongod':
            process.pop('backupRestoreUrl', None)

    __post_automation_config(gid, automation_config)
    wait_for_goal_state(gid)

    logging.info("Done")



def wait_for_goal_state(group_id):

    count = 0
    while True:
        continue_to_wait = False
        status = get_automation_status(group_id)
        goal_version = status['goalVersion']

        for process in status['processes']:
            logging.debug("Round: %s GoalVersion: %s Process: %s (%s) LastVersionAchieved: %s Plan: %s "
                 % (count, goal_version, process['name'], process['hostname'], process['lastGoalVersionAchieved'], process['plan']))

            if process['lastGoalVersionAchieved'] < goal_version:
                continue_to_wait = True

        if continue_to_wait:
            time.sleep(5)
        else:
            logging.info("All processes in Goal State. GoalVersionAchieved: %s" % goal_version)
            break

        count += 1


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
        ,help='the OpsMgr (source) group id'
        ,required=True)
requiredNamed.add_argument("--username"
        ,help='OpsMgr user name'
        ,required=True)
requiredNamed.add_argument("--apiKey"
        ,help='OpsMgr api key for the user'
        ,required=True)
requiredNamed.add_argument("--clusterName"
        ,help='Replica set name OR sharded cluster name'
        ,required=True)

actionsParser = parser.add_argument_group('actions')
actionsParser.add_argument("--restore",dest='action', action='store_const'
        ,const=restore
        ,help='Restore')
actionsParser.add_argument("--printSnapshots",dest='action', action='store_const'
        ,const=printSnapshots
        ,help='Print snapshots')



optionsParser = parser.add_argument_group('options')
optionsParser.add_argument("--snapshotId"
        ,help='Snapshot Id to restore'
        ,required=False)
optionsParser.add_argument("--destGroup"
        ,help='Destination group id (optional, if restoring snapshot to different group)'
        ,required=False)
optionsParser.add_argument("--destCluster"
        ,help='Destination cluster name (optional, if restoring snapshot to different group)'
        ,required=False)




args = parser.parse_args()

if args.action is None:
    parser.parse_args(['-h'])







# based on the argument passed, this will call the "const" function from the parser config
# e.g. --disableAlertConfigs argument will call disableAlerts()
args.action()




