import re
import sys
import os
from conans import ConanFile, tools
from os.path import isdir

# This conan file is used to build gem5 simulator or gem5 shared library
# You can use below commands to build.

# python3 `which conan` create . demo/testing -o python_config="/usr/local/bin/python3-config"

# For virtual python environment, the scons path and python lib path might by given
# conan create . demo/tesing  \
#    -o python_lib_path="/nfs/site/proj/dpg/arch/perfhome/python/miniconda37/lib/" \
#    -o scons_path="/nfs/pdx/home/ziyangpe/.local/bin/scons"

class Gem5Conan(ConanFile):
    name = 'gem5'
    description = 'Gem5 Simulator'
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "fPIC": [True, False],
        "CONANPKG": ["ON", "OFF"],
        "buildGem5": [True, False],
        "buildLib": [True, False],
        "shared": [True, False],
        "buildvariants": ["debug", "opt", "fast"],
        "isa": ["RISCV", "ARM", "X86"],  # Other valid ISAS: MIPS, POWER, SPARC
        "cxxconfig": [True, False],
        "tcmalloc": [True, False],
        "systemc": [True, False],
        "duplicate_sources": [True, False],
        "python_config": "ANY",
        "scons_path": "ANY",
        "python_lib_path": "ANY"
    }
    default_options = {
        "fPIC": True,
        "CONANPKG": "OFF",
        "buildGem5": True,
        "buildLib": False,
        "shared": True,
        "buildvariants": "opt",
        "isa": "ARM",
        "cxxconfig": True,
        "tcmalloc": False,
        "systemc": False,
        "duplicate_sources": False,
        "python_config": "",
        "scons_path": "",
        "python_lib_path": ""
    }
    requires = ()
    version = "1.0"
    url = "https://gitlab.devtools.intel.com/syssim/cofluent" # TODO
    license = "Proprietary"
    exports_sources = (
        "include/*",
        "src/*",
        "lib/*"
    )

    generators = "scons"

    def build(self):
        build_dir = "build/" + str(self.options.isa)
        print("build_dir: ", build_dir)
        if not isdir(build_dir):
            os.makedirs(build_dir)
        build_tool = "scons"
        if self.options.scons_path != "" :
            # using named scons
            build_tool = str(self.options.scons_path)
        print("Using build tool: ", build_tool)
        # Set the building config
        # build_config = "-default=" + str(self.options.isa)
        build_config = ""
        build_config += ' --with-cxx-config' if self.options.cxxconfig == True else ''
        build_config += ' --without-tcmalloc' if self.options.tcmalloc == False else ''
        build_config += ' USE_SYSTEMC=0' if self.options.systemc == False else ''
        if self.options.python_lib_path != "":
            # using given python lib
            python_lib_path = ' --python_lib_path=' + str(self.options.python_lib_path)
            build_config += python_lib_path
        if self.options.python_config != "" :
            # using named python
            PYTHON_CONFIG = ' PYTHON_CONFIG=' + str(self.options.python_config)
            build_config += PYTHON_CONFIG

        if (self.options.buildGem5):
            with tools.chdir(build_dir):
                # just build basic gem5
                build_config += ' --duplicate-sources' if self.options.duplicate_sources == True else ''
                build_target = "gem5." + str(self.options.buildvariants)
                print("build_target: ", build_target)
                self.run('{} {} -u {} -j4'.format(build_tool, build_config, build_target))

        if (self.options.buildLib == True):
            build_lib_target = ""
            if (self.options.shared == True):  # recommended
                build_lib_target = "libgem5_opt.so"
                # For MAC / OSX this command should be used
                # build_lib_target = "libgem5_opt.dylib"
            else:
                build_lib_target = "libgem5_opt.a"
            with tools.chdir(build_dir):
                # build gem5 lib
                build_config += ' --duplicate-sources' # Otherwise, the header file will not in the include folder
                print("build_target: ", build_lib_target)
                self.run('{} {} -u {} -j4'.format(build_tool, build_config, build_lib_target))

    def package(self):
        isa = str(self.options.isa)
        build_dir = "build/" + isa + "/"
        cp_cmd = "cp -r " + build_dir + " conan_package/"
        os.system(cp_cmd)
        with tools.chdir("conan_package/"):
            rename_cmd = "mv " + isa + "/ include"
            os.system(rename_cmd)
            os.system("cp -r ../ext/gdbremote include/")
            os.system("./clean_include.bash")
           
            self.copy("*", dst = "include", src="include")
            self.copy("*.a", dst = "lib", keep_path=False)
            self.copy("*.so", dst = "lib", src="lib")

    def package_info(self):
        self.cpp_info.name = "gem5_shared_lib"
        self.cpp_info.components["libgem5_opt"].libs = ["gem5_opt"]
        
