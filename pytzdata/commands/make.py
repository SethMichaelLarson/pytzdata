# -*- coding: utf-8 -*-

import os
import errno
import shutil
import tarfile
import subprocess

from urllib.request import urlopen
from contextlib import closing
from distutils.dir_util import copy_tree
from cleo import Command


class MakeCommand(Command):
    """
    Make tzdata files.

    make
        {path? : The destination directory.}
    """

    FILES = [
        'tzcode-latest.tar.gz',
        'tzdata-latest.tar.gz',
    ]

    BASE_URL = 'http://www.iana.org/time-zones/repository'

    def __init__(self):
        super(MakeCommand, self).__init__()

        self.path = None

    def handle(self):
        self.path = self.argument('path') or self.get_build_dir()

        self.mkdir(self.path)

        self.download()
        self.line('')
        self.uncompress()
        self.line('')
        self.build()
        self.line('')
        self.copy()
        self.line('')
        self.clean()
        self.line('')

    def download(self):
        self.line('[<comment>Downloading archives</>]')
        for filename in self.FILES:
            url = os.path.join(self.BASE_URL, filename)
            self.write('<comment>Downloading</> <fg=cyan>{}</>'.format(filename))
            dest = os.path.join(self.path, filename)
            with closing(urlopen(url)) as r:
                with open(dest, 'wb') as f:
                    shutil.copyfileobj(r, f)

            self.overwrite('<info>Downloaded</> <fg=cyan>{}</> '.format(filename))
            self.line('')

    def uncompress(self):
        self.line('[<comment>Uncompressing archives</>]')
        dest_path = os.path.join(self.path, 'tz')
        self.mkdir(dest_path)

        for filename in self.FILES:
            filepath = os.path.join(self.path, filename)
            self.write('<comment>Uncompressing</> <fg=cyan>{}</>'.format(filename))
            with closing(tarfile.open(filepath)) as f:
                f.extractall(dest_path)

            self.overwrite('<info>Uncompressed</> <fg=cyan>{}</> '.format(filename))
            self.line('')

    def build(self):
        self.line('[<comment>Building tzdata</>]')
        dest_path = os.path.join(self.path, 'tz')

        # Getting VERSION
        with open(os.path.join(dest_path, 'version')) as f:
            version = f.read().strip()

        self.write('  <comment>Building</> version <fg=cyan>{}</>'.format(version))
        os.chdir(dest_path)

        with open(os.devnull, 'w') as temp:
            subprocess.call(
                ['make', 'TOPDIR={}'.format(dest_path), 'install'],
                stdout=temp,
                stderr=temp
            )

        self.overwrite('<info>Built</> version <fg=cyan>{}</>'.format(version))
        self.line('')

    def copy(self):
        self.line('[<comment>Copying tzdata</>]')
        tzdata_dir = os.path.join(self.path, 'tz', 'etc', 'zoneinfo')
        local_dir = os.path.join(os.path.dirname(__file__), '..', 'zoneinfo')
        copy_tree(tzdata_dir, local_dir)

    def clean(self):
        self.line('[<comment>Cleaning up</>]')
        for filename in self.FILES:
            filepath = os.path.join(self.path, filename)
            self.write('<comment>Removing</> <fg=cyan>{}</>'.format(filename))
            os.remove(filepath)

            self.overwrite('<info>Removed</> <fg=cyan>{}</> '.format(filename))
            self.line('')

        self.write('<comment>Removing</> <fg=cyan>tz/*</>')
        shutil.rmtree(os.path.join(self.path, 'tz'))
        self.overwrite('<info>Removed</> <fg=cyan>tz/*</>')

    def get_build_dir(self):
        return os.path.join(os.path.dirname(__file__), '..', '..', '_build')

    def mkdir(self, path, mode=0o777):
        try:
            os.makedirs(path, mode)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise