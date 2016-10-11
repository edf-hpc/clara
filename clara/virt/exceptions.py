#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2015 EDF SA
# Contact:
#       CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#       1, Avenue du General de Gaulle
#       92140 Clamart
#
# Authors: CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#
# This file is part of VirPilot.
#
# VirPilot is free software: you can redistribute in and/or
# modify it under the terms of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with VirPilot. If not, see
# <http://www.gnu.org/licenses/>.
#
# On Calibre systems, the complete text of the GNU General
# Public License can be found in `/usr/share/common-licenses/GPL'.

"""
Set of Exceptions for VirPilot application.
"""

__all__ = ["VirPilotException",
           "VirPilotRuntimeError",
           "VirPilotArgumentException",
           "VirPilotConfigurationException"]


class VirPilotException(Exception):

    """Base class for exceptions in VirPilot"""

    def __init__(self, msg):

        super(VirPilotException, self).__init__(msg)
        self.msg = msg

    def __str__(self):

        return self.msg


class VirPilotRuntimeError(VirPilotException):

    """Class for runtime errors exceptions in VirPilot"""

    def __init__(self, msg):

        super(VirPilotRuntimeError, self).__init__(msg)


class VirPilotArgumentException(VirPilotException):

    """Class for argument parsing exceptions in VirPilot"""

    def __init__(self, msg):

        super(VirPilotArgumentException, self).__init__(msg)


class VirPilotConfigurationException(VirPilotException):

    """Class for configuration file exceptions in VirPilot"""

    def __init__(self, msg):

        super(VirPilotConfigurationException, self).__init__(msg)
