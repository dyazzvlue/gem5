# SCons config file for building systemc lib

Import('systemc', 'SystemCSource')

SystemCSource(
    'sc_attribute.cpp',
    'sc_cthread_process.cpp',
    'sc_event.cpp',
    'sc_except.cpp',
    'sc_join.cpp',
    'sc_main.cpp',
    'sc_main_main.cpp',
    'sc_method_process.cpp',
    'sc_module.cpp',
    'sc_module_name.cpp',
    'sc_module_registry.cpp',
    'sc_name_gen.cpp',
    'sc_object.cpp',
    'sc_object_manager.cpp',
    'sc_phase_callback_registry.cpp',
    'sc_process.cpp',
    'sc_reset.cpp',
    'sc_sensitive.cpp',
    'sc_simcontext.cpp',
    'sc_spawn_options.cpp',
    'sc_thread_process.cpp',
    'sc_time.cpp',
    'sc_wait.cpp',
    'sc_wait_cthread.cpp',
    'sc_ver.cpp',
)
coroutine_lib = systemc['COROUTINE_LIB']
if coroutine_lib == 'qt':
    SystemCSource('sc_cor_qt.cpp')
elif coroutine_lib == 'pthreads':
    systemc.Append(CXXFLAGS=['-pthread'])
    systemc.Append(CFLAGS=['-pthread'])
    SystemCSource('sc_cor_pthread.cpp')
elif coroutine_lib == 'fiber':
    SystemCSource('sc_cor_fiber.cpp')
else:
    print('Unrecognized threading implementation \'%s\'' % coroutine_lib)
    Exit(1)
