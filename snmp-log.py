#!/bin/python3.9

###############################
#   LAST EDIT 28.08.2024      #
#   Version 1.0      #
###############################
import os
import yaml
import json
import sys
from os.path import abspath
from subprocess import check_output as cmd
from subprocess import DEVNULL


###############################
#   READ CONFIG / CREDENTIALS
###############################
# get config location
try:
    config_location = sys.argv[1]
except IndexError:
    config_location = "/opt/splunkforwarder/etc/apps/TA_socc_snmp/bin/snmp-info.yaml"



# load config
try:
    config = yaml.safe_load(open(abspath(config_location), "r"))
except:
    print("Error parsing configuration")
    exit(1)

def get_creds(config):
    '''
        stores the credentials in the config, if the config has a credentials file defined.
        if passed the root of the config file, will apply credentials to all groups as well.
    '''
    try:
        creds_lines = open(abspath(config["credentials_file"]), "r").read().splitlines()
        for line in creds_lines:
            if 'password' in line.lower():
                config["password"] = line.replace(" ", "").split("=")[-1]
            
            if 'privkey' in line.lower():
                config["privkey"] = line.replace(" ", "").split("=")[-1]

            if 'user' in line.lower():
                config["user"] = line.replace(" ", "").split("=")[-1]

        # if config contains categories, if key "oids" is present, config is category itself
        if "oids" not in config:
            for group in config:
                config[group]["password"] = config["password"]
                config[group]["privkey"] = config["privkey"]
                config[group]["user"] = config["user"]
                
    except:
        pass

    return config


###############################
#   SNMP ACTIONS
###############################
def snmp_run(config, ip: str):
    '''
        get and return all info for a specific device
    '''
    snmp_device = _snmp_for_device(config, ip)
    snmp_device["ports"] = _snmp_for_ports(config, ip)
    return snmp_device


def snmp_get(config, oid: str, target: str):
    '''
        get info for oid from target, returns {'err':'err'} if snmp failed
    '''
    try:
        walk = [
            'snmpwalk', '-v3', 
            '-a', 'SHA', 
            '-A', config["password"], 
            '-x', 'AES', 
            '-X', config["privkey"],
            '-u', config["user"], 
            '-l', 'authPriv', 
            target, 
            oid
        ]
        # get snmp response and split by line
        stdout = cmd(walk, universal_newlines=True, stderr=DEVNULL).split('\n')
    except:
        return { 'err': 'err' }

    snmp = {}
    for line in stdout:
        # extract key/value pairs from snmp response
        sline = line.split(".")[-1].replace(" ", "")
        key = sline.split("=")[0]
        value = sline.split(":")[-1]
        
        # remove empty pairs and store all else
        if key:
            snmp[key] = value
    
    return snmp


def _snmp_for_device(config, ip: str):
    '''
        get all defined oids of config group "oids/device" for a specific device
    '''
    snmp = {}
    try:
        for name,oid in config["oids"]["device"].items():
            # get info
            snmp_info = snmp_get(config, oid, ip)

            # this oid for nexus devices contains a lot of irrelevant data
            if oid == "1.3.6.1.4.1.9.9.91.1.1.1.1.4":
                # the last 5 are: Center, Fan-side, Port-side, Die-1, Control-1
                snmp_info = dict(list(snmp_info.items())[-5:])

            # if info is single key/value pair, remove the nesting
            if len(snmp_info) == 1:
                (key, value), = snmp_info.items()
                snmp_info = value
            
            # store info
            snmp[name] = snmp_info
    except:
        print("Error parsing OIDs for device")
        exit(2)

    return snmp


def _snmp_for_ports(config, ip: str):
    '''
        get all defined oids of config group "oids/ports" for a specific device
    '''
    snmp = {}
    try:
        # get info for all logical and physical ports
        for name,oid in config["oids"]["ports"].items():
            snmp_info = snmp_get(config, oid, ip)

            for port_num,port_info in snmp_info.items():
                # remove number from state, otherwise one of: up(1) down(2) testing(3)
                if "state" in name:
                    port_info = port_info[:-3]
                    
                try:
                    snmp[port_num][name] = port_info
                except:
                    snmp[port_num] = {}
                    snmp[port_num][name] = port_info
        
        # remove logical ports by removing all that is not "ethernet"
        for num,info in snmp.copy().items():
            if "ethernet" not in info["name"].lower():
                del snmp[num]
    except:
        print("Error parsing OIDs for ports")
        exit(2)

    return snmp


###############################
#   DEVICE TYPES
###############################
def switch(config):
    '''
        does all the snmp magic for switches.
        tested for catalyst and nexus.
    '''
    # ignore groups without targets
    if config["targets"]:
        for target,address in config["targets"].items():
            snmp = {}
            snmp["target"] = target
            snmp.update(snmp_run(config, address))

            return snmp

def good_luck(config):
    '''
        could not test for anything other than switches, good luck
    '''
    switch(config)


###############################
#   EXECUTION
###############################
def log(device_return):
    if device_return:
        print(json.dumps(device_return))
    

if __name__ == "__main__":
    # set global creds for every group
    config = get_creds(config)

    for group in config:
        # set group-local creds if available
        config[group] = get_creds(config[group])

        if "switch" in group:
            log(switch(config[group]))

        if "router" in group:
            log(good_luck(config[group]))

        if "firewall" in group:
            log(good_luck(config[group]))

        if "storage" in group:
            log(good_luck(config[group]))

        if "genuscreen" in group:
            log(good_luck(config[group]))
