# All rights reserved.
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Copyright (c) 2021 Huawei International
# Copyright (c) 2012-2014 Mark D. Hill and David A. Wood
# Copyright (c) 2009-2011 Advanced Micro Devices, Inc.
# Copyright (c) 2006-2007 The Regents of The University of Michigan
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

import argparse
import sys
from os import path

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.util import addToPath, fatal, warn
from m5.util.fdthelper import *

addToPath('../../../../configs')
addToPath('../../../../configs/common/')

from ruby import Ruby

from common.FSConfig import *
from common.SysPaths import *
from common.Benchmarks import *
from common import Simulation
from common import CacheConfig
from common import CpuConfig
from common import MemConfig
from common import ObjectList
from common.Caches import *
from common import Options

# ------------------------- Usage Instructions ------------------------- #
# Common system confirguration options (cpu types, num cpus, checkpointing
# etc.) should be supported
#
# Ruby not supported in this config file. Not tested on RISC-V FS Linux (as
# of 25 March 2021).
#
# Options (Full System):
# --kernel (required):          Bootloader + kernel binary (e.g. bbl with
#                               linux kernel payload)
# --disk-image (optional):      Path to disk image file. Not needed if using
#                               ramfs (might run into issues though).
# --virtio-rng (optional):      Enable VirtIO entropy source device
# --command-line (optional):    Specify to override default.
# --dtb-filename (optional):    Path to DTB file. Auto-generated if empty.
# --bare-metal (boolean):       Use baremetal Riscv (default False). Use this
#                               if bbl is built with "--with-dts" option.
#                               (do not forget to include bootargs in dts file)
#
# Not Used:
# --command-line-file, --script, --frame-capture, --os-type, --timesync,
# --dual, -b, --etherdump, --root-device, --ruby


# ----------------------- DTB Generation Function ---------------------- #

def generateMemNode(state, mem_range):
    node = FdtNode("memory@%x" % int(mem_range.start))
    node.append(FdtPropertyStrings("device_type", ["memory"]))
    node.append(FdtPropertyWords("reg",
        state.addrCells(mem_range.start) +
        state.sizeCells(mem_range.size()) ))
    return node

def generateDtb(system):
    state = FdtState(addr_cells=2, size_cells=2, cpu_cells=1)
    root = FdtNode('/')
    root.append(state.addrCellsProperty())
    root.append(state.sizeCellsProperty())
    root.appendCompatible(["riscv-virtio"])

    for mem_range in system.mem_ranges:
        root.append(generateMemNode(state, mem_range))

    sections = [*system.cpu, system.platform]

    for section in sections:
        for node in section.generateDeviceTree(state):
            if node.get_name() == root.get_name():
                root.merge(node)
            else:
                root.append(node)

    fdt = Fdt()
    fdt.add_rootnode(root)
    fdt.writeDtsFile(path.join(m5.options.outdir, 'device.dts'))
    fdt.writeDtbFile(path.join(m5.options.outdir, 'device.dtb'))

# ----------------------------- Add Options ---------------------------- #
parser = argparse.ArgumentParser()
Options.addCommonOptions(parser)
Options.addFSOptions(parser)
parser.add_argument("--bare-metal", action="store_true",
    help="Provide the raw system without the linux specific bits")
parser.add_argument("--dtb-filename", action="store", type=str,
    help="Specifies device tree blob file to use with device-tree-"\
        "enabled kernels")
parser.add_argument("--virtio-rng", action="store_true",
    help="Enable VirtIORng device")

# ---------------------------- Parse Options --------------------------- #
args = parser.parse_args()

# CPU and Memory
(CPUClass, mem_mode, FutureClass) = Simulation.setCPUClass(args)
#MemClass = Simulation.setMemClass(args) # TODO check what it does

np = args.num_cpus
#np = 1

kernel_path="/home/pzy/Documents/gem5/gem5/linux-kernel/riscv-bootloader-vmlinux-5.10"
disk_image_path="/home/pzy/Documents/gem5/gem5/linux-kernel/riscv-disk-img"
# ---------------------------- Setup System ---------------------------- #
# Default Setup
system = System()
mdesc = SysConfig(disks=args.disk_image, rootdev=args.root_device,
                        mem=args.mem_size, os_type=args.os_type)
system.mem_mode = mem_mode
system.mem_ranges = [AddrRange(start=0x80000000, size=mdesc.mem())]

system.workload = RiscvLinux()
system.workload.object_file = args.kernel

system.iobus = IOXBar()
system.membus = MemBus()

