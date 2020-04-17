import pytest
import collections
import os


@pytest.fixture(scope="session")
def data_dir(pytestconfig):
    """This fixture helps to access files from data directory"""
    TestFiles = collections.namedtuple('TestFiles', 'root clara_conf id_rsa virt_conf')
    repository_root = os.path.join(pytestconfig.rootdir.dirname,
                             pytestconfig.rootdir.basename)
    root_data = os.path.join(pytestconfig.rootdir.dirname,
                             pytestconfig.rootdir.basename,
                             'tests/data')

    return TestFiles(root_data,
                     os.path.join(repository_root,'example-conf/config.ini'),
                     os.path.join(root_data, 'id_rsa'),
                     os.path.join(root_data, 'virt.ini'))
