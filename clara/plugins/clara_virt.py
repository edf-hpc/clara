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
    clara virt list [--details] [--legacy] [--color] [--host=<host>] [--virt-config=<path>]
    clara virt define <vm_names> --host=<host> [--template=<template_name>] [--virt-config=<path>]
    clara virt undefine <vm_names> [--host=<host>] [--virt-config=<path>]
    clara virt start <vm_names> [--host=<host>] [--wipe] [--virt-config=<path>]
    clara virt stop <vm_names> [--host=<host>] [--hard] [--virt-config=<path>]
    clara virt migrate [<vm_names>] [--dest-host=<dest_host>] [--host=<host>] [--virt-config=<path>] [--dry-run] [--quiet] [--yes-i-really-really-mean-it] [--exclude=<exclude>] [--include=<include>]
    clara virt getmacs <vm_names> [--template=<template_name>] [--virt-config=<path>]
    clara virt -h | --help | help

Options:
    <vm_names>                     List of VM names (ClusterShell nodeset)
    <host>                         Physical host where the action should be applied
    --details                      Display details (hosts and volumes)
    --legacy                       Old School printing
    --color                        Colorize or not output
    --wipe                         Wipe the content of the storage volume before starting
    --hard                         Perform a hard shutdown
    --dest-host=<dest_host>        Destination host of a migration
    --template=<template_name>     Use this template instead of the in config
    --virt-config=<path>           Path of the virt config file [default: /etc/clara/virt.ini]
    --quiet                        Proceed silencely. Don't ask any question!
    --dry-run                      Just simulate migrate action! Don't really do anything
    --yes-i-really-really-mean-it  Force migrate action execution without any further validation
    --exclude=<exclude>            Exclude pattern in VMs [default: service]
    --include=<include>            Include pattern in VMs

