# SCons config file for building systemc lib

from __future__ import print_function

import os

Import('systemc', 'SystemCSource')

coroutine_lib = systemc['COROUTINE_LIB']
if coroutine_lib == 'qt':
    SystemCSource('qt.c')
    qt_arch = systemc.get('QT_ARCH', None)
    if not qt_arch:
        print('No architecture selected for the QT coroutine library.')
        Exit(1)
    if qt_arch in ('i386', 'iX86_64'):
        SystemCSource(os.path.join('md',qt_arch + '.s'))
    else:
        print('Don\'t know what to do for QT arch %s.' % qt_arch)
        Exit(1)
