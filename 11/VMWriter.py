"""
VMWriter: 输出 VM 命令到 .vm 文件。

Routine
Constructor(output file/steam): -> VMWriter 
Creates a new output .vm file/stream and prepares it for writing VM commands.

writePush(segment: CONST/ARG/LOCAL/STATIC/THIS/THAT/POINTER/TEMP, index: int): -> void 
Writes a VM push command.

writePop(segment: CONST/ARG/LOCAL/STATIC/THIS/THAT/POINTER/TEMP, index: int): -> void 
Writes a VM pop command.

writeArithmetic(command: ADD/SUB/NEG/EQ/GT/LT/AND/OR/NOT): -> void
Writes a VM arithmetic command.

writeLabel(label: String): -> void 
Writes a VM label command.

writeGoto(label: String): -> void 
Writes a VM goto command.

writeIf(label: String): -> void 
Writes a VM If-goto command.

writeCall(name: String, nArgs: int): -> void 
Writes a VM call command.

writeFunction(name: String, nLocals: int): -> void 
Writes a VM function command.

writeReturn(): -> void 
Writes a VM return command.

close(): -> void 
Closes the output file/stream.
"""

class VMWriter:
    # 段
    CONST = 'constant'
    ARG = 'argument'
    LOCAL = 'local'
    STATIC = 'static'
    THIS = 'this'
    THAT = 'that'
    POINTER = 'pointer'
    TEMP = 'temp'

    # 算术 / 逻辑命令
    ADD = 'add'
    SUB = 'sub'
    NEG = 'neg'
    EQ = 'eq'
    GT = 'gt'
    LT = 'lt'
    AND = 'and'
    OR = 'or'
    NOT = 'not'

    def __init__(self, output_path):
        self.f = open(output_path, 'w', encoding='utf-8')

    def writePush(self, segment, index):
        self.f.write(f'push {segment} {index}\n')

    def writePop(self, segment, index):
        self.f.write(f'pop {segment} {index}\n')

    def writeArithmetic(self, command):
        self.f.write(f'{command}\n')

    def writeLabel(self, label):
        self.f.write(f'label {label}\n')

    def writeGoto(self, label):
        self.f.write(f'goto {label}\n')

    def writeIf(self, label):
        self.f.write(f'if-goto {label}\n')

    def writeCall(self, name, n_args):
        self.f.write(f'call {name} {n_args}\n')

    def writeFunction(self, name, n_locals):
        self.f.write(f'function {name} {n_locals}\n')

    def writeReturn(self):
        self.f.write('return\n')

    def close(self):
        self.f.close()
