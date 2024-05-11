int a = 6, b, cc[6]/*, gg[6]*/;
/*
struct SSS{
    int s1;
    int s2[10];
} ;
*/
int print(char *s);
int printf(char *s, ...);
/*
int wtf1(){
     ggggggggggggggg();
    int wtff;
    int a = 123, b = wtff+2, c = a;

    a = b *= c + 1 + 2 +3 +4 +5;
    return 8;
}
*/


int f1(){
    int v1;
    int v2 = 12345;

    v1 = 1 + 999 * 5 / v2 * 2 - 3;

    printf("f1 xc printf %d\n", v1);

    return v1;
}

int f2(){
f1();
    printf("f2 xc printf %d\n", 666);
    return 666;
}

int f3(){
    //int aaa = 7779 + 1 + 2-(7780 * 2);
    //int bbb = 4;
    int aaa = 100 / 7 * 2 + 3;
    int a = ++ ++aaa  + (2); //1  && -3;
    //printf("xc printf %d wtf666", print("12"));
    //printf("xc printf %d wtf %d %d %d", 1, 2, aaa, b);
    printf("a = %d   \n", a);

    int result = f1();
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

int f4(){

    int arr[10][222];
}


int main(){
    // f3()

    f3();
    f4();

    //printf("xc printf wtf %d %d %s %d %d %d", 1, 22, "wtfffffffffff", 44, 555, 666);

    //a++;
    //cc[1] = cc[2] = v1 = 999;

//print("666");
    // wtf;



//666.a();

    return 0;
}
