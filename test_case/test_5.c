int print(char *s);
int printf(char *s, ...);


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

        for(int i = 0; i < 3; ++ i){
            for(int j = 0; j < 3; ++ j){
                printf("loop %d %d\n", i, j);
            }
        }
    }

    int c = 444;
    printf("scope %d\n", c);

    for(int i = 0; i < 3; ++ i){
        for(int j = 0; j < 3; ++ j){
            printf("loop %d %d\n", i, j);
        }
    }


}



int main(){
    scope();
    scope();

    return 0;
}