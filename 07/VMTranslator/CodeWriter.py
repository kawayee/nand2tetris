'''
Generates assembly code from the parsed VM command
The components/fields of each VM command are supplied by the Parser routines;
Implement true as -1 (minus 1) and false as 0;

Routines
• constructor(): 
    opens an output file/stream and gets ready to write into it.
• writeArithmetic():
    writes to the output file the assembly code 
    that implements the given arithmetic-logical command. 
• WritePushPop():
    writes to the output file the assembly code 
    that implements the given push or pop command. 
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
        asm += [
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",
        ]
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

    # ================== 工具 ==================

    def _write(self, asm_lines):
        self.output.write("\n".join(asm_lines) + "\n")

    def close(self):
        self.output.close()