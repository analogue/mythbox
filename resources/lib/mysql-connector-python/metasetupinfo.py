# MySQL Connector/Python - MySQL driver written in Python.
# Copyright (c) 2009, 2012, Oracle and/or its affiliates. All rights reserved.

# MySQL Connector/Python is licensed under the terms of the GPLv2
# <http://www.gnu.org/licenses/old-licenses/gpl-2.0.html>, like most
# MySQL Connectors. There are special exceptions to the terms and
# conditions of the GPLv2 as it is applied to this software, see the
# FLOSS License Exception
# <http://www.mysql.com/about/legal/licensing/foss-exception.html>.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import sys
import os
from distutils.sysconfig import get_python_lib

from version import VERSION

# Development Status Trove Classifiers significant for Connector/Python
DEVELOPMENT_STATUSES = {
    'a': '3 - Alpha',
    'b': '4 - Beta',
    None: '5 - Production/Stable'
}

if sys.version_info >= (3, 1):
    sys.path = ['python3/'] + sys.path
    package_dir = { '': 'python3' }
elif sys.version_info >= (2, 4) and sys.version_info < (3, 0):
    sys.path = ['python2/'] + sys.path
    package_dir = { '': 'python2' }
else:
    raise RuntimeError(
        "Python v%d.%d is not supported" % sys.version_info[0:2])

name = 'mysql-connector-python'
version = '.'.join(map(str, VERSION[0:3]))
if VERSION[3] and VERSION[4]:
    version += VERSION[3] + str(VERSION[4])

try:
    from support.distribution.commands import sdist, bdist, dist_rpm
    cmdclasses = {
        'sdist': sdist.GenericSourceGPL,
        'sdist_gpl': sdist.SourceGPL,
        'bdist_com': bdist.BuiltCommercial,
        'bdist_com_rpm': dist_rpm.BuiltCommercialRPM,
        'sdist_gpl_rpm': dist_rpm.SourceRPM,
    }
    
    if sys.version_info >= (2, 7):
        # MSI only supported for Python 2.7 and greater
        from support.distribution.commands import (dist_msi)
        cmdclasses.update({
            'bdist_com': bdist.BuiltCommercial,
            'bdist_com_msi': dist_msi.BuiltCommercialMSI,
            'sdist_gpl_msi': dist_msi.SourceMSI,
            })

except ImportError:
    # Part of Source Distribution
    cmdclasses = {}

packages = [
    'mysql',
    'mysql.connector', 
    'mysql.connector.locales',
    'mysql.connector.locales.eng',
    ]
description = "MySQL driver written in Python"
long_description = """\
MySQL driver written in Python which does not depend on MySQL C client
libraries and implements the DB API v2.0 specification (PEP-249).
"""
author = 'Oracle and/or its affiliates'
author_email = ''
maintainer = 'Geert Vanderkelen'
maintainer_email = 'geert.vanderkelen@oracle.com'
license = "GNU GPLv2 (with FOSS License Exception)"
keywords = "mysql db",
url = 'http://dev.mysql.com/usingmysql/python/'
download_url = 'http://dev.mysql.com/usingmysql/python/'
url = 'http://dev.mysql.com/doc/connector-python/en/index.html'
download_url = 'http://dev.mysql.com/downloads/connector/python/'
classifiers = [
    'Development Status :: %s' % (DEVELOPMENT_STATUSES[VERSION[3]]),
    'Environment :: Other Environment',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'Intended Audience :: Information Technology',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2.4',
    'Programming Language :: Python :: 2.5',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.1',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'Topic :: Database',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    'Topic :: Software Development :: Libraries :: Python Modules'
]

