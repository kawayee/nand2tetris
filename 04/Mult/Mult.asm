// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
// The algorithm is based on repetitive addition.

/* Assume that R0 ≥ 0, R1 ≥ 0, and R0 * R1 < 32768
 Your code should not change the values of R0 and R1.

def mult(R0, R1) {
    r0=R0;
    r1=R1;
    R2=0;
    while (r0 > 0) {
        r0 -= 1;
        R2 += r1;
    }
    return R2;
 }
*/
    @R0
    D=M
    @r0
    M=D
    @R1
    D=M
    @r1
    M=D
    @R2
    M=0
(LOOP)
    @r0
    D=M
    @END
    D;JLE
    @r0
    M=M-1
    @r1
    D=M
    @R2
    M=D+M
    @LOOP
    0;JMP
(END)
    @END
    0;JMP