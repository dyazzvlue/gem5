#!/bin/bash

echo "========= gem5-riscv-systemc cosim ========="

echo ">>>>>>>>>       Run CHI Test       >>>>>>>>>"

echo "--------- Step 1: load config file ---------"
../../build/RISCV_CHI/gem5.opt conf/ruby/riscv_tlm2CHI.py

echo "--------- Step 2: Run simulation   ---------"
./build_chi/examples/slave_port/gem5.sc m5out/config.ini &>logs/chi_test.log

    