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

import re

from clara.virt.exceptions import VirtRuntimeError
from clara.virt.libvirt.volume import Volume


class Pool():
    """Virt Storage Pool
    """
    def __init__(self, conf, group, pool_name=None):
        self.conf = conf
        if pool_name is None:
            pool_name = self.conf.get_pool_default()
        self.name = pool_name
        self.group = group
        self.volumes = {}
        self.vol_pattern = self.conf.get_pool_vol_pattern(self.name)
        re_pattern = self.vol_pattern.format(
            vm_name='(?P<vm_name>[a-zA-Z0-9_]+)',
            vol_role='(?P<vol_role>[a-zA-Z0-9_]+)'
        )
        logger.debug("Volume Regexp: '%s'", re_pattern)
        self.vol_re = re.compile(re_pattern)
        self.client = None

    def refresh(self):
        clients = self.group.get_clients().values()
        if len(clients) == 0:
            raise VirtRuntimeError(
                "Pool discovery needs at least one client in the node group.")
        self.client = clients[0]
        pool_list = self.client.get_pool_list()
        if self.name not in pool_list:
            raise VirtRuntimeError(
                "Can't find pool %s in pool list (%s)" % (self.name, pool_list))
        vol_list = self.client.get_vol_list(self.name)
        for vol_name in vol_list:
            vol_info = self.parse_volume_name(vol_name)
            if vol_info is None:
                logger.debug("%s does not match rules for pool %s",
                             vol_name, self.name)
                continue
            if vol_name not in self.volumes.keys():
                self.volumes[vol_name] = Volume(
                    self.conf, vol_name, self.group, self)
        for volume in self.volumes.values():
            volume.refresh()

    def parse_volume_name(self, volume_name):
        match = self.vol_re.match(volume_name)
        if match is not None:
            volume_info = {
                'vol_name': volume_name,
                'vm_name':  match.group('vm_name'),
                'vol_role': match.group('vol_role'),
            }
            return volume_info
        else:
            return None

    def get_volume_name(self, vm_name, vol_role):
        return self.vol_pattern.format(vm_name=vm_name, vol_role=vol_role)

    def get_name(self):
        return self.name

    def get_volumes(self):
        return self.volumes

    def get_volumes_for_vm(self, vm_name):
        result = []
        for volume in self.volumes.values():
            if volume.get_vm_name() == vm_name:
                result.append(volume)
        return result

    def get_volume(self, vm_name, vol_role):
        name = self.get_volume_name(vm_name, vol_role)
        return self.volumes[name]

    def create_volume(self, xml_desc):
        self.client.vol_create(self.name, xml_desc)
