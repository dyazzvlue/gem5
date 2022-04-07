# SCons config file for building systemc lib

Import('systemc', 'SystemCSource')

SystemCSource(
    'sc_fxcast_switch.cpp',
    'sc_fxdefs.cpp',
    'sc_fxnum.cpp',
    'sc_fxnum_observer.cpp',
    'sc_fxtype_params.cpp',
    'sc_fxval.cpp',
    'sc_fxval_observer.cpp',
    'scfx_mant.cpp',
    'scfx_pow10.cpp',
    'scfx_rep.cpp',
    'scfx_utils.cpp',
)
