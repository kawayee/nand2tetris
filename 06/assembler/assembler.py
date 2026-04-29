"""
Initialize
Opens the input file (Prog.asm) and gets ready to process it.
Constructs a symbol table, and adds to it all the predefined symbols.

First pass
Reads the input file, line by line, focusing only on (label) declarations.
Adds the found labels to the symbol table.

Second pass (main loop)
(starts again from the beginning of the file)
While there are more lines to process:
    Gets the next instruction, and parses it
    If the instruction is @ symbol
        If symbol is not in the symbol table, adds it to the table
        Translates the symbol into its binary value
    If the instruction is dest =comp ; jump
        Translates each of the three fields into its binary value
    Assembles the binary values into a string of sixteen 0’s and 1’s.
    Writes the string to the output file.
"""

import os
import sys

from hack_parser import Parser
from code import Code
from symbol_table import SymbolTable


class Assembler:
    VAR_START_ADDRESS = 16

    def __init__(self, input_file: str):
        self.input_file = input_file
        self.parser = Parser(input_file)
        self.symbol_table = SymbolTable()
        self.next_var_address = self.VAR_START_ADDRESS

    # -------- 对外主流程 --------
    def assemble(self) -> list[str]:
        self._first_pass()
        return self._second_pass()

    # -------- 第一遍：收集标签 --------
    def _first_pass(self) -> None:
        rom_address = 0
        self.parser.reset()
        while self.parser.has_more_commands():
            self.parser.advance()
            ctype = self.parser.instructionType()
            if ctype == Parser.L_INSTRUCTION:
                label = self.parser.symbol()
                if not self._is_valid_symbol(label):
                    raise ValueError(f"非法标签名：{label!r}")
                self.symbol_table.addEntry(label, rom_address)
            else:
                rom_address += 1

    # -------- 第二遍：翻译指令 --------
    def _second_pass(self) -> list[str]:
        output: list[str] = []
        self.parser.reset()
        while self.parser.has_more_commands():
            self.parser.advance()
            ctype = self.parser.instructionType()
            if ctype == Parser.A_INSTRUCTION:
                output.append(self._translate_a())
            elif ctype == Parser.C_INSTRUCTION:
                output.append(self._translate_c())
            # L 指令不产生代码
        return output

    def _translate_a(self) -> str:
        sym = self.parser.symbol()
        if sym.isdigit():
            address = int(sym)
        else:
            if not self._is_valid_symbol(sym):
                raise ValueError(f"非法符号：{sym!r}")
            if not self.symbol_table.contains(sym):
                self.symbol_table.addEntry(sym, self.next_var_address)
                self.next_var_address += 1
            address = self.symbol_table.getAddress(sym)

        if not 0 <= address < (1 << 15):
            raise ValueError(f"A 指令地址越界：{address}")
        return f'0{address:015b}'

    def _translate_c(self) -> str:
        comp_bits = Code.comp(self.parser.comp())
        dest_bits = Code.dest(self.parser.dest())
        jump_bits = Code.jump(self.parser.jump())
        return f'111{comp_bits}{dest_bits}{jump_bits}'

    # -------- 工具 --------
    @staticmethod
    def _is_valid_symbol(s: str) -> bool:
        """Hack 符号规则：字母、数字、_、.、$、:；不得以数字开头。"""
        if not s:
            return False
        if s[0].isdigit():
            return False
        allowed = set("_.$:")
        return all(ch.isalnum() or ch in allowed for ch in s)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python assembler.py <input.asm>", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    if not input_file.endswith('.asm'):
        print("警告：输入文件不是 .asm 后缀", file=sys.stderr)
    output_file = os.path.splitext(input_file)[0] + '.hack'

    try:
        binary = Assembler(input_file).assemble()
    except (ValueError, FileNotFoundError) as e:
        print(f"汇编失败：{e}", file=sys.stderr)
        sys.exit(2)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(binary))
    #    if binary:
    #        f.write('\n')

    print(f"Assembled: {input_file}  →  {output_file}  ({len(binary)} instructions)")


if __name__ == '__main__':
    main()