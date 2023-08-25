#!/bin/bash
mkdir lib
cd include
find -name "*.pyo" -delete
find -name "*.os" -delete
find -name "*SConscript" -delete
find -name "*.py" -delete
find -name "*.o" -delete
find -name "gem5py*" -delete
find -name "gem5.opt*" -delete
for gem5_lib in $(find -name "libgem5_opt.so")
do
    mv $gem5_lib ../lib
done
for link in $(find ./ -type l)
do
    loc=$(dirname $link)
    dir=$(readlink -f $link)
    rm $link
    cp $dir $link -rf
done