"""

import logging
import docopt
import sys
import os.path
import ClusterShell
import re
import json
from clara import utils

try:
    import operator
    from prettytable import PrettyTable as prettytable
except:
    print("[WARN] PLS raise 'pip install prettytable' or install 'python3-prettytable' package!")
    pass


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

from clara.utils import Colorizer, yes_or_no, do_print

logger = logging.getLogger(__name__)

def do_list(conf, details=False, legacy=False, host_name=None, color=False):
    # Define print format
    if details:
        vm_line = "VM:{:16} State:{:12} Host:{:16} Total:{:4} Cpus:{:3}"
    else:
        vm_line = "VM:{:16} State:{:12} Host:{:16}"
    host_line = "    Host:{:16} HostState:{:16}"
    vol_line = "    Volume:{:32} Pool:{:16} Capacity:{:12}"

    group = NodeGroup(conf)
    vms = group.get_vms()

    if details:
        # Retrieve KVM server host memory et CPUs information
        memory, cpus = group.get_nodeinfo()
    else:
        memory = cpus = {}

    if legacy:
        table = vm_line
    else:
        try:
            table = prettytable()
            data = ['Fake', 'Host', 'VM', 'State']
            if details:
                data += ['memory', 'cpus']
            if details:
                data += ['Volume', 'Pool', 'Capacity']
            if not legacy:
                table.field_names = data
        except:
            table = vm_line

    # simple antiaffinity rule base on VM node role, following bellow scheme:
    # vm_name = <prefix (any 2 caracters)><role><arbitrar integer digits>
    # antiaffinity stand for a VM placement relative of carateristics or labels like role
    pattern = re.compile(r"[a-z]{2}([a-z0-9]*[a-z]+)\d+")
    antiaffinity = {}
    vmname = {}
    vmstate = {}
    hoststates = {}
    vmrole = {}
    vmhost = {}
    vm_free = {}
    vm_usage = {}
    done = {}
    max_mem = {}
    vcpus = {}
    total_mem = {}
    total_cpu = {}

    # Go through all VMs a first time to retrieve needfull informations like antiaffinity
    for vm in vms.values():
        host_states = vm.get_host_state()
        vm_name = vm.get_name()
        vm_state = vm.get_state()
        if len(host_states) == 1:
            host = list(host_states.keys())[0]
        elif legacy:
            host = ''
        else:
            host = '__empty__'

        vmhost[vm] = host

        hoststates[vm] = host_states
        vmname[vm] = vm_name
        vmstate[vm] = vm_state

        if vm_state == 'RUNNING':
            #If VM is UP and RUNNING, we retrieve his memory & CPU usage
            _, max_mem[vm], _, vcpus[vm], _ = vm.get_info()
            max_mem[vm] = int(max_mem[vm] / 1024 / 1024)
            total_mem[host] = total_mem[host] + max_mem[vm] if host in total_mem else max_mem[vm]
            total_cpu[host] = total_cpu[host] + vcpus[vm] if host in total_cpu else vcpus[vm]

        # if host is RUNNING, try to figure out if it's up on same KVM
        # server host than another VM with same role! Same role stand
        # of VM with the same <prefix> whitch is arbitrary the first 2
        # digits
        if len(host) > 1 and not host == '__empty__':
            if host not in antiaffinity:
                antiaffinity[host] = {}
            match = pattern.search(vm_name);
            if match and vm_state == 'RUNNING':
                role = match.group(1)
                if role != 'service':
                   vmrole[vm] = role
                   if role in antiaffinity[host]:
                       antiaffinity[host][role] += 1
                   else:
                       antiaffinity[host][role] = 1

    # Go again one more time through all VMs, but using previously retrieved data!
    # So we avoid doing job two times!
    for vm in vms.values():
        # Retrieve previously collected VM data
        host_states = hoststates[vm]
        host = vmhost[vm]
        vm_name = vmname[vm]
        vm_state = vmstate[vm]

        _max_mem = _vcpus = ''

        # Add some colorization, if --color is used!
        if vm_state == 'MISSING':
            vm_state = Colorizer.red(vm_state, color=color)
        elif vm_state == 'SHUTOFF':
            vm_state = Colorizer.blue(vm_state, color=color)

        if vm in vmrole and host in antiaffinity and role in antiaffinity[host]:
            role = vmrole[vm]
            if antiaffinity[host][role] > 1:
                 vm_name = Colorizer.red(vm_name, color=color)

        vm_info = []
        if details:
            if vm_state == 'RUNNING':
                #If VM is UP and RUNNING, we retrieve his memory & CPU usage
                _max_mem = max_mem[vm]
                _vcpus = vcpus[vm]
                vm_info = [_max_mem, _vcpus]
            else:
                #Can't figure out a way to retieve simply not RUNNING VM information
                vm_info = ['', '']

        # Use somle tricks here to print KVM server host just one time
        # For slim printing!
        if host in done:
            _host = '__empty__'
        else:
            _memory = _cpu_usage = _cpus = ''
            _host = host
            if host in total_mem and host in memory and host in cpus and host in total_cpu:
                # total KVM server host memory
                _host_mem = int(memory[host] / 1024)
                _memory = "%s/%s" % (total_mem[host], _host_mem)
                # number of CPUs of KVM server host
                _cpus = cpus[host]
                # KVM server host CPUs usage
                _cpu_usage = "%s/%s" % (total_cpu[host], _cpus)
                if total_cpu[host] > _cpus:
                    _host = Colorizer.red(host, color=color)
                    _cpu_usage = Colorizer.red(_cpu_usage, color=color)

                if total_mem[host] > _host_mem:
                    _host = Colorizer.red(host, color=color)
                    _memory = Colorizer.red(_memory, color=color)

            if not legacy:
                done[host] = 0
                data = [host, _host, '', '']
                if details:
                    data += [ _memory, _cpu_usage, '', '', '']
                if host != '':
                    do_print(table, data, legacy)

        data = []
        if legacy:
            table = vm_line

        if host_name:
            if host_name == host:
                if legacy:
                    data = [vm_name, vm_state, host]
                    if details:
                        data += vm_info
                else:
                    data = [host, '', vm_name, vm_state ] + vm_info
        else:
            if legacy:
                data = [vm_name, vm_state, host]
                if details:
                    data += vm_info
            else:
                data = [host, '', vm_name, vm_state] + vm_info

        if details:
            if host_name:
                for host, state in host_states.items():
                    if host_name == host:
                        if legacy:
                            table += "\n  Hosts:\n%s\n  Volumes:" % host_line
                            data += [host, state]
            else:
                if legacy:
                    table += "\n  Hosts:\n"
                for host, state in host_states.items():
                    if legacy:
                        table += "%s\n  Volumes:" % host_line
                        data += [host, state]

            count = 1
            if legacy:
                table += vol_line
            if host_name:
                for vol in vm.get_volumes():
                    vol_name = vol.get_name()
                    if vol_name == vmname[vm] + "_system" and host_name == host:
                        data += [vol_name, vol.get_pool().get_name(), vol.get_capacity()]
                        count = 0
            else:
                for vol in vm.get_volumes():
                    vol_name = vol.get_name()
                    if vol_name == vmname[vm] + "_system":
                        data += [vol_name, vol.get_pool().get_name(), vol.get_capacity()]
                        count = 0
            if count and len(data):
                data += ['', '', '']

        if len(data):
            do_print(table, data, legacy)

    try:
        if table._get_rows({'oldsortslice': False,'start': 0, 'end': 1, 'sortby': False}):
            table.align["VM"] = "l"
            table.align["Host"] = "r"

            table_txt = ''
            match_line = 0
            empty_cell = False
            pattern = re.compile(r"service|__empty__")
            # simulate here some tricks not yet supported by prettytable used version!
            for number, line in enumerate(table.get_string(sort_key=operator.itemgetter(0, 1), sortby = "Fake", fields = table.field_names[1:]).split('\n')):
                if number == 0:
                    horizontal = line
                elif number == 1:
                    header = line.replace('Host', '    ')
                # retrieve second cell content
                cell = ''.join([l for n, l in enumerate(line.split('|')) if n == 1])
                # New service node info start here!
                # before writing service node, insert horizontal line!
                if pattern.search(cell) and empty_cell:
                    empty_cell = False
                    if host_name:
                        if re.search(host_name, cell):
                            line = line.replace('__empty__', '         ')
                            table_txt = '%s%s\n' % (table_txt, horizontal)
                    else:
                        table_txt = '%s%s\n' % (table_txt, horizontal)
                # writing here service node line
                if pattern.search(cell):
                    if not re.search('__empty__', line):
                        if host_name:
                            if re.search(host_name, cell):
                                table_txt = '%s%s\n' % (table_txt, line)
                        else:
                            table_txt = '%s%s\n' % (table_txt, line)
                else:
                    table_txt = '%s%s\n' % (table_txt, line)
                if pattern.search(cell):
                    # Now, we are after service node line,
                    # so we insert separate horizontal line!
                    empty_cell = False
                    match_line = number
                    if not re.search('__empty__', line):
                        if host_name:
                            if re.search(host_name, cell):
                                table_txt = '%s%s\n' % (table_txt, horizontal)
                        else:
                            table_txt = '%s%s\n' % (table_txt, horizontal)
                elif re.search(r"^\s+$", cell):
                    # we found here second empty cell! Meaning new service start here!
                    empty_cell = True
            print(table_txt)
    except:
        pass


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

    host = params['host']
    if action == 'migrate':
        # For live migration, we try to automatically figure out
        # involved migrate candidate!
        dry_run = params['dry_run']
        force = params['force']
        # we enforce virtual service node have been migrated!
        exclude = "service|%s" % params['exclude'] if 'exclude' in params else 'service'
        include = params['include'] if 'include' in params else None
        epattern = re.compile(r'%s' % exclude)
        ipattern = re.compile(r'%s' % include)
        if 'vm_names' not in params and params['host']:
            # Use tricks to avoid call twice function vm.get_name()
            # := operator can be use instead to definite local variable
            # in list comprehension, bu that need pypthon 3.8+
            # https://peps.python.org/pep-0572/
            if include:
                params['vm_names'] = [vm_name for vm in group.get_vms().values()
                        for vm_name in [vm.get_name()] if vm_name
                        for host, state in vm.get_host_state().items()
                        if state == 'RUNNING' and host == params['host']
                        and not epattern.search(vm_name) and ipattern.search(vm_name)]
            else:
                params['vm_names'] = [vm_name for vm in group.get_vms().values()
                        for vm_name in [vm.get_name()] if vm_name
                        for host, state in vm.get_host_state().items()
                        if state == 'RUNNING' and host == params['host']
                        and not epattern.search(vm_name)]

            if 'vm_names' in params:
                if params['vm_names'] == []:
                    message = "No involved VM(s) can be computed based on provided information\n"
                    utils.clara_exit(message)
                else:
                    message = "Be aware that as you had not provided involved VM(s),\n"
                    message += "all currently running VM(s) on source host %s will be migrated!\n" % host
                    logger.warn("%s" % message)
        if 'vm_names' not in params:
            utils.clara_exit("Without provided VM to migrate, you need to use --host switch")


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
            quiet = params['quiet']
            if params['dest_host']:
                dest_host = params['dest_host']
            elif isinstance(params['vm_names'], dict):
                dest_host = params['vm_names'][vm_name]
            else:
                dest_host = None
                message = "Migration needs a destination host, but you haven't provided it!\n"
                logger.warn("%s" % message)
                message += "We can choose one automatically for you! Let continue ?\n"
                if force or quiet or dry_run:
                    dest_host = group.elect_dest_host(machine)
                    logger.info("You had chosen automatic election of destination host: %s!\n",
                                 dest_host)
                elif yes_or_no(message):
                    dest_host = group.elect_dest_host(machine)
            if dest_host is None:
                logger.error('Migration needs a destination host. You must provide one!')
                continue
            message = "Migration action will be done right now on VM %s" % vm_name
            if force or (dry_run and quiet):
                machine.migrate(host=host, dest_host=dest_host, dry_run=dry_run)
            elif yes_or_no(message):
                machine.migrate(host=host, dest_host=dest_host, dry_run=dry_run)
            if dry_run:
                message = "no action have been really done as dry run mode is enabled!\n"
                logger.warn("%s" % message)

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
        details = dargs['--details']
        legacy = dargs['--legacy']
        color = dargs['--color']

        if '--host' in dargs.keys():
            host_name = dargs['--host']
        else:
            host_name = None

        do_list(virt_conf, details, legacy, host_name, color)

    else:
        params['force'] = dargs['--yes-i-really-really-mean-it']
        if dargs['<vm_names>']:
            try:
                params['vm_names'] = json.loads(dargs['<vm_names>'])
            except:
                params['vm_names'] = ClusterShell.NodeSet.NodeSet(dargs['<vm_names>'])
            # when VM list had been provided, no default to dry run mode
            # so usage it's as legacy one!
            params['force'] = True
            params['dry_run'] = False
        elif dargs['migrate']:
            # when no VM had been provided, use dry run mode
            params['dry_run'] = False if params['force'] else True
            if params['dry_run']:
                message = "migrate action is in dry run mode by default\n"
                message += "when you had not provided involved VM(s)!\n"
                logger.warn("%s" % message)

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
            params['quiet'] = dargs['--quiet']
            params['dest_host'] = dargs['--dest-host']
            params['exclude'] = dargs['--exclude']
            params['include'] = dargs['--include']
            do_action(virt_conf, params, 'migrate')
        elif dargs['getmacs']:
            params['template'] = dargs['--template']
            do_getmacs(virt_conf, params)


if __name__ == '__main__':
    main()
