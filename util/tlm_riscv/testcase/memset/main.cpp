#include <iostream>
#include <stdio.h>
#include <string.h>
using namespace std;

int main(){
    std::cout << "Test function started" << std::endl;
    int size = 50;
    char str[size];
    char dest[size];
    memset(str, 0, sizeof(str));
    strcpy(str, "Test function for memset");
    //std::cout << "str: " << str << std::endl;
    memset(dest, 0, sizeof(dest));
    for (int i = 0; i<size;i++){
        strncpy(dest,str,i);
        //std::cout << i << " dest: " << dest << std::endl;
    }
    std::cout << "Test function completed" << std::endl;
    
    return 0;
}