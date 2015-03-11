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
    verifytree [options] checksum <file>
    verifytree [options] validate <dir> [-u] [--no-subdirs]
    verifytree [options] freshen <dir> [-u] [--no-subdirs]
    verifytree [options] scan <dir>

Options:
    -v --verbose            Verbose logging
    -d --debug              Debug logging
    -b <blocksize>          File chunk size [default: 1048576]
    -u                      Update checksum files
    -f                      Force update checksum files
    --no-subdirs            Don't descend into sub-directories 

"""

from __future__ import print_function
import sys, os, logging, shutil, time
from filecmp import dircmp

from version import __version__

# External pkg imports
import docopt
import yaml
import hashlib, xxhash, frogress
import file_checksum
import dir_checksum
import check_dirs


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
        self.update_hash_files = False
        self.force_update_hash_files = False
        self.freshen_hash_files = False
        self.timing = { 'start': 0,
                        'end': 0,
                      }

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
        elif self.args['validate'] or self.args['freshen']:
            self.dir_to_validate = self.args['<dir>']
            if self.args['-u']:
                self.update_hash_files = True
            if self.args['-f']:
                self.force_update_hash_files = True
            if self.args['freshen']:
                self.freshen_hash_files = True

        elif self.args['scan']:
            self.dir_to_validate = self.args['<dir>']


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

    def report_timing(self):
        #print("="*40)
        duration = self.timing['end'] - self.timing['start']
        h = int(duration / (60*60))
        m = int((duration - h*60*60) / 60)
        s = int(duration - h*60*60 - m*60)
        print("\nElapsed time: %dh %dm %ds\n" % (h,m,s))
        #print("="*40)
        
        
    def go(self, argv):
        """ 
            The main entry point into VerifyTree

            #. Do something
            #. Do something else
        """
        reload(sys)
        sys.setdefaultencoding('utf8')
        # Read the command line options

        self.get_options(argv)

        self.timing['start'] = time.time()

        if self.args['checksum']:
            fc = file_checksum.FileChecksum()
            print ("Checksumming %s" % (self.file_to_checksum), end='')
            #print (self._get_hash(self.file_to_checksum))
            print (fc.get_hash(self.file_to_checksum))
        elif self.args['validate'] or self.args['freshen']:
            # Scan the directory
            checker = check_dirs.CheckDirs()
            print("Building file list:")
            num_dirs, num_files, size_files = checker.scan(self.dir_to_validate)
            print("%d dirs, %d files, %7.2fGB" % (num_dirs, num_files, float(size_files)/(2**30)))

            if self.force_update_hash_files:
                print("Force updating checksum files")
                checker.force_update_hash_files = self.force_update_hash_files
                checker.update_hash_files = self.update_hash_files
            elif self.update_hash_files:
                print("Updating checksum files")
                checker.update_hash_files = self.update_hash_files
            if self.freshen_hash_files:
                print("Only freshening checksums for new files since last scan")
                checker.freshen_hash_files = self.freshen_hash_files

            if self.args['--no-subdirs']:
                checker.validate_single_directory(self.dir_to_validate)
            else:
                checker.validate(self.dir_to_validate)
        elif self.args['scan']:
            pass
        else:
            error("Shouldn't be here!")

        self.timing['end'] = time.time()
        self.report_timing()
            


def main():
    args = docopt.docopt(__doc__, version='Verifytree %s' % __version__)
    script = VerifyTree()
    script.go(args)

if __name__ == '__main__':
    main()

