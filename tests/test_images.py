from configparser import ConfigParser
from clara.plugins.clara_images import base_install, mount_chroot, umount_chroot, system_install, genimg
import tempfile
import os
import pytest
from tests.common import fakeconfig


def test_base_install(mocker):
    test_dir = tempfile.mkdtemp()
    os.makedirs(os.path.join(test_dir, "usr/sbin"))
    os.makedirs(os.path.join(test_dir, "etc/apt"))
    os.mkdir(os.path.join(test_dir, "etc/apt/preferences.d/"))
    os.mkdir(os.path.join(test_dir, "etc/apt/apt.conf.d/"))
    os.makedirs(os.path.join(test_dir, "etc/dpkg/dpkg.cfg.d/"))

    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    m_run = mocker.patch("clara.plugins.clara_images.run")
    mocker.patch("clara.plugins.clara_images.subprocess.Popen")

    base_install(test_dir, 'calibre9')
    # we assert files created
    assert os.path.isfile(os.path.join(test_dir, "etc/apt/preferences.d/00custompreferences"))
    assert os.path.isfile(os.path.join(test_dir, "usr/sbin/policy-rc.d"))
    assert os.path.isfile(os.path.join(test_dir, "etc/apt/apt.conf.d/99nocheckvalid"))
    assert os.path.isfile(os.path.join(test_dir, "etc/dpkg/dpkg.cfg.d/excludes"))
    m_run.assert_called_with(['debootstrap', u'--keyring=/usr/share/keyrings/scibian-archive-keyring.gpg', u'jessie', test_dir, u'http://debian/debian/'])

def test_mount_chroot(mocker):
    m_run = mocker.patch("clara.plugins.clara_images.run")
    work_dir = "/test"
    mount_chroot(work_dir)
    m_run.assert_any_call(["chroot", work_dir, "mount", "-t", "proc", "none", "/proc"])
    m_run.assert_any_call(["chroot", work_dir, "mount", "-t", "sysfs", "none", "/sys"])


def test_umount_chroot(mocker):
    mocker.patch("clara.plugins.clara_images.os.path.ismount")
    m_run = mocker.patch("clara.plugins.clara_images.run")
    work_dir = "/test"
    umount_chroot(work_dir)
    m_run.assert_any_call(["chroot", work_dir, "umount", "/proc/sys/fs/binfmt_misc"])
    m_run.assert_any_call(["chroot", work_dir, "umount", "/sys"])
    m_run.assert_any_call(["chroot", work_dir, "umount","-lf", "/proc"])


def test_system_install(mocker):
    mocker.patch("clara.plugins.clara_images.mount_chroot")
    mocker.patch("clara.plugins.clara_images.umount_chroot")
    m_crun = mocker.patch("clara.plugins.clara_images.run_chroot")
    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    work_dir = "/test"
    system_install(work_dir, 'calibre9')
    m_crun.assert_any_call(["chroot", work_dir, "apt-get", "update"], '/test')


def test_genimg(mocker):
    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    mocker.patch("clara.plugins.clara_images.os.chmod")
    mocker.patch("clara.plugins.clara_images.docopt.docopt")
    mocker.patch("clara.plugins.clara_images.run_chroot")
    mocker.patch("clara.plugins.clara_images.run")
    # This error should be Fixed, img parameter should be checked before
    with pytest.raises(FileNotFoundError):
        genimg('calibre9.img', '/test', 'calibre9')
