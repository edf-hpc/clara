#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#  Copyright (C) 2014-2017 EDF SA                                            #
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
    clara ipmi connect [-jf] <host>
    clara ipmi getmac <hostlist>
    clara ipmi [--p=<level>] deconnect <hostlist>
    clara ipmi [--p=<level>] (on|off|reboot|soft) <hostlist>
    clara ipmi [--p=<level>] status <hostlist>
    clara ipmi [--p=<level>] setpwd <hostlist>
    clara ipmi [--p=<level>] pxe <hostlist>
    clara ipmi [--p=<level>] disk <hostlist>
    clara ipmi [--p=<level>] ping <hostlist>
    clara ipmi [--p=<level>] blink <hostlist>
    clara ipmi [--p=<level>] immdhcp <hostlist>
    clara ipmi [--p=<level>] bios <hostlist>
    clara ipmi [--p=<level>] reset <hostlist>
    clara ipmi [--p=<level>] sellist <hostlist>
    clara ipmi [--p=<level>] selclear <hostlist>
    clara ipmi ssh <hostlist> <command>
    clara ipmi [--p=<level>] command <hostlist> <command>...
    clara ipmi -h | --help
Alternative:
    clara ipmi <host> connect [-jf]
    clara ipmi <hostlist> getmac
    clara ipmi [--p=<level>] <hostlist> deconnect
    clara ipmi [--p=<level>] <hostlist> (on|off|reboot|soft)
    clara ipmi [--p=<level>] <hostlist> status
    clara ipmi [--p=<level>] <hostlist> setpwd
    clara ipmi [--p=<level>] <hostlist> pxe
    clara ipmi [--p=<level>] <hostlist> disk
    clara ipmi [--p=<level>] <hostlist> ping
    clara ipmi [--p=<level>] <hostlist> blink
    clara ipmi [--p=<level>] <hostlist> immdhcp
    clara ipmi [--p=<level>] <hostlist> bios
    clara ipmi [--p=<level>] <hostlist> reset
    clara ipmi [--p=<level>] <hostlist> sellist
    clara ipmi [--p=<level>] <hostlist> selclear
    clara ipmi <hostlist> ssh <command>
    clara ipmi [--p=<level>] <hostlist> command <command>...
