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
import humanize

from clara.virt.exceptions import VirtRuntimeError

logger = logging.getLogger(__name__)


class Volume:

    """VirPilot Storage Volume
    """
    def __init__(self, conf, name, group, pool):
        self.conf = conf
        self.name = name
        self.group = group
        self.pool = pool
        data = self.pool.parse_volume_name(self.name)
        if data is None:
            raise VirtRuntimeError(
                "Failed to parse the name of the volume " +
                "'%s' with the pool %s", (self.name, self.pool.get_name())
            )
        self.vm_name = data['vm_name']
        self.role = data['vol_role']
        self.client = None
        self.capacity_bytes = 0
        self.allocation_bytes = 0
        self.path = ""

    def refresh(self):
        clients = list(self.group.get_clients().values())
        if len(clients) == 0:
            raise VirtRuntimeError(
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
            self.capacity_bytes = 0
            self.allocation_bytes = 0
            self.path = ""

    def wipe(self):
        result = self.client.vol_wipe(self.pool.get_name(), self.name)
        self.refresh()
        return result

    def get_capacity(self):
        return humanize.naturalsize(self.capacity_bytes)

    def get_allocation(self):
        return humanize.naturalsize(self.allocation_bytes)

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
