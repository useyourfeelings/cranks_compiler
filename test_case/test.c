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

/*
int f1(){
    int v1;
    int v2 = 12345;

    v1 = 1 + 999 * 5 / v2 * 2 - 1665555555;

    printf("f1 xc printf %d\n", v1);

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


int loop1(){

    //int arr[2][222];

    //int i;
    //i++ ;
int aa = 9;
printf("xc printf %d wtf2\n", aa);
    if(1){

        printf("xc printf %d wtf2\n", aa);
    }
    int i = 50;
    for(; i > 3; ){
    i--;
    i--;
        printf("xc printf  wtf1 %d\n", ------i);
        printf("xc printf  wtf2 %d\n", i++);
        printf("xc printf  wtf3 %d\n", --i);
    }
    int g= 3;
    while(g > 0){
        printf("xc printf  g %d\n", --g);
        g;
    }

    g= 0;
    do{
        printf("xc printf  g %d\n", --g);
        g;
    }while(g > 0);
}

int pointer(){

    int a = 666 +999;
    //int **const* p;// = &a;

    int * p;// = 2;

    a = 2222;

    //printf("pointer a = %d\n", a);

    p = &a;
    printf("pointer a = %d, p = 0x%x\n", a, p);

    int *b = &a;

    *p =  2* *b;

    printf("pointer a = %d, p = 0x%x *p = %d\n", a, p, *p);
}
*/

int array(){
    int a = 10;
    int arrrrrrr[3][10];

    // arrrrrrr[a+1][2] = 1689;

    int *p = &a;

    arrrrrrr[1][2] = *p;//0x6666;

    printf("array printf 0x%x\n", arrrrrrr[1][2]);
    printf("array printf 0x%x\n", arrrrrrr[1][3]);
    printf("array printf 0x%x\n", arrrrrrr[2][4]);
    printf("array printf 0x%x\n", arrrrrrr[1][4]);
    arrrrrrr[1][2] = 0x6667;
    arrrrrrr[1][3] = 0x6668;
    arrrrrrr[2][4] = 0x6669;
    printf("array printf 0x%x\n", arrrrrrr[1][2]);
    printf("array printf 0x%x\n", arrrrrrr[1][3]);
    printf("array printf 0x%x\n", arrrrrrr[2][4]);
    printf("array printf 0x%x\n", arrrrrrr[1][4]);
    arrrrrrr[1][2] = 0x9999;
    arrrrrrr[2][4] = arrrrrrr[1][2];
    printf("array printf 0x%x\n", arrrrrrr[1][2]);
    printf("array printf 0x%x\n", arrrrrrr[1][3]);
    printf("array printf 0x%x\n", arrrrrrr[2][4]);
    printf("array printf 0x%x\n", arrrrrrr[1][4]);

    int b[3][4][5];
    b[1][2][3] = b[2][3][4] = 0x3333;
    printf("array printf 0x%x\n", b[1][2][3]);
    printf("array printf 0x%x\n", b[2][3][4]);

    *p = b[1][2][3] + 0x1111;
    printf("array printf p = 0x%x *p = 0x%x\n", p, *p);

    printf("array printf 0x%x 0x%x\n", a, 2*(1+a));
    printf("array printf 0x%x\n", b[1][2][3] + b[2][3][4] + 1);
}

int main(){
    //f2();
    //int v2 = 3;
    //int v1 = 1 + 999 * 5 / v2 * 2 - 1665555555;
    array();
    //f3();

    //printf("f1 xc printf \n");

    //loop1();

    //printf("xc printf wtf %d %d %s %d %d %d", 1, 22, "wtfffffffffff", 44, 555, 666);

    //a++;
    //cc[1] = cc[2] = v1 = 999;

//print("666");
    // wtf;



//666.a();

    return 0;
}
