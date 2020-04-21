from configparser import ConfigParser
from clara.plugins.clara_show import show
from tests.common import fakeconfig

def test_show(mocker, capsys):
    mocker.patch("clara.plugins.clara_show.getconfig",
                 side_effect=fakeconfig)

    show(section="common")
    captured = capsys.readouterr()
    assert "master_passwd" in captured.out
    show(section="repo")
    captured = capsys.readouterr()
    assert "clustername" in captured.out
    show(section="repo", dist="calibre8")
    captured = capsys.readouterr()
    assert len(captured.out.split('\n')) == 29
