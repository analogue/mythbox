# MySQL Connector/Python - MySQL driver written in Python.
# Copyright (c) 2009, 2012, Oracle and/or its affiliates. All rights reserved.

# MySQL Connector/Python is licensed under the terms of the GPLv2
# <http://www.gnu.org/licenses/old-licenses/gpl-2.0.html>, like most
# MySQL Connectors. There are special exceptions to the terms and
# conditions of the GPLv2 as it is applied to this software, see the
# FOSS License Exception
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
import signal
try:
    import ctypes
except:
    pass
import re
from shutil import rmtree
import tempfile
import subprocess
import logging
import time

import tests

logger = logging.getLogger(tests.LOGGER_NAME)

if os.name == 'nt':
    EXEC_MYSQLD = 'mysqld.exe'
    EXEC_MYSQL = 'mysql.exe'
else:
    EXEC_MYSQLD = 'mysqld'
    EXEC_MYSQL = 'mysql'

class MySQLInstallError(Exception):

    def __init__(self, m):
        self.msg = m

    def __str__(self):
        return repr(self.msg)
        
class MySQLBootstrapError(MySQLInstallError):
    pass

class MySQLdError(MySQLInstallError):
    pass

class MySQLInstallBase(object):
    
    def __init__(self, basedir, optionFile=None):
        self._basedir = basedir
        self._bindir = None
        self._sbindir = None
        self._sharedir = None
        self._init_mysql_install()
        
        if optionFile is not None and os.access(optionFile,0):
            MySQLBootstrapError("Option file not accessible: %s" % \
                optionFile)
        self._optionFile = optionFile

    def _init_mysql_install(self):
        """Checking MySQL installation

        Check the MySQL installation and set the directories where
        to find binaries and SQL bootstrap scripts.

        Raises MySQLBootstrapError when something fails.
        """
        locs = ('libexec', 'bin', 'sbin')
        for loc in locs:
            d = os.path.join(self._basedir,loc)
            if os.access(os.path.join(d, EXEC_MYSQLD), 0):
                self._sbindir = d
            if os.access(os.path.join(d, EXEC_MYSQL), 0):
                self._bindir = d

        if self._bindir is None or self._sbindir is None:
            raise MySQLBootstrapError("MySQL binaries not found under %s" %\
                self._basedir)

        locs = ('share', 'share/mysql')
        for loc in locs:
            d = os.path.normpath(os.path.join(self._basedir,loc))
            if os.access(os.path.join(d,'mysql_system_tables.sql'),0):
                self._sharedir = d
                break

        if self._sharedir is None:
            raise MySQLBootstrapError("MySQL bootstrap scripts not found\
                under %s" % self._basedir)

class MySQLBootstrap(MySQLInstallBase):
    
    def __init__(self, topdir, datadir=None, optionFile=None,
                 basedir='/usr/local/mysql', tmpdir=None,
                 readOptionFile=False):
        if optionFile is not None:
            MySQLBootstrapError("No default option file support (yet)")
        self._topdir = topdir
        self._datadir = datadir or os.path.join(topdir,'data')
        self._tmpdir = tmpdir or os.path.join(topdir,'tmp')
        self.extra_sql = list()
        super(MySQLBootstrap, self).__init__(basedir, optionFile)
        
    def _create_directories(self):
        """Create directory structure for bootstrapping
        
        Create the directories needed for bootstrapping a MySQL
        installation, i.e. 'mysql' directory.
        The 'test' database is deliberately not created.
        
        Raises MySQLBootstrapError when something fails.
        """
        logger.debug("Creating %(d)s %(d)s/mysql and %(d)s/test" % dict(
            d=self._datadir))
        try:
            os.mkdir(self._topdir)
            os.mkdir(os.path.join(self._topdir, 'tmp'))
            os.mkdir(self._datadir)
            os.mkdir(os.path.join(self._datadir, 'mysql'))
        except OSError, e:
            raise MySQLBootstrapError("Failed creating directories: " + str(e))

    def _get_bootstrap_cmd(self):
        """Get the command for bootstrapping.
        
        Get the command which will be used for bootstrapping. This is
        the full path to the mysqld executable and its arguments.
        
        Returns a list (used with subprocess.Popen)
        """
        cmd = [
          os.path.join(self._sbindir, EXEC_MYSQLD),
          '--no-defaults',
          '--bootstrap',
          '--basedir=%s' % self._basedir,
          '--datadir=%s' % self._datadir,
          '--log-warnings=0',
          #'--loose-skip-innodb',
          '--loose-skip-ndbcluster',
          '--max_allowed_packet=8M',
          '--default-storage-engine=myisam',
          '--net_buffer_length=16K',
          '--tmpdir=%s' % self._tmpdir,
        ]
        return cmd
    
    def bootstrap(self):
        """Bootstrap a MySQL installation
        
        Bootstrap a MySQL installation using the mysqld executable
        and the --bootstrap option. Arguments are defined by reading
        the defaults file and options set in the _get_bootstrap_cmd()
        method.
        
        Raises MySQLBootstrapError when something fails.
        """
        if os.access(self._datadir,0):
            raise MySQLBootstrapError("Datadir exists, can't bootstrap MySQL")
        
        # Order is important
        script_files = (
            'mysql_system_tables.sql',
            'mysql_system_tables_data.sql',
            'fill_help_tables.sql',
            )
        
        self._create_directories()
        try:
            cmd = self._get_bootstrap_cmd()
            sql = list()
            sql.append("USE mysql;")
            for f in script_files:
                logger.debug("Reading SQL from '%s'" % f)
                fp = open(os.path.join(self._sharedir,f),'r')
                sql += [ line.strip() for line in fp.readlines() ]
                fp.close()
            sql += self.extra_sql
            devnull = open(os.devnull, 'w')
            prc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                   stderr=devnull, stdout=devnull)
            prc.communicate('\n'.join(sql))
        except Exception, e:
            raise MySQLBootstrapError(e)

