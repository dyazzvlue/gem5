#include <stdio.h>

#define VEC_SIZE 5

int add(int a, int b){
    return a+b;
}

void sampleFunc(int a[], int b[]){
    for (int i =0 ; i< VEC_SIZE; i ++){
        int c = add(a[i], b[i]);
        printf("[User function]Return c: %d\n", c);
    }
}


int main(){
    int an[VEC_SIZE];
    int bn[VEC_SIZE];
    printf("[User function1]Init an, bn\n");
    for (int i = 0; i < VEC_SIZE ; i ++){
        an[i] = i;
        bn[i] = i+i;
    }
    printf("[User function]run sample\n");
    sampleFunc(an, bn);
    return 0;
}