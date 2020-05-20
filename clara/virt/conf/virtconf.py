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

import configparser
import os
import collections

from clara import utils
from clara.virt.exceptions import VirtConfigurationException

from ClusterShell.NodeSet import NodeSet


class VirtConf(configparser.ConfigParser):

    def __init__(self, filename):

        super(VirtConf, self).__init__()

        self.filename = filename

    def read(self):
        """Check if configuration file exists and then read it. Raises
           VirPilotConfigurationException if configuration file does not exist.
        """

        if not os.path.exists(self.filename):
            raise VirtConfigurationException(
                "file %s does not exist" % (self.filename))

        super(VirtConf, self).read(self.filename)

    def get_template_list(self):
        """Get the list of all template names. Sections [template:XXX]
        """
        template_list = []
        for section in self.sections():
            if section.startswith("template:"):
                template_list.append(section[9:])
        return template_list

    def get_template_default(self):
        """Get the name of the first template where the default attribute
           is true.
        """
        template_list = self.get_template_list()
        for template in template_list:
            section = "template:%s" % template
            if self.getboolean(section, 'default', fallback=False):
                return template

    def get_template_for_vm(self, vm_name):
        template_list = self.get_template_list()
        for template in template_list:
            section = "template:%s" % template
            vm_names = self.get(section, 'vm_names', fallback='')
            if vm_names == '':
                continue
            vm_nodeset = NodeSet(vm_names)
            if vm_name in vm_nodeset:
                return template
        return None

    def get_template_vol_roles(self, template_name):
        section = "template:%s" % template_name
        role_list = self.get(
            section, 'vol_role', fallback='system').split(',')
        roles = {}
        for role_name in role_list:
            roles[role_name] = {}
            roles[role_name]['capacity'] = self.getint(
                section, "vol_roles_%s_capacity" % role_name, fallback=60000000000)
        return roles

    def get_template_vm_params(self, template_name):
        section = "template:%s" % template_name
        params = {
            'memory_kib': self.getint(
                section, "memory_kib", fallback=2097152),
            'core_count': self.getint(
                section, "core_count", fallback=4),
            'serial_tcp_host': self.get(
                section, "serial_tcp_host", fallback="127.0.0.1"),
            'serial_tcp_port': self.get(
                section, "serial_tcp_port", fallback="0"),
            'network_list': self.get(
                section, "networks", fallback="administration").split(",")
        }
        return params

    def get_template_xml_name(self, template_name):
        section = "template:%s" % template_name
        return self.get(section, 'xml', fallback='default.xml')

    def get_vm_list(self):
        """Get the list of all VM names. Sections [vm:XXX]
        """
        vm_list = []
        for section in self.sections():
            if section.startswith("vm:"):
                vm_list.append(section[3:])
        return vm_list

    def get_vm_networks(self, vm_name, network_list):
        section = "vm:%s" % vm_name
        networks = collections.OrderedDict()
        for network_name in network_list:
            networks[network_name] = {
                'mac_address': self.get(
                    section, 'net_%s_mac' % network_name, fallback="")
            }
        return networks

    def get_vm_params(self, vm_name):
        section = "vm:%s" % vm_name
        params = {}
        value = self.getint(section, "memory_kib", fallback=None)
        if value is not None:
            params['memory_kib'] = value
        value = self.getint(section, "core_count", fallback=None)
        if value is not None:
            params['core_count'] = value
        value = self.get(section, "serial_tcp_host", fallback='0')
        if value is not None:
            params['serial_tcp_host'] = value
        value = self.get(section, "serial_tcp_port", fallback='0')
        if value is not None:
            params['serial_tcp_port'] = value
        value = self.get(section, "networks", fallback=None)
        if value is not None:
            params['network_list'] = value.split(',')
        return params

    def get_nodegroup_list(self):
        """Get the list of all node groups names. Sections [nodegroup:XXX]
        """
        group_list = []
        for section in self.sections():
            if section.startswith("nodegroup:"):
                group_list.append(section[10:])
        return group_list


    def get_nodegroup_default(self):
        """Get the name of the first nodegroup where the default attribute
           is true.
        """
        group_list = self.get_nodegroup_list()
        for group in group_list:
            section = "nodegroup:%s" % group
            if self.get(section, 'default', fallback=False):
                return group

    def get_nodegroup_host_list(self, group_name):
        """Get list of all hostnames for a nodegroup.
        """
        section = "nodegroup:%s" % group_name
        folded_list = self.get(section, 'nodes', fallback='').split(',')
        expanded_list = []
        for folded_element in folded_list:
            nodeset = NodeSet(folded_element)
            for node in nodeset:
                if node not in expanded_list:
                    expanded_list.append(node)
        return expanded_list

    def get_pool_list(self):
        """Get the list of all pool names. Sections [pool:XXX]
        """
        pool_list = []
        for section in self.sections():
            if section.startswith("pool:"):
                pool_list.append(section[5:])
        return pool_list

    def get_pool_default(self):
        """Get the name of the first pool where the default attribute
           is true.
        """
        pool_list = self.get_pool_list()
        for pool in pool_list:
            section = "pool:%s" % pool
            if self.getboolean(section, 'default', fallback=False):
                return pool

    def get_pool_vol_pattern(self, pool_name):
        """Get the volume pattern for the pool
        """
        section = "pool:%s" % pool_name
        return self.get(
            section, 'vol_pattern', fallback='\%(vm_name)s_\%(vol_role)%')
