#from context import sftp
from clara.sftp import Sftp
import socket
import pytest
import paramiko
import pytest_mock
import mock



def test_init():
    with pytest.raises(TypeError):
        new_stfp = Sftp()


def test_init_no_key():
    # private key not found
    with pytest.raises(IOError):
        new_stfp = Sftp('', '', '', '')

    with pytest.raises(IOError):
        new_stfp = sftp.Sftp('', '', '/tmp/noexist', '')


def test_init_blank_key():
    open('/tmp/clarakey', 'a')
    with pytest.raises(IndexError):
        new_stfp = sftp.Sftp('', '', '/tmp/clarakey', '')


#def test_init_key():
#    new_stfp = sftp.Sftp('', '', 'data/id_rsa', '')

def test_upload_fake_hosts(mocker):
    new_stfp = Sftp(['host1'], '', 'data/id_rsa', '')
    mock_logger = mocker.patch("clara.sftp.logging.error")

    new_stfp.upload("file", 'destination')
    mock_logger.assert_called_with("sftp/push: Failed to connect to host host1")

def test_upload_ssh_error(mocker):
    mock_logger = mocker.patch("clara.sftp.logging.error")
    mock_paramiko = mocker.patch("clara.sftp.paramiko.Transport.connect",
                                 side_effect=paramiko.ssh_exception.SSHException)
    mocker.patch("clara.sftp.paramiko.SFTPClient")
    mocker.patch("clara.sftp.Sftp._upload")

    new_stfp = Sftp(['localhost'], '', 'data/id_rsa', '')
    new_stfp.upload("file", 'destination')
    mock_logger.assert_called_with("sftp/push: SSH failed to @localhost")




# def test_upload(mocker):
#     new_stfp = Sftp(['host1', 'host2'], '', 'data/id_rsa', '')
#     #new_stfp = sftp.Sftp([], '', 'tests/data/id_rsa', '')
#     mock_logger = mocker.patch("clara.sftp.logging.info")
#     new_stfp.upload("file", 'destination')
#     #mock_logger = mocker.patch("clara.sftp.logging.info")
#
#     mock_logger.assert_called_with("sftp/push: pushing data on hosts %s")
#     #mock_open.assert_called()
