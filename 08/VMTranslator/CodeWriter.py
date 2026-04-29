'''
Generates assembly code from the parsed VM command
The components/fields of each VM command are supplied by the Parser routines;
Implement true as -1 (minus 1) and false as 0;

Routines
• constructor(output file/stream): 
    opens an output file/stream and gets ready to write into it.
• setFileName(fileName: string): 
    informs that the translation of a new VM file has started(called by the VMTranslator).
• writeArithmetic(command: string):
    writes to the output file the assembly code 
    that implements the given arithmetic-logical command. 
• WritePushPop(command: C_PUSH/C_POP, segment: string, index: int):
    writes to the output file the assembly code 
    that implements the given push or pop command. 
• writeInit():
    writes the assembly instructions that effect the VM initialization
    (also called bootstrap code): SP=256 and call Sys.init,
    and this code must be placed at the beginning of the generated *.asm file.
• writeLabel(label: string):
    writes assembly code that effects the label command.
• writeGoto(label: string):
    writes assembly code that effects the goto command.
• writeIf(label: string):
    writes assembly code that effects the if-goto command.
• writeFunction(functionName: string, nVars: int):
    writes assembly code that effects the function command.
• writeCall(functionName: string, nArgs: int):
    writes assembly code that effects the call command.
• writeReturn():
    writes assembly code that effects the return command.
• close(): 
    close the output file.
'''

