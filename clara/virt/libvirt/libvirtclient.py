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

import libvirt
from libvirt import libvirtError


class LibVirtClient():
    state_name = {
        libvirt.VIR_DOMAIN_RUNNING:     'RUNNING',
        libvirt.VIR_DOMAIN_BLOCKED:     'BLOCKED',
        libvirt.VIR_DOMAIN_PAUSED:      'PAUSED',
        libvirt.VIR_DOMAIN_SHUTDOWN:    'SHUTDOWN',
        libvirt.VIR_DOMAIN_SHUTOFF:     'SHUTOFF',
        libvirt.VIR_DOMAIN_CRASHED:     'CRASHED',
        libvirt.VIR_DOMAIN_PMSUSPENDED: 'PMSUSPENDED'
    }

    """Libvirt client to a particular host.
    """
    def __init__(self, conf, hostname):
        self.conf = conf
        self.hostname = hostname
        self.conn = None

    def _connect(self):
        if self.conn is None:
            self.conn = libvirt.open("qemu+ssh://%s/system" % self.hostname)

    def _get_domain(self, domain_name):
        self._connect()
        return self.conn.lookupByName(domain_name)

    def _get_storage_pool(self, pool_name):
        self._connect()
        return self.conn.storagePoolLookupByName(pool_name)

    def _get_storage_vol(self, pool_name, vol_name):
        self._connect()
        pool = self._get_storage_pool(pool_name)
        vol = pool.storageVolLookupByName(vol_name)
        return vol

    def test_connection(self):
        try:
            self._connect()
        except libvirtError:
            logger.warn("Failed to connect to %s" % self.hostname)
        if self.conn is None:
            return False
        else:
            return True

    def get_pool_list(self):
        self._connect()
        pool_list = []
        for pool in self.conn.listAllStoragePools():
            pool_list.append(pool.name())
        return pool_list

    def get_vol_list(self, pool_name):
        pool = self._get_storage_pool(pool_name)
        return pool.listVolumes()

    def get_vol_capacity_bytes(self, pool_name, vol_name):
        vol = self._get_storage_vol(pool_name, vol_name)
        info = vol.info()
        return info[1]

    def get_vol_allocation_bytes(self, pool_name, vol_name):
        vol = self._get_storage_vol(pool_name, vol_name)
        info = vol.info()
        return info[2]

    def get_vol_path(self, pool_name, vol_name):
        vol = self._get_storage_vol(pool_name, vol_name)
        return vol.path()

    def vol_wipe(self, pool_name, vol_name):
        # vol.wipe() would be nice if it was supported by ceph pools
        vol = self._get_storage_vol(pool_name, vol_name)
        xml_desc = vol.XMLDesc()
        vol.delete()
        self.vol_create(pool_name, xml_desc)

    def vol_create(self, pool_name, xml_desc):
        pool = self._get_storage_pool(pool_name)
        pool.createXML(xml_desc)

    def get_vm_list(self):
        self._connect()
        vm_list = []
        for domain in self.conn.listAllDomains():
            vm_list.append(domain.name())
        return vm_list

    def get_vm_state(self, vm_name):
        domain = self._get_domain(vm_name)
        state, reason = domain.state()
        return LibVirtClient.state_name[state]

    def vm_stop(self, vm_name, hard=False):
        domain = self._get_domain(vm_name)
        if self.get_vm_state(vm_name) is 'RUNNING':
            if hard:
                logger.warn("Destroying VM '%s'", vm_name)
                success = domain.destroy() == 0
            else:
                logger.warn("Shutting down VM '%s'", vm_name)
                success = domain.shutdown() == 0
            if not success:
                logger.warn("Failed to request shutdown of VM '%s'", vm_name)
            return success
        else:
            logger.warn("VM '%s' is not running, can't shutdown", vm_name)
            return False

    def vm_start(self, vm_name):
        domain = self._get_domain(vm_name)
        if self.get_vm_state(vm_name) is not 'RUNNING':
            success = domain.create() == 0
            if not success:
                logger.warn("Failed to request start of VM '%s'" % vm_name)
            return success
        else:
            logger.warn("VM '%s' is already running, can't start" % vm_name)
            return False

    def vm_define(self, xml_desc):
        self.conn.defineXML(xml_desc)

    def vm_undefine(self, vm_name):
        domain = self._get_domain(vm_name)
        if self.get_vm_state(vm_name) is 'RUNNING':
            logger.warn("VM '%s' is running, can't undefine.", vm_name)
            return False
        domain.undefine()
        return True

    def vm_migrate(self, vm_name, dest_client):
        domain = self._get_domain(vm_name)
        dest_conn = dest_client.conn
        flags = libvirt.VIR_MIGRATE_LIVE + \
                libvirt.VIR_MIGRATE_PERSIST_DEST + \
                libvirt.VIR_MIGRATE_UNDEFINE_SOURCE
        return domain.migrate(dest_conn, flags)
