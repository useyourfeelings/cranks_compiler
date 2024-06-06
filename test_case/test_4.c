int print(char *s);
int printf(char *s, ...);

int array(){
    int a = 10;
    int arrrrrrr[3][10];

    // arrrrrrr[a+1][2] = 1689;

    int *p = &a;

    arrrrrrr[1][2] = *p;//0x6666;
    arrrrrrr[2][2] = arrrrrrr[2][3] = 0x777;

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
    printf("array printf *p = 0x%x\n", *p);

    printf("array printf 0x%x 0x%x\n", a, 2*(1+a));
    printf("array printf 0x%x\n", b[1][2][3] + b[2][3][4] + 1);
}


int main(){
    array();
    return 0;
}