; cranks_libc.asm
; xc 20240322
; some c library and helper functions

extern __imp_GetStdHandle:proc
extern __imp_WriteFile:proc
;extern __imp_StringCbPrintfA:proc
extern __imp_wsprintfA:proc ; user32.lib

    .data

buffer byte 1024 dup (6) ; for printf
temp_var qword ?

    .code

; string must in rcx. 0-terminated.
print proc
    ; use GetStdHandle/WriteFile
    push rbp
    mov rbp, rsp
    sub rsp, 8

    mov rdi, rsp

    mov rdx, rcx

    ; get string length
    push rcx
    push rdx
    xor r8, r8 ; clean

    print_loop_1:
        mov dl, [rcx]
        cmp dl, 0
        je print_loop_1_over
        inc rcx
        inc r8
        jmp print_loop_1
    print_loop_1_over:
        pop rdx ; recover
        pop rcx ; recover


    ; WriteFile has 5 args
    ; 32 Shadow storage for 4 args, 8 for 5th arg, 8 for alignment. 32+8+8=48=0x30
    sub rsp, 30h

    mov rcx, -11                      ; -11=STD_OUTPUT
    call qword ptr __imp_GetStdHandle ;Returns handle in RAX

    xor rcx, rcx                      ; clean
    mov [rsp + 4 * 8], rcx            ; clean 5th arg
    mov  r9, rdi                      ; 4th args

    mov  rcx, rax                     ; handle in rax returned by __imp_GetStdHandle
    call qword ptr __imp_WriteFile

    leave
    ret
print endp

printf proc
    ; use wsprintfA/print
    push rbp
    mov rbp, rsp

    ; force alignment
    and rsp, -16

    ; https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-wsprintfa
    ; mov temp_var, rcx; save rcx
    lea rcx, buffer ; 1st arg is inbuffer

    ; args count in r15

    ; alloc
    ; must be 16-aligned before call
    mov r14, r15
    inc r14 ; printf args + inbuffer

    ; https://stackoverflow.com/questions/49116747/assembly-check-if-number-is-even
    ; odd or even?
    test r14b, 1
    jz args_count_even
        inc r14 ; make it even
    args_count_even:

    ; shadow space. at least 4 args.
    cmp r14, 4
    jge args_count_ge_4
        mov r14, 4
    args_count_ge_4:

    imul r14, 8
    sub rsp, r14

    ; set args from 2nd arg
    mov r13, rsp ; new arg address
    add r13, 8 ; 2nd shadow arg
    mov r12, rbp ; old arg address
    add r12, 16 ; format string

    mov rdx, [r12]; 2nd arg to rdx

    mov r14, r15 ; r14 = args count

    ; if has 2nd arg
    cmp r14, 2
    jl printf_no_2_args
    mov r8, [r12 + 8]
    printf_no_2_args:

    ; if has 3rd arg
    cmp r14, 3
    jl printf_no_3_args
    mov r9, [r12 + 16]
    printf_no_3_args:

    ; set stack args
    mov [rsp], rcx; lea [rsp], buffer ; 1st arg is inbuffer

    printf_loop_1:
        cmp r14, 0
        je printf_loop_1_ok

        mov r11, [r12] ; copy arg
        mov [r13], r11
        dec r14
        add r12, 8 ; next address
        add r13, 8 ; next address
        jmp printf_loop_1
    printf_loop_1_ok:

    call qword ptr __imp_wsprintfA;

    lea rcx, buffer
    call print

    ; free

    leave
    ret
printf endp

end