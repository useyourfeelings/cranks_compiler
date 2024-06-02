//int a = 6, b, cc[6]/*, gg[6]*/;
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

*/


/*
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
    int aa = 6666;

    //printf("pointer a = %d\n", a);

    p = &a;
    printf("pointer a = %d, p = 0x%x\n", a, p);

    int *b = &aa;

    *p =   *b -1234;

    printf("pointer a = %d, p = 0x%x *p = %d\n", a, p, *p);
}


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
}*/


int wtf1;

struct S1 {
    int a, ***b;
    int c, d, array[100];
} s0, saaaaa[10][10];


struct S2 {
    int a, aa;
    struct S1 s1;
    int c, d;
} s2;

int struct_test2(){
    //struct S2 s2;
    s2.s1.a = 6662;
    printf("s2.s1.a = %d, s2.s1.c = %d, s2.a = %d\n", s2.s1.a, s2.s1.c, s2.a);


    struct S2 *p1 = &s2;
    p1->c = 111;
    printf("%d %d %d %d\n", p1->s1.a, p1->s1.c, p1->a, p1->c);

    ///

    printf("0x%x \n", p1);

    struct S2 sa1[20];
    struct S2 *ppp;// = 255;
    ppp = sa1;
    //ppp = 255;
    printf("0x%x 0x%x 0x%x 0x%x 0x%x\n", ppp, sa1, &sa1[0], &sa1[1], &sa1[3]);

    sa1[6].aa = 222;
    sa1[6].s1.d = 333;
    printf("%d %d %d\n", sa1[6].aa, sa1[6].d, sa1[6].s1.d);
    ppp = &sa1[6];
    ppp->aa = 678;
    printf("0x%x 0x%x 0x%x\n", sa1, ppp, &sa1[6]);
    printf("%d %d %d %d\n", ppp->aa, sa1[6].aa, ppp->d, ppp->s1.d);

    //return 0;



    ///
    struct S2 sa[5][24];

    sa[3][20].aa = 222;
    sa[3][20].s1.d = 333;
    printf("%d %d %d\n", sa[3][20].aa, sa[3][20].d, sa[3][20].s1.d);

    struct S2 *p2 = &sa[3][20];
    struct S2 *p3 = &sa[0][0];
    printf("0x%x 0x%x 0x%x 0x%x\n", sa, p3, &sa[3][20], p2);
    printf("%d %d %d\n", p2->aa, p2->d, p2->s1.d);

}


int struct_test(){



    struct S1 s1;
    s1++;
    s1.a = 666;
    s1.d = s1.a + 111;
    s1.b = s1.d + s1.a;

    int *p = &s1.c;
    *p = 888 + 1;

    printf("struct_test s1.a = %d s1.b = %d s1.c = %d s1.d = %d \n", s1.a, s1.b, s1.c, s1.d);
    printf("struct_test &a = 0x%x &b = 0x%x &c = 0x%x &d = 0x%x \n", &s1.a, &s1.b, &s1.c, &s1.d);

    struct S1 sa[10][10];
    printf("wtf1\n");
    sa[1][2].a = 666;
    sa[6][2].b = 12445;
    sa[1][5].c = sa[6][2].b + sa[1][2].a;
    printf("struct_test %d %d %d %d\n", sa[1][2].a, sa[1][2].b, sa[6][7].a, sa[1][5].c);



    {
        struct S1 s1;
        s1.a = s1.b = s1.c = s1.d = 3 * 5;
        printf("struct_test s1.a = %d s1.b = %d s1.c = %d s1.d = %d \n", s1.a, s1.b, s1.c, s1.d);
    }
    printf("struct_test s1.a = %d s1.b = %d s1.c = %d s1.d = %d \n", s1.a, s1.b, s1.c, s1.d);


    for(int i = 0; i < 3; ++ i){
        for(int j = 0; j < 3; ++ j){
            printf("loop %d %d\n", i, j);
        }
    }

    s0.a =1;
    s0.d =1*9+1111;
    printf("s0 %d %d %d\n", s0.a, s0.c, s0.d);
    saaaaa[0][1].a = 111;
    saaaaa[9][9].d = 222;
    printf("saaaaa %d %d\n", saaaaa[0][1].a, saaaaa[9][9].d);

    int *p1 = &wtf1;
    struct S1 *p2 = &s0;

    *p1 = 123;
    *p2 = 666;
    printf("wtf1 = %d, *p1 = %d *p2 = %d\n", wtf1, *p1, *p2);

    s0.c = 777;
    printf("s0.c = %d, p2->c = %d\n", s0.c, p2->c);

    p2->c = 778;
    printf("s0.c = %d, p2->c = %d\n", s0.c, p2->c);

    s0.d = 11111111;
    int *pp = &p2->c;
    *pp = 111 + p2->d;

    printf("s0.c = %d, p2->c = %d\n", s0.c, p2->c);


}


/*
const int aaa =888;
int bbb = aaa * 2;
int ccc[666];


void scope(){
    bbb = 123;

    ccc[122] = 789;

    ccc[665] = ccc[122] + 1;

    //aaa = 111;
    printf("scope %d %d %d %d\n", aaa, bbb, ccc[122], ccc[665]);

    {
        int a = 222, b= 333;
        printf("scope %d %d\n", a, b);
    }

    int c = 444;
    printf("scope %d\n", c);

    for(int i = 0; i < 3; ++ i){
        for(int j = 0; j < 3; ++ j){
            printf("loop %d %d\n", i, j);
        }
    }
}
*/

int main(){
    //f2();
    //int v2 = 3;
    //int v1 = 1 + 999 * 5 / v2 * 2 - 1665555555;
    //array();
    //f3();



    struct_test2();
    struct_test();
    //scope();
    //printf("f1 xc printf \n");
    //pointer();
    //loop1();

    //printf("xc printf wtf %d %d %s %d %d %d", 1, 22, "wtfffffffffff", 44, 555, 666);

    //a++;
    //cc[1] = cc[2] = v1 = 999;

//print("666");
    // wtf;



//666.a();

    return 0;
}