class CodeWriter:
    # 段名 -> Hack 中对应的基址符号
    SEGMENT_POINTERS = {
        "local": "LCL",
        "argument": "ARG",
        "this": "THIS",
        "that": "THAT",
    }

    def __init__(self, output_file):
        self.output = open(output_file, "w", encoding="utf-8")
        self.label_count = 0   # eq/gt/lt 生成唯一 label 用
        self.file_name = ""    # 当前翻译的 .vm 文件名（不含路径和扩展名）
        self.current_function = None  # 当前正在翻译的函数名（用于 label/goto 前缀）
        self.call_counts = {}         # 每个函数内部的 call 计数，用于生成唯一返回标签

    def setFileName(self, file_name: str):
        """切换文件时调用，用于 static 段的符号前缀。"""
        self.file_name = file_name

    # ================== 算术/逻辑命令 ==================

    def writeArithmetic(self, command: str):
        if command == "add":
            self._binary_op("M=D+M")
        elif command == "sub":
            self._binary_op("M=M-D")
        elif command == "and":
            self._binary_op("M=D&M")
        elif command == "or":
            self._binary_op("M=D|M")
        elif command == "neg":
            self._unary_op("M=-M")
        elif command == "not":
            self._unary_op("M=!M")
        elif command in ("eq", "gt", "lt"):
            self._comparison(command)
        else:
            raise ValueError(f"未知算术命令: {command}")

    def _binary_op(self, op):
        """
        从栈顶弹出 y，把栈顶 x 替换为 x op y。
        SP 整体减一。
        """
        asm = [
            "@SP",
            "AM=M-1",   # SP--, A 指向 y
            "D=M",      # D = y
            "A=A-1",    # A 指向 x
            op,         # M = x op y
        ]
        self._write(asm)

    def _unary_op(self, op):
        """对栈顶元素原地施加一元运算。"""
        asm = [
            "@SP",
            "A=M-1",
            op,
        ]
        self._write(asm)

    def _comparison(self, command):
        """eq / gt / lt：比较栈顶两个元素，把 true(-1) 或 false(0) 写回栈顶。"""
        jump = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}[command]
        label_true = f"TRUE_{self.label_count}"
        label_end = f"END_{self.label_count}"
        self.label_count += 1

        asm = [
            "@SP",
            "AM=M-1",
            "D=M",          # D = y
            "A=A-1",        # A 指向 x
            "D=M-D",        # D = x - y
            f"@{label_true}",
            f"D;{jump}",
            "@SP",
            "A=M-1",
            "M=0",          # false
            f"@{label_end}",
            "0;JMP",
            f"({label_true})",
            "@SP",
            "A=M-1",
            "M=-1",         # true
            f"({label_end})",
        ]
        self._write(asm)

    # ================== push / pop ==================

    def writePushPop(self, command, segment: str, index: int):
        if command == "C_PUSH":
            self._push(segment, index)
        elif command == "C_POP":
            self._pop(segment, index)
        else:
            raise ValueError(f"不是 push/pop 命令: {command}")

    def _push(self, segment, index):
        if segment == "constant":
            asm = [
                f"@{index}",
                "D=A",
            ]
        elif segment in self.SEGMENT_POINTERS:
            base = self.SEGMENT_POINTERS[segment]
            asm = [
                f"@{index}",
                "D=A",
                f"@{base}",
                "A=D+M",       # A = base + index
                "D=M",         # D = *(base+index)
            ]
        elif segment == "temp":
            # temp 基址为 R5，共 8 个槽位
            asm = [
                f"@{5 + index}",
                "D=M",
            ]
        elif segment == "pointer":
            # pointer 0 -> THIS, pointer 1 -> THAT
            base = "THIS" if index == 0 else "THAT"
            asm = [
                f"@{base}",
                "D=M",
            ]
        elif segment == "static":
            # 静态变量使用  文件名.索引  的符号
            asm = [
                f"@{self.file_name}.{index}",
                "D=M",
            ]
        else:
            raise ValueError(f"未知段: {segment}")

        # 统一的压栈尾部：*SP = D; SP++
        asm += self._push_d()
        self._write(asm)

    def _pop(self, segment, index):
        if segment == "constant":
            raise ValueError("不能 pop 到 constant 段")

        if segment in self.SEGMENT_POINTERS:
            base = self.SEGMENT_POINTERS[segment]
            # 先把目标地址 base+index 存到 R13，再弹栈写入
            asm = [
                f"@{index}",
                "D=A",
                f"@{base}",
                "D=D+M",        # D = base + index
                "@R13",
                "M=D",          # R13 = base + index
                "@SP",
                "AM=M-1",
                "D=M",          # D = 栈顶的值
                "@R13",
                "A=M",
                "M=D",
            ]
        elif segment == "temp":
            asm = [
                "@SP",
                "AM=M-1",
                "D=M",
                f"@{5 + index}",
                "M=D",
            ]
        elif segment == "pointer":
            base = "THIS" if index == 0 else "THAT"
            asm = [
                "@SP",
                "AM=M-1",
                "D=M",
                f"@{base}",
                "M=D",
            ]
        elif segment == "static":
            asm = [
                "@SP",
                "AM=M-1",
                "D=M",
                f"@{self.file_name}.{index}",
                "M=D",
            ]
        else:
            raise ValueError(f"未知段: {segment}")

        self._write(asm)

    # ================== 分支命令 ==================

    def writeLabel(self, label: str):
        """label 命令：生成带函数作用域的汇编标签。"""
        self._write([f"({self._scoped_label(label)})"])

    def writeGoto(self, label: str):
        """goto 命令：无条件跳转到 functionName$label。"""
        asm = [
            f"@{self._scoped_label(label)}",
            "0;JMP",
        ]
        self._write(asm)

    def writeIf(self, label: str):
        """if-goto 命令：弹出栈顶，若非 0 则跳转。"""
        asm = [
            "@SP",
            "AM=M-1",
            "D=M",
            f"@{self._scoped_label(label)}",
            "D;JNE",
        ]
        self._write(asm)

    def _scoped_label(self, label: str) -> str:
        """按照 Symbol Conventions：标签形如 functionName$label。"""
        if self.current_function:
            return f"{self.current_function}${label}"
        return label

    # ================== 函数命令 ==================

    def writeFunction(self, function_name: str, n_vars: int):
        """
        函数入口：生成 (functionName) 标签，
        然后 push n_vars 个 0 初始化 local 段。
        """
        self.current_function = function_name
        asm = [f"({function_name})"]
        for _ in range(n_vars):
            asm += [
                "@SP",
                "A=M",
                "M=0",
                "@SP",
                "M=M+1",
            ]
        self._write(asm)

    def writeCall(self, function_name: str, n_args: int):
        """
        call functionName nArgs 的标准实现：
          push returnAddress
          push LCL / ARG / THIS / THAT
          ARG = SP - 5 - nArgs
          LCL = SP
          goto functionName
          (returnAddress)
        """
        caller = self.current_function if self.current_function else "null"
        i = self.call_counts.get(caller, 0)
        self.call_counts[caller] = i + 1
        return_label = f"{caller}$ret.{i}"

        asm = []

        # push returnAddress
        asm += [f"@{return_label}", "D=A"]
        asm += self._push_d()

        # push LCL, ARG, THIS, THAT
        for sym in ("LCL", "ARG", "THIS", "THAT"):
            asm += [f"@{sym}", "D=M"]
            asm += self._push_d()

        # ARG = SP - 5 - nArgs
        asm += [
            "@SP",
            "D=M",
            "@5",
            "D=D-A",
            f"@{n_args}",
            "D=D-A",
            "@ARG",
            "M=D",
        ]

        # LCL = SP
        asm += [
            "@SP",
            "D=M",
            "@LCL",
            "M=D",
        ]

        # goto functionName
        asm += [f"@{function_name}", "0;JMP"]

        # (returnAddress)
        asm += [f"({return_label})"]

        self._write(asm)

    def writeReturn(self):
        """
        return 的标准实现（R13 = endFrame，R14 = retAddr）：
          endFrame = LCL
          retAddr  = *(endFrame - 5)
          *ARG     = pop()
          SP       = ARG + 1
          THAT     = *(endFrame - 1)
          THIS     = *(endFrame - 2)
          ARG      = *(endFrame - 3)
          LCL      = *(endFrame - 4)
          goto retAddr
        """
        asm = [
            # R13 = LCL (endFrame)
            "@LCL", "D=M",
            "@R13", "M=D",

            # R14 = *(endFrame - 5) (retAddr)
            # 此时 D 仍然等于 endFrame
            "@5", "A=D-A",
            "D=M",
            "@R14", "M=D",

            # *ARG = pop()
            "@SP", "AM=M-1",
            "D=M",
            "@ARG", "A=M",
            "M=D",

            # SP = ARG + 1
            "@ARG", "D=M+1",
            "@SP", "M=D",

            # THAT = *(endFrame - 1)
            "@R13", "AM=M-1",
            "D=M",
            "@THAT", "M=D",

            # THIS = *(endFrame - 2)
            "@R13", "AM=M-1",
            "D=M",
            "@THIS", "M=D",

            # ARG = *(endFrame - 3)
            "@R13", "AM=M-1",
            "D=M",
            "@ARG", "M=D",

            # LCL = *(endFrame - 4)
            "@R13", "AM=M-1",
            "D=M",
            "@LCL", "M=D",

            # goto retAddr
            "@R14", "A=M",
            "0;JMP",
        ]
        self._write(asm)

    # ================== 工具 ==================

    def _push_d(self):
        """把 D 寄存器的值压栈：*SP = D; SP++。"""
        return [
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",
        ]

    def _write(self, asm_lines):
        self.output.write("\n".join(asm_lines) + "\n")

    def close(self):
        self.output.close()
    
    # ================== Bootstrap ==================

    def writeInit(self):
        """引导代码：SP=256，然后 call Sys.init 0。"""
        asm = [
            "@256",
            "D=A",
            "@SP",
            "M=D",
        ]
        self._write(asm)
        self.writeCall("Sys.init", 0)