class MySQLd(MySQLInstallBase):
    
    def __init__(self, basedir, optionFile):
        self._process = None
        super(MySQLd, self).__init__(basedir, optionFile)
        self._version = self._get_version()
        
    def _get_cmd(self):
        cmd = [
            os.path.join(self._sbindir, EXEC_MYSQLD),
            "--defaults-file=%s" % (self._optionFile)
        ]

        if os.name == 'nt':
            cmd.append('--standalone')

        return cmd

    def _get_version(self):
        """Get the MySQL server version
        
        This method executes mysqld with the --version argument. It parses
        the output looking for the version number and returns it as a
        tuple with integer values: (major,minor,patch)
        
        Returns a tuple.
        """
        cmd = [
            os.path.join(self._sbindir, EXEC_MYSQLD),
            '--version'
        ]
        
        prc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        verstr = str(prc.communicate()[0])
        matches = re.match(r'.*Ver (\d)\.(\d).(\d{1,2}).*', verstr)
        if matches:
            return tuple([int(v) for v in matches.groups()])
        else:
            raise MySQLdError('Failed reading version from mysqld --version')
    
    @property
    def version(self):
        """Returns the MySQL server version
        
        Returns a tuple.
        """
        return self._version
        
    def start(self):
        try:
            cmd = self._get_cmd()
            devnull = open(os.devnull, 'w')
            self._process = subprocess.Popen(cmd, stdout=devnull,
                                             stderr=devnull)
        except Exception, e:
            raise MySQLdError(e)
    
    def stop(self):
        try:
            try:
                self._process.terminate()
            except AttributeError:
                # Python 2.5 and earlier
                if os.name == 'nt':
                    ctypes.windll.kernel32.TerminateProcess(
                        int(self._process._handle), -1)
                else:
                    os.kill(self._process.pid, signal.SIGKILL)
        except Exception, e:
            raise MySQLdError(e)

class MySQLInit(object):
    
    def __init__(self, basedir, topdir, cnf, option_file, bind_address, port,
                 unix_socket, ssldir):
        self._cnf = cnf
        self._option_file = option_file
        self._unix_socket = unix_socket
        self._bind_address = bind_address
        self._port = port
        self._topdir = topdir
        self._basedir = basedir
        self._ssldir = ssldir
        
        self._install = None
        self._server = None
        self._debug = False

        self._server = MySQLd(self._basedir, self._option_file)

    @property
    def version(self):
        """Returns the MySQL server version
        
        Returns a tuple.
        """
        return self._server.version

    def _slashes(self, path):
        """Convert forward slashes with backslashes

        This method replaces forward slashes with backslashes. This
        is necessary using Microsoft Windows for location of files in
        the option files.

        Returns a string.
        """
        if os.name == 'nt':
            nmpath = os.path.normpath(path)
            return path.replace('\\', '\\\\')
        return path
        
    def bootstrap(self):
        """Bootstrap a MySQL server"""
        try:
            self._install = MySQLBootstrap(self._topdir,
                basedir=self._basedir)
            self._install.extra_sql = (
                "CREATE DATABASE myconnpy;",)
            self._install.bootstrap()
        except Exception, e:
            logger.error("Failed bootstrapping MySQL: %s" % e)
            if self._debug is True:
                raise
            sys.exit(1)
    
    def start(self):
        """Start a MySQL server"""
        options = {
            'mysqld_basedir': self._slashes(self._basedir),
            'mysqld_datadir': self._slashes(self._install._datadir),
            'mysqld_tmpdir': self._slashes(self._install._tmpdir),
            'mysqld_bind_address': self._bind_address,
            'mysqld_port': self._port,
            'mysqld_socket': self._slashes(self._unix_socket),
            'ssl_dir': self._slashes(self._ssldir),
            }
        try:
            fp = open(self._option_file,'w')
            fp.write(self._cnf % options)
            fp.close()
            self._server = MySQLd(self._basedir, self._option_file)
            self._server.start()
            time.sleep(3)
        except MySQLdError, err:
            logger.error("Failed starting MySQL server: %s" % err)
            if self._debug is True:
                raise
            sys.exit(1)

    def stop(self):
        try:
            self._server.stop()
        except MySQLdError, e:
            logger.error("Failed stopping MySQL server: %s" % e)
            if self._debug is True:
                raise
        else:
            logger.info("MySQL server stopped.")
    
    def remove(self):
        try:
            rmtree(self._topdir)
        except Exception, e:
            logger.debug("Failed removing %s: %s" % (self._topdir, e))
            if self._debug is True:
                raise
        else:
            logger.info("Removed %s" % self._topdir)

