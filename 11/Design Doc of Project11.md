Project 11: Extend the syntax analyzer into a full-scale compiler
Stage 0: Syntax analyzer (done)
Stage 1: Symbol table handling
Stage 2: Code generation.

Stage 1
Extending the handling of identifiers:
In addition to outputting the identifier, we’ll also output:
1. the identifier’s category: var, argument, static, field, class, subroutine.
2. if the category is var, argument, static, field: the running index assigned to this variable.
3. whether the identifier is being defined, or being used.

Implementation / testing
1. Implement the SymbolTable API.
2. Extend the syntax analyzer developed in project 10 with the outputs described above
(plan and use your own output format).
3. Test your symbol table implementation by running the extended syntax analyzer on the test programs given in project 10.

Stage 2
Test your evolving compiler on the supplied test programs, in the shown order.
Each test program is designed to test some of the compiler’s capabilities.
Test programs
1. Seven
2. ConvertToBin
3. Square
4. Average
5. Pong
6. ComplexArrays

For each test program:
1. Use your compiler to compile the program folder
2. Inspect the generated code;
If there’s a problem, fix your compiler and go to stage 1
3. Load the folder into the VM emulator
4. Run the compiled program, inspect the results
5. If there’s a problem, fix your compiler and go to stage 1.