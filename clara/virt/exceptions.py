#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2016 EDF SA
# Contact:
#       CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#       1, Avenue du General de Gaulle
#       92140 Clamart
#
# Authors: CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#
# This file is part of clara.
#
# Virt is free software: you can redistribute in and/or
# modify it under the terms of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with Virt. If not, see
# <http://www.gnu.org/licenses/>.
#
# On Calibre systems, the complete text of the GNU General
# Public License can be found in `/usr/share/common-licenses/GPL'.

"""
Set of Exceptions for Virt application.
"""

__all__ = ["VirtException",
           "VirtRuntimeError",
           "VirtConfigurationException"]


class VirtException(Exception):

    """Base class for exceptions in Virt"""

    def __init__(self, msg):

        super(VirtException, self).__init__(msg)
        self.msg = msg

    def __str__(self):

        return self.msg


class VirtRuntimeError(VirtException):

    """Class for runtime errors exceptions in Virt"""

    def __init__(self, msg):

        super(VirtRuntimeError, self).__init__(msg)


class VirtConfigurationException(VirtException):

    """Class for configuration file exceptions in Virt"""

    def __init__(self, msg):

        super(VirtConfigurationException, self).__init__(msg)
