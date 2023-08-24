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

addToPath('../../configs')
addToPath('../../configs/common/')

from common import Options
from common.Caches import *

parser = argparse.ArgumentParser()
Options.addCommonOptions(parser)
Options.addSEOptions(parser)

args = parser.parse_args()

use_tlm_port = False

multiprocesses =[]
multibinary = []
# create the system we are going to simulate
system = System()

# Set the clock fequency of the system (and all of its children)
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '1GHz'
system.clk_domain.voltage_domain = VoltageDomain()

# Create a memory bus, a system crossbar, in this case
system.membus = SystemXBar()
# TODO SystemXBar or CoherentXBar ?

system.system_port = system.membus.cpu_side_ports

# Create CPU cluster
# Craete BigCore/PerformanceCore
big_core_id = 0
big_core_num = 1
print("create big core ", big_core_id)
system.big_core = O3CPU(cpu_id=big_core_id)
system.big_core.createInterruptController()
system.big_core.icache = L1_ICache(size="64kB", cpu_cluster_id=big_core_id,
                                    snoop_group_id=big_core_id)
system.big_core.dcache = L1_DCache(size="64kB", cpu_cluster_id=big_core_id,
                                    snoop_group_id=big_core_id)   
system.big_core.tol2bus = L2XBar(width=64, clk_domain=system.clk_domain)
system.big_core.l2cache = L2Cache(size="1MB")
# bind Big Core devices
# bind L1 To Core
system.big_core.icache.cpu_side = system.big_core.icache_port
system.big_core.dcache.cpu_side = system.big_core.dcache_port
# bind L1 to L2Bus
system.big_core.icache.mem_side = system.big_core.tol2bus.cpu_side_ports
system.big_core.dcache.mem_side = system.big_core.tol2bus.cpu_side_ports
# bind L2Bus to L2Cache
system.big_core.tol2bus.mem_side_ports = system.big_core.l2cache.cpu_side
# bind L2Cache to system membus
system.big_core.l2cache.mem_side = system.membus.cpu_side_ports
# TODO
# addPMUs()   
print("big core init completed ", big_core_id)

# Create Workforce Cores
workforce_core_id = 1 # the id of first workforce core
workforce_core_num = 2
workforce_core_cluster_num = 1
system.workforce_core = [O3CPU(cpu_id=i+workforce_core_id ) for i in range(workforce_core_num * workforce_core_cluster_num)]
for i in range(workforce_core_cluster_num):
    for j in range(workforce_core_num):
        global_core_id = workforce_core_id + i * workforce_core_num + j
        core_id = i * workforce_core_num + j
        print("create workforce core " ,core_id)
        system.workforce_core[core_id].createInterruptController()
        system.workforce_core[core_id].icache = L1_ICache(size="64kB", cpu_cluster_id=global_core_id,
                                            snoop_group_id=global_core_id)
        system.workforce_core[core_id].dcache = L1_DCache(size="64kB", cpu_cluster_id=global_core_id,
                                            snoop_group_id=global_core_id)
        system.workforce_core[core_id].tol2bus = L2XBar(width=64, clk_domain=system.clk_domain)
        system.workforce_core[core_id].l2cache = L2Cache(size="512kB")
        # bind WorkForce Core devices
        # bind L1 to Core
        system.workforce_core[core_id].icache.cpu_side = system.workforce_core[core_id].icache_port
        system.workforce_core[core_id].dcache.cpu_side = system.workforce_core[core_id].dcache_port
        # bind L1 to L2Bus
        system.workforce_core[core_id].icache.mem_side = system.workforce_core[core_id].tol2bus.cpu_side_ports
        system.workforce_core[core_id].dcache.mem_side = system.workforce_core[core_id].tol2bus.cpu_side_ports
        # bind L2Bus to L2Cache
        system.workforce_core[core_id].tol2bus.mem_side_ports = system.workforce_core[core_id].l2cache.cpu_side
        # bind L2Cache to system membus
        system.workforce_core[core_id].l2cache.mem_side = system.membus.cpu_side_ports
        # TODO 
        # addPMUs()
    print("workforce_core cluster %d init complete" % (i))

