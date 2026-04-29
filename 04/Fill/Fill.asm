// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

// curr 语义：最后一个已写入的地址
// 初始值设为 SCREEN-1，表示"尚未写入任何像素"

    @SCREEN
    D=A
    @curr
    M=D-1          // curr = SCREEN - 1（哨兵初值，屏幕为空状态）

(LISTENER_LOOP)
    @KBD
    D=M
    @MAKE_BLACK
    D;JGT
    @MAKE_WHITE
    0;JMP

(MAKE_BLACK)
    // 若 curr >= KBD-1，屏幕已满，不再推进
    @KBD
    D=A
    D=D-1
    @curr
    D=D-M
    @LISTENER_LOOP
    D;JLE
    // 推进 curr，涂黑
    @curr
    M=M+1          // curr++
    A=M
    M=-1
    @LISTENER_LOOP
    0;JMP

(MAKE_WHITE)
    // 若 curr < SCREEN，屏幕已空，不再后退
    @SCREEN
    D=A
    @curr
    D=D-M
    @LISTENER_LOOP
    D;JGT
    // 清白当前格，后退 curr
    @curr
    A=M
    M=0
    @curr
    M=M-1          // curr--
    @LISTENER_LOOP
    0;JMP