# SCons config file for building systemc lib

Import('systemc', 'SystemCSource')

SystemCSource(
    'sc_trace.cpp',
    'sc_trace_file_base.cpp',
    'sc_vcd_trace.cpp',
    'sc_wif_trace.cpp',
)
