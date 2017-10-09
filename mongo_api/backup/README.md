# Restore
Restore scripts for Ops Manager / Automation via the Public API



Usage
------
```
usage: restore.py [-h] --host HOST --group GROUP --username USERNAME --apiKey
                  APIKEY --clusterName CLUSTERNAME [--restore]
                  [--printSnapshots] [--printRestoreJobs]
                  [--snapshotId SNAPSHOTID] [--destGroup DESTGROUP]
                  [--destCluster DESTCLUSTER]

Restore

optional arguments:
  -h, --help            show this help message and exit

required arguments:
  --host HOST           the OpsMgr host with protocol and port, e.g.
                        http://server.com:8080
  --group GROUP         the OpsMgr (source) group id
  --username USERNAME   OpsMgr user name
  --apiKey APIKEY       OpsMgr api key for the user
  --clusterName CLUSTERNAME
                        Source Replica set name OR sharded cluster name

actions:
  --restore             Restore
  --printSnapshots      Print snapshots
  --printRestoreJobs    Print restore jobs

options:
  --snapshotId SNAPSHOTID
                        Snapshot Id to restore
  --destGroup DESTGROUP
                        Destination group id (optional, if restoring snapshot
                        to different group)
  --destCluster DESTCLUSTER
                        Destination cluster name (optional, if restoring
                        snapshot to different group)
```


Examples
---------
Import an existing replica set:

```
python restore.py \
    --host http://opsmanager.mydomain.com:8080 \
    --group 57d13b4be4b0b2a48ed49999 \
    --apiKey 11111111-7777-8888-9999-0000005e3db4 \
    --username user@mydomain.com \
    --importReplicaSet \
    --rsName shard0 --rsPort 27017 \
    --rsUser admin --rsPassword admin \
    --rsHost mongo1.foo.com
```



