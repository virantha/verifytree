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


import os, logging
import dir_checksum

class CheckDirs(object):

    def __init__(self):
        self.update_hash_files = False  # Write out the checksum on modified/deleted files with proper timestamps
        self.force_update_hash_files = False # Force on checksum error to new hash (only do this if you're sure this wasn't a bit-rot or file corruption!)
        pass


    def validate_single_directory(self, path):
        dc = dir_checksum.DirChecksum(path)
        dc.update_hash_files = self.update_hash_files
        dc.force_update_hash_files = self.force_update_hash_files
        dc.validate()
        return dc

    def validate(self, path):
        total = dir_checksum.Results()
        for root, subdirs, files in os.walk(path):
            result = self.validate_single_directory(root)

            # Make a sanity check of the total files processed by making sure
            # everything sums up to list of files in dir minus the checksum file plus the deleted files
            if result.dbname in files: files.remove(result.dbname)
            result.results.files_total += len(files)
            result.results.files_total += result.results.files_deleted
            total += result.results


        print ("Summary")
        print (total)


        