"""

import errno
import multiprocessing
import logging
import os
import re
import subprocess
import sys

import ClusterShell
import docopt
from clara.utils import clara_exit, run, get_from_config, get_from_config_or, get_bool_from_config_or, value_from_file, has_config_value


def full_hostname(host):
    prefix = get_from_config("ipmi", "prefix")
    suffix = get_from_config_or("ipmi", "suffix", "")
    return (prefix + host + suffix)


def ipmi_run(cmd):

    ipmi_p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    output = ipmi_p.communicate()[0].strip()
    exit_code = ipmi_p.wait()
    if exit_code:
        return "ERROR: " + output
    else:
        return "OK: " + output


def ipmi_do(hosts, *cmd):

    imm_user = value_from_file(get_from_config("common", "master_passwd_file"), "IMMUSER")
    os.environ["IPMI_PASSWORD"] = value_from_file(get_from_config("common", "master_passwd_file"), "IMMPASSWORD")
    nodeset = ClusterShell.NodeSet.NodeSet(hosts)

    p = multiprocessing.Pool(parallel)
    result_map = {}

    for host in nodeset:

        pat = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        if not pat.match(host):
            host = full_hostname(host)

        ipmitool = ["ipmitool", "-I", "lanplus", "-H", host, "-U", imm_user, "-E", "-e!"]
        ipmitool.extend(cmd)
        logging.debug("ipmi/ipmi_do: {0}".format(" ".join(ipmitool)))
        result_map[host] = p.apply_async(ipmi_run, (ipmitool,))

    p.close()
    p.join()

    for host, result in result_map.items():
        print host, result.get()


def getmac(hosts):
    imm_user = value_from_file(get_from_config("common", "master_passwd_file"), "IMMUSER")
    os.environ["IPMI_PASSWORD"] = value_from_file(get_from_config("common", "master_passwd_file"), "IMMPASSWORD")
    nodeset = ClusterShell.NodeSet.NodeSet(hosts)
    for host in nodeset:

        pat = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        if not pat.match(host):
            host = full_hostname(host)

        logging.info("{0}: ".format(host))
        cmd = ["ipmitool", "-I", "lanplus", "-H", host,
               "-U", imm_user, "-E", "fru", "print", "0"]

        logging.debug("ipmi/getmac: {0}".format(" ".join(cmd)))

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        # The data we want is in line 15
        lines = proc.stdout.readlines()
        if (len(lines) < 14):
            clara_exit("Host {0} can't be reached".format(host))
        full_mac = lines[14].split(":")[1].strip().upper()
        mac_address1 = "{0}:{1}:{2}:{3}:{4}:{5}".format(full_mac[0:2],
                                                        full_mac[2:4],
                                                        full_mac[4:6],
                                                        full_mac[6:8],
                                                        full_mac[8:10],
                                                        full_mac[10:12])

        mac_address2 = "{0}:{1}:{2}:{3}:{4}:{5}".format(full_mac[12:14],
                                                        full_mac[14:16],
                                                        full_mac[16:18],
                                                        full_mac[18:20],
                                                        full_mac[20:22],
                                                        full_mac[22:24])

        logging.info("  eth0's MAC address is {0}\n"
                     "  eth1's MAC address is {1}".format(mac_address1, mac_address2))


def do_connect_ipmi(host):

    imm_user = value_from_file(get_from_config("common", "master_passwd_file"), "USER")
    os.environ["IPMI_PASSWORD"] = value_from_file(get_from_config("common", "master_passwd_file"), "IMMPASSWORD")

    pat = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
    if not pat.match(host):
        host = full_hostname(host)

    ipmitool = ["ipmitool", "-I", "lanplus", "-H", host, "-U", imm_user, "-E", "-e!", "sol", "activate"]
    logging.debug("ipmi/ipmi_do: {0}".format(" ".join(ipmitool)))
    run(ipmitool)


def do_connect(host, j=False, f=False):
    nodeset = ClusterShell.NodeSet.NodeSet(host)
    if (len(nodeset) != 1):
        clara_exit('Only one host allowed for this command')

    pat = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
    if pat.match(host):
        logging.debug("The host is an IP adddres: {0}. Using ipmitool without conman.".format(host))
        do_connect_ipmi(host)
    else:
        conmand = get_from_config_or("ipmi", "conmand", '')
        port = int(get_from_config("ipmi", "port"))
        if (len(conmand) == 0):
            do_connect_ipmi(host)
            return

        cmd = []
        ssh_jhost = get_bool_from_config_or("ipmi", "ssh_jump_host")

        if ssh_jhost:
            cmd += ["ssh", "-t", conmand]
            conmand = "localhost"
        cmd += ["conman"]

        try:
            if j:
                cmd = cmd + ["-j"]
            if f:
                cmd = cmd + ["-f"]
            cmd = cmd + ["-d", conmand, host, "-e!"]
            run(cmd, exit_on_error=False)
        except RuntimeError as e:
            logging.warning("Conman failed, fallback to ipmitool")
            do_connect_ipmi(host)


def do_ping(hosts):
    nodes = ClusterShell.NodeSet.NodeSet(hosts)
    cmd = ["fping", "-r1", "-u", "-s"] + list(nodes)
    run(cmd)


def do_ssh(hosts, command):
    hosts_l = [ full_hostname(host) for host in ClusterShell.NodeSet.NodeSet(hosts) ]
    hosts = ClusterShell.NodeSet.NodeSet('')
    hosts.updaten(hosts_l)

    os.environ["SSHPASS"] = \
        value_from_file(get_from_config("common", "master_passwd_file"),
                        "IMMPASSWORD")
    imm_user = \
        value_from_file(get_from_config("common", "master_passwd_file"),
                        "IMMUSER")

    task = ClusterShell.Task.task_self()
    task.set_info("ssh_user", imm_user)
    task.set_info("ssh_path", "/usr/bin/sshpass -e /usr/bin/ssh")
    task.set_info("ssh_options", "-oBatchMode=no")
    task.shell(command, nodes=hosts.__str__())
    task.resume()

    for buf, nodes in task.iter_buffers():
        print "---\n%s:\n---\n %s" \
              % (ClusterShell.NodeSet.fold(",".join(nodes)),
                 buf)

def main():
    logging.debug(sys.argv)
    dargs = docopt.docopt(__doc__)

    global parallel
    # Use the value provided by the user in the command line
    if dargs['--p'] is not None and dargs['--p'].isdigit():
        parallel = int(dargs['--p'])
    # Read the value from the config file and use 1 if it hasn't been set
    elif has_config_value("ipmi", "parallel"):
        parallel = int(get_from_config("ipmi", "parallel"))
    else:
        logging.debug("parallel hasn't been set in config.ini, using 1 as default")
        parallel = 1

    if dargs['connect']:
        do_connect(dargs['<host>'], dargs['-j'], dargs['-f'])
    elif dargs['deconnect']:
        ipmi_do(dargs['<hostlist>'], "sol", "deactivate")
    elif dargs['status']:
        ipmi_do(dargs['<hostlist>'], "power", "status")
    elif dargs['setpwd']:
        imm_user = value_from_file(get_from_config("common", "master_passwd_file"), "IMMUSER")
        imm_pwd = value_from_file(get_from_config("common", "master_passwd_file"), "IMMPASSWORD")
        ipmi_do(dargs['<hostlist>'], "user", "set", "name", "2", imm_user)
        ipmi_do(dargs['<hostlist>'], "user", "set", "password", "2", imm_pwd)
    elif dargs['getmac']:
        getmac(dargs['<hostlist>'])
    elif dargs['on']:
        ipmi_do(dargs['<hostlist>'], "power", "on")
    elif dargs['off']:
        ipmi_do(dargs['<hostlist>'], "power", "off")
    elif dargs['soft']:
        ipmi_do(dargs['<hostlist>'], "power", "soft")
    elif dargs['reboot']:
        ipmi_do(dargs['<hostlist>'], "chassis", "power", "reset")
    elif dargs['blink']:
        ipmi_do(dargs['<hostlist>'], "chassis", "identify", "1")
    elif dargs['bios']:
        ipmi_do(dargs['<hostlist>'], "chassis", "bootparam", "set", "bootflag", "force_bios")
    elif dargs['immdhcp']:
        ipmi_do(dargs['<hostlist>'], "lan", "set", "1", "ipsrc", "dhcp")
    elif dargs['pxe']:
        ipmi_do(dargs['<hostlist>'], "chassis", "bootdev", "pxe")
    elif dargs['disk']:
        ipmi_do(dargs['<hostlist>'], "chassis", "bootdev", "disk")
    elif dargs['reset']:
        response = raw_input('Do you really want to restart BMC interface? (N/y) ')
        if response in ('Y', 'y'):
            ipmi_do(dargs['<hostlist>'], "mc", "reset", "cold")
    elif dargs['sellist']:
        ipmi_do(dargs['<hostlist>'], "sel", "list")
    elif dargs['selclear']:
        ipmi_do(dargs['<hostlist>'], "sel", "clear")
    elif dargs['ping']:
        do_ping(dargs['<hostlist>'])
    elif dargs['ssh']:
        do_ssh(dargs['<hostlist>'], dargs['<command>'])
    elif dargs['command']:
        ipmi_do(dargs['<hostlist>'], *dargs['<command>'])

if __name__ == '__main__':
    main()
