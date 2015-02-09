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


""" Class to represent a directory of files and their checksums

"""
import os, logging
from file_checksum import FileChecksum

class DirectoryMissing(Exception): pass

class DirChecksum(object):

    def __init__ (self, path):
        self.path = path
        if not os.path.exists(self.path):
            raise DirectoryMissing('%s does not exist' % self.path)
        self.dbname = '.verifytree_checksum'
        fs = FileChecksum()

    def generate_checksum(self, checksum_filename):
        root, dirs, files = os.walk(self.path).next()
        hashes = {}
        for filename in files:
            hashes[filename] = fc.get_hash(os.path.join(root,filename))
        print (hashes)


    def validate(self):
        logging.debug("Validating directory %s" % self.path)
        checksum_filename = os.path.join(self.path, self.dbname)
        if not os.path.isfile(checksum_filename):
            self.generate_checksum(checksum_filename)


        



    
