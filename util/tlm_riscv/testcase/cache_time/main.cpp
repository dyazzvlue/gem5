#include <bits/stdc++.h>

#include <iostream>
#include <vector>

using namespace std;
int main()
{
    double t1, t2;  // time
    clock_t st, ed; // start clock and end clock
    // init x[i]
    int n = 1000;
    int an[n];
    int tmp;
    for (int i = 0; i < n; i++)
    {
        an[i] = rand();
    }
    // T1 suppose spend more time
    std::cout << "T1 test " << std::endl;
    st = clock();
    for (int loop = 0; loop < 10000; loop++)
    {
        for (int i = 0; i < n; i++)
        {
            tmp = an[i] + loop;
        }
    }
    ed = clock();
    t1 = (double)(ed - st) / CLOCKS_PER_SEC;
    std::cout << "T1: " << t1 << std::endl;

    // T2 suppose spend less time
    std::cout << "T2 test " << std::endl;
    st = clock();
    for (int loop = 0; loop < 10000; loop++)
    {
        for (int i = 0; i < n; i++)
        {
            tmp = an[i] + loop;
        }
    }
    ed = clock();
    t2 = (double)(ed - st) / CLOCKS_PER_SEC;
    std::cout << "T2: " << t2 << std::endl;

    return 0;
}
