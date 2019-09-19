#!/usr/bin/env python
from __future__ import print_function

import os
import subprocess
import sys
import re

from setuptools import setup

try:
    from Cython.Build import cythonize
    from Cython.Distutils import Extension, build_ext
except ImportError:
    print('You need to install cython first - sudo pip install cython', file=sys.stderr)
    sys.exit(1)


# https://gist.github.com/smidm/ff4a2c079fed97a92e9518bd3fa4797c
def pkgconfig(*packages, **kw):
    """
    Query pkg-config for library compile and linking options. Return configuration in distutils
    Extension format.

    Usage:

    pkgconfig('opencv')

    pkgconfig('opencv', 'libavformat')

    pkgconfig('opencv', optional='--static')

    pkgconfig('opencv', config=c)

    returns e.g.

    {'extra_compile_args': [],
     'extra_link_args': [],
     'include_dirs': ['/usr/include/ffmpeg'],
     'libraries': ['avformat'],
     'library_dirs': []}

     Intended use:

     distutils.core.Extension('pyextension', sources=['source.cpp'], **c)

     Set PKG_CONFIG_PATH environment variable for nonstandard library locations.

    based on work of Micah Dowty (http://code.activestate.com/recipes/502261-python-distutils-pkg-config/)
    """
    config = kw.setdefault('config', {})
    optional_args = kw.setdefault('optional', '')
    # { <distutils Extension arg>: [<pkg config option>, <prefix length to strip>], ...}
    flag_map = {'include_dirs': ['--cflags-only-I', 2],
                'library_dirs': ['--libs-only-L', 2],
                'libraries': ['--libs-only-l', 2],
                'extra_compile_args': ['--cflags-only-other', 0],
                'extra_link_args': ['--libs-only-other', 0],
                }
    for package in packages:
        for distutils_key, (pkg_option, n) in flag_map.items():
            items = subprocess.check_output(['pkg-config', optional_args, pkg_option, package]).decode('utf8').split()
            config.setdefault(distutils_key, []).extend([i[n:] for i in items])
    return config

# Poppler 0.72.0+ GooString.h uses c_str() instead of getCString()
def use_poppler_cstring(path):
    for el in path.split(os.path.sep)[::-1]:
        version = el.split('.')
        if len(version) == 3 and (int(version[0]) > 0 or int(version[1]) >= 72):
            return True
    return False

# Mac OS build fix:
mac_compile_args = ["-std=c++11", "-stdlib=libc++", "-mmacosx-version-min=10.7"]
POPPLER_ROOT = os.environ.get('POPPLER_ROOT', None)
if POPPLER_ROOT:
    POPPLER_CPP_LIB_DIR = os.path.join(POPPLER_ROOT, 'cpp/')
    poppler_ext = Extension('pdfparser-clv.poppler', ['pdfparser-clv/poppler.pyx'], language='c++',
                            extra_compile_args=mac_compile_args if sys.platform == 'darwin' else ["-std=c++11"],
                            include_dirs=[POPPLER_ROOT, os.path.join(POPPLER_ROOT, 'poppler')],
                            library_dirs=[POPPLER_ROOT, POPPLER_CPP_LIB_DIR],
                            runtime_library_dirs=['$ORIGIN'],
                            libraries=['poppler','poppler-cpp'],
                            cython_compile_time_env={'USE_CSTRING': use_poppler_cstring(POPPLER_ROOT)})
    package_data = {'pdfparser-clv': ['*.so.*', 'pdfparser-clv/*.so.*']}
else:
    poppler_config = pkgconfig("poppler", "poppler-cpp")
    # Mac OS build fix:
    if sys.platform == 'darwin':
        poppler_config.setdefault('extra_compile_args', []).extend(mac_compile_args)
        poppler_config.setdefault('extra_link_args', []).extend(mac_compile_args)

    poppler_config.setdefault('cython_compile_time_env', {}).update({
        'USE_CSTRING': use_poppler_cstring(poppler_config['include_dirs'][0])
    })
    poppler_ext = Extension('pdfparser-clv.poppler', ['pdfparser-clv/poppler.pyx'], language='c++', **poppler_config)
    package_data = {}

# get version from package
pkg_file= os.path.join(os.path.split(__file__)[0], 'pdfparser-clv', '__init__.py')
m=re.search(r"__version__\s*=\s*'([\d.]+)'", open(pkg_file).read())
if not m:
    print (sys.stderr, 'Cannot find version of package')
    sys.exit(1)
version= m.group(1)

setup(name='pdfparser-clv',
      version = version,
      classifiers=[
          # How mature is this project? Common values are
          #   3 - Alpha
          #   4 - Beta
          #   5 - Production/Stable
          'Development Status :: 4 - Beta',

          # Indicate who your project is intended for
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries :: Python Modules',

          'License :: OSI Approved :: Apple Public Source License',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          
      ],
      description="python bindings for poppler",
      long_description="Binding for libpoppler with a focus on fast text extraction from PDF documents.",
      keywords='poppler pdf parsing mining extracting',
      url='https://github.com/nghiapq77/pdfparser',
      install_requires=['cython', ],
      packages=['pdfparser-clv', ],
      package_data=package_data,
      include_package_data=True,
      cmdclass={"build_ext": build_ext},
      ext_modules=[poppler_ext], # a workaround since Extension is an old-style class
                                 # removed cythonize for the list in ext_modules
      zip_safe=False
      )