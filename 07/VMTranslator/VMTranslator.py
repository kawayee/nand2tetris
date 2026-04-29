'''
VMTranslator
• Constructs a Parser to handle the input file;
• Constructs a CodeWriter to handle the output file;
• Iterates through the input file, parsing each line and generating
assembly code from it, using the services of the Parser and a CodeWriter.

Input: fileName.vm
Output: An assembly file named fileName.asm
(the fileName may contain a file path; the first character of fileName must be an uppercase letter).
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
        else:
            # Project 7 不会遇到其它类型
            raise NotImplementedError(f"Project 7 不支持: {ctype}")


def main():
    if len(sys.argv) != 2:
        print("用法: python VMTranslator.py <input.vm 或 目录>")
        sys.exit(1)

    input_path = sys.argv[1]

    if os.path.isfile(input_path) and input_path.endswith(".vm"):
        # 单文件：Xxx.vm -> Xxx.asm
        output_file = input_path[:-3] + ".asm"
        writer = CodeWriter(output_file)
        translate_file(input_path, writer)
        writer.close()
        print(f"已生成: {output_file}")

    elif os.path.isdir(input_path):
        dir_path = os.path.normpath(input_path)
        dir_name = os.path.basename(dir_path)
        output_file = os.path.join(dir_path, dir_name + ".asm")
        writer = CodeWriter(output_file)
        for fname in sorted(os.listdir(dir_path)):
            if fname.endswith(".vm"):
                translate_file(os.path.join(dir_path, fname), writer)
        writer.close()
        print(f"已生成: {output_file}")

    else:
        print(f"错误: {input_path} 不是有效的 .vm 文件或目录")
        sys.exit(1)


if __name__ == "__main__":
    main()