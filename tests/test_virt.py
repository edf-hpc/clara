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

    def shutdown(self):
        return 0


class virStorageVol:
    """ Fake class for libvirt.virStorageVol"""
    def info(self):
        return [3, 10000000000, 0]
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

    def createXML(self, xml_desc):
        return True

class virConnect:
    """ Fake class for libvirt.virConnect"""

    pools = [virStoragePool('bb-pool', ['node1_disk']),
             virStoragePool('bb2-pool', ['node2_disk'])]

    def_domains = {'qemu+ssh://hw1/system': [virDomain('node1', [1, 2])],
                   'qemu+ssh://hw2/system': [virDomain('node2', [1, 3])]}

    def __init__(self, host):
        self.domains = self.def_domains[host]
        self.pools = self.pools


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
def nodegroup(mocker, data_dir):
    """it setup mock object for libvirt module and returns
    Nodegroup object
    """
    mocker.patch("clara.virt.libvirt.libvirtclient.libvirt.open",
                 side_effect=virConnect)
    virt_conf = VirtConf(data_dir.virt_conf)
    virt_conf.read()
    return NodeGroup(virt_conf)


def test_load_virtualconf(data_dir):
    virt_conf = VirtConf(data_dir.virt_conf)
    virt_conf.read()


def test_nodegroup_init(nodegroup):
    """It tests NodeGroup object initialisation"""
    # the order is not always guaranteed
    assert sorted(list(nodegroup.clients.keys())) == ['hw1', 'hw2']


def test_nodegroup_vms(nodegroup):
    vms = nodegroup.get_vms()
    vm1 = vms['node1']
    assert vm1.get_host_state() == {'hw1': 'RUNNING'}
    assert vm1.get_name() == "node1"
    assert vm1.get_state() == "RUNNING"
    volumes = vm1.get_volumes()
    assert volumes[0].get_name() == "node1_disk"
    assert volumes[0].get_capacity() == '10.0 GB'


def test_vm_actions(nodegroup):
    """It tests VM actions"""
    vms = nodegroup.get_vms()
    vm1 = list(vms.values())[0]
    assert vm1.wipe() is False
    assert vm1.start() is False
    assert vm1.stop() is True
    assert vm1.undefine() is False
    # this is buggy None is returned
    assert vm1.migrate('host2') not in [True, False]


def test_get_macs(nodegroup):
    """It tests that assigned macs are different"""
    vms = nodegroup.get_vms()
    vm1 = vms['node1']
    vm2 = vms['node2']
    assert vm1.get_macs("") == {'administration': '00:16:3e:c8:96:1f'}
    # different MAC
    assert vm2.get_macs("") != {'administration': '00:16:3e:c8:96:1f'}

def test_create_volume(nodegroup, data_dir):
    vms = nodegroup.get_vms()
    vm1 = list(vms.values())[0]
    vm1.create_volumes("node", data_dir.root)
