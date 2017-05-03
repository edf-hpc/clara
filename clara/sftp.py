#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#  Copyright (C) 2014-2016 EDF SA                                            #
#                                                                            #
#  This file is part of Clara                                                #
#                                                                            #
#  This software is governed by the CeCILL-C license under French law and    #
#  abiding by the rules of distribution of free software. You can use,       #
#  modify and/ or redistribute the software under the terms of the CeCILL-C  #
#  license as circulated by CEA, CNRS and INRIA at the following URL         #
#  "http://www.cecill.info".                                                 #
#                                                                            #
#  As a counterpart to the access to the source code and rights to copy,     #
#  modify and redistribute granted by the license, users are provided only   #
#  with a limited warranty and the software's author, the holder of the      #
#  economic rights, and the successive licensors have only limited           #
#  liability.                                                                #
#                                                                            #
#  In this respect, the user's attention is drawn to the risks associated    #
#  with loading, using, modifying and/or developing or reproducing the       #
#  software by the user in light of its specific status of free software,    #
#  that may mean that it is complicated to manipulate, and that also         #
#  therefore means that it is reserved for developers and experienced        #
#  professionals having in-depth computer knowledge. Users are therefore     #
#  encouraged to load and test the software's suitability as regards their   #
#  requirements in conditions enabling the security of their systems and/or  #
#  data to be ensured and, more generally, to use and operate it in the      #
#  same conditions as regards security.                                      #
#                                                                            #
#  The fact that you are presently reading this means that you have had      #
#  knowledge of the CeCILL-C license and that you accept its terms.          #
#                                                                            #
##############################################################################

import logging

import os
import paramiko
import stat
import socket


class Sftp:
    """Class which sends files of SFTP"""
    def __init__(self, hosts, username, private_key, passphrase=None):
        self.hosts = hosts
        self.username = username
        self.private_key = paramiko.RSAKey.from_private_key_file(private_key, password=passphrase)

    @staticmethod
    def _is_dir(sftp_client, path):
        try:
            is_dir = stat.S_ISDIR(sftp_client.stat(path).st_mode)
        except IOError:
            is_dir = False
        return is_dir

    @staticmethod
    def _mkdir(sftp_client, path):
        if Sftp._is_dir(sftp_client, path):
            return
        else:
            parent = os.path.dirname(path[:-1])
            Sftp._mkdir(sftp_client, parent)
        sftp_client.mkdir(path)

    def _upload(self, source_paths, sftp_client, remote_host, destination_path, mode=None):
        hostname = socket.gethostname()
        # Upload the files
        for source_file_path in source_paths:
            source_dir_path = os.path.dirname(source_file_path)
            # Ignore if uploading from one of the hosts and to the same destination
            if source_dir_path == destination_path and hostname == remote_host:
                # Alternatively, one could check against socket.gethostbyaddr(sftp_client.get_transport().getpeername()[0])[0]
                logging.info("sftp/upload: skipping upload of %s to %s" % (source_file_path, hostname))
            else:
                dest_file_path = os.path.join(destination_path, os.path.basename(source_file_path))
                # Create remote directory if necessary
                logging.info("sftp/upload: uploading %s to %s:%s" % (source_file_path, remote_host, dest_file_path))
                Sftp._mkdir(sftp_client, destination_path)
                sftp_client.put(source_file_path, dest_file_path)
                if mode:
                    sftp_client.chmod(dest_file_path, mode)

    def upload(self, files, destination, mode=None):
        logging.info("sftp/push: pushing data on hosts %s", self.hosts)

        for host in self.hosts:
            try:
                transport = paramiko.Transport((host, 22))
                transport.connect(username=self.username, pkey=self.private_key)
            except socket.gaierror as e:
                logging.error("sftp/push: Failed to connect to host %s" % host)
                logging.info("sftp/push: Connection error: %s." % e)
                continue
            except paramiko.ssh_exception.SSHException as e:
                logging.error("sftp/push: SSH failed to %s@%s" % (self.username, host))
                logging.info("sftp/push: SSH error: %s." % e)
                continue
            sftp_client = paramiko.SFTPClient.from_transport(transport)

            logging.debug("sftp/push: copying files")
            self._upload(files, sftp_client, host, destination, mode)
            sftp_client.close()
