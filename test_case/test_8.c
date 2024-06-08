int print(char *s);
int printf(char *s, ...);

int wtf1;




int f(int g, int  *pwtf, const int yyy){
    //printf("f wtf1 %d %d %d\n", g, *pwtf, yyy);

    // 1 778 777
    (*pwtf) ++;
    // 1 779 777
    ++(*pwtf);
    // 1 780 777

    printf("f wtf2 %d %d %d\n", g, *pwtf, yyy);

    return *pwtf;
}


int f2(int gg){
    printf("f2 gg = %d\n", gg);
    if(gg <= 0) return;

    --gg;

    f2(gg - 100);
}

int main(){

int wtf = 777;
// 777
     f(1, &wtf, wtf++);

     // 1 780 3
     f2(12 + f(1, &wtf, 3)); // f2(12 + 782)

     f(1, &wtf, wtf); // 1 782 780


    return 0;
}
