int print(char *s);
int printf(char *s, ...);

int wtf1;

struct S1 {
    int a, ***b;
    int c, d, array[100];
} s0, saaaaa[10][10];


int struct_test(){

    struct S1 s1;
    s1++;
    s1.a = 666;
    s1.d = s1.a + 111;
    s1.b = s1.d + s1.a;

    int *p = &s1.c;
    *p = 888 + 1;

    printf("struct_test s1.a = %d s1.b = %d s1.c = %d s1.d = %d \n", s1.a, s1.b, s1.c, s1.d);
    // printf("struct_test &a = 0x%x &b = 0x%x &c = 0x%x &d = 0x%x \n", &s1.a, &s1.b, &s1.c, &s1.d);

    printf("struct_test %d %d %d %d\n", &s1.b - &s1.a, &s1.c - &s1.a, &s1.d - &s1.c, &s1.array - &s1.a);

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


int main(){

    struct_test();

    struct_test2();

    return 0;
}
