#!/usr/bin/env python2.7
# Copyright 2015 Virantha Ekanayake All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Verify that two trees have identical files.

Usage:
    verifytree [options] compare <src> <dst>
    verifytree [options] checksum <file>
    verifytree [options] validate <dir>

Options:
    -v --verbose            Verbose logging
    -d --debug              Debug logging
    -b <blocksize>          File chunk size [default: 1048576]

"""

from __future__ import print_function
import docopt
import sys, os
import logging
import shutil

from version import __version__
import yaml

from filecmp import dircmp
import hashlib, xxhash, frogress
import file_checksum
import dir_checksum


"""
   
.. automodule:: verifytree
    :private-members:
"""

class VerifyTree(object):
    """
        The main clas.  Performs the following functions:

    """

    def __init__ (self):
        """ 
        """
        self.config = None

    def _get_config_file(self, config_file):
        """
           Read in the yaml config file

           :param config_file: Configuration file (YAML format)
           :type config_file: file
           :returns: dict of yaml file
           :rtype: dict
        """
        with config_file:
            myconfig = yaml.load(config_file)
        return myconfig


    def _get_file_size(self, filename):
        """
            Returns the file size in bytes. -1 if file does not exist
            :param filename: Filename to check size
            :type filename: string
            :returns: size of file
            :rtype: int
        """
        if os.path.exists(filename):
            statinfo = os.stat(filename)
            return statinfo.st_size
        else:
            return -1
    
    def _iter_file(self, f):
        buf = f.read(self.blocksize)
        while len(buf) > 0:
            yield buf
            buf = f.read(self.blocksize)

    def _get_hash(self, filename):
        #hasher = hashlib.md5()
        hasher = xxhash.xxh64()

        widgets = [ frogress.PercentageWidget, 
                    frogress.BarWidget, 
                    frogress.TransferWidget(filename+' '),
                    frogress.EtaWidget,
                    frogress.TimerWidget]
        with open(filename, 'rb') as f:
            chunks = self._iter_file(f)
            #for chunk in frogress.bar(chunks, source=f, steps=filesize/self.blocksize):
            for chunk in frogress.bar(chunks, source=f, widgets=widgets):
                hasher.update(chunk)

        return hasher.hexdigest()


    def get_options(self, argv):
        """
            Parse the command-line options and set the following object properties:

            :param argv: usually just sys.argv[1:]
            :returns: Nothing

            :ivar debug: Enable logging debug statements
            :ivar verbose: Enable verbose logging
            :ivar config: Dict of the config file

        """
        self.args = argv
        if argv['--verbose']:
            logging.basicConfig(level=logging.INFO, format='%(message)s')
        if argv['--debug']:
            logging.basicConfig(level=logging.DEBUG, format='%(message)s')                

        if self.args['-b']:
            self.blocksize = int(self.args['-b'])
            file_checksum.blocksize = self.blocksize

        if self.args['checksum']:
            self.file_to_checksum = self.args['<file>']
        elif self.args['validate']:
            self.dir_to_validate = self.args['<dir>']
        else:
            self.src_tree = self.args['<src>']
            self.dst_tree = self.args['<dst>']


    def run_compare(self, dcmp, level):
        if level <= 2:
            print("Checking %s" % (dcmp.left))
        #for name in dcmp.diff_files:
        
        #for name in dcmp.right_only:
            #print("Different files %s" % name)
        print("Starting loop")
        for name in dcmp.same_files:
            print("checking %s" % (name))
            md5_src = self._get_hash(os.path.join(dcmp.left,name))
            md5_dest = self._get_hash(os.path.join(dcmp.right,name))
            if md5_src == md5_dest:
                print("Same file %s (%s)" % (name, md5_src))
            else:
                print("MD5 mismatch on %s (%s vs %s)" % (name, md5_src, md5_dest))
        for sub_dcmp in dcmp.subdirs.values():
            self.run_compare(sub_dcmp, level+1)


    def go(self, argv):
        """ 
            The main entry point into VerifyTree

            #. Do something
            #. Do something else
        """
        # Read the command line options
        self.get_options(argv)
        if self.args['checksum']:
            fc = file_checksum.FileChecksum()
            print ("Checksumming %s" % (self.file_to_checksum), end='')
            #print (self._get_hash(self.file_to_checksum))
            print (fc.get_hash(self.file_to_checksum))
        elif self.args['validate']:
            dc = dirchecksum.DirChecksum(self.dir_to_validate)
            dc.validate()
        else:
            print("Verifying that destination %s matches with source %s" % (self.dst_tree, self.src_tree))
            dcmp = dircmp(self.src_tree, self.dst_tree)
            self.run_compare(dcmp,0)

        #dcmp.report_full_closure()


def main():
    args = docopt.docopt(__doc__, version='Verifytree %s' % __version__)
    script = VerifyTree()
    script.go(args)

if __name__ == '__main__':
    main()
