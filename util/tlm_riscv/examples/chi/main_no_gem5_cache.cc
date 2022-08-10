/*
 * Copyright (c) 2015, University of Kaiserslautern
 * Copyright (c) 2016, Dresden University of Technology (TU Dresden)
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its
 *    contributors may be used to endorse or promote products derived from
 *    this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
 * TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER
 * OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/**
 * @file
 *
 *  Example top level file for SystemC-TLM integration with C++-only
 *  instantiation.
 *
 *  Using external CHI models
 *
 */

#include <systemc>
#include <tlm>

using namespace sc_core;
using namespace sc_dt;

#include "bus_wrapper.h"
#include "chi-memory.h"
#include "cli_parser.hh"
#include "report_handler.hh"
#include "sim_control.hh"
#include "simple_bus.h"
#include "slave_transactor.hh"
#include "stats.hh"
#include "tlm-modules/cache-chi.h"
#include "tlm-modules/iconnect-chi.h"
#include "tlm-modules/sn-chi.h"
#include "txn_router.h"

#define NODE_ID_RNF0 0
#define NODE_ID_RNF1 1

//#define CACHE_SIZE 256
#define CACHE_SIZE 64

/*
GEM5 <-> CHI interface
System Architecture:
+------- ----+  +------- ----+      ^
| TimingCPU0 |  | TimingCPU1 |      | Tips: No gem5 cache here
+------+-----+  +------+-----+      |
       |               |            |
       |               |            |
+------v---------------v-----+      |gem5 World
|           MemBus           |      |
+-----+---------------+------+      |
              |              |      |
              |              |      v
+-------------V--------------+      Exteral Port
|        Transactor          |      ^
+-----+---------------+------+      |
      |               |             |
    socket0        socket1          |
      |               |             |
+-----v------+  +-----v------+      |
|txn_router0 |  |txn_router1 |      | TLM world
+-----+------+  +-----+------+      |
      |               |             |
      |               |             |
+-----v------+  +-----v------+      ----------
| chi-cache0 |  | chi-cache1 |      |
+-----+------+  +-----+------+      |
      |               |             |
      |               |             |
+-----v---------------v------+      |
|     CHI Interconnet        |      |
+-------------+--------------+      | Xlinx CHI lib
              |                     |
              |                     |
+-------------v--------------+      |
|         Slave node         |      |
+-------------+--------------+      |
              |                     |
+-------------v--------------+      -----------
|       Simple memory        |      | Memory model based on sc_module
+-------------+--------------+      v

*/

template<typename T1, typename T2>
void connect_rn(T1& rn, T2& port_RN_F) {
        rn.txreq_init_socket(port_RN_F->rxreq_tgt_socket);
        rn.txdat_init_socket(port_RN_F->rxdat_tgt_socket);
        rn.txrsp_init_socket(port_RN_F->rxrsp_tgt_socket);
        port_RN_F->txsnp_init_socket(rn.rxsnp_tgt_socket);
        port_RN_F->txrsp_init_socket(rn.rxrsp_tgt_socket);
        port_RN_F->txdat_init_socket(rn.rxdat_tgt_socket);
}

template<typename T1, typename T2>
void connect_sn(T1& sn, T2& port_SN) {
        port_SN->txreq_init_socket(sn.rxreq_tgt_socket);
        port_SN->txdat_init_socket(sn.rxdat_tgt_socket);
        sn.txrsp_init_socket(port_SN->rxrsp_tgt_socket);
        sn.txdat_init_socket(port_SN->rxdat_tgt_socket);
}

int
sc_main(int argc, char **argv)
{
    CliParser parser;
    parser.parse(argc, argv);

    //int core_num = parser.getCpuCores();
    int core_num = 2;

    assert (core_num > 0 && core_num <= 2);

    sc_core::sc_report_handler::set_handler(reportHandler);

    Gem5SystemC::Gem5SimControl sim_control("gem5",
                                           parser.getConfigFile(),
                                           parser.getSimulationEnd(),
                                           parser.getDebugFlags());

    //unsigned long long int memorySize = 512*1024*1024ULL;
    unsigned long long int memorySize = 2048*1024*1024ULL;
    unsigned long long int mem_start_addr = 0x00000000;
    // For FS model, memory address should start at 0x80000000
    // using  "-o 2147483648"
    if (parser.getMemoryOffset() != 0){
      mem_start_addr = parser.getMemoryOffset();
    }
    //unsigned long long int mem_start_addr = 0x80000000; // FS mode
    unsigned long long int mem_end_addr = mem_start_addr + memorySize - 1;
    
    int socket_num = core_num; 
    // key: socket id , value: core num
    std::map<uint32_t, std::vector<int>> socket_map = {
        {0, {0,1}}, {1,{2,3}}
        //{0, {0,1,2,3,4,5,6}}
    };

    Gem5SystemC::Gem5SlaveTransactor_Multi transactor("transactor",
            "transactor", socket_num, false);
    transactor.setSocketCoreMap(socket_map);
    /*
        Setting external systemc world
    */

    SimpleBus<2,1> bus("SimpleBus");

    bus.ports[0] = new PortMapping(mem_start_addr, mem_end_addr);

    TxnRouter txn_router0("txn_router0", mem_start_addr,
                         memorySize, parser.getVerboseFlag());
    TxnRouter txn_router1("txn_router1", mem_start_addr,
                         memorySize, parser.getVerboseFlag());

    // Using CHI cache model
    cache_chi<NODE_ID_RNF0, CACHE_SIZE> rnf0("rnf0");
    cache_chi<NODE_ID_RNF1, CACHE_SIZE> rnf1("rnf1");

    iconnect_chi<> icn("iconnect_chi");
    SlaveNode_F<> sn("sn");

    SimpleMemory mem("SimpleMemory", memorySize, mem_start_addr, mem_end_addr);
    std::cout << "Try binding ports " << std::endl;
    /*
        connect chi components
    */
    // connenct gem5 world to txn_router
    bus.isocks[0].bind(mem.tsock);

    transactor.sockets[0].bind(txn_router0.tsock);
    transactor.sockets[1].bind(txn_router1.tsock);

    txn_router0.isock_mem(rnf0.target_socket);
    txn_router1.isock_mem(rnf1.target_socket);

    txn_router0.isock_bus(bus.tsocks[0]);
    txn_router1.isock_bus(bus.tsocks[1]);

    connect_rn(rnf0, icn.port_RN_F[0]);
    connect_rn(rnf1, icn.port_RN_F[1]);

    connect_sn(sn, icn.port_SN);

    sn.init_socket(mem.tsock_sn);

    transactor.sim_control.bind(sim_control);

    SC_REPORT_INFO("sc_main", "Start of Simulation");

    sc_core::sc_start();

    SC_REPORT_INFO("sc_main", "End of Simulation");

    CxxConfig::statsDump();

    return EXIT_SUCCESS;
}
