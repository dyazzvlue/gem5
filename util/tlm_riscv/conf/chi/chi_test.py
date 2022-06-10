# Copyright (c) 2015, University of Kaiserslautern
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER
# OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import m5
from m5.objects import *
from m5.util import addToPath, fatal, warn
import argparse

addToPath('../../../../configs')
addToPath('../../../../configs/common/')

from common import Options

parser = argparse.ArgumentParser()
Options.addCommonOptions(parser)
Options.addSEOptions(parser)

args = parser.parse_args()
np = args.num_cpus
multiprocesses =[]
multibinary = []

#
# +------- ----+  +------- ----+      ^
# | TimingCPU0 |  | TimingCPU1 |      |
# +------+-----+  +------+-----+      |
#        |               |            |
#        |               |            |
# +------v-----+  +------v-----+      |gem5 World
# |  MemBus0   |  |  MemBus1   |      |
# +-----+------+  +-----+------+      |
#       |               |             |
#       |               |             v
# +-----v------+  +-----v------+      Exteral Port
# |Transactor0 |  |Transactor1 |      ^
# +-----+------+  +-----+------+      |
#       |               |             | TLM world
#       |               |             |
# +-----v------+  +-----v------+      ----------
# | chi-cache0 |  | chi-cache1 |      |
# +-----+------+  +-----+------+      |
#       |               |             |
#       |               |             |
# +-----v---------------v------+      |
# |     CHI Interconnet        |      |
# +-------------+--------------+      | Xlinx CHI lib
#               |                     |
#               |                     |
# +-------------v--------------+      |
# |         Slave node         |      |
# +-------------+--------------+      |
#               |                     |
# +-------------v--------------+      -----------
# |       Simple memory        |      | Memory model based on sc_module
# +-------------+--------------+      v

# Create a system with a Crossbar and a TrafficGenerator as CPU:
system = System()
system.membus = [SystemXBar(width = 16) for i in range(np)]

system.physmem = SimpleMemory() # This must be instanciated, even if not needed

system.cpu =  [TimingSimpleCPU(cpu_id=i) for i in range(np)]
system.clk_domain = SrcClockDomain(clock = '1.5GHz',
    voltage_domain = VoltageDomain(voltage = '1V'))

isa = str(m5.defines.buildEnv['TARGET_ISA']).lower()
thispath = os.path.dirname(os.path.realpath(__file__))

binary = os.path.join(thispath, '../../', 'testcase/hello/rv64_hello')
multibinary.append(binary)

# Create a external TLM port:
system.tlm0 = ExternalSlave()
system.tlm0.addr_ranges = [AddrRange('512MB')]
system.tlm0.port_type = "tlm_slave"
system.tlm0.port_data = "transactor0"

system.tlm1 = ExternalSlave()
system.tlm1.addr_ranges = [AddrRange('512MB')]
system.tlm1.port_type = "tlm_slave"
system.tlm1.port_data = "transactor1"

# Route the connections:
for i in range(np):
    system.cpu[i].icache_port = system.membus[i].cpu_side_ports
    system.cpu[i].dcache_port = system.membus[i].cpu_side_ports
    system.cpu[i].createInterruptController()

system.membus[0].mem_side_ports = system.tlm0.port
system.membus[1].mem_side_ports = system.tlm1.port

# system.system_port = system.membus.cpu_side_ports

for i in range(np):
    # Create a process for a simple "Hello World" application
    process = Process(pid = 100 + i)
    # Set the command
    # cmd is a list which begins with the executable (like argv)
    if (np > 1):
        process.cmd = [binary]
    else:
        process.cmd = [binary]
    multiprocesses.append(process)
    # Set the cpu to use the process as its workload and create thread contexts
    system.cpu[i].workload = multiprocesses[i]
    system.cpu[i].createThreads()

if (np > 1 ):
    #mp0_path = multiprocesses[0].executable
    #system.workload = SEWorkload.init_compatible(mp0_path)
    system.workload = SEWorkload.init_compatible(binary)
else:
    system.workload = SEWorkload.init_compatible(binary)


# Start the simulation:
root = Root(full_system = False, system = system)
root.system.mem_mode = 'timing'

m5.instantiate()
m5.simulate() #Simulation time specified later on commandline
