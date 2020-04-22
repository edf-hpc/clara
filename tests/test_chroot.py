from configparser import ConfigParser
import tempfile
import os
from clara.plugins.clara_chroot import (base_install, mount_chroot,
                                        umount_chroot, system_install, install_files)
from tests.common import fakeconfig


def test_base_install(mocker):
    test_dir = tempfile.mkdtemp()
    # Creating fake directories
    os.makedirs(os.path.join(test_dir, "usr/sbin"))
    os.makedirs(os.path.join(test_dir, "etc/apt"))
    os.mkdir(os.path.join(test_dir, "etc/apt/preferences.d/"))
    os.mkdir(os.path.join(test_dir, "etc/apt/apt.conf.d/"))
    os.makedirs(os.path.join(test_dir, "etc/dpkg/dpkg.cfg.d/"))

    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    m_run = mocker.patch("clara.plugins.clara_chroot.run")
    mocker.patch("clara.plugins.clara_chroot.subprocess.Popen")

    base_install(test_dir, 'calibre9', os.path.join(test_dir, 'etc/apt/sources.list'))
    # we assert the existance of created files
    file_permisions = os.stat(os.path.join(test_dir, 'usr/sbin/policy-rc.d'))
    assert os.path.isfile(os.path.join(test_dir, "etc/apt/preferences.d/00custompreferences"))
    assert os.path.isfile(os.path.join(test_dir, "usr/sbin/policy-rc.d"))
    assert os.path.isfile(os.path.join(test_dir, "etc/apt/apt.conf.d/99nocheckvalid"))
    assert os.path.isfile(os.path.join(test_dir, "etc/dpkg/dpkg.cfg.d/excludes"))
    assert file_permisions.st_mode == 33261
    m_run.assert_called_with(['debootstrap', u'--keyring=/usr/share/keyrings/scibian-archive-keyring.gpg',
                              u'jessie', test_dir, u'http://debian/debian/'])


def test_mount_chroot(mocker):
    m_run = mocker.patch("clara.plugins.clara_chroot.run")
    work_dir = "/test"

    mount_chroot(work_dir, 'calibre9')

    m_run.assert_any_call(["chroot", work_dir, "mount", "-t", "proc", "none", "/proc"])
    m_run.assert_any_call(["chroot", work_dir, "mount", "-t", "sysfs", "none", "/sys"])


def test_umount_chroot(mocker):
    mocker.patch("clara.plugins.clara_chroot.os.path.ismount")
    m_run = mocker.patch("clara.plugins.clara_chroot.run")
    work_dir = "/test"

    umount_chroot(work_dir, 'calibre9')

    m_run.assert_any_call(["chroot", work_dir, "umount", "/proc/sys/fs/binfmt_misc"])
    m_run.assert_any_call(["chroot", work_dir, "umount", "/sys"])
    m_run.assert_any_call(["chroot", work_dir, "umount", "/proc"])


def test_system_install(mocker):
    mocker.patch("clara.plugins.clara_chroot.mount_chroot")
    mocker.patch("clara.plugins.clara_chroot.umount_chroot")
    m_crun = mocker.patch("clara.plugins.clara_chroot.run_chroot")
    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    work_dir = "/test"

    system_install(work_dir, 'calibre9')

    m_crun.assert_any_call(["chroot", work_dir, "apt-get", "update"])
    m_crun.assert_any_call(["chroot", work_dir, "apt-get", "clean"])


def test_system_install(mocker):
    mocker.patch("clara.plugins.clara_chroot.os.remove")
    mocker.patch("clara.plugins.clara_chroot.mount_chroot")
    mocker.patch("clara.plugins.clara_chroot.umount_chroot")
    m_crun = mocker.patch("clara.plugins.clara_chroot.run_chroot")
    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)

    work_dir = "/test"

    install_files(work_dir, 'calibre9')

    m_crun.assert_any_call(["chroot", work_dir, "touch", '/etc/hostname'])
