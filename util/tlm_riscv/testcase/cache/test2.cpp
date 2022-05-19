#include "header.h"

using namespace std;

int main(){
    double t1,t2;
    clock_t st, ed;

    int an_column = 10;
    int an_row = 10;
    int an[an_column][an_row];
    for (int i = 0; i < an_column; i ++ ){
        for (int j = 0; j < an_row; j ++){
            an[i][j] = rand() % 100;
        }
    }

    int bn_column = 10;
    int bn_row = 10;
    int bn[bn_column][bn_row];
    for (int i = 0; i < bn_column; i ++ ){
        for (int j = 0; j < bn_row; j ++){
            bn[i][j] = rand() % 100;
        }
    }
    //assert(an_column == bn_row);
    int result[an_row][bn_column];

    std::cout << "Test 2 " << std::endl;
    memset(result, 0, sizeof(result));
    st = clock();
    for (int i = 0; i < an_row; i++){
        for (int k = 0; k < an_column; k++){
            for (int j = 0; j < bn_column; j++){
                result[i][j] += an[i][k] * bn[k][j];
            }
        }
    }
    ed = clock();
    t2 = (double)(ed - st) / CLOCKS_PER_SEC;
    std::cout << "T2: " << t2 << std::endl;
    return 0;
}