system.cpu_side_bus = [SystemXBar() for i in range(np)]
#system.cpu_side_bus = [IOXBar() for i in range(np)]
#system.cpu_side_bus = [MemBus() for i in range(np)]

#system.system_port = system.membus.cpu_side_ports
system.system_port = system.cpu_side_bus[0].cpu_side_ports # pass single core

# HiFive Platform
system.platform = HiFive()

# RTCCLK (Set to 100MHz for faster simulation)
system.platform.attachPlic()
system.platform.clint.num_threads = np # on chip device

system.platform.rtc = RiscvRTC(frequency=Frequency("100MHz"))  # on chip device
system.platform.clint.int_pin = system.platform.rtc.int_pin

# VirtIOMMIO
image = CowDiskImage(child=RawDiskImage(read_only=True), read_only=False)
image.child.image_file = mdesc.disks()[0]
system.platform.disk = RiscvMmioVirtIO( # off chip device
    vio=VirtIOBlock(image=image),
    interrupt_id=0x8,
    pio_size=4096,
    pio_addr=0x10008000
)

# VirtIORng
if args.virtio_rng:
    system.platform.rng = RiscvMmioVirtIO( # off chip device
        vio=VirtIORng(),
        interrupt_id=0x8,   
        pio_size=4096,
        pio_addr=0x10007000
    )

# cpu <=> cpu_bus <=> cpu_side_bridge <=> membus
system.cpu_side_bridge = [Bridge(delay='50ns') for i in range(np)] 
system.on_chip_bridge = [Bridge(delay='10ns') for i in range(np)] 
system.cpu_on_chip_side_bus = SystemXBar()
for i in range(np):
    system.cpu_side_bridge[i].mem_side_port = system.membus.cpu_side_ports
    system.cpu_side_bridge[i].cpu_side_port = system.cpu_side_bus[i].mem_side_ports
   # system.cpu_side_bridge[i].ranges = system.platform._off_chip_ranges() + system.platform._on_chip_ranges()
    system.cpu_side_bridge[i].ranges = system.platform._off_chip_ranges()
    
    system.on_chip_bridge[i].mem_side_port = system.cpu_on_chip_side_bus.cpu_side_ports
    system.on_chip_bridge[i].cpu_side_port = system.cpu_side_bus[i].mem_side_ports
    system.on_chip_bridge[i].ranges = system.platform._on_chip_ranges()

system.bridge = Bridge(delay='50ns')
system.bridge.mem_side_port = system.iobus.cpu_side_ports
system.bridge.cpu_side_port = system.membus.mem_side_ports
system.bridge.ranges = system.platform._off_chip_ranges()


#system.platform.attachOnChipIO(system.membus)
#system.platform.attachOnChipIO(system.cpu_side_bus[0]) #  pass single core
system.platform.attachOnChipIO(system.cpu_on_chip_side_bus)
#system.platform.attachOnChipIO(system.iobus)
system.platform.attachOffChipIO(system.iobus)

system.platform.attachPlic()
system.platform.setNumCores(np)

# ---------------------------- Default Setup --------------------------- #

# Set the cache line size for the entire system
system.cache_line_size = args.cacheline_size

# Create a top-level voltage domain
system.voltage_domain = VoltageDomain(voltage = args.sys_voltage)

# Create a source clock for the system and set the clock period
system.clk_domain = SrcClockDomain(clock =  args.sys_clock,
        voltage_domain = system.voltage_domain)

# Create a CPU voltage domain
system.cpu_voltage_domain = VoltageDomain()

# Create a source clock for the CPUs and set the clock period
system.cpu_clk_domain = SrcClockDomain(clock = args.cpu_clock,
                                            voltage_domain =
                                            system.cpu_voltage_domain)

system.workload.object_file = args.kernel

# NOTE: Not yet tested
if args.script is not None:
    system.readfile = args.script

system.init_param = args.init_param

system.cpu = [CPUClass(clk_domain=system.cpu_clk_domain, cpu_id=i)
                for i in range(np)]
for i in range (np):
    system.cpu[i].createInterruptController()
    icache = L1_ICache(size="32kB")
    dcache = L1_DCache(size="32kB")
    iwalkcache = PageTableWalkerCache()
    dwalkcache = PageTableWalkerCache()
    system.cpu[i].addPrivateSplitL1Caches(icache, dcache,
                                            iwalkcache, dwalkcache)
    
    system.cpu[i].connectBus(system.cpu_side_bus[i])


