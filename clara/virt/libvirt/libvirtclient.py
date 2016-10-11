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

import libvirt
from libvirt import libvirtError


class VirPilotLibVirtClient():
    state_name = {
        libvirt.VIR_DOMAIN_RUNNING:     'RUNNING',
        libvirt.VIR_DOMAIN_BLOCKED:     'BLOCKED',
        libvirt.VIR_DOMAIN_PAUSED:      'PAUSED',
        libvirt.VIR_DOMAIN_SHUTDOWN:    'SHUTDOWN',
        libvirt.VIR_DOMAIN_SHUTOFF:     'SHUTOFF',
        libvirt.VIR_DOMAIN_CRASHED:     'CRASHED',
        libvirt.VIR_DOMAIN_PMSUSPENDED: 'PMSUSPENDED'
    }

    """VirPilot Libvirt client to a particular host.
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
        return VirPilotLibVirtClient.state_name[state]

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
