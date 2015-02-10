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


""" Class to generate file hash

"""
import os
import hashlib, xxhash, frogress
import logging

blocksize = 4096


class FileChecksum(object):

    def __init__(self):
        self.blocksize = blocksize

    def _iter_file(self, f, blocksize):
        buf = f.read(blocksize)
        while len(buf) > 0:
            yield buf
            buf = f.read(self.blocksize)

    def _get_file_size(self, filename):
        return os.stat(filename).st_size

    def get_hash(self, filename):
        #hasher = hashlib.md5()
        hasher = xxhash.xxh64()

        widgets = [ frogress.PercentageWidget, 
                    frogress.BarWidget, 
                    frogress.TransferWidget(filename+' '),
                    frogress.EtaWidget,
                    frogress.TimerWidget]
        filesize = self._get_file_size(filename)
        with open(filename, 'rb') as f:
            chunks = self._iter_file(f, self.blocksize)
            if filesize == 0:
                for chunk in chunks:
                    hasher.update(chunk)
                print("100.0%% | [##########] | %s 0-bytes | ETA: -- | Time: 0.0s" % filename)  
            else:
                for chunk in frogress.bar(chunks, source=f, widgets=widgets):
                    hasher.update(chunk)
                print
        return hasher.hexdigest()

