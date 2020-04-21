import os
from clara.plugins.clara_repo import do_key, do_sync
import clara.plugins.clara_repo as clara_repo
from clara.utils import get_from_config
from tests.common import FakeConfig, fakeconfig


def fake_subprocess(cmd, stdout=None, stderr=None):
    return 0


def test_dokey(mocker):

    """ We test with a password not that long"""
    mocker.patch("clara.plugins.clara_repo.os.path.isfile")
    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    mocker.patch("clara.plugins.clara_repo.value_from_file",
                 side_effect=lambda f, k: "password")
    mocker.patch("clara.plugins.clara_repo.clara_exit")
    do_key()


def test_dokey_lpasswd(mocker):

    mocker.patch("clara.plugins.clara_repo.os.path.isfile")
    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    mocker.patch("clara.plugins.clara_repo.value_from_file",
                 side_effect=lambda f, k: "passwordlooooooooooong")
    m_subprocess = mocker.patch("clara.plugins.clara_repo.subprocess.call",
                                side_effect=fake_subprocess)
    do_key()


def test_doinit(mocker, tmpdir_factory):

    fn = tmpdir_factory.mktemp("repo")
    repo_path = os.path.join(str(fn), 'repo')
    mirror_path = os.path.join(str(fn), 'mirror')
    os.mkdir(mirror_path)

    def fake_getfromconfig(section, value, dist=''):
        if section == "repo" and value == "repo_dir":
            return repo_path
        if section == "repo" and value == "mirror_local":
            return mirror_path

        return get_from_config(section, value, dist)

    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    mocker.patch("clara.plugins.clara_repo.get_from_config", side_effect=fake_getfromconfig)
    m_run = mocker.patch("clara.plugins.clara_repo.run")
    clara_repo._opt['dist'] = 'calibre9'

    clara_repo.do_init()


def test_dosycn(mocker):

    mocker.patch("clara.plugins.clara_repo.os.path.isfile")
    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    mocker.patch("clara.plugins.clara_repo.configparser.ConfigParser",
                 side_effect=FakeConfig)
    m_run = mocker.patch("clara.plugins.clara_repo.run")

    do_sync('calibre9')

    m_run.assert_called_with(['debmirror', '--diff=none',
                              '--nosource', '--ignore-release-gpg',
                              '--ignore-missing-release', '--method=http',
                              '--arch=amd64', '--host=forge.hpc.edf.fr',
                              '--root=calibre-hpc', '--dist=calibre9',
                              '--section=main,contrib,non-free,main/debian-installer',
                              u'/srv/clara/website/mirror/calibre9-hpc'])


def test_doreprepro(mocker):

    mocker.patch("clara.plugins.clara_repo.os.path.isfile")
    mocker.patch("clara.utils.getconfig", side_effect=fakeconfig)
    m_run = mocker.patch("clara.plugins.clara_repo.run")
    clara_repo._opt['dist'] = 'calibre9'

    clara_repo.do_reprepro('list')

    m_run.assert_called_with(['reprepro', '--silent', '--ask-passphrase',
                              '--basedir', u'/srv/clara/calibre9/local-mirror',
                              '--outdir', u'/srv/clara/website/mirror/calibre9-cluster',
                              'list', 'calibre9'])