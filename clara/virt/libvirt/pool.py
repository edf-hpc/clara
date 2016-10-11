#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2016 EDF SA
# Contact:
#       CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#       1, Avenue du General de Gaulle
#       92140 Clamart
#
# Authors: CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#
# This file is part of clara.
#
# VirPilot is free software: you can redistribute in and/or
# modify it under the terms of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with VirPilot. If not, see
# <http://www.gnu.org/licenses/>.
#
# On Calibre systems, the complete text of the GNU General
# Public License can be found in `/usr/share/common-licenses/GPL'.

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
