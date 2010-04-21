#!/usr/bin/env python
# -*- coding: utf-8 -*-
# MySQL Connector/Python - MySQL driver written in Python.
# Copyright 2009 Sun Microsystems, Inc. All rights reserved
# Use is subject to license terms. (See COPYING)

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation.
# 
# There are special exceptions to the terms and conditions of the GNU
# General Public License as it is applied to this software. View the
# full text of the exception in file EXCEPTIONS-CLIENT in the directory
# of this software distribution or see the FOSS License Exception at
# www.mysql.com.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

"""Script for creating releases

* Updates the version in mysql.connector._version
* Builds source distributions.
"""

import sys
import os.path
from shutil import copy2
from optparse import OptionParser

from distutils.core import run_setup

class Error(Exception):
    pass

def add_options(p):
    p.add_option('-R','--release-version', dest='rel_version',
        metavar='STRING',
        help='Release version, e.g. 0.1.13-devel')
    p.add_option('-D','--release-dir', dest='rel_dir',
        metavar='PATH',
        help='Where to start to releases ones builds')
        
def parse_version(v):
    
    try:
        (ver,tag) = v.split('-',2)
        version = map(int,ver.split('.',3))
        version.append(tag)
        version.append('')
    except:
        raise Error("Release version must be  x.y.z-tag, e.g. 0.1.13-devel")
        
    return tuple(version)

def write_version_info(version_info):
    
    version_file = "mysql/connector/_version.py"
    
    fp = None
    try:
        fp = open(version_file,'r')
    except:
        raise Error("Failed opening %s for reading" % (version_file))
    else:
        lines = fp.readlines()
        fp.close()
    
    try:
        fp = open(version_file,'w')
    except:
        raise Error("Failed opening %s for writing" % (version_file))
        
    changed = False
    for (nr,line) in enumerate(lines):
        if line[0:7] == 'version':
            lines[nr] = "version = %s" % (repr(version_info))
            changed = True
            break
    
    if changed is True:
        fp.truncate()
        lines.append('\n')
        fp.writelines(lines)
        fp.close()
    else:
        fp.close()
        raise Error("Failed writing version in _version.py")

def make_sdist():
    dist = run_setup('setup.py',['sdist'])

def copy_dist_files(destdir):
    distdir = os.path.abspath('dist/')
    destdir = os.path.abspath(destdir)
    filelist = []
    try:
        filelist = os.listdir(distdir)
    except:
        raise Error("Failed getting file list from \n   %s" % (distdir))
    
    if filelist == []:
        raise Error("No distributions available")
    
    for f in filelist:
        print "Copying %s" % (f)
        destfile =  "%s/%s" % (destdir,f)
        distfile = "%s/%s" % (distdir,f)
        try:
            copy2(distfile,destfile)
        except:
            raise Error("Failed copying %s\n  to %s" % (distfile,destfile))
    
def main():
    usage = 'usage: %prog [options]'
    parser = OptionParser()
    add_options(parser)
    
    (options, args) = parser.parse_args()
    version_info = None
    
    if not os.path.isdir(options.rel_dir):
        print "Please specify a valid directory to put builds"
        parser.print_help()
        sys.exit(1)
        
    try:
        version_info = parse_version(options.rel_version)
        write_version_info(version_info)
    except Error, e:
        print e
        sys.exit(1)
    
    try:
        make_sdist()
        copy_dist_files(options.rel_dir)
    except Error, e:
        print e
    else:
        print "Success!"
    
if __name__ == '__main__':
    main()
