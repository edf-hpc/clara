from clara.sftp import Sftp
import pytest
import paramiko


def test_init():
    with pytest.raises(TypeError):
        new_stfp = Sftp()


def test_init_no_key():
    # private key not found
    with pytest.raises(IOError):
        new_stfp = Sftp('', '', '', '')

    with pytest.raises(IOError):
        new_stfp = Sftp('', '', '/tmp/noexist', '')


def test_init_blank_key():
    open('/tmp/clarakey', 'a')
    with pytest.raises(paramiko.ssh_exception.SSHException):
        new_stfp = Sftp('', '', '/tmp/clarakey', '')


def test_upload_fake_hosts(mocker, data_dir):
    new_stfp = Sftp(['host1'], '', data_dir.id_rsa, '')
    mock_logger = mocker.patch("clara.sftp.logging.error")

    new_stfp.upload("file", 'destination')
    mock_logger.assert_called_with("sftp/push: Failed to connect to host host1")

def test_upload_ssh_error(mocker, data_dir):
    mock_logger = mocker.patch("clara.sftp.logging.error")
    mock_paramiko = mocker.patch("clara.sftp.paramiko.Transport.connect",
                                 side_effect=paramiko.ssh_exception.SSHException)
    mocker.patch("clara.sftp.paramiko.SFTPClient")
    mocker.patch("clara.sftp.Sftp._upload")

    new_stfp = Sftp(['localhost'], '', data_dir.id_rsa, '')
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
