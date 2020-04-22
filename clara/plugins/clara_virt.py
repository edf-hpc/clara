#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#  Copyright (C) 2016 EDF SA                                                 #
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
Manages VMs used in a cluster.

Usage:
    clara virt list [--details] [--host=<host>] [--virt-config=<path>]
    clara virt define <vm_names> --host=<host> [--template=<template_name>] [--virt-config=<path>]
    clara virt undefine <vm_names> [--host=<host>] [--virt-config=<path>]
    clara virt start <vm_names> [--host=<host>] [--wipe] [--virt-config=<path>]
    clara virt stop <vm_names> [--host=<host>] [--hard] [--virt-config=<path>]
    clara virt migrate <vm_names> --dest-host=<dest_host> [--host=<host>] [--virt-config=<path>]
    clara virt getmacs <vm_names> [--template=<template_name>] [--virt-config=<path>]
    clara virt -h | --help | help

Options:
    <vm_names>                  List of VM names (ClusterShell nodeset)
    <host>                      Physical host where the action should be applied
    --details                   Display details (hosts and volumes)
    --wipe                      Wipe the content of the storage volume before starting
    --hard                      Perform a hard shutdown
    --dest-host=<dest_host>     Destination host of a migration
    --template=<template_name>  Use this template instead of the in config
    --virt-config=<path>        Path of the virt config file [default: /etc/clara/virt.ini]

"""

import logging
import docopt
import sys
import os.path
import ClusterShell
from clara import utils

# Version 10.2.9 is Debian Jessie
# earlier versions might work but are not tested.
# Debian Squeeze is not OK though
try:
    import libvirt
except ImportError:
    utils.clara_exit("LibVirt Missing, needs version >= 10.2.9.")

libvirt_version = libvirt.getVersion()
if libvirt_version < 1002009:
    utils.clara_exit("LibVirt too old (%d.%d.%d), needs version >= 10.2.9." % (
        libvirt_version / 1000000,
        (libvirt_version % 1000000) / 1000,
        libvirt_version % 1000
    ))

from clara.virt.conf.virtconf import VirtConf
from clara.virt.libvirt.nodegroup import NodeGroup
from clara.virt.exceptions import VirtConfigurationException

logger = logging.getLogger(__name__)


def do_list(conf, show_hosts=False, show_volumes=False, host_name=None):
    vm_line = "VM:{0:16} State:{1:12} Host:{2:16}"
    host_line = "    Host:{0:16} HostState:{1:16}"
    vol_line = "    Volume:{0:32} Pool:{1:16} Capacity:{2:12}"
    group = NodeGroup(conf)
    vms = group.get_vms()
    for vm in vms.values():
        host_states = vm.get_host_state()
        if len(host_states) == 1:
            host = list(host_states.keys())[0]
        else:
            host = ''
        vm_name = vm.get_name()
        if host_name:
            if host_name == host:
                print(vm_line.format(vm_name, vm.get_state(), host))
        else:
            print(vm_line.format(vm_name, vm.get_state(), host))
        if show_hosts:            
            if host_name:
                for host, state in host_states.items():
                    if host_name == host:
                        print("Host:")
                        print(host_line.format(host, state))
                        print("  Volumes:")
            else:
                print("  Hosts:")
                for host, state in host_states.items():
                    print(host_line.format(host, state))
                    print("  Volumes:")
        if show_volumes:
            if host_name:
                for vol in vm.get_volumes():
                    if vol.get_name() == vm_name+"_system" and host_name==host:
                        print(vol_line.format(
                            vol.get_name(),
                            vol.get_pool().get_name(),
                            vol.get_capacity()
                        ))


def do_action(conf, params, action):
    group = NodeGroup(conf)
    if 'wipe' in params.keys():
        wipe = params['wipe']
    else:
        wipe = False
    if 'hard' in params.keys():
        hard = params['hard']
    else:
        hard = False
    if 'dest_host' in params.keys():
        dest_host = params['dest_host']
    else:
        dest_host = None
    host = params['host']

    for vm_name in params['vm_names']:
        logging.info("Action: %s on %s.", action, vm_name)
        machine = group.get_vm(vm_name)
        if action == 'start':
            if wipe:
                success = machine.wipe()
                if not success:
                    logger.error("Wipe failed, not starting %s", vm_name)
                    continue
            machine.start(host)
        elif action == 'stop':
            machine.stop(host, hard)
        elif action == 'undefine':
            machine.undefine(host)
        elif action == 'migrate':
            if dest_host is None:
                logger.error('Migration needs a destination host.')
                continue
            machine.migrate(host=host, dest_host=dest_host)
        else:
            logging.error("Action %s not supported.", action)
            exit(1)


def do_define(conf, params):
    group = NodeGroup(conf)
    vm_names = params['vm_names']
    template_dir = params['template_dir']
    host = params['host']
    template_name = params['template']
    for vm_name in vm_names:
        if host is None:
            logger.error("Need a physical host to define a VM.")
            continue
        config_template = conf.get_template_for_vm(vm_name)
        if template_name is None:
            if config_template is not None:
                template_name = config_template
            else:
                template_name = conf.get_template_default()

        machine = group.get_vm(vm_name, create=True)

        machine.create_volumes(template_name, template_dir)
        machine.define(template_name, template_dir, host)


def do_getmacs(conf, params):
    group = NodeGroup(conf)
    vm_names = params['vm_names']
    template_name = params['template']
    for vm_name in vm_names:
        config_template = conf.get_template_for_vm(vm_name)
        if template_name is None:
            if config_template is not None:
                template_name = config_template
            else:
                template_name = conf.get_template_default()

        machine = group.get_vm(vm_name, create=True)
        print("%s:" % vm_name)
        for net, mac in machine.get_macs(template_name).items():
            print("  %s: %s" % (net, mac))


def main():
    logging.debug(sys.argv)
    dargs = docopt.docopt(__doc__)
    virt_conf = VirtConf(dargs['--virt-config'])
    config_dir = os.path.dirname(dargs['--virt-config'])
    template_dir = os.path.join(config_dir, 'templates')

    try:
        virt_conf.read()
    except VirtConfigurationException as err:
        utils.clara_exit("Configuration Error: %s" % err)

    params = {
        'config_dir': config_dir,
        'template_dir': template_dir,
    }

    if dargs['list']:
        show_hosts = dargs['--details']
        show_volumes = dargs['--details']
        
        if '--host' in dargs.keys():
            host_name = dargs['--host']
        else:
            host_name = None

        do_list(virt_conf, show_hosts, show_volumes, host_name)

    else:
        params['vm_names'] = ClusterShell.NodeSet.NodeSet(dargs['<vm_names>'])

        if '--host' in dargs.keys():
            params['host'] = dargs['--host']
        else:
            params['host'] = None

        if dargs['define']:
            params['template'] = dargs['--template']
            do_define(virt_conf, params)
        elif dargs['undefine']:
            do_action(virt_conf, params, 'undefine')
        elif dargs['start']:
            params['wipe'] = dargs['--wipe']
            do_action(virt_conf, params, 'start')
        elif dargs['stop']:
            params['hard'] = dargs['--hard']
            do_action(virt_conf, params, 'stop')
        elif dargs['migrate']:
            params['dest_host'] = dargs['--dest-host']
            do_action(virt_conf, params, 'migrate')
        elif dargs['getmacs']:
            params['template'] = dargs['--template']
            do_getmacs(virt_conf, params)


if __name__ == '__main__':
    main()
