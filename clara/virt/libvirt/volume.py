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
# This file is part of VirPilot.
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

from VirPilot.Exceptions import VirPilotRuntimeError


class VirPilotVolume():

    """VirPilot Storage Volume
    """
    def __init__(self, conf, name, group, pool):
        self.conf = conf
        self.name = name
        self.group = group
        self.pool = pool
        data = self.pool.parse_volume_name(self.name)
        if data is None:
            raise VirPilotRuntimeError(
                    "Failed to parse the name of the volume " +
                    "'%s' with the pool %s" % (self.name, self.pool.get_name())
            )
        self.vm_name = data['vm_name']
        self.role = data['vol_role']
        self.client = None
        self.capacity_bytes = 0L
        self.allocation_bytes = 0L
        self.path = ""

    def refresh(self):
        clients = self.group.get_clients().values()
        if len(clients) == 0:
            raise VirPilotRuntimeError(
                "Volume discovery needs at least one client in the node group.")
        self.client = clients[0]
        pool_name = self.pool.get_name()
        vol_list = self.client.get_vol_list(pool_name)
        if self.name in vol_list:
            self.state = "PRESENT"
            self.capacity_bytes = self.client.get_vol_capacity_bytes(
                pool_name, self.name)
            self.allocation_bytes = self.client.get_vol_allocation_bytes(
                pool_name, self.name)
            self.path = self.client.get_vol_path(pool_name, self.name)
        else:
            self.state = "MISSING"
            self.capacity_bytes = 0L
            self.allocation_bytes = 0L
            self.path = ""

    def wipe(self):
        result = self.client.vol_wipe(self.pool.get_name(), self.name)
        self.refresh()
        return result

    def get_capacity(self):
        return self.capacity_bytes

    def get_allocation(self):
        return self.allocation_bytes

    def get_name(self):
        return self.name

    def get_vm_name(self):
        return self.vm_name

    def get_role(self):
        return self.role

    def get_state(self):
        return self.state

    def get_path(self):
        return self.path

    def get_pool(self):
        return self.pool
