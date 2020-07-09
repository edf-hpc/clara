from configparser import ConfigParser
from clara.plugins.clara_ipmi import (do_connect, getmac, do_ping, do_ssh)
import clara.plugins.clara_ipmi as clara_ipmi
from subprocess import Popen, PIPE
from tests.common import fakeconfig
import os


class FakeTask:

    def set_info(self, *opts):
        pass

    def shell(self, comand, nodes=None):
        pass

    def resume(self):
        return True

    def iter_buffers(self):
        return [('ok', 'host1'), ('ok', 'host2')]


def fake_task():
    return FakeTask()


def fake_popen(cmd = None, stdout=None, stderr=None, universal_newlines=None):
    if "-e!" in cmd:
        return Popen('echo \"Chassis Power is on\"',
                     stdout=PIPE, shell=True, universal_newlines=True)

    fake_ipmi_cmd = 'python3 {}/data/bin/impi'.format(os.path.dirname(__file__))

    return Popen(fake_ipmi_cmd, stdout=PIPE, shell=True, universal_newlines=True)


def test_do_coonect(mocker):
    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    mocker.patch("clara.plugins.clara_ipmi.do_connect_ipmi")
    m_logging = mocker.patch("clara.plugins.clara_build.logging.debug")

    do_connect('host1')

    m_logging.assert_called_with('Conman not running. Message on connect: Errno -2 - Name or service not known')


def test_do_coonect(mocker):
    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    mocker.patch("clara.plugins.clara_ipmi.do_connect_ipmi")
    mocker.patch("clara.plugins.clara_ipmi.socket")
    mocker.patch("clara.plugins.clara_build.logging.warning")
    m_run = mocker.patch("clara.plugins.clara_ipmi.run")

    do_connect('host1')

    m_run.assert_called_with(['conman', '-d', u'atadmin1', 'host1'], exit_on_error=False)


def test_do_coonect(mocker):
    mocker.patch("clara.plugins.clara_ipmi.do_connect_ipmi")
    m_logging = mocker.patch("clara.plugins.clara_ipmi.logging.debug")

    do_connect('192.168.1.2')

    m_logging.assert_called_with('The host is an IP adddres: 192.168.1.2. Using ipmitool without conman.')


def test_getmac(mocker):
    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    mocker.patch("clara.plugins.clara_ipmi.value_from_file", side_effect=lambda f, k: 'password')
    mocker.patch("clara.plugins.clara_ipmi.subprocess.Popen", side_effect=fake_popen)
    m_logging = mocker.patch("clara.plugins.clara_ipmi.logging.info")

    getmac('host1')

    m_logging.assert_called_with("  eth0's MAC address is 12:34:56:78:90:12\n  eth1's MAC address is 34:56:78:9A:B:")


def test_ipmido_status(mocker, capsys):
    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    mocker.patch("clara.plugins.clara_ipmi.value_from_file", side_effect=lambda f, k: 'password')
    mocker.patch("clara.plugins.clara_ipmi.subprocess.Popen", side_effect=fake_popen)

    clara_ipmi._opts['parallel'] = 2
    clara_ipmi.ipmi_do('host[1-2]', "power", "status")

    captured = capsys.readouterr()
    assert "immhost1 OK" in captured.out
    assert "immhost2 OK" in captured.out


def test_doping(mocker):
    m_run = mocker.patch("clara.plugins.clara_ipmi.run")

    do_ping('host[1-2]')

    m_run.assert_called_with(["fping", "-r1", "-u", "-s", 'host1', 'host2'])


def test_dossh(mocker):
    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    mocker.patch("clara.plugins.clara_ipmi.value_from_file", side_effect=lambda f, k: 'password')
    mocker.patch("clara.plugins.clara_ipmi.ClusterShell.Task.task_self",side_effect=fake_task)

    do_ssh('host[1-2]', 'date')