"""
if args.caches or args.l2cache:
    # By default the IOCache runs at the system clock
    system.iocache = IOCache(addr_ranges = system.mem_ranges)
    system.iocache.cpu_side = system.iobus.mem_side_ports
    system.iocache.mem_side = system.membus.cpu_side_ports
elif not args.external_memory_system:
    print("Not external memory")
    system.iobridge = Bridge(delay='50ns', ranges = system.mem_ranges)
    system.iobridge.cpu_side_port = system.iobus.mem_side_ports
    system.iobridge.mem_side_port = system.membus.cpu_side_ports
"""
system.iocache = IOCache(addr_ranges = system.mem_ranges)
system.iocache.cpu_side = system.iobus.mem_side_ports
#system.iocache.mem_side = system.membus.cpu_side_ports
#system.iocache.mem_side = system.cpu_on_chip_side_bus.cpu_side_ports
system.iocache.mem_side = system.cpu_side_bus[0].cpu_side_ports
#system.iobridge = Bridge(delay='50ns', ranges = system.mem_ranges)
#system.iobridge.cpu_side_port =  system.iobus.mem_side_ports
#system.iobridge.mem_side_port = system.membus.cpu_side_ports

# Sanity check
if args.simpoint_profile:
    if not ObjectList.is_noncaching_cpu(CPUClass):
        fatal("SimPoint generation should be done with atomic cpu")
    if np > 1:
        fatal("SimPoint generation not supported with more than one CPUs")

for i in range(np):
    if args.simpoint_profile:
        system.cpu[i].addSimPointProbe(args.simpoint_interval)
    if args.checker:
        system.cpu[i].addCheckerCpu()
    if not ObjectList.is_kvm_cpu(CPUClass):
        if args.bp_type:
            bpClass = ObjectList.bp_list.get(args.bp_type)
            system.cpu[i].branchPred = bpClass()
        if args.indirect_bp_type:
            IndirectBPClass = ObjectList.indirect_bp_list.get(
                args.indirect_bp_type)
            system.cpu[i].branchPred.indirectBranchPred = \
                IndirectBPClass()
    system.cpu[i].createThreads()

# ----------------------------- PMA Checker ---------------------------- #

uncacheable_range = [
    *system.platform._on_chip_ranges(),
    *system.platform._off_chip_ranges()
]

# PMA checker can be defined at system-level (system.pma_checker)
# or MMU-level (system.cpu[0].mmu.pma_checker). It will be resolved
# by RiscvTLB's Parent.any proxy
for cpu in system.cpu:
    cpu.mmu.pma_checker = PMAChecker(uncacheable=uncacheable_range)

# --------------------------- DTB Generation --------------------------- #

if not args.bare_metal:
    if args.dtb_filename:
        system.workload.dtb_filename = args.dtb_filename
    else:
        generateDtb(system)
        system.workload.dtb_filename = path.join(
            m5.options.outdir, 'device.dtb')

    # Default DTB address if bbl is bulit with --with-dts option
    system.workload.dtb_addr = 0x87e00000

# Linux boot command flags
    if args.command_line:
        system.workload.command_line = args.command_line
    else:
        kernel_cmd = [
            "console=ttyS0",
            "root=/dev/vda",
            "ro"
        ]
        system.workload.command_line = " ".join(kernel_cmd)

# ---------------------------- Default Setup --------------------------- #

if args.elastic_trace_en and args.checkpoint_restore == None and \
    not args.fast_forward:
    CpuConfig.config_etrace(CPUClass, system.cpu, args)

#CacheConfig.config_cache(args, system)

#MemConfig.config_mem(args, system)
#system.physmem = SimpleMemory()
system.rnf0 = m5.objects.ExternalSlave(
            port_type="tlm_slave",
            port_data="transactor0",
            port=system.cpu_side_bus[0].mem_side_ports,
            addr_ranges=system.mem_ranges)

if (np == 2):
    system.rnf1 = m5.objects.ExternalSlave(
                port_type="tlm_slave",
                port_data="transactor1",
                port=system.cpu_side_bus[1].mem_side_ports,
                addr_ranges=system.mem_ranges)

system.external_tlm_memory =  m5.objects.ExternalSlave(
            port_type="tlm_slave",
            port_data="external_tlm_memory",
            port=system.membus.mem_side_ports,
            addr_ranges=system.mem_ranges)
#for i in range(np):
    #system.cpu[i].icache_port = system.cpu_side_bus[i].cpu_side_ports
    #system.cpu[i].dcache_port = system.cpu_side_bus[i].cpu_side_ports
    #system.cpu[i].createInterruptController()
    #system.cpu[i].connectBus(system.cpu_side_bus[i])
    

system.workload.addr_check = False

root = Root(full_system=True, system=system)

Simulation.setWorkCountOptions(system, args)
Simulation.run(args, root, system, FutureClass)
