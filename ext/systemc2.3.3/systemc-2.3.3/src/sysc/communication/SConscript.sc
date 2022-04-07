# SCons config file for building systemc lib

Import('systemc', 'SystemCSource')

SystemCSource(
    'sc_clock.cpp',
    'sc_event_finder.cpp',
    'sc_event_queue.cpp',
    'sc_export.cpp',
    'sc_interface.cpp',
    'sc_mutex.cpp',
    'sc_port.cpp',
    'sc_prim_channel.cpp',
    'sc_semaphore.cpp',
    'sc_signal.cpp',
    'sc_signal_ports.cpp',
    'sc_signal_resolved.cpp',
    'sc_signal_resolved_ports.cpp',
)
