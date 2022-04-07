# SCons config file for building systemc lib

Import('systemc', 'SystemCSource')

SystemCSource(
    'sc_int_base.cpp',
    'sc_int_mask.cpp',
    'sc_length_param.cpp',
    'sc_nbexterns.cpp',
    'sc_nbutils.cpp',
    'sc_signed.cpp',
    'sc_uint_base.cpp',
    'sc_unsigned.cpp',
)
