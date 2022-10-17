import re
import sys
import os
from conans import ConanFile, tools
from os.path import isdir

# python3 `which conan` create . demo/testing


class Gem5Conan(ConanFile):
    name = 'gem5'
    description = 'Gem5 Simulator'
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "fPIC": [True, False],
        "CONANPKG": ["ON", "OFF"],
        "buildLib": [True, False],
        "shared": [True, False],
        "buildvariants": ["debug", "opt", "fast"],
        "isa": ["RISCV", "ARM", "X86"],  # Other valid ISAS: MIPS, POWER, SPARC
        "cxxconfig": [True, False],
        "tcmalloc": [True, False],
        "systemc": [True, False]
    }
    default_options = {
        "fPIC": True,
        "CONANPKG": "OFF",
        "buildLib": True,
        "shared": True,
        "buildvariants": "opt",
        "isa": "RISCV",
        "cxxconfig": True,
        "tcmalloc": False,
        "systemc": False
    }
    version = "1.0"
    url = "https://gitlab.devtools.intel.com/syssim/cofluent"  # TODO
    license = "Proprietary"  # TODO

    exports_sources = (
        "build_opts/*",
        "build_tools/*",
        "configs/*",
        "ext/*",
        "include/*",
        "site_scons/*",
        "src/*",
        "util/*",
        "SConstruct",
        "COPYING",
        "LICENSE",
        "README"
    )

    generators = "scons"

    def build(self):
        build_target = "gem5." + str(self.options.buildvariants)
        build_lib_target = ""
        build_dir = "build/" + str(self.options.isa)
        print("build_target: ", build_target)
        print("build_dir: ", build_dir)
        if not isdir(build_dir):
            os.makedirs(build_dir)
        with tools.chdir(build_dir):
            # just build basic gem5
            # self.run('scons -u {} -j4'.format(build_target))
            pass

        if (self.options.buildLib == True):
            if (self.options.shared == True):  # recommended
                build_lib_target = "libgem5_opt.so"
                # For MAC / OSX this command should be used
                # build_lib_target = "libgem5_opt.dylib"
            else:
                build_lib_target = "libgem5_opt.a"
            #build_config = "-default=" + str(self.options.isa)
            build_config = ""
            build_config += ' --with-cxx-config' if self.options.cxxconfig == True else ''
            build_config += ' --without-tcmalloc' if self.options.tcmalloc == False else ''
            build_config += ' USE_SYSTEMC=0' if self.options.systemc == False else ''
            with tools.chdir(build_dir):
                # build gem5 lib
                self.run('scons {} -u {} -j4'.format(build_config, build_lib_target))

    def package(self):
        #self.copy("*.h", "include", src="include")  # TODO
        #self.copy("*.lib", "lib", keep_path=False)
        #self.copy("*.a", "lib", keep_path=False)
        self.copy("*", "RISCV", src="build/RISCV")

    def package_info(self):
        self.cpp_info.name = "gem5"
        self.cpp_info.components["libgem5_opt"].libs = ["gem5_opt"]
        
