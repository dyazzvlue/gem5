all : main.cpp
	riscv64-unknown-elf-g++ -std=c++14 main.cpp -o main

test1 : test1.cpp
	riscv64-unknown-elf-g++ -std=c++14 test1.cpp -o test1

test2 : test2.cpp
	riscv64-unknown-elf-g++ -std=c++14 test2.cpp -o test2

dump-code-1 : test1.cpp
	riscv64-unknown-elf-objdump -D test1 >test1.dump

dump-code-2 : test2.cpp
	riscv64-unknown-elf-objdump -D test2 >test2.dump