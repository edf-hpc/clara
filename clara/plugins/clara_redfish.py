#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#  Copyright (C) 2023 EDF SA                                                 #
#                                                                            #
#  This file is part of Clara                                                #
#                                                                            #
#  This software is governed by the CeCILL-C license under French law and    #
#  abiding by the rules of distribution of free software. You can use,       #
#  modify and/ or redistribute the software under the terms of the CeCILL-C  #
#  license as circulated by CEA, CNRS and INRIA at the following URL         #
#  "http://www.cecill.info".                                                 #
#                                                                            #
#  As a counterpart to the access to the source code and rights to copy,     #
#  modify and redistribute granted by the license, users are provided only   #
#  with a limited warranty and the software's author, the holder of the      #
#  economic rights, and the successive licensors have only limited           #
#  liability.                                                                #
#                                                                            #
#  In this respect, the user's attention is drawn to the risks associated    #
#  with loading, using, modifying and/or developing or reproducing the       #
#  software by the user in light of its specific status of free software,    #
#  that may mean that it is complicated to manipulate, and that also         #
#  therefore means that it is reserved for developers and experienced        #
#  professionals having in-depth computer knowledge. Users are therefore     #
#  encouraged to load and test the software's suitability as regards their   #
#  requirements in conditions enabling the security of their systems and/or  #
#  data to be ensured and, more generally, to use and operate it in the      #
#  same conditions as regards security.                                      #
#                                                                            #
#  The fact that you are presently reading this means that you have had      #
#  knowledge of the CeCILL-C license and that you accept its terms.          #
#                                                                            #
##############################################################################
"""
Manages and get the status from the nodes of a cluster.

Usage:
    clara redfish getmac <hostlist>
    clara redfish [--p=<level>] ping <hostlist>
    clara redfish [--p=<level>] (on|off|reboot) <hostlist>
    clara redfish [--p=<level>] sellist <hostlist>
    clara redfish [--p=<level>] selclear <hostlist>
    clara redfish [--p=<level>] status <hostlist>
    clara redfish [--p=<level>] pxe <hostlist>
    clara redfish [--p=<level>] dflt <hostlist>
    clara redfish [--p=<level>] bios <hostlist>
    clara redfish [--p=<level>] disk <hostlist>
    clara redfish -h | --help
Alternative:
    clara redfish <hostlist> getmac
    clara redfish [--p=<level>] <hostlist> ping
    clara redfish [--p=<level>] <hostlist> (on|off|reboot)
    clara redfish [--p=<level>] <hostlist> sellist
    clara redfish [--p=<level>] <hostlist> selclear
    clara redfish [--p=<level>] <hostlist> status
    clara redfish [--p=<level>] <hostlist> pxe
    clara redfish [--p=<level>] <hostlist> dflt
    clara redfish [--p=<level>] <hostlist> bios
    clara redfish [--p=<level>] <hostlist> disk
"""

import errno
import multiprocessing
import logging
import os
import re
import subprocess
import sys
from datetime import datetime

import ClusterShell
import docopt
from requests.auth import HTTPBasicAuth

from clara.utils import clara_exit, run, get_from_config, get_from_config_or, get_bool_from_config_or, value_from_file, has_config_value, get_response

# Global dictionary
_opts = {'parallel': 1}

urls = {'powerstatus': '',
        'poweron': '/Actions/ComputerSystem.Reset',
        'poweroff': '/Actions/ComputerSystem.Reset',
        'powerreboot': '/Actions/ComputerSystem.Reset',
        'sellist': '/LogServices/SEL/Entries',
        'selclear': '/LogServices/SEL/Actions/LogService.ClearLog',
        'bootdevpxe': '',
        'bootdevdflt': '',
        'bootdevbios': '',
        'bootdevhdd': '',
       }

def get_authentication():

    imm_user = os.getenv('IMMUSER')
    if not imm_user:
        try:
            imm_user = value_from_file(get_from_config("common", "master_passwd_file"), "IMMUSER")
        except:
            logging.info("Please export IMMUSER and IPMI_PASSWORD")
            sys.exit(1)

    imm_password = os.getenv('IPMI_PASSWORD')
    if not imm_password:
        try:
            imm_password = value_from_file(get_from_config("common", "master_passwd_file"), "IMMPASSWORD")
        except:
            logging.info("Please export IPMI_PASSWORD")
            sys.exit(1)

    return imm_user, imm_password

