# -*- coding: utf-8 -*-
# Copyright (c) 2015 Jason Power
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

""" This file creates a barebones system and executes 'hello', a simple Hello
World application.
See Part 1, Chapter 2: Creating a simple configuration script in the
learning_gem5 book for more information about this script.

IMPORTANT: If you modify this file, it's likely that the Learning gem5 book
           also needs to be updated. For now, email Jason <power.jg@gmail.com>

"""

import argparse

# import the m5 (gem5) library created when gem5 is built
import m5
# import all of the SimObjects
from m5.objects import *
from m5.util import addToPath, fatal, warn

addToPath('../../../configs')

# set cpu num
from common import Options

parser = argparse.ArgumentParser()
Options.addCommonOptions(parser)
Options.addSEOptions(parser)

args = parser.parse_args()
np = args.num_cpus
# np = 2

multiprocesses =[]
multibinary = []
# create the system we are going to simulate
system = System()

# Set the clock fequency of the system (and all of its children)
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '1GHz'
system.clk_domain.voltage_domain = VoltageDomain()

# Create a simple CPU
#system.cpu = TimingSimpleCPU()
system.cpu = [TimingSimpleCPU(cpu_id=i) for i in range(np)]

# Create a memory bus, a system crossbar, in this case
system.membus = SystemXBar()
# system.membus = IOXBar(width = 16)

# This must be instantiated when using systemc cosim, even if not needed
#system.physmem = SimpleMemory()
system.physmem = SimpleMemory(range = AddrRange('512MB'))

# Create a external TLM port:
#system.tlm = ExternalSlave()
#system.tlm.addr_ranges = [AddrRange('512MB')]
#system.tlm.port_type = "tlm_slave"
#system.tlm.port_data = "transactor"

#system.cpu.port = system.membus.slave
system.system_port = system.membus.cpu_side_ports
system.membus.mem_side_ports = system.physmem.port

# Hook the CPU ports up to the membus (membus.slave)
for i in range(np):
    system.cpu[i].icache_port = system.membus.cpu_side_ports
    system.cpu[i].dcache_port = system.membus.cpu_side_ports
    # create the interrupt controller for the CPU and connect to the membus
    system.cpu[i].createInterruptController()

# get ISA for the binary to run.
isa = str(m5.defines.buildEnv['TARGET_ISA']).lower()
print(isa)
# Default to running 'hello', use the compiled ISA to find the binary
# grab the specific path to the binary
thispath = os.path.dirname(os.path.realpath(__file__))

# abort with ExtraData invaild error
#binary = os.path.join(thispath, '../../../',
#                      'tests/test-progs/hello/bin/', isa, 'linux/hello')

# pass test
#binary1 = "/home/pzy/Documents/Spike/spike-testing/hello/rv64_hello"
#binary2 = "/home/pzy/Documents/Spike/spike-testing/test1/riscv64-test1"

binary1 = os.path.join(thispath, '../', 'testcase/array_add/riscv64-test1')
binary2 = os.path.join(thispath, '../', 'testcase/array_add/riscv64-test2')

binary3 = os.path.join(thispath, '../', 'testcase/array_add_2/riscv_test_new')
binary4 = os.path.join(thispath, '../',
                       'testcase/array_add_2/riscv_test_new_2')

binary5 = os.path.join(thispath, '../', 'testcase/threads/main')

multibinary.append(binary1)
multibinary.append(binary2)
multibinary.append(binary3)
multibinary.append(binary4)
multibinary.append(binary5)

for i in range(np):
    # Create a process for a simple "Hello World" application
    process = Process(pid = 100 + i)
    # Set the command
    # cmd is a list which begins with the executable (like argv)
    if (np > 1):
        # process.cmd = [multibinary[i]]
        process.cmd = [multibinary[4]]
    else:
        process.cmd = [binary1]
    multiprocesses.append(process)
    # Set the cpu to use the process as its workload and create thread contexts
    #system.cpu[i].workload = multiprocesses[i]
    system.cpu[i].workload = process
    system.cpu[i].createThreads()

if (np > 1 ):
    #mp0_path = multiprocesses[0].executable
    #system.workload = SEWorkload.init_compatible(mp0_path)
    system.workload = SEWorkload.init_compatible(binary1)
else:
    system.workload = SEWorkload.init_compatible(binary5)

# set up the root SimObject and start the simulation
root = Root(full_system = False, system = system)
root.system.mem_mode = 'timing'

# instantiate all of the objects we've created above
m5.instantiate()

#print("Beginning simulation!")
#exit_event = m5.simulate()
m5.simulate()
#print('Exiting @ tick %i because %s' % (m5.curTick(), exit_event.getCause()))
