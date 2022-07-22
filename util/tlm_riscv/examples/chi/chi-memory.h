#ifndef RISCV_ISA_MEMORY_H
#define RISCV_ISA_MEMORY_H

#include <stdint.h>
#include <tlm_utils/simple_target_socket.h>

#include <iostream>
#include <systemc>

#include <boost/iostreams/device/mapped_file.hpp>

#include "load_if.h"
#include "simple_bus.h"

struct SimpleMemory : public sc_core::sc_module, public load_if
{
        tlm_utils::simple_target_socket<SimpleMemory> tsock;
        tlm_utils::simple_target_socket<SimpleMemory> tsock_sn;

        uint8_t *data;
        uint32_t size;
        bool read_only;
        sc_core::sc_mutex access_mux;
        uint64_t mem_start_addr;
        uint64_t mem_end_addr;

        SimpleMemory(sc_core::sc_module_name, uint32_t size,
                uint64_t mem_start_addr, uint64_t mem_end_addr,
                bool read_only = false)
            : data(new uint8_t[size]()), size(size), mem_start_addr(mem_start_addr),
                mem_end_addr(mem_end_addr), read_only(read_only) {
                assert(mem_end_addr == mem_start_addr + size -1 );
                tsock.register_b_transport(this, &SimpleMemory::transport_bus);
                tsock.register_get_direct_mem_ptr(this, &SimpleMemory::get_direct_mem_ptr);
                tsock.register_transport_dbg(this, &SimpleMemory::transport_dbg);
                tsock_sn.register_b_transport(this, &SimpleMemory::transport);
                tsock_sn.register_get_direct_mem_ptr(this, &SimpleMemory::get_direct_mem_ptr);
                tsock_sn.register_transport_dbg(this, &SimpleMemory::transport_dbg);
        }

        ~SimpleMemory(void) {
                delete[] data;
        }

        void load_data(const char *src, uint64_t dst_addr, size_t n) override {
                assert(dst_addr + n <= size);
                memcpy(&data[dst_addr], src, n);
        }

        void load_zero(uint64_t dst_addr, size_t n) override {
                assert(dst_addr + n <= size);
                memset(&data[dst_addr], 0, n);
        }

        void load_binary_file(const std::string &filename, unsigned addr) {
                boost::iostreams::mapped_file_source f(filename);
                assert(f.is_open());
                write_data(addr, (const uint8_t *)f.data(), f.size());
        }

        void write_data(unsigned addr, const uint8_t *src, unsigned num_bytes) {
                assert(addr + num_bytes <= size);
                memcpy(data + addr, src, num_bytes);
        }

        void read_data(unsigned addr, uint8_t *dst, unsigned num_bytes) {
                assert(addr + num_bytes <= size);
                memcpy(dst, data + addr, num_bytes);
        }

        void transport_bus(tlm::tlm_generic_payload &trans, sc_core::sc_time &delay) {
                access_mux.lock();
                transport(trans, delay);
                access_mux.unlock();
        }

        void transport(tlm::tlm_generic_payload &trans, sc_core::sc_time &delay) {
                transport_dbg(trans);
                delay += sc_core::sc_time(10, sc_core::SC_NS);
                trans.set_dmi_allowed(true);
                trans.set_response_status(tlm::TLM_OK_RESPONSE);
        }

        unsigned transport_dbg(tlm::tlm_generic_payload &trans) {
                tlm::tlm_command cmd = trans.get_command();
                unsigned addr = trans.get_address();
                auto *ptr = trans.get_data_ptr();
                auto len = trans.get_data_length();
                unsigned int streaming_width = trans.get_streaming_width();
                unsigned char *be = trans.get_byte_enable_ptr();
                unsigned int be_len = trans.get_byte_enable_length();

                if (streaming_width == 0) {
                        streaming_width = len;
                }
                if ((addr + len) > (mem_end_addr)) {
                        trans.set_response_status(tlm::TLM_ADDRESS_ERROR_RESPONSE);
                        SC_REPORT_FATAL("Memory", "Unsupported access\n");
                        return 0;
                }

                if (trans.get_command() == tlm::TLM_READ_COMMAND) {
                        read_data(addr - mem_start_addr, ptr, len);
                }
                else if (cmd == tlm::TLM_WRITE_COMMAND) {
                        write_data(addr - mem_start_addr, ptr, len);
                }
                else{
                        SC_REPORT_FATAL("Memory", "Unsupported tlm command\n");
                }

                return len;
        }

        bool get_direct_mem_ptr(tlm::tlm_generic_payload &trans, tlm::tlm_dmi &dmi) {
                (void)trans;
                dmi.set_start_address(0);
                dmi.set_end_address(size);
                dmi.set_dmi_ptr(data);
                if (read_only)
                        dmi.allow_read();
                else
                        dmi.allow_read_write();
                return true;
        }
};

#endif  // RISCV_ISA_MEMORY_H
