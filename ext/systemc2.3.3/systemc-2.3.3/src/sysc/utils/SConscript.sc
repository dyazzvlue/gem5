# SCons config file for building systemc lib

Import('systemc', 'SystemCSource')

SystemCSource(
    'sc_hash.cpp',
	'sc_list.cpp',
	'sc_mempool.cpp',
	'sc_pq.cpp',
	'sc_report.cpp',
	'sc_report_handler.cpp',
	'sc_stop_here.cpp',
	'sc_string.cpp',
	'sc_utils_ids.cpp',
	'sc_vector.cpp',
)
