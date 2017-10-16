from lib.automation_api_base import AutomationApiBase
from lib.db_lock import DbLock
import copy
import logging

class StopStart(AutomationApiBase):

    def __init__(self, base_url, group_id, api_user, api_key, host_port, rs_user, rs_password, lock_mongo_uri):
        AutomationApiBase.__init__(self, base_url, group_id, api_user, api_key)
        self.host_port = host_port
        self.rs_user = rs_user
        self.rs_password = rs_password
        hostPort = host_port.split(':')
        if len(hostPort) != 2:
            print "ERROR Invalid hostPort %s, should be of the form mongohost1.foo.com:27017" % (host_port)
            sys.exit(2)
        self.host = hostPort[0]
        self.port = hostPort[1]
        self.lock = DbLock(mongo_uri=lock_mongo_uri)

    def startStopHost(self, disabledState):
        self.lock.lock()
        config = self.get_automation_config()
        new_config = copy.deepcopy(config)

        modifiedCount = 0
        for item in list(new_config['processes']):
            if item.get('hostname') == self.host and item.get('args2_6', {}).get('net', {}).get('port') == int(self.port):
                modifiedCount += 1
                processName = item.get('name')
                if disabledState:
                    logging.info('Asked to stop process ' + processName)
                    item['disabled'] = disabledState
                else:
                    logging.info('Asked to start process ' + processName)
                    if item.get('disabled'):
                        del item['disabled']

        if modifiedCount > 0:
            self.post_automation_config(new_config)
            self.wait_for_goal_state()
            self.lock.unlock()

        # TODO - improve this logic to handle waiting for the connection
        #        if not disabledState:
        #            waitForSecondary()
        else:
            print "WARNING No matching host(s) %s found in automation config" % (args.hostPort)
            self.lock.unlock()
            sys.exit(1)


    def stopHost(self):
        self.startStopHost(True)


    def startHost(self):
        self.startStopHost(False)

    #
    # Wait for a given member to become either
    # PRIMARY', 'SECONDARY',  or 'ARBITER' before exiting the script
    #
    def waitForSecondary():
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

