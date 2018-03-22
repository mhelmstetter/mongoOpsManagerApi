# Deploy
Deploy scripts for Ops Manager / Automation via the Public API



Usage
------
```
deploy.py [-h] --host HOST --group GROUP --username USERNAME --apiKey
                 APIKEY [--printAutomationConfig] [--addReplicaSet]
                 [--removeReplicaMember] [--addReplicaMember]
                 [--rsName RSNAME] [--rsHosts RSHOSTS]
                 [--rsTemplate RSTEMPLATE] [--hostPort HOSTPORT]
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
  --addReplicaSet       Add new replica set
  --removeReplicaMember
                        Remove member from existing replica set
  --addReplicaMember    Add member to existing replica set

options:
  --rsName RSNAME       Replica Set Name
  --rsHosts RSHOSTS     Comma separated list of replica set hosts
  --rsTemplate RSTEMPLATE
                        Input file containing JSON template for replica set
                        config
  --hostPort HOSTPORT   host:port of the replica member to remove
```

Add Replica Set
---------------
```
python deploy.py --host http://opsmanager.mydomain.com:8080 \
--apiKey fa052147-e81b-488b-8eea-e3881388cd9a --group 5ab18e0b9590dd70a0bb58e7 \
--username user@mydomain.com --rsName rs1 \
--rsHosts host1.mydomain.com,host2.mydomain.com,host3.mydomain.com \
--rsTemplate rsTemplate.json --addReplicaSet
```

Remove Replica Member
---------------------
```
python deploy.py --host http://opsmanager.mydomain.com:8080 \
--apiKey fa052147-e81b-488b-8eea-e3881388cd9a --group 5ab18e0b9590dd70a0bb58e7 \
--username user@mydomain.com --rsName rs1 \
--hostPort host1.mydomain.com:27017 \
--removeReplicaMember 
```

Add Replica Member
------------------
```
python deploy.py --host http://opsmanager.mydomain.com:8080 \
--apiKey fa052147-e81b-488b-8eea-e3881388cd9a --group 5ab18e0b9590dd70a0bb58e7 \
--username user@mydomain.com --rsName rs1 \
--hostPort host1.mydomain.com:27017 \
--rsTemplate rsTemplate.json --addReplicaMember 
```

Stop mongod on Host
-------------------
```
python stopStart.py -host http://opsmanager.mydomain.com:8080 \
--apiKey fa052147-e81b-488b-8eea-e3881388cd9a --group 5ab18e0b9590dd70a0bb58e7 \
--username user@mydomain.com \
--hostPort host1.mydomain.com:27017 \
--stopHost 
```

Start mongod on Host
-------------------
```
python stopStart.py -host http://opsmanager.mydomain.com:8080 \
--apiKey fa052147-e81b-488b-8eea-e3881388cd9a --group 5ab18e0b9590dd70a0bb58e7 \
--username user@mydomain.com \
--hostPort host1.mydomain.com:27017 \
--startHost 
```

