"""
Routines
• Constructor / initializer: Creates a Parser and opens the source text file
• Getting the current instruction:
    hasMoreLines(): Checks if there is more work to do (boolean)
    advance(): Gets the next instruction and makes it the current instruction (string)
• Parsing the current instruction:
    instructionType(): Returns the type of the current instruction, as a constant:
        A_INSTRUCTION for @xxx
        C_INSTRUCTION for dest=comp;jump
        L_INSTRUCTION for (label)
    symbol(): Returns the instruction’s symbol (string)
    dest(): Returns the instruction’s dest field (string)
    comp(): Returns the instruction’s comp field (string)
    jump(): Returns the instruction’s jump field (string)
"""

class Parser:
    A_INSTRUCTION = 'A_INSTRUCTION'
    C_INSTRUCTION = 'C_INSTRUCTION'
    L_INSTRUCTION = 'L_INSTRUCTION'   # 伪指令：标签定义

    def __init__(self, input_file: str):
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_lines = f.readlines()
        # 预处理：去除注释与全部空白；丢弃空行
        self.lines = [s for s in (self._clean(ln) for ln in raw_lines) if s]
        self.current = -1

    @staticmethod
    def _clean(line: str) -> str:
        idx = line.find('//')
        if idx != -1:
            line = line[:idx]
        # Hack 汇编标识符不含空格，可以安全去除全部空白
        return ''.join(line.split())

    def has_more_commands(self) -> bool:
        return self.current + 1 < len(self.lines)

    def advance(self) -> None:
        self.current += 1

    def reset(self) -> None:
        """两遍扫描之间重置游标。"""
        self.current = -1

    def instructionType(self) -> str:
        line = self.lines[self.current]
        if line.startswith('@'):
            return self.A_INSTRUCTION
        if line.startswith('(') and line.endswith(')'):
            return self.L_INSTRUCTION
        return self.C_INSTRUCTION

    def symbol(self) -> str:
        """仅用于 A 指令或 L 指令。"""
        line = self.lines[self.current]
        if line.startswith('@'):
            return line[1:]
        if line.startswith('('):
            return line[1:-1]
        raise ValueError(f"symbol() 不适用于 C 指令：{line}")

    def dest(self) -> str:
        line = self.lines[self.current]
        return line.split('=', 1)[0] if '=' in line else ''

    def comp(self) -> str:
        line = self.lines[self.current]
        if '=' in line:
            line = line.split('=', 1)[1]
        if ';' in line:
            line = line.split(';', 1)[0]
        return line

    def jump(self) -> str:
        line = self.lines[self.current]
        return line.split(';', 1)[1] if ';' in line else ''