def full_hostname(host):
    prefix = get_from_config("ipmi", "prefix")
    suffix = get_from_config_or("ipmi", "suffix", "")
    return prefix + host + suffix

def get_topurl(hosts, auth):
    nodeset = ClusterShell.NodeSet.NodeSet(hosts)
    endpoint = ""
    host = nodeset[0]

    pat = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
    if not pat.match(host):
        host = full_hostname(host)

    url = "https://{0}/redfish/v1/Systems".format(host)
    response = get_response(url, endpoint, auth)
    members = [response['Members'] if 'Members' in response else '']
    members = members[0][0]

    return(members['@odata.id'])


def getmac(hosts):

    imm_user, imm_password = get_authentication()
    auth  = HTTPBasicAuth(imm_user, imm_password)

    topurl = get_topurl(hosts, auth)
    endpoint = "/EthernetInterfaces"

    nodeset = ClusterShell.NodeSet.NodeSet(hosts)
    for host in nodeset:

        pat = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        if not pat.match(host):
            host = full_hostname(host)

        url = "https://{0}{1}".format(host, topurl)
        logging.debug(f"{url} {endpoint}")
        logging.info("{0}: ".format(host))
        if "Self" in topurl:
            url = url.replace('Systems','Managers')
            response = get_response(url, endpoint + "/eth0", auth)
            mac_address1 = [response['MACAddress'] if 'MACAddress' in response else '']
            response = get_response(url, endpoint + "/eth1", auth)
            mac_address2 = [response['MACAddress'] if 'MACAddress' in response else '']

            logging.info("  eth0's MAC address is {0}\n"
                         "  eth1's MAC address is {1}".format(mac_address1, mac_address2))
        else:
            response = get_response(url, endpoint, auth)
            nbr = [response['Members@odata.count'] if 'Members@odata.count' in response else 0]
            for n in range(nbr[0]):
                response = get_response(url, endpoint + "/" + str(n + 1), auth)
                mac_address = [response['MACAddress'] if 'MACAddress' in response else '']
                logging.info( "eth" + str(n) + "'s MAC address is {0} ".format(mac_address[0].replace('-',':')))

def do_ping(hosts):
    nodes = ClusterShell.NodeSet.NodeSet(hosts)
    cmd = ["/sbin/fping", "-r1", "-u", "-s"] + list(nodes)
    run(cmd)

