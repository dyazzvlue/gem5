#ifndef __GEM5_BLOCKING_PACKET_HELPER_HH__
#define __GEM5_BLOCKING_PACKET_HELPER_HH__

#include <map>
#include <systemc>
#include <tlm>

#include "sc_slave_port.hh"

namespace Gem5SystemC
{

enum pktType {Request, Response};

class BlockingPacketHelper
{
    public:
        BlockingPacketHelper();
        virtual ~BlockingPacketHelper() {};

        // TODO: maybe change core_id to socket_id?
        void updateBlockingMap(unsigned int core_id,
                            tlm::tlm_generic_payload *blocking_trans,
                            pktType type);
        tlm::tlm_generic_payload* getBlockingTrans(unsigned int core_id,
                                                pktType type);
        void init(unsigned int num);
        bool isBlocked(unsigned int core_id, pktType type);
        bool isBlockingTrans(tlm::tlm_generic_payload *blockingRequest,
                                pktType type);

        bool needToSendRequestRetry(unsigned int core_id);
        void updateRetryMap(unsigned int core_id, bool state);

        /**
         * @brief Get the Blocking Response object
         * If there is any blocking response transaction, return it.
         * If not, return nullptr.
         *
         * @return tlm::tlm_generic_payload*
         */
        tlm::tlm_generic_payload* getBlockingResponse();

    private:
        int socket_num;
        /**
        * Using a map to save blocking transactions. Transaction will not be
        * blocked when a packet from another core is processing.
        *
        * key: core id  value: tlm_genric_payload
        */
        std::map<unsigned int, tlm::tlm_generic_payload*> blockingRequestMap;
        std::map<unsigned int, tlm::tlm_generic_payload*> blockingResponseMap;

        std::map<unsigned int, bool> needToSendRequestRetryMap;
        // if packet from system writeback/functional/interrupt port,
        // always blocked
        bool isSystemPortBlocked = false;
};

}

#endif
