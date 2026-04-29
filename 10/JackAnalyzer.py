"""
JackAnalyzer module (main driver)
=================================
nand2tetris Project 10 的顶层驱动。

用法：
    python JackAnalyzer.py <source>
其中 <source> 是单个 .jack 文件或包含多个 .jack 文件的目录。
对每个输入文件 Foo.jack，本程序输出两个文件：
    FooT.xml  ——  词法分析结果（tokens）
    Foo.xml   ——  语法分析结果（parse tree）

input: 
fileName.jack: name of a single file containing a Jack class, or
folderName: name of a folder containing one or more .jack files
output: 
If the input is a single file, the Jack analyzer generates the file fileName.xml
If the input is a folder, the Jack analyzer generates one .xml file for every .jack file
(the generated .xml files are stored in the same folder containing the source .jack files)

Implementation
JackAnalyzer is the main module. For each file in the input, it:
1. Creates a JackTokenizer from fileName.jack
2. Creates an output file named fileName.xml
3. Creates a CompilationEngine, and calls the compileClass method
(compileClass will then do the rest of the parsing, recursively)
4. Closes the output file.
"""

import os
import sys

from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine

XML_ESCAPE = {'<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;'}

def writeTokensXml(tokenizer, outputPath):
    """输出仅包含 token 列表的 XML（供 TextComparer 对照 xxxT.xml）。"""
    tokenizer.reset()
    with open(outputPath, 'w', encoding='utf-8') as f:
        f.write('<tokens>\n')
        while tokenizer.hasMoreTokens():
            tokenizer.advance()
            tt = tokenizer.tokenType()
            if tt == tokenizer.KEYWORD:
                f.write(f'<keyword> {tokenizer.keyword()} </keyword>\n')
            elif tt == tokenizer.SYMBOL:
                sym = XML_ESCAPE.get(tokenizer.symbol(), tokenizer.symbol())
                f.write(f'<symbol> {sym} </symbol>\n')
            elif tt == tokenizer.IDENTIFIER:
                f.write(f'<identifier> {tokenizer.identifier()} </identifier>\n')
            elif tt == tokenizer.INT_CONST:
                f.write(f'<integerConstant> {tokenizer.intVal()} </integerConstant>\n')
            elif tt == tokenizer.STRING_CONST:
                f.write(f'<stringConstant> {tokenizer.stringVal()} </stringConstant>\n')
        f.write('</tokens>\n')


def analyzeFile(jackPath):
    base, _ = os.path.splitext(jackPath)
    tokensXml = base + 'T.xml'
    parseXml = base + '.xml'

        # 先生成 tokens XML
    try:
        tokenizer = JackTokenizer(jackPath)
        writeTokensXml(tokenizer, tokensXml)

       # 重置后由 CompilationEngine 驱动生成解析树 XML
        tokenizer.reset()
        CompilationEngine(tokenizer, parseXml)

        print(f'[ok] {jackPath}')
        print(f'      -> {tokensXml}')
        print(f'      -> {parseXml}')
    except Exception as e:
        # 加上 try-catch，如果某个文件有语法错误或读取失败，只报错不退出
        print(f'[error] Failed to process {jackPath}: {e}')


def main():
    if len(sys.argv) != 2:
        print('Usage: python JackAnalyzer.py <file.jack | directory>')
        sys.exit(1)

    input_path = os.path.normpath(sys.argv[1])

    if os.path.isfile(input_path):
        if not input_path.endswith('.jack'):
            print('Input file must have .jack extension')
            sys.exit(1)
        analyzeFile(input_path)
    elif os.path.isdir(input_path):
        jackFiles = sorted(
            os.path.join(input_path, name)
            for name in os.listdir(input_path)
            if name.endswith('.jack')
        )
        if not jackFiles:
            print(f'No .jack files found in {input_path}')
            sys.exit(1)
        for jp in jackFiles:
            analyzeFile(jp)
    else:
        print(f'Invalid path: {input_path}')
        sys.exit(1)


if __name__ == '__main__':
    main()
