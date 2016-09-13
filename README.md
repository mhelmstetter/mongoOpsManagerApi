# mongoOpsManagerApi
MongoDB Ops Manager API examples

Installation
------------
Download the python file(s) from github. The easiest way to install is with `curl`:

```
curl -OL https://raw.githubusercontent.com/mhelmstetter/mongoOpsManagerApi/master/opsManagerApi.py
```

Usage
------
```
python opsManagerApi.py [-h] --host HOST --group GROUP --username USERNAME
                        --apiKey APIKEY [--disableAlertConfigs]
                        [--enableAlertConfigs] [--alertHostname ALERTHOSTNAME]
                        [--printAlertConfigs]
```

                      
Examples
---------
Disable alerts for host `host1.mydomain.com`:
```
python opsManagerApi.py \
    --host http://opsmanager.mydomain.com:8080 \
    --group 57d13b4be4b0b2a48ed49999 \
    --apiKey 11111111-7777-8888-9999-0000005e3db4 \
    --username user@mydomain.com \
    --disableAlertConfigs \
    --alertHostname host1.mydomain.com
```

Enable alerts for host `host1.mydomain.com`:
```
python opsManagerApi.py \
    --host http://opsmanager.mydomain.com:8080 \
    --group 57d13b4be4b0b2a48ed49999 \
    --apiKey 11111111-7777-8888-9999-0000005e3db4 \
    --username user@mydomain.com \
    --enableAlertConfigs \
    --alertHostname host1.mydomain.com
```

Delete all alerts in group
'''
python opsManagerApi.py \
    --host http://opsmanager.mydomain.com:8080 \
    --group 57d13b4be4b0b2a48ed49999 \
    --apiKey 11111111-7777-8888-9999-0000005e3db4 \
    --username user@mydomain.com \
    --deleteAlertConfigs
```

