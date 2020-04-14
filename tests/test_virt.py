from clara.virt.libvirt.nodegroup import NodeGroup
from clara.virt.conf.virtconf import VirtConf
import pytest

class virDomain:
    """ Fake class for libvirt.VirDomain"""
    def __init__(self, name, state):
        self._name = name
        self._state = state

    def name(self):
        return self._name

    def state(self):
        return self._state


class virStorageVol:
    """ Fake class for libvirt.virStorageVol"""
    def info(self):
        return [3, 10000000000L, 0L]
    def path(self):
        return "/some_path"


class virStoragePool:
    """ Fake class for libvirt.virStoragePool"""
    def __init__(self, name, volumes):
        self._name = name
        self.volumes = volumes

    def name(self):
        return self._name

    def listVolumes(self):
        return self.volumes

    def storageVolLookupByName(self, name):
        return virStorageVol()


class virConnect:
    """ Fake class for libvirt.virConnect"""

    pools = [virStoragePool('bb-pool', ['node1_disk']), virStoragePool('bb2-pool', ['node2_disk'])]
    def_domains = {'qemu+ssh://hw1/system': [virDomain('node1', [1, 2])],
               'qemu+ssh://hw2/system': [virDomain('node2', [1, 3])]}

    def __init__(self, host):
        self.domains = self.def_domains[host]
        self.pools = pools

    def listAllStoragePools(self):
        return self.pools

    def storagePoolLookupByName(self, name):
        for pool in self.pools:
            if pool.name() == name:
                return pool

    def listAllDomains(self):
        return self.domains

    def lookupByName(self, name):
        return self.domains[0]

@pytest.fixture
def nodegroup(mocker):
    mocker.patch("clara.virt.libvirt.libvirtclient.libvirt.open",
                 side_effect=virConnect)
    virt_conf = VirtConf('data/virt.ini')
    virt_conf.read()
    return NodeGroup(virt_conf)

def test_load_virtualconf():
    virt_conf = VirtConf('data/virt.ini')
    virt_conf.read()


def test_nodegroup_init(mocker, nodegroup):
    print(nodegroup.clients)
    assert nodegroup.clients.keys() == ['hw2', 'hw1']

def test_nodegroup_vms(mocker, nodegroup):
    vms = nodegroup.get_vms()
    vm1 = vms.values()[0]
    assert vm1.get_host_state() == {'hw1': 'RUNNING'}
