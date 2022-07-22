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

#include "blocking_packet_helper.hh"
#include "sc_ext.hh"
#include "sc_mm.hh"
#include "sc_slave_port.hh"
#include "slave_transactor.hh"

namespace Gem5SystemC
{

/**
 * Instantiate a tlm memory manager that takes care about all the
 * tlm transactions in the system
 */
MemoryManager mm;

/**
 * Convert a gem5 packet to a TLM payload by copying all the relevant
 * information to a previously allocated tlm payload
 */
void
packet2payload(gem5::PacketPtr packet, tlm::tlm_generic_payload &trans)
{
    trans.set_address(packet->getAddr());
    /* Check if this transaction was allocated by mm */
    sc_assert(trans.has_mm());

    unsigned int size = packet->getSize();
    unsigned char *data = packet->getPtr<unsigned char>();

    trans.set_data_length(size);
    trans.set_streaming_width(size);
    trans.set_data_ptr(data);

    if (packet->isRead()) {
        trans.set_command(tlm::TLM_READ_COMMAND);
    }
    else if (packet->isInvalidate()) {
        /* Do nothing */
    } else if (packet->isWrite()) {
        trans.set_command(tlm::TLM_WRITE_COMMAND);
    } else {
        SC_REPORT_FATAL("SCSlavePort", "No R/W packet");
    }
}

/**
 * Similar to TLM's blocking transport (LT)
 */
gem5::Tick
SCSlavePort::recvAtomic(gem5::PacketPtr packet)
{
    CAUGHT_UP;
    SC_REPORT_INFO("SCSlavePort", "recvAtomic hasn't been tested much");

    panic_if(packet->cacheResponding(), "Should not see packets where cache "
             "is responding");

    panic_if(!(packet->isRead() || packet->isWrite()),
             "Should only see read and writes at TLM memory\n");

    sc_core::sc_time delay = sc_core::SC_ZERO_TIME;

    /* Prepare the transaction */
    tlm::tlm_generic_payload * trans = mm.allocate();
    trans->acquire();
    packet2payload(packet, *trans);

    /* Attach the packet pointer to the TLM transaction to keep track */
    Gem5Extension* extension = new Gem5Extension(packet);
    unsigned int core_id = this->getCoreID(packet->requestorId());
    extension->setCoreID(core_id);
    trans->set_auto_extension(extension);

    /* Execute b_transport: */
    if (packet->cmd == gem5::MemCmd::SwapReq) {
        SC_REPORT_FATAL("SCSlavePort", "SwapReq not supported");
    } else if (packet->isRead()) {
        if (transactor != nullptr) {
            transactor->socket->b_transport(*trans, delay);
        } else if (transactor_multi != nullptr) {
            transactor_multi->sockets[core_id]->b_transport(*trans, delay);
        } else{
            // no transactor , Exit
            SC_REPORT_FATAL("SCSlavePort", "No binded transactor, please check");
        }
    } else if (packet->isInvalidate()) {
        // do nothing
    } else if (packet->isWrite()) {
        if (transactor != nullptr) {
            transactor->socket->b_transport(*trans, delay);
        } else if (transactor_multi != nullptr) {
            transactor_multi->sockets[core_id]->b_transport(*trans, delay);
        } else {
            // no transactor , Exit
            SC_REPORT_FATAL("SCSlavePort", "No binded transactor, please check");
        }
    } else {
        SC_REPORT_FATAL("SCSlavePort", "Typo of request not supported");
    }

    if (packet->needsResponse()) {
        packet->makeResponse();
    }

    trans->release();

    return delay.value();
}

/**
 * Similar to TLM's debug transport
 */
void
SCSlavePort::recvFunctional(gem5::PacketPtr packet)
{
    /* Prepare the transaction */
    tlm::tlm_generic_payload * trans = mm.allocate();
    trans->acquire();
    packet2payload(packet, *trans);

    /* Attach the packet pointer to the TLM transaction to keep track */
    Gem5Extension* extension = new Gem5Extension(packet);
    unsigned int core_id = this->getCoreID(packet->requestorId());
    extension->setCoreID(core_id);
    trans->set_auto_extension(extension);

    /* Execute Debug Transport: */
    unsigned int bytes;
    if (transactor != nullptr) {
        bytes = transactor->socket->transport_dbg(*trans);
    } else if (transactor_multi != nullptr) {
        bytes = transactor_multi->sockets[core_id]->transport_dbg(*trans);
    } else {
        SC_REPORT_FATAL("SCSlavePort", "No binded transactor, please check");
    }
    if (bytes != trans->get_data_length()) {
        SC_REPORT_FATAL("SCSlavePort","debug transport was not completed");
    }

    trans->release();
}

bool
SCSlavePort::recvTimingSnoopResp(gem5::PacketPtr packet)
{
    /* Snooping should be implemented with tlm_dbg_transport */
    SC_REPORT_FATAL("SCSlavePort","unimplemented func.: recvTimingSnoopResp");
    return false;
}

void
SCSlavePort::recvFunctionalSnoop(gem5::PacketPtr packet)
{
    /* Snooping should be implemented with tlm_dbg_transport */
    SC_REPORT_FATAL("SCSlavePort","unimplemented func.: recvFunctionalSnoop");
}

/**
 *  Similar to TLM's non-blocking transport (AT)
 */
bool
SCSlavePort::recvTimingReq(gem5::PacketPtr packet)
{
    CAUGHT_UP;
    panic_if(packet->cacheResponding(), "Should not see packets where cache "
             "is responding");

    panic_if(!(packet->isRead() || packet->isWrite()),
             "Should only see read and writes at TLM memory\n");

    /* We should never get a second request after noting that a retry is
     * required */
    sc_assert(!needToSendRequestRetry);

    unsigned int core_id = this->getCoreID(packet->requestorId()); // get coreid
    /* Remember if a request comes in while we're blocked so that a retry
     * can be sent to gem5 */

    // only request from system port will be set to blocking request
    if (blockingRequest) {
        needToSendRequestRetry = true;
        return false;
    }
    // packet from core model will be set to blocking_packet_helper
    if (blocking_packet_helper->isBlocked(core_id, pktType::Request)) {
        blocking_packet_helper->updateRetryMap(core_id, true);
        return false;
    }

    /*  NOTE: normal tlm is blocking here. But in our case we return false
     *  and tell gem5 when a retry can be done. This is the main difference
     *  in the protocol:
     *  if (requestInProgress)
     *  {
     *      wait(endRequestEvent);
     *  }
     *  requestInProgress = trans;
    */

    /* Prepare the transaction */
    tlm::tlm_generic_payload * trans = mm.allocate();
    trans->acquire();
    packet2payload(packet, *trans);

    /* Attach the packet pointer to the TLM transaction to keep track */
    Gem5Extension* extension = new Gem5Extension(packet);

    extension->setCoreID(core_id);
    trans->set_auto_extension(extension);
    /*
     * Pay for annotated transport delays.
     *
     * The header delay marks the point in time, when the packet first is seen
     * by the transactor. This is the point int time, when the transactor needs
     * to send the BEGIN_REQ to the SystemC world.
     *
     * NOTE: We drop the payload delay here. Normally, the receiver would be
     *       responsible for handling the payload delay. In this case, however,
     *       the receiver is a SystemC module and has no notion of the gem5
     *       transport protocol and we cannot simply forward the
     *       payload delay to the receiving module. Instead, we expect the
     *       receiving SystemC module to model the payload delay by deferring
     *       the END_REQ. This could lead to incorrect delays, if the XBar
     *       payload delay is longer than the time the receiver needs to accept
     *       the request (time between BEGIN_REQ and END_REQ).
     *
     * TODO: We could detect the case described above by remembering the
     *       payload delay and comparing it to the time between BEGIN_REQ and
     *       END_REQ. Then, a warning should be printed.
     */
    auto delay = sc_core::sc_time::from_value(packet->payloadDelay);
    // reset the delays
    packet->payloadDelay = 0;
    packet->headerDelay = 0;

    /* Starting TLM non-blocking sequence (AT) Refer to IEEE1666-2011 SystemC
     * Standard Page 507 for a visualisation of the procedure */
    tlm::tlm_phase phase = tlm::BEGIN_REQ;
    tlm::tlm_sync_enum status;

    if (transactor != nullptr){
        status = transactor->socket->nb_transport_fw(*trans, phase, delay);
    } else if (transactor_multi != nullptr) {
        status = transactor_multi->sockets[core_id]->nb_transport_fw(*trans,
                                                                phase, delay);
    }else {
        SC_REPORT_FATAL("SCSlavePort", "No binded transactor, please check");
    }
    /* Check returned value: */
    if (status == tlm::TLM_ACCEPTED) {
        sc_assert(phase == tlm::BEGIN_REQ);
        /* Accepted but is now blocking until END_REQ (exclusion rule)*/
        if (core_id == 0){ // transaction from system port
            blockingRequest = trans;
        }else {
            blocking_packet_helper->updateBlockingMap(core_id, trans,
                                                    pktType::Request);
        }
    } else if (status == tlm::TLM_UPDATED) {
        /* The Timing annotation must be honored: */
        sc_assert(phase == tlm::END_REQ || phase == tlm::BEGIN_RESP);
        PayloadEvent<SCSlavePort> * pe;
        pe = new PayloadEvent<SCSlavePort>(*this,
            &SCSlavePort::pec, "PEQ");
        pe->notify(*trans, phase, delay);
    } else if (status == tlm::TLM_COMPLETED) {
        /* Transaction is over nothing has do be done. */
        sc_assert(phase == tlm::END_RESP);
        trans->release();
    }

    return true;
}

void
SCSlavePort::pec(
    PayloadEvent<SCSlavePort> * pe,
    tlm::tlm_generic_payload& trans,
    const tlm::tlm_phase& phase)
{
    sc_time delay;

    if (phase == tlm::END_REQ ||
              (blocking_packet_helper->isBlockingTrans(&trans, pktType::Request)
              && phase == tlm::BEGIN_RESP) ||
              (&trans == blockingRequest && phase == tlm::BEGIN_RESP)
              ) {
        // system port is blocked, send retry
        if (&trans == blockingRequest){
            sc_assert(&trans == blockingRequest);
            blockingRequest = NULL;
            if (needToSendRequestRetry) {
                needToSendRequestRetry = false;
                sendRetryReq();
            }
        } else // cpu port is blocked, send retry
        {
            sc_assert(blocking_packet_helper->isBlockingTrans(&trans,
                                                            pktType::Request));
            unsigned int core_id =
                                Gem5Extension::getExtension(trans).getCoreID();
            auto tmp = blocking_packet_helper->getBlockingTrans(core_id,
                                                            pktType::Request);
            blocking_packet_helper->updateBlockingMap(core_id, NULL,
                                                    pktType::Request);
            /* Did another request arrive while blocked, schedule a retry */
            if (blocking_packet_helper->needToSendRequestRetry(core_id)){
                blocking_packet_helper->updateRetryMap(core_id, false);
                sendRetryReq();
            }
        }
    }
    if (phase == tlm::BEGIN_RESP)
    {
        CAUGHT_UP;

        auto& extension = Gem5Extension::getExtension(trans);
        auto packet = extension.getPacket();
        unsigned int core_id = extension.getCoreID();
        if (core_id == 0){
            sc_assert(!blockingResponse);
        }else {
            sc_assert(!blocking_packet_helper->getBlockingTrans(core_id,
                                                            pktType::Response));
        }

        bool need_retry = false;

        // If there is another gem5 model under the receiver side, and already
        // make a response packet back, we can simply send it back. Otherwise,
        // we make a response packet before sending it back to the initiator
        // side gem5 module.
        if (packet->needsResponse()) {
            packet->makeResponse();
        }
        if (packet->isResponse()) {
            need_retry = !sendTimingResp(packet);
        }

        if (need_retry) {
            if (core_id == 0){
                blockingResponse = &trans;
            }else {
                blocking_packet_helper->updateBlockingMap(core_id, &trans,
                                                        pktType::Response);
            }
        } else {
            if (phase == tlm::BEGIN_RESP) {
                /* Send END_RESP and we're finished: */
                tlm::tlm_phase fw_phase = tlm::END_RESP;
                sc_time delay = SC_ZERO_TIME;
                if (transactor != nullptr) {
                    transactor->socket->nb_transport_fw(trans, fw_phase, delay);
                } else if (transactor_multi != nullptr) {
                    transactor_multi->sockets[core_id]->nb_transport_fw(trans,
                                                            fw_phase, delay);
                } else {
                    SC_REPORT_FATAL("SCSlavePort",
                                    "No binded transactor, please check");
                }
                /* Release the transaction with all the extensions */
                trans.release();
            }
        }
    }
    delete pe;
}

void
SCSlavePort::recvRespRetry()
{
    CAUGHT_UP;

    /* Retry a response */
    //sc_assert(blockingResponse);
    auto response = blocking_packet_helper->getBlockingResponse();
    while (response != nullptr || blockingResponse != NULL) {
        tlm::tlm_generic_payload *trans;
        gem5::PacketPtr packet;
        unsigned int core_id;
        if (blockingResponse != NULL){
            trans = blockingResponse;
            blockingResponse = NULL;
            packet = Gem5Extension::getExtension(trans).getPacket();
            core_id = Gem5Extension::getExtension(trans).getCoreID();
        }else if (response != nullptr){
            trans = response;
            packet = Gem5Extension::getExtension(trans).getPacket();
            core_id = Gem5Extension::getExtension(trans).getCoreID();
            blocking_packet_helper->updateBlockingMap(core_id, NULL,
                                                    pktType::Response);
        }

        bool need_retry = !sendTimingResp(packet);

        sc_assert(!need_retry);

        sc_core::sc_time delay = sc_core::SC_ZERO_TIME;
        tlm::tlm_phase phase = tlm::END_RESP;
        if (transactor != nullptr ){
            transactor->socket->nb_transport_fw(*trans, phase, delay);
        } else if (transactor_multi != nullptr) {
            transactor_multi->sockets[core_id]->nb_transport_fw(*trans,
                                                                phase, delay);
        } else {
            SC_REPORT_FATAL("SCSlavePort",
                        "No binded transactor, please check");
        }

        // Release transaction with all the extensions
        trans->release();
        response = blocking_packet_helper->getBlockingResponse();
    }
}

tlm::tlm_sync_enum
SCSlavePort::nb_transport_bw(tlm::tlm_generic_payload& trans,
    tlm::tlm_phase& phase,
    sc_core::sc_time& delay)
{
    PayloadEvent<SCSlavePort> * pe;
    pe = new PayloadEvent<SCSlavePort>(*this, &SCSlavePort::pec, "PE");
    pe->notify(trans, phase, delay);
    return tlm::TLM_ACCEPTED;
}

SCSlavePort::SCSlavePort(const std::string &name_,
    const std::string &systemc_name,
    gem5::ExternalSlave &owner_) :
    gem5::ExternalSlave::ExternalPort(name_, owner_),
    blockingRequest(NULL),
    needToSendRequestRetry(false),
    blockingResponse(NULL),
    transactor(nullptr),
    blocking_packet_helper(new BlockingPacketHelper())
{

}

void
SCSlavePort::bindToTransactor(Gem5SlaveTransactor* transactor)
{
    sc_assert(this->transactor == nullptr);

    this->transactor = transactor;

    transactor->socket.register_nb_transport_bw(this,
                                                &SCSlavePort::nb_transport_bw);
}

void
SCSlavePort::bindToTransactor(Gem5SlaveTransactor_Multi* transactor)
{
    sc_assert(this->transactor == nullptr);

    this->transactor_multi = transactor;
    for (int i = 0; i < transactor->getSocketNum(); i++){
        transactor->sockets[i].register_nb_transport_bw(this,
                                                &SCSlavePort::nb_transport_bw);
    }
}

gem5::ExternalSlave::ExternalPort*
SCSlavePortHandler::getExternalPort(const std::string &name,
                                    gem5::ExternalSlave &owner,
                                    const std::string &port_data)
{
    // Create and register a new SystemC slave port
    auto* port = new SCSlavePort(name, port_data, owner);
    control.registerSlavePort(port_data, port);

    return port;
}

unsigned int SCSlavePort::getCoreID(gem5::RequestorID id)
{
    unsigned int core_id = 0;
    for (auto it = cpuPorts.begin();it != cpuPorts.end(); it++){
        auto it_find = std::find(it->second.begin(),it->second.end(),id);
        if (it_find != it->second.end()){
            // TODO:
            // socket0 is used for system port now, change it to a special tag
            return core_id + 1;
        }else{
            core_id++;
        }
    }
    // not found, is from system port
    return 0;
}

void SCSlavePort::
updateCorePortMap(std::map<const std::string, std::list<gem5::RequestorID>> map)
{
    this->cpuPorts = map;
    blocking_packet_helper->init(map.size() + 1);
    // print the map, TODO: can be removed
    auto it = this->cpuPorts.begin();
    while (it != this->cpuPorts.end()){
        auto it_2 = it->second;
        auto it_3 = it_2.begin();
        while (it_3 != it_2.end()){
            std::cout << it->first << " " << *it_3<< std::endl;
            it_3 ++;
        }
        it ++;
    }
}

}
