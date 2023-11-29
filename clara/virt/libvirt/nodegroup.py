#!/usr/bin/python
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

import logging
logger = logging.getLogger(__name__)

from clara.virt.libvirt.libvirtclient import LibVirtClient
from clara.virt.libvirt.vm import VM
from clara.virt.libvirt.pool import Pool


class NodeGroup:

    """Group of nodes acting as physical hosts for VMs

        Hosts in the group are assumed to share storage pools.
    """
    def __init__(self, conf, group_name=None):
        self.conf = conf
        self.clients = {}
        self.vms = {}
        if group_name is None:
            group_name = self.conf.get_nodegroup_default()
        self.name = group_name
        hosts = self.conf.get_nodegroup_host_list(self.name)
        for host in hosts:
            client = LibVirtClient(self.conf, host)
            if client.test_connection():
                self.clients[host] = client
        self.pools = {}


    def get_nodeinfo(self):
        memory = {}
        cpus = {}
        for client in self.clients.values():
            host = client.hostname
            _, memory[host], cpus[host], _, _, _, _, _ = client.get_nodeinfo()

        return memory, cpus

    def refresh(self):
        pool = self.get_pool()
        # Get defined VMs
        for client in self.clients.values():
            vm_list = client.get_vm_list()
            for vm_name in vm_list:
                if vm_name not in self.vms.keys():
                    self.vms[vm_name] = VM(self.conf, vm_name, self, [pool])
        # Get VMs with only a volume in the default pool
        for volume in pool.get_volumes().values():
            vm_name = volume.get_vm_name()
            if vm_name not in self.vms.keys():
                self.vms[vm_name] = VM(self.conf, vm_name, self, [pool])
        for vm in self.vms.values():
            vm.refresh()

    def get_pool(self, pool_name=None):
        if pool_name is None:
            pool_name = self.conf.get_pool_default()
        if pool_name not in self.pools.keys():
            self.pools[pool_name] = Pool(self.conf, pool_name=pool_name, group=self)
            self.pools[pool_name].refresh()
        return self.pools[pool_name]

    def vm_start(self, vm_name, host=None):
        if host is None:
            host = self.get_vm_host(vm_name)
        if host is not None:
            return self.clients[host].vm_start(vm_name)
        else:
            logger.error("No host found with VM %s", vm_name)
            return False

    def vm_stop(self, vm_name, host=None, hard=False):
        if host is None:
            host = self.get_vm_host(vm_name)
        if host is not None:
            return self.clients[host].vm_stop(vm_name, hard)
        else:
            logger.error("No host found with VM %s", vm_name)
            return False

    def vm_undefine(self, vm_name, host=None):
        if host is None:
            host = self.get_vm_host(vm_name)
        if host is not None:
            return self.clients[host].vm_undefine(vm_name)
        else:
            logger.error("No host found with VM %s", vm_name)
            return False

    def vm_migrate(self, vm_name, dest_host, host=None, dry_run=False):
        if dest_host not in self.clients.keys():
            logger.error("No active connection to destination host %s",
                         dest_host)
            return False
        if host is None:
            host = self.get_vm_host(vm_name)
        if host is not None:
            if dry_run:
                return True
            else:
                status = self.clients[host].vm_migrate(vm_name,
                                                       self.clients[dest_host])
                self.refresh()
            return status
        else:
            logger.error("No host found with VM %s", vm_name)
            return False

    def get_vm_host_list(self, vm_name):
        hosts = []
        for hostname, client in self.clients.items():
            vm_list = client.get_vm_list()
            if vm_name in vm_list:
                hosts.append(hostname)
        return hosts

    def get_vm_state(self, vm_name, host):
        if host is None:
            host = self.get_vm_host(vm_name)
        if host is not None:
            return self.clients[host].get_vm_state(vm_name)
        else:
            return 'MISSING'

    def get_vm_info(self, vm_name, host=None):
        if host is None:
            host = self.get_vm_host(vm_name)
        if host:
            return self.clients[host].get_vm_info(vm_name)
        else:
            return None

    def get_vm_host(self, vm_name):
        hosts = self.get_vm_host_list(vm_name)
        if len(hosts) > 1:
            logger.error(
                "VM '%s' found on multiple hosts (%s), can't choose",
                vm_name, hosts
            )
            return None
        elif len(hosts) == 1:
            return hosts[0]
        else:
            logger.warn("VM '%s' not found", vm_name)
            return None

    def vm_define(self, host_name, xml_desc):
        self.clients[host_name].vm_define(xml_desc)

    def get_vms(self):
        """Return a list of VirPilotVM objects from this node group.
        """
        self.refresh()
        return self.vms

    def get_vm(self, vm_name, create=False):
        """Return a particular VirPilotVM object from this node group.
        """
        self.refresh()
        if create and vm_name not in self.vms.keys():
            self.vms[vm_name] = VM(self.conf, vm_name, self, [self.get_pool()])
            self.vms[vm_name].refresh()

        return self.vms[vm_name]

    def get_clients(self):
        return self.clients

    def elect_dest_host(self, vm):
        try:
            elect = max({host: len(client.get_vm_list())
                    for host, client in self.clients.items()
                    for _host, state in vm.get_host_state().items()
                    if not host == _host and state == 'RUNNING'
                    })
        except:
            elect = None
        return elect
