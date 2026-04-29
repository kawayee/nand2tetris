'''
Usage:
Where source is either a single fileName.vm, or a folderName containing one or more .vm files;
(The source may contain a file path; the first character of filename must be an uppercase letter)
Output: A single assembly file named source.asm
(stored in the same folder as the source files)

Action
• Constructs a CodeWriter to handle the output file;
• If source is a .vm file:
    Constructs a Parser to handle the input file;
    For each VM command in the input file:
    uses the Parser to parse the command,
    uses the CodeWriter to generate assembly code from it
• If source is a folder:
    Handles every .vm file in the folder in the manner described above.
'''
import os
import sys

from VMParser import Parser
from CodeWriter import CodeWriter


def translate_file(vm_path, code_writer):
    """把一个 .vm 文件的所有命令翻译并追加到 code_writer。"""
    file_name = os.path.splitext(os.path.basename(vm_path))[0]
    code_writer.setFileName(file_name)

    parser = Parser(vm_path)
    while parser.hasMoreCommands():
        parser.advance()
        ctype = parser.commandType()

        if ctype == Parser.C_ARITHMETIC:
            code_writer.writeArithmetic(parser.arg1())
        elif ctype in (Parser.C_PUSH, Parser.C_POP):
            code_writer.writePushPop(ctype, parser.arg1(), parser.arg2())
        elif ctype == Parser.C_LABEL:
            code_writer.writeLabel(parser.arg1())
        elif ctype == Parser.C_GOTO:
            code_writer.writeGoto(parser.arg1())
        elif ctype == Parser.C_IF:
            code_writer.writeIf(parser.arg1())
        elif ctype == Parser.C_FUNCTION:
            code_writer.writeFunction(parser.arg1(), parser.arg2())
        elif ctype == Parser.C_CALL:
            code_writer.writeCall(parser.arg1(), parser.arg2())
        elif ctype == Parser.C_RETURN:
            code_writer.writeReturn()
        else:
            raise NotImplementedError(f"不支持的命令类型: {ctype}")


def main():
    if len(sys.argv) != 2:
        print("用法: python VMTranslator.py <input.vm 或 目录>")
        sys.exit(1)

    input_path = sys.argv[1]

    if os.path.isfile(input_path) and input_path.endswith(".vm"):
        # 单文件：Xxx.vm -> Xxx.asm，不生成 bootstrap
        output_file = input_path[:-3] + ".asm"
        writer = CodeWriter(output_file)
        try:
            translate_file(input_path, writer)
        finally:
            writer.close()
        print(f"已生成: {output_file}")

    elif os.path.isdir(input_path):
        dir_path = os.path.normpath(input_path)
        dir_name = os.path.basename(dir_path)
        output_file = os.path.join(dir_path, dir_name + ".asm")

        vm_files = sorted(f for f in os.listdir(dir_path) if f.endswith(".vm"))
        if not vm_files:
            print(f"错误: 目录 {dir_path} 中没有 .vm 文件")
            sys.exit(1)

        writer = CodeWriter(output_file)
        try:
            # 目录模式：生成 bootstrap
            writer.writeInit()
            for fname in vm_files:
                translate_file(os.path.join(dir_path, fname), writer)
        finally:
            writer.close()
        print(f"已生成: {output_file}")


if __name__ == "__main__":
    main()