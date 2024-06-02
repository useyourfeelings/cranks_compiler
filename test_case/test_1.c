int a = 6, b, cc[6];

int print(char *s);
int printf(char *s, ...);


int f1(){
    int v1;
    int v2 = 12345;

    v1 = 1 + 999 * 5 / v2 * 2 - 1665555555; // -1665555554

    printf("f1 printf %d\n", v1);

    return v1;
}

int f2(){
    // f1();
    printf("f2 xc printf %d\n", 666);
    return 666;
}

int f3(){
    //int aaa = 7779 + 1 + 2-(7780 * 2);
    //int bbb = 4;
    int aaa = 100 / 7 * 2 + 3; // 31
    int a = ++ ++aaa  + (2); //1  && -3;
    //printf("xc printf %d wtf666", print("12"));
    printf("f3 printf %d wtf %d %d %d %d\n", 1, 2, aaa, b, a);

    int result = f1();
    printf("f1 result = %d\n", result);
    f2();

    //f1();
    //printf("xc printf  wtf2");
    //print("xc printf %d wtf1");
    //print("xc printf %d wtf2");
    //print("xc printf %d wtf3");
    //printf("xc printf wtf %d %d %d %d %d %s", 1, 22, 333, 4444, 55, "wtfffffffffff");
    //printf("xc printf wtf %d %d %s %d %d %d %d", 1, 22, "wtfffffffffff", 44, 555, 666, aaa);
    //printf("xc printf wtf1");
    printf("result = %d wtf2999阿斯顿999999999999999\n", f2());
}



int main(){
    f2();
    printf("f2 result = %d\n", f2());
    int v2 = 3;
    int v1 = 1 + 999 * 5 / v2 * 2 - 1665555555; // -1665552224

    printf("v1 = %d, v2 = %d\n", v1, v2);

    f3();

    return 0;
}
