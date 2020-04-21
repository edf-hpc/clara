import clara.plugins.clara_p2p as clara_p2p
from configparser import ConfigParser


def fake_config():
    config = ConfigParser()
    config.read('example-conf/config.ini')
    return config


def test_mktorrent(mocker):
    mocker.patch("clara.utils.getconfig", side_effect=fake_config)
    mocker.patch("clara.plugins.clara_p2p.os.path.isfile")
    mocker.patch("clara.plugins.clara_p2p.os.path.isfile")
    mocker.patch("clara.plugins.clara_p2p.os.remove")
    mocker.patch("clara.plugins.clara_p2p.os.chmod")
    m_run = mocker.patch("clara.plugins.clara_p2p.run")
    clara_p2p._opts['dist'] ='calibre9'
    clara_p2p.mktorrent(None)
    m_run.assert_called_with(["/usr/bin/mktorrent", "-a",
                              "http://server2:6881/announce", '-o',
                              u'/srv/clara/website/boot/file2.torrent',
                              u'/srv/clara/website/boot/calibre9.squashfs'])