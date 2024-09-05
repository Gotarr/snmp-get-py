#   TUTORIAL
to run the script: ./snmp-log.py
the default config path of "snmp-info.yaml" in current working directory will be assumed

to run the script with custom config path: ./snmp-log.py /path/to/file
the path can be relative or absolute

currently only switches (cisco catalyst and nexus) are supported

#   EXIT CODES
1 -> could not read config file
2 -> config file structure not as expected

#   CONFIG FILE
the expected config file structure is as follows
'''
router-group:
    oids:
        device:
            cpu: 1.3.6.1.4.1.9.2.1.56

        ports:
            name: 1.3.6.1.2.1.2.2.1.2

    targets:
        HOSTNAME: i.p.v.4

switch-group:
    oids:
        device:
            cpu: 1.3.6.1.4.1.9.2.1.56
            temp: 1.3.6.1.4.1.9.9.13.1.3.1.3
            mem_free: 1.3.6.1.4.1.9.2.1.8

        ports:
            name: 1.3.6.1.2.1.2.2.1.2
            in: 1.3.6.1.2.1.2.2.1.10
            out: 1.3.6.1.2.1.2.2.1.16

    targets:
        HOSTNAME: i.p.v.4
        HOSTNAME: i.p.v.4
    
    credentials_file: creds-switch

credentials_file: creds-generic
'''
oids can be added and/or removed where other oids already are
the label that is assigned to the oid will be used in the output

group "oids/device" will be run first and contains "per device" info
group "oids/ports" will be run after and contains "per port" info

order of OIDs is respected

#   CREDENTIALS FILE
you can have either one credential file for all categories or
one credential file each
credentials file at location specified in config file has to contain
'''
password = abcdefgh1234
privkey = ijklmn5678
user = myuser
'''
spaces are ignored so your creds should not contain them

each group can have its own credentials
if a group does not have its own credentials, the global credentials file is used

in the example in section "CONFIG FILE" the category "router-group" will use the credentials 
in "creds-generic" and those in category "switch-group" "creds-switch"