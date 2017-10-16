import fcntl
import errno
import time

class FileLock:
    def __init__(self, filename=None):
        self.filename = './MONGODB_AUTOMATION_LOCK_FILE' if filename is None else filename
        self.lock_file = open(self.filename, 'w+')

    def unlock(self):
        fcntl.flock(self.lock_file, fcntl.LOCK_UN)

    def lock(self, maximum_wait=10):
        waited = 0
        while True:
            try:
                fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                print ("file locked")
                return True
            except pymongo.errors.DuplicateKeyError as e:
                if e.errno != errno.EAGAIN:
                    raise e
                else:
                    time.sleep(1)
                    waited += 1
                    if waited >= maximum_wait:
                        return False