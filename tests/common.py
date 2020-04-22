# This files is used to provide fake methods used for testing

from configparser import ConfigParser
import os

repo_dir, _ = os.path.split(os.path.dirname(__file__))


class FakeConfig(ConfigParser):

    def read(self, filenames, encoding=None):
        super(FakeConfig, self).read(os.path.join(repo_dir,'example-conf/repos.ini'))


def fakeconfig():
    config = ConfigParser()
    config.read(os.path.join(repo_dir,'example-conf/config.ini'))
    return config
