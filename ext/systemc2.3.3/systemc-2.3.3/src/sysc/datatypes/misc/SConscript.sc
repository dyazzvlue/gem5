# SCons config file for building systemc lib

Import('systemc', 'SystemCSource')

SystemCSource(
    'sc_concatref.cpp',
    'sc_value_base.cpp',
)
