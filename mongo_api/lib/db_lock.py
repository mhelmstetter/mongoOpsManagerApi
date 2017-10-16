import fcntl
import errno
import time
import pymongo
import datetime
import logging

class DbLock:

    def __init__(self, mongo_uri, maximum_wait=120):
        self.client = pymongo.MongoClient(mongo_uri)
        db = self.client["admin"]
        ping = db.command("ping")
        self.db = self.client["opsManagerLock"]
        self.maximum_wait = maximum_wait

    def unlock(self):
        self.db.opsManagerLock.remove({'_id': 'lock'})

    def lock(self):
        waited = 0
        while True:
            try:
                result = self.db.opsManagerLock.insert({'_id': 'lock', "date": datetime.datetime.utcnow()})
                logging.info("lock acquired")
                return True
            except pymongo.errors.DuplicateKeyError as e:
                logging.info("waiting for lock")
                time.sleep(5)
                waited += 5
                if waited >= self.maximum_wait:
                    return False