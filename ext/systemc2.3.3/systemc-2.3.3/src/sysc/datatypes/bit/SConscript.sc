# SCons config file for building systemc lib

Import('systemc', 'SystemCSource')

SystemCSource(
    'sc_bit.cpp',
    'sc_bv_base.cpp',
    'sc_logic.cpp',
    'sc_lv_base.cpp',
)
