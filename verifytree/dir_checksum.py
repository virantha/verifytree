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
import os, logging, copy
from file_checksum import FileChecksum
import yaml, tabulate
from exceptions import *

class Results(object):

    def __init__(self):
        self.files_total = 0
        self.files_new = 0
        self.files_deleted = 0
        self.files_changed = 0
        self.files_validated = 0
        self.files_chksum_error = 0
        self.files_size_error = 0
        self.files_disk_error = 0

        self.dirs_total = 0
        self.dirs_missing = 0
        self.dirs_new = 0

        self.directory = ""

    def __add__(self, other):
        sumr = Results()
        for attr in self.__dict__:
            if attr.startswith('files') or attr.startswith('dirs'):
                sumr.__dict__[attr] = self.__dict__[attr] + other.__dict__[attr]
            elif attr == 'directory':
                if type(self.__dict__[attr]) is not list:
                    src = [self.__dict__[attr]]
                else:
                    src = copy.copy(self.__dict__[attr])
                if type(other.__dict__[attr]) is list:
                    src.extend(copy.copy(other.__dict__[attr]))
                else:
                    src.append(other.__dict__[attr])
                sumr.__dict__[attr] = src
        return sumr

    def __str__ (self):
        res = []
        headers = [x for x in self.__dict__ if x.startswith('dirs_')]
        table = [ [self.__dict__[x] for x in headers] ]
        res.append(tabulate.tabulate(table, headers))

        
        headers = [x for x in self.__dict__ if x.startswith('files_')]
        table = [ [self.__dict__[x] for x in headers] ]
        res.append(tabulate.tabulate(table, headers))

        return '\n\n'.join(res)


