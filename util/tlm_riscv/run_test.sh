#!/bin/bash

echo "========= gem5-riscv-systemc cosim ========="

echo "--------- Step 1: load config file ---------"
 ../../build/RISCV/gem5.opt ./conf/riscv_core2tlm.py -n=2

echo "--------- Step 2: Run simulation   ---------"
./build2.3.3/examples/slave_port/gem5.sc  m5out/config.ini -v &>multi.log



 