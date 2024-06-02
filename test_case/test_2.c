int print(char *s);
int printf(char *s, ...);



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


int main(){

    loop1();

    return 0;
}