class DirChecksum(object):

    def __init__ (self, path):
        self.path = path
        if not os.path.exists(self.path):
            raise DirectoryMissing('%s does not exist' % self.path)
        self.dbname = '.verifytree_checksum'
        self.fc = FileChecksum()
        self.results = Results()
        self.results.directory = self.path
        self.update_hash_files = False
        self.force_update_hash_files = False
        self.freshen_hash_files = False
                                
    def generate_checksum(self, checksum_filename):
        root, dirs, files = os.walk(self.path).next()
        hashes = {  'dirs': dirs,
                    'files': {}
                }
        for filename in files:
            entry = self._gen_file_checksum(os.path.join(root,filename))
            if filename != self.dbname:
                hashes['files'][filename] = entry
                self.results.files_new += 1

        # Write out the hashes for the current directory
        logging.debug(hashes)

        return hashes

    def _gen_file_checksum(self, filename):
        fstat = os.stat(filename)
        file_entry = { 'size': fstat.st_size,
                       'mtime': fstat.st_mtime,
                       }
        
        _hash = self.fc.get_hash(filename)
        if _hash:
            file_entry['hash'] = _hash
        else:
            # Hmm, some kind of error (IOError!)
            print("ERROR: file %s disk error while generating checksum" % (filename))
            file_entry['hash'] = ""
            self.results.files_disk_error += 1
        return file_entry

    def _load_checksums(self, checksum_file):
        with open(checksum_file) as f:
            hashes = yaml.load(f)
        return hashes

    def _save_checksums(self, hashes, checksum_file):
        with open(checksum_file, 'w') as f:
            f.write(yaml.dump(hashes))

    def _check_hashes(self, root, hashes, checksum_file):
        file_hashes = copy.deepcopy(hashes['files'])
        update = False
        #print("Checking %d files" % (len(hashes['files'])))
        if self.freshen_hash_files:
            for f, stats in hashes['files'].items():
                if stats['hash'] == '' or stats['hash'] is None:
                    full_path = os.path.join(root, f)
                    self.results.files_new += 1
                    print("Freshening file %s" % (f))
                    file_hashes[f] = self._gen_file_checksum(full_path)
                    update = True

        else:
            for f, stats in hashes['files'].items():
                full_path = os.path.join(root, f)
                fstat = os.stat(full_path)
                if fstat.st_mtime != int(stats['mtime']):
                    print("File %s changed, updating hash" % (f))
                    self.results.files_changed += 1
                    if self.update_hash_files:
                        file_hashes[f] = self._gen_file_checksum(full_path)
                        update = True
                elif fstat.st_size != long(stats['size']):
                    print("ERROR: file %s has changed in size from %s to %s" % (f, stats['size'], fstat.st_size))
                    self.results.files_size_error += 1
                    if self.force_update_hash_files:
                        file_hashes[f] = self._gen_file_checksum(full_path)
                        update = True
                        print("Updating checksum to new value")
                    else:
                        print("Use -f option and rerun to force new checksum computation to accept changed file and get rid of this error")
                else:
                    # mtime and size look good, so now check the hashes
                    #print (full_path)
                    new_hash = self._gen_file_checksum(full_path)
                    if new_hash['hash'] != stats.get('hash',""):
                        print("ERROR: file %s hash has changed from %s to %s" % (f, stats['hash'], new_hash['hash']))
                        self.results.files_chksum_error += 1
                        if self.force_update_hash_files:
                            file_hashes[f] = new_hash
                            update=True
                            print("Updating checksum to new value")
                        else:
                            print("Use -f option and rerun to force new checksum computation to accept changed file and get rid of this error")
                    else:
                        self.results.files_validated += 1
        if update:
            hashes['files'] = file_hashes
            self._save_checksums(hashes,checksum_file) 


    def _are_sub_dirs_same(self, hashes, root, dirs):
        self.results.dirs_total += len(dirs)
        if 'dirs' in hashes:
            # Just a check for backwards compatibility with old versions that
            # did not save the subdirectory names
            hashes_set = set(hashes['dirs'])
            disk_set = set(dirs)

            new_dirs = disk_set - hashes_set
            if len(new_dirs) != 0:
                print("New sub-directories found:")
                print ('\n'.join(["- %s" % (os.path.join(root,x)) for x in new_dirs]))
                self.results.dirs_new += len(new_dirs)

            missing_dirs = hashes_set - disk_set
            if len(missing_dirs) != 0:
                print("Missing sub-directories from last scan found:")
                print ('\n'.join(["- %s" % (os.path.join(root,x)) for x in missing_dirs]))
                self.results.dirs_missing += len(missing_dirs)

            if disk_set != hashes_set:
                # There were differences, so we let's update the hashes
                hashes['dirs'] = dirs
                return False
            else:
                return True
        else:
            # Ah ha, the hashes files was created by an old version of this program
            # so just add it now
            hashes['dirs'] = copy.deepcopy(dirs)
            self.results.dirs_new += len(dirs)
            print hashes
            return False

    def _validate_hashes(self, hashes, checksum_file):
        file_hashes = hashes['files']
        root, dirs, files = os.walk(self.path).next()

        # First, make sure the sub-directories previously recorded are all here
        if not self._are_sub_dirs_same(hashes, root, dirs):
            # Uh oh, sub directory hashes were different, so let's update the hash file
            if self.update_hash_files:
                self._save_checksums(hashes, checksum_file)



        set_filenames_hashes = set(file_hashes.keys())
        set_filenames_disk = set(files)
        set_filenames_disk.remove(self.dbname)

        if set_filenames_hashes != set_filenames_disk: # Uh oh, different number of files on disk vs hash file

            if set_filenames_disk > set_filenames_hashes: # New files on disk
                print("New files detected since last validation")
                new_files = set_filenames_disk-set_filenames_hashes
                self._check_hashes(root, hashes, checksum_file)
                for f in new_files:
                    file_hashes[f] = self._gen_file_checksum(os.path.join(root,f))
                    self.results.files_new += 1
                if self.update_hash_files:
                    self._save_checksums(hashes, checksum_file)

            elif set_filenames_hashes > set_filenames_disk: # Files on disk deleted
                missing_files = set_filenames_hashes - set_filenames_disk
                print("Missing files since last validation")
                for f in missing_files:
                    print(f)
                    self.results.files_deleted += 1
                    del file_hashes[f]
                if self.update_hash_files:
                    self._save_checksums(hashes, checksum_file)
                self._check_hashes(root, hashes, checksum_file)
                    
        else:
            self._check_hashes(root, hashes, checksum_file)


    def validate(self):

        #self.update_hash_files = update_hash_files
        checksum_filename = os.path.join(self.path, self.dbname)
        if not os.path.isfile(checksum_filename):
            print("Generating checksums for new directory %s" % self.path)
            hashes = self.generate_checksum(checksum_filename)
            self._save_checksums(hashes, checksum_filename)
        else:
            #print ("Validating %s " % (self.path))
            hashes = self._load_checksums(checksum_filename)
            self._validate_hashes(hashes, checksum_filename)




        



    
