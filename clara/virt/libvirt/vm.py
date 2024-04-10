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

import os.path
from jinja2 import Template
import hashlib

class VM():

    """VirPilot Reporter application which generates usage report based on
       database content.
    """
    def __init__(self, conf, name, group, pools):
        self.conf = conf
        self.group = group
        self.pools = pools
        self.name = name
        self.host_state = {}
        self.host_list = []
        self.state = 'UNKNOWN'
        self.volumes = {}

    def generate_mac(self, net_name, salt=''):
        mix_name = "{}{}{}".format(self.name, net_name, salt).encode('utf-8')
        digest = hashlib.sha1(mix_name).hexdigest()[:6]
        mac = ['00', '16', '3e',
               digest[:2],
               digest[2:4],
               digest[4:6]]
        return ':'.join(mac)

    def refresh(self):
        self.host_list = self.group.get_vm_host_list(self.name)
        self.host_state = {}
        for host in self.host_list:
            self.host_state[host] = self.group.get_vm_state(self.name, host)
        if len(self.host_list) == 0:
            self.state = 'MISSING'
        elif len(self.host_list) == 1:
            self.state = self.host_state[self.host_list[0]]
        else:
            self.state = 'INCONSISTENT'
        for pool in self.pools:
            pool_name = pool.get_name()
            pool_volumes = pool.get_volumes_for_vm(self.name)
            if pool_name not in self.volumes.keys():
                self.volumes[pool_name] = {}
            for vol in pool_volumes:
                self.volumes[pool_name][vol.get_name()] = vol

    def start(self, host=None):
        """Start the virtual machine.

            If host is None, let the system choose the right one,
            this will only work if the vm is not in an 'INCONSISTENT'
            state.
        """
        return self.group.vm_start(self.name, host)

    def stop(self, host=None, hard=False):
        """Stop the virtual machine.

            If host is None, let the system choose the right one,
            this will only work if the vm is not in an 'INCONSISTENT'
            state.
        """
        return self.group.vm_stop(self.name, host, hard)

    def undefine(self, host=None):
        """Undefine the virtual machine.

            If host is None, let the system choose the right one,
            this will only work if the vm is not in an 'INCONSISTENT'
            state.
        """
        return self.group.vm_undefine(self.name, host)

    def wipe(self):
        """Wipe the virtual machine.

           Only works if the machine is 'SHUTOFF' or 'MISSING'
        """
        if self.state in ['SHUTOFF', 'MISSING']:
            for vol in self.get_volumes():
                vol.wipe()
            return True
        else:
            logger.warning("Bad state to wipe disks (%s) for VM %s",
                        self.state, self.name)
            return False

    def migrate(self, dest_host, host=None, dry_run=False):
        """Migrate the virtual machine to dest_host
        """
        self.group.vm_migrate(self.name, dest_host, host, dry_run)

    def create_volumes(self, template_name, template_dir):
        vol_roles = self.conf.get_template_vol_roles(template_name)
        pool = self.group.get_pool()
        for vol_role, role_params in vol_roles.items():
            try:
                volume = pool.get_volume(self.name, vol_role)
                vol_exists = True
            except KeyError:
                vol_exists = False

            if vol_exists:
                logger.info("Volume %s for VM %s already exists.",
                            volume.get_name(), self.name)
                continue

            vol_name = pool.get_volume_name(self.name, vol_role)

            template_path = os.path.join(
                template_dir,
                'volume',
                'default.xml'
            )
            template_file = open(template_path)
            template_str = template_file.read()
            template_file.close()

            template = Template(template_str)
            xml_desc = template.render(
                vol_name=vol_name,
                vol_capacity_bytes=role_params['capacity']
            )
            pool.create_volume(xml_desc)
            pool.refresh()
        self.refresh()

    def define(self, template_name, template_dir, host):
        pool = self.group.get_pool()
        pool.refresh()
        vol_roles = self.conf.get_template_vol_roles(template_name)
        if self.state != 'MISSING':
            logger.info("VM %s already exists.", self.name)
            return False
        template_params = self.conf.get_template_vm_params(template_name)
        vm_params = self.conf.get_vm_params(self.name)
        params = template_params.copy()
        params.update(vm_params)
        networks = self.conf.get_vm_networks(self.name, params['network_list'])
        volumes = {}
        for vol_role in vol_roles.keys():
            volumes[vol_role] = {
                'pool_name': pool.get_name(),
                'name': pool.get_volume_name(self.name, vol_role),
                'path': pool.get_volume(self.name, vol_role).get_path(),
            }
        params.update({
            'name': self.name,
            'networks': networks.copy(),
            'volumes': volumes,
        })

        for net_name in networks:
            mac_address = params['networks'][net_name]['mac_address']
            if mac_address == '':
                mac_address = self.generate_mac(net_name)
            params['networks'][net_name]['mac_address'] = mac_address

        template_path = os.path.join(
            template_dir,
            'vm',
            self.conf.get_template_xml_name(template_name)
        )
        template_file = open(template_path)
        template_str = template_file.read()
        template_file.close()

        logger.debug("Generating template with parameters: %s", params)
        template = Template(template_str)
        xml_desc = template.render(params)

        logger.debug("Rendered XML: %s", xml_desc)
        self.group.vm_define(host, xml_desc)


    def get_info(self):
        return self.group.get_vm_info(self.name)

    def get_state(self):
        return self.state

    def get_host_state(self):
        return self.host_state

    def get_name(self):
        return self.name

    def get_volumes(self):
        result = []
        for pool_volumes in self.volumes.values():
            for vol in pool_volumes.values():
                result.append(vol)
        return result

    def get_macs(self, template_name):
        """Returns a dict of network/mac pairs for the VM."""

        macs = {}  # return result dict

        # merge templtate/vm params into params dict
        template_params = self.conf.get_template_vm_params(template_name)
        vm_params = self.conf.get_vm_params(self.name)
        params = template_params.copy()
        params.update(vm_params)
        networks = self.conf.get_vm_networks(self.name, params['network_list'])
        # iterate over the networks
        for net_name in networks:
            mac_address = networks[net_name]['mac_address']
            if mac_address == '':
                mac_address = self.generate_mac(net_name)
            macs[net_name] = mac_address

        return macs
