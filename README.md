# mongoOpsManagerApi
MongoDB Ops Manager API examples

Installation
------------


Usage
------
```
opsManagerApi.py [-h] --host HOST --group GROUP --username USERNAME
                        --apiKey APIKEY [--disableAlertConfigs]
                        [--enableAlertConfigs] [--alertHostname ALERTHOSTNAME]
                        [--printAlertConfigs]
```

                      
Examples
---------
1. Disable alerts for host `host1.mydomain.com`:
```
python opsManagerApi.py \
    --host http://opsmanager.mydomain.com:8080 \
    --group 57d13b4be4b0b2a48ed49999 \
    --apiKey 11111111-7777-8888-9999-0000005e3db4 \
    --username mark.helmstetter@mongodb.com \
    --disableAlertConfigs \
    --alertHostname host1.mydomain.com
```

1. Enable alerts for host `host1.mydomain.com`:
```
python opsManagerApi.py \
    --host http://opsmanager.mydomain.com:8080 \
    --group 57d13b4be4b0b2a48ed49999 \
    --apiKey 11111111-7777-8888-9999-0000005e3db4 \
    --username mark.helmstetter@mongodb.com \
    --enableAlertConfigs \
    --alertHostname host1.mydomain.com
```
