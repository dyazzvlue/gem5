#!/bin/bash

echo "========= gem5-riscv-systemc cosim ========="

echo ">>>>>>>>>     Run Test Case1       >>>>>>>>>"

echo "--------- Step 1: load config file ---------"
 ../../build/RISCV/gem5.opt ./conf/riscv_core2tlmWithCache.py --testcase=test1

echo "--------- Step 2: Run simulation   ---------"
./build/examples/slave_port/gem5.sc  m5out/config.ini &>logs/cache_test1_n_300.log

echo ">>>>>>>>>     Run Test Case2       >>>>>>>>>"

echo "--------- Step 1: load config file ---------"
 ../../build/RISCV/gem5.opt ./conf/riscv_core2tlmWithCache.py --testcase=test2

echo "--------- Step 2: Run simulation   ---------"
./build/examples/slave_port/gem5.sc  m5out/config.ini  &>logs/cache_test2_n_300.log

    