def redfish_do(hosts, *cmd):

    imm_user, imm_password = get_authentication()
    auth  = HTTPBasicAuth(imm_user, imm_password)
    headers = {'content-type': 'application/json'}

    topurl = get_topurl(hosts, auth)
    value = ""
    endpoint = ""
    if 'user' in cmd and 'set' in cmd:
        logging.debug(f"{cmd}")
    else:
        for i in range(len(cmd) - 2, len(cmd), 1):
            value = value + cmd[i]
        endpoint = urls[value]

    nodeset = ClusterShell.NodeSet.NodeSet(hosts)
    for host in nodeset:

        pat = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        if not pat.match(host):
            host = full_hostname(host)

        url = "https://{0}{1}".format(host, topurl)

        if value == "powerstatus":
            response = get_response(url, endpoint, auth)
            logging.debug(f"redfish/redfish_do: {url} {endpoint} {response} {response['PowerState']}")
            redfishtool = [response['PowerState'] if 'PowerState' in response else '']
            logging.debug("redfish/redfish_do: {0}".format(" ".join(redfishtool)))
            logging.info(f"{host} OK: Chassis Power is {redfishtool[0]}")
        elif value == "sellist":
            if 'Self' in url:
                endpoint = endpoint.replace('SEL','BIOS')
            response = get_response(url, endpoint, auth, headers)
            logging.info("{0}: ".format(host))
            for mbr in response['Members']:
                fmt = '%Y/%m/%d | %H:%M:%S'
                if 'Self' in url:
                    tab = mbr['Message'].split(',')
                    datecreated = datetime.strptime(mbr['Created'], '%Y-%m-%dT%H:%M:%Sz').astimezone()
                    logging.info(f"{mbr['Id']} | {datecreated.strftime(fmt)} | {mbr['SensorType']} | {tab[9].split(':')[1]} | {mbr['EntryCode']} ")
                else:
                    dtcreated = mbr['Created'].split('+')
                    datecreated = dtcreated[0] + "+" + dtcreated[1].replace(':','')
                    datecreated = datetime.strptime(datecreated, '%Y-%m-%dT%H:%M:%S%z')
                    logging.info(f"{mbr['Id']} | {datecreated.strftime(fmt)} | {mbr['SensorType']} | {mbr['Message']} | {mbr['EntryCode']} ")
        elif value == "selclear":
            if 'Self' in url:
                endpoint = endpoint.replace('SEL', 'BIOS')
            body = {}
            logging.debug(f"redfish/redfish_do: {url} {endpoint} {body}")
            response = get_response(url, endpoint, auth, headers, data=body)
        elif value == "poweron":
            body = {"ResetType" : "On"}
            logging.debug(f"redfish/redfish_do: {url} {endpoint} {body}")
            response = get_response(url, endpoint, auth, headers, data=body)
        elif value == "poweroff":
            body  = {"ResetType" : "ForceOff"}
            logging.debug(f"redfish/redfish_do: {url} {endpoint} {body}")
            response = get_response(url, endpoint, auth, headers, data=body)
        elif value == "powerreboot":
            body  = {"ResetType" : "ForceRestart"}
            response = get_response(url, endpoint, auth, headers, data=body)
        elif value == "bootdevpxe":
            body = {"Boot": { "BootSourceOverrideEnabled": "Continuous", "BootSourceOverrideTarget": "Pxe"}}
            response = get_response(url, endpoint, auth, headers, data=body, method="PATCH")
        elif value == "bootdevdflt":
            body = {"Boot": { "BootSourceOverrideEnabled": "Disabled", "BootSourceOverrideTarget": "None"}}
            response = get_response(url, endpoint, auth, headers, data=body, method="PATCH")
        elif value == "bootdevbios":
            body = {"Boot": { "BootSourceOverrideEnabled": "Continuous", "BootSourceOverrideTarget": "BiosSetup"}}
            response = get_response(url, endpoint, auth, headers, data=body, method="PATCH")
        elif value == "bootdevhdd":
            body = {"Boot": { "BootSourceOverrideEnabled": "Continuous", "BootSourceOverrideTarget": "Hdd"}}
            response = get_response(url, endpoint, auth, headers, data=body, method="PATCH")

def main():
    logging.debug(sys.argv)
    dargs = docopt.docopt(__doc__)

    # Use the value provided by the user in the command line
    if dargs['--p'] is not None and dargs['--p'].isdigit():
        _opts['parallel'] = int(dargs['--p'])
    # Read the value from the config file and use 1 if it hasn't been set
    elif has_config_value("redfish", "parallel"):
        _opts['parallel'] = int(get_from_config("redfish", "parallel"))
    else:
        logging.debug("parallel hasn't been set in config.ini, using 1 as default")

    if dargs['status']:
        redfish_do(dargs['<hostlist>'], "power", "status")
    elif dargs['getmac']:
        getmac(dargs['<hostlist>'])
    elif dargs['sellist']:
        redfish_do(dargs['<hostlist>'], "sel", "list")
    elif dargs['selclear']:
        redfish_do(dargs['<hostlist>'], "sel", "clear")
    elif dargs['ping']:
        do_ping(dargs['<hostlist>'])
    elif dargs['on']:
        redfish_do(dargs['<hostlist>'], "power", "on")
    elif dargs['off']:
        redfish_do(dargs['<hostlist>'], "power", "off")
    elif dargs['reboot']:
        redfish_do(dargs['<hostlist>'], "power", "reboot")
    elif dargs['pxe']:
        redfish_do(dargs['<hostlist>'], "chassis", "bootdev", "pxe")
    elif dargs['dflt']:
        redfish_do(dargs['<hostlist>'], "chassis", "bootdev", "dflt")
    elif dargs['bios']:
        redfish_do(dargs['<hostlist>'], "chassis", "bootdev", "bios")
    elif dargs['disk']:
        redfish_do(dargs['<hostlist>'], "chassis", "bootdev", "disk")

if __name__ == '__main__':
    main()
