int print(char *s);
int printf(char *s, ...);



int pointer(){

    int a = 666 +999;
    //int **const* p;// = &a;

    int * p;// = 2;


    a = 2222;
    int aa = 6666;

    //printf("pointer a = %d\n", a);

    p = &a;
    printf("pointer a = %d\n", a);

    int *b = &aa;

    int *p2 = &a;
     *p2  =   *b -1234;
     //*p2 = 1;
//printf("0x%x 0x%x 0x%x\n", p2, &a, b);

    printf("pointer a = %d, *p = %d, *p2 = %d\n", a, *p, *p2); // , p == p2
}



int main(){
    pointer();
    return 0;
    }