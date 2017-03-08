# Import
Import existing MongoDB clusters into Ops Manager for Automation via the Public API



Usage
------
```
usage: import.py [-h] --host HOST --group GROUP --username USERNAME --apiKey
                 APIKEY [--printAutomationConfig] [--importReplicaSet]
                 [--rsName RSNAME] [--rsHosts RSHOSTS] [--rsPort RSPORT]
                 [--rsUser RSUSER] [--rsPassword RSPASSWORD] [--rsKey RSKEY]
```

Arguments
---------
```
optional arguments:
  -h, --help            show this help message and exit

required arguments:
  --host HOST           the OpsMgr host with protocol and port, e.g.
                        http://server.com:8080
  --group GROUP         the OpsMgr group id
  --username USERNAME   OpsMgr user name
  --apiKey APIKEY       OpsMgr api key for the user

actions:
  --printAutomationConfig
                        Get Automation Config
  --importReplicaSet    Import an existing replica set

options:
  --rsName RSNAME       Replica Set Name
  --rsHost RSHOST       Hostname of one replica member used as the import
                        "seed"
  --rsPort RSPORT       MongoDB port number
  --rsUser RSUSER       MongoDB username to connect to replica set
  --rsPassword RSPASSWORD
                        MongoDB password to connect to replica set
``


Note that this script must be run from a host that has the replica set keyFile
in the same location as the replica member. This can be done by running this script
directly from one of the replica members.

Examples
---------
Import an existing replica set:
```
python import.py \
    --host http://opsmanager.mydomain.com:8080 \
    --group 57d13b4be4b0b2a48ed49999 \
    --apiKey 11111111-7777-8888-9999-0000005e3db4 \
    --username user@mydomain.com \
    --importReplicaSet \
    --rsName shard0 --rsPort 27017 \
    --rsUser admin --rsPassword admin \
    --rsHosts mongo1.foo.com
```

