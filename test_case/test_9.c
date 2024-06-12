int print(char *s);
int printf(char *s, ...);

int wtf1;

struct S1 {
    int a, b, c, d, e;
};


typedef int WTF, WTFFffff;

typedef WTFFffff WTF2,  *WTFffff2;

WTFffff2 w1, w2;

struct S1 sssss1;

typedef struct S1 TS1;

TS1 ts1;

typedef TS1 TTS1;

typedef TTS1 *pTTS1;

pTTS1 p1;

int main(){

    TS1 t1;

    t1.b = 666;

    printf("t1.b = %d\n", t1.b);

    pTTS1 p2 = &t1;
    //printf("p2 = 0x%x\n", p2);

    printf("p2->b = %d *p2.b = %d\n", p2->b, (*p2).b);

    int g1, g2;

    {
        int g3, g4;
    }

    return 0;
}