# Create efficiency cores
efficiency_core_id = 3 # the id of first efficiency core
efficiency_core_num  = 4 # total number
# TODO maybe implanted as complexex - single or dual type
efficiency_core_cluster_num = 2 # as dual-core cluster 
efficiency_core_num_per_cluster = 2 # each cluster has 2 cores, these 2 cores share 1 L2 Cache
system.efficiency_core = [MinorCPU(cpu_id=i+efficiency_core_id ) for i in range(efficiency_core_num)]
system.efficiency_core_tol2bus = [L2XBar(width=64) for i in range(efficiency_core_cluster_num)]
system.efficiency_core_l2cache = [L2Cache(size="256kB") for i in range(efficiency_core_cluster_num)]
for i in range(efficiency_core_cluster_num):
    for j in range(workforce_core_num):
        global_core_id = efficiency_core_id + i * efficiency_core_num_per_cluster + j
        core_id = i * efficiency_core_num_per_cluster + j
        print("create efficiency core " ,core_id)
        system.efficiency_core[core_id].createInterruptController()
        system.efficiency_core[core_id].icache = L1_ICache(size="64kB", cpu_cluster_id=global_core_id,
                                            snoop_group_id=global_core_id)
        system.efficiency_core[core_id].dcache = L1_DCache(size="64kB", cpu_cluster_id=global_core_id,
                                            snoop_group_id=global_core_id)
        # bind Efficiency core devices
        # bind L1 to Core
        system.efficiency_core[core_id].icache.cpu_side = system.efficiency_core[core_id].icache_port
        system.efficiency_core[core_id].dcache.cpu_side = system.efficiency_core[core_id].dcache_port
        # bind L1 to L2Bus
        system.efficiency_core[core_id].icache.mem_side = system.efficiency_core_tol2bus[i].cpu_side_ports
        system.efficiency_core[core_id].dcache.mem_side = system.efficiency_core_tol2bus[i].cpu_side_ports
    # bind L2Bus to L2Cache
    system.efficiency_core_tol2bus[i].mem_side_ports = system.efficiency_core_l2cache[i].cpu_side
    # bind L2Cache to system membus
    system.efficiency_core_l2cache[i].mem_side = system.membus.cpu_side_ports
    # TODO 
    # addPMUs()
    print("efficiency_core cluster %d init complete" % (i))    

if (use_tlm_port):
    # This must be instantiated when using systemc cosim, even if not needed
    system.physmem = SimpleMemory()
    # Create a external TLM port:
    system.tlm = ExternalSlave()
    system.tlm.addr_ranges = [AddrRange('2048MB')]
    system.tlm.port_type = "tlm_slave"
    system.tlm.port_data = "transactor"
    system.membus.mem_side_ports = system.tlm.port
else:
    # Using pure Gem5 model
    system.mem_mode = 'timing'               # Use timing accesses
    system.mem_ranges = [AddrRange('2048MB')]
    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = DDR3_1600_8x8()
    system.mem_ctrl.dram.range = system.mem_ranges[0]
    system.mem_ctrl.port = system.membus.mem_side_ports

# get ISA for the binary to run.
#isa = str(m5.defines.buildEnv['TARGET_ISA']).lower()
#print("Current isa is ",isa)

thispath = os.path.dirname(os.path.realpath(__file__))

# abort with ExtraData invaild error
#binary = os.path.join(thispath, '../../../',
#                      'tests/test-progs/hello/bin/', isa, 'linux/hello')

binary = os.path.join(thispath,'hello')
#binary_stream = os.path.join(thispath, '../../', 'testcase/arm/stream/stream_arm')
#binary = os.path.join(thispath, '../../', 'testcase/hello/rv64_hello')

multibinary.append(binary)

#thread_process = Process()
#thread_process.cmd = [multibinary[0]]
default_pid = 100
process = Process(pid = 100 + big_core_id, output="big_core_output.log")
#process.cmd = [binary_stream]
process.cmd = [binary]
system.big_core.workload = process
system.big_core.createThreads()

for i in range(workforce_core_cluster_num):
    for j in range (workforce_core_num):
        global_core_id = workforce_core_id + i * workforce_core_num + j
        core_id = i * workforce_core_num + j
        current_pid = default_pid + global_core_id
        output_file = "workforce_core_output" + str(core_id)  +".log"
        # Create a process for a simple "Hello World" application
        process = Process(pid = current_pid, output=output_file)
        # Set the command
        # cmd is a list which begins with the executable (like argv)
        #process.cmd = [multibinary[0]]
        process.cmd = [binary]
        # Set the cpu to use the process as its workload and create thread contexts
        system.workforce_core[core_id].workload = process
        system.workforce_core[core_id].createThreads()

for i in range(efficiency_core_cluster_num):
    for j in range (efficiency_core_num_per_cluster):
        core_id = i * efficiency_core_num_per_cluster + j
        global_core_id = efficiency_core_id + i * efficiency_core_num_per_cluster + j
        current_pid = default_pid + global_core_id
        output_file = "efficiency_core_output" + str(core_id)  +".log"
        # Create a process for a simple "Hello World" application
        process = Process(pid = current_pid, output=output_file)
        # Set the command
        # cmd is a list which begins with the executable (like argv)
        #process.cmd = [multibinary[0]]
        process.cmd = [binary]
        # Set the cpu to use the process as its workload and create thread contexts
        system.efficiency_core[core_id].workload = process
        system.efficiency_core[core_id].createThreads()
system.workload = SEWorkload.init_compatible(binary)

# set up the root SimObject and start the simulation
root = Root(full_system = False, system = system)
root.system.mem_mode = 'timing'
# instantiate all of the objects we've created above
print("Begin instantiate")
m5.instantiate()

print("Beginning simulation!")
if (use_tlm_port == False):
    exit_event = m5.simulate()
    #m5.simulate()
    print('Exiting @ tick %i because %s' % (m5.curTick(), exit_event.getCause()))
