#include <cstdio>
#include <iostream>

using namespace std;

#define VEC_SIZE 5

int add(int a, int b){
    return a+b;
}

void sampleFunc(int a[], int b[]){
    std::cout << "[User function]A start address: " << &a[0]
        << " end address " << &a[VEC_SIZE-1] << " " << &a << std::endl;

    std::cout << "[User function]B start address: " << &b[0]
        << " end address " << &b[VEC_SIZE-1] << " " << &b << std::endl;

    for (int i =0 ; i< VEC_SIZE; i ++){
        int c = add(a[i], b[i]);
        printf("[User function]Return c: %d\n", c);
        // after add. update a[i], b[i]
        a[i] = a[i] * 10;
        b[i] = b[i] * 10;
        c = add(a[i], b[i]);
        printf("[User function]Return update c: %d\n", c);
    }
}


int main(){
    int an[VEC_SIZE];
    int bn[VEC_SIZE];
    printf("[User function]Init an, bn\n");
    std::cout << "Main An address: " << &an << std::endl;
    std::cout << "Main Bn address: " << &bn << std::endl;
    for (int i = 0; i < VEC_SIZE ; i ++){
        an[i] = i;
        bn[i] = i+i;
    }
    std::cout << "Main An address: " << &an << std::endl;
    std::cout << "Main Bn address: " << &bn << std::endl;
    printf("[User function]run sample\n");
    sampleFunc(an, bn);
    for (int i = 0; i < VEC_SIZE ; i ++){
        std::cout << an[i] << " , " << bn[i] << std::endl;
    }
    return 0;
}

