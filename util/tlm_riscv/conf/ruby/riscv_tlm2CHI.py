import argparse
import sys

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.util import addToPath, fatal, warn
from m5.params import NULL

addToPath('../../../../configs')
addToPath('../../../../configs/common/')
addToPath('../../../../configs/ruby/')
addToPath('../../../../configs/network/')
from common import Options
from ruby import Ruby
from ruby import CHI
parser = argparse.ArgumentParser()
Options.addCommonOptions(parser)
Options.addSEOptions(parser)
Ruby.define_options(parser)

args = parser.parse_args()
np = args.num_cpus
multiprocesses =[]
multibinary = []

system = System()
system.cpu = [TimingSimpleCPU(cpu_id=i) for i in range(np)]
system.mem_mode = 'timing'
# Create a top-level voltage domain
system.voltage_domain = VoltageDomain(voltage = args.sys_voltage)

# Create a source clock for the system and set the clock period
system.clk_domain = SrcClockDomain(clock =  args.sys_clock,
                                   voltage_domain = system.voltage_domain)

# Create a CPU voltage domain
system.cpu_voltage_domain = VoltageDomain()

# Create a separate clock domain for the CPUs
system.cpu_clk_domain = SrcClockDomain(clock = args.cpu_clock,
                                       voltage_domain =
                                       system.cpu_voltage_domain)
for cpu in system.cpu:
    cpu.clk_domain = system.cpu_clk_domain

 # create a bus and memory
system.membus = SystemXBar()

system.mem_ranges = [AddrRange('512MB')]
#system.mem_ctrl = MemCtrl()
#system.mem_ctrl.dram = DDR3_1600_8x8()
#system.mem_ctrl.dram.range = system.mem_ranges[0]
#system.mem_ctrl.port = system.membus.mem_side_ports

system.physmem = SimpleMemory()
system.tlm = ExternalSlave()
#system.tlm.addr_ranges = [AddrRange('512MB')]
system.tlm.addr_ranges = system.mem_ranges
system.tlm.port_type = "tlm_slave"
system.tlm.port_data = "transactor"
system.membus.mem_side_ports = system.tlm.port

Ruby.create_system(args, False, system, None, [], None, None,
                    system.membus, AddrRange('512MB'),
                    system.membus.cpu_side_ports)
assert(args.num_cpus == len(system.ruby._cpu_ports))
system.ruby.clk_domain = SrcClockDomain(clock = args.ruby_clock,
                                    voltage_domain = system.voltage_domain)
for i in range(np):
    ruby_port = system.ruby._cpu_ports[i]
    # Create the interrupt controller and connect its ports to Ruby
    # Note that the interrupt controller is always present but only
    # in x86 does it have message ports that need to be connected
    system.cpu[i].createInterruptController()
    # Connect the cpu's cache ports to Ruby
    ruby_port.connectCpuPorts(system.cpu[i])

binary = os.path.join(thispath, "../../",
                    "testcase/array_add_2/riscv_test_new")
multibinary.append(binary)
for i in range(np):
    # Create a process for a simple "Hello World" application
    process = Process(pid = 100 + i)
    # Set the command
    # cmd is a list which begins with the executable (like argv)
    if (np > 1):
        process.cmd = [multibinary[i]]
    else:
        process.cmd = [binary]
    multiprocesses.append(process)
    # Set the cpu to use the process as its workload
    # and create thread contexts
    system.cpu[i].workload = multiprocesses[i]
    system.cpu[i].createThreads()

system.workload = SEWorkload.init_compatible(binary_test)
root = Root(full_system = False, system = system)
m5.instantiate()
m5.simulate()
