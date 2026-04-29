"""
JackCompiler: 编译器主入口。
用法:
    python JackCompiler.py <Xxx.jack>     # 编译单个文件
    python JackCompiler.py <directory>    # 编译目录中所有 .jack 文件

input: 
    fileName.jack: name of a single file containing a Jack class, or
    folderName: name of a folder containing one or more .jack files
output: 
    If the input is a single file, the compiler generates the file fileName.vm
    If the input is a folder, the compiler generates one .vm file for every .jack file
    (the generated .vm files are stored in the same folder containing the source .jack files)

For each source .jack file, the compiler creates a JackTokenizer and an output .vm file;
Next, the compiler uses the CompilationEngine to write the VM code into the output .vm file.
"""

import os
import sys

from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine
from VMWriter import VMWriter


def compile_file(jack_path):
    base, _ = os.path.splitext(jack_path)
    vm_path = base + '.vm'

    tokenizer = JackTokenizer(jack_path)
    vm_writer = VMWriter(vm_path)
    engine = CompilationEngine(tokenizer, vm_writer)
    engine.compileClass()
    vm_writer.close()
    print(f'Compiled: {jack_path}  ->  {vm_path}')


def main():
    if len(sys.argv) != 2:
        print('Usage: python JackCompiler.py <file.jack | directory>')
        sys.exit(1)

    input_path = sys.argv[1]

    if os.path.isdir(input_path):
        jack_files = sorted(
            os.path.join(input_path, fname)
            for fname in os.listdir(input_path)
            if fname.endswith('.jack')
        )
        if not jack_files:
            print(f'No .jack files found in {input_path}')
            sys.exit(1)
        for path in jack_files:
            compile_file(path)
    elif os.path.isfile(input_path) and input_path.endswith('.jack'):
        compile_file(input_path)
    else:
        print(f'Invalid input_path: {input_path}')
        sys.exit(1)


if __name__ == '__main__':
    main()
