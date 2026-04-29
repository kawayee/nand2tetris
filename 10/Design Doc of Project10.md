# nand2tetris Project 10 — Jack Syntax Analyzer

本目录实现 *The Elements of Computing Systems* Part II 第 10 章要求的 Jack 语言语法分析器。程序读入 Jack 源文件，输出两个 XML 文件：

- `XxxT.xml`：词法分析结果（token 列表）。
- `Xxx.xml`：语法分析结果（parser tree）。

生成的 XML 可直接交给教材附带的 `TextComparer` 与参考答案逐行比对。

## 文件结构

| 文件 | 作用 |
| ---- | ---- |
| `JackTokenizer.py`   | 词法分析器。去注释、切 token，并提供教材规定的 API。|
| `CompilationEngine.py` | 递归下降解析器。按 Jack 文法逐条匹配非终结符并输出 XML。|
| `JackAnalyzer.py`    | 顶层驱动，接受文件或目录参数并调度前两者。|

## 使用方法

```bash
# 对单个文件进行分析
python JackAnalyzer.py path/to/Main.jack

# 对整个目录下的所有 .jack 文件进行分析
python JackAnalyzer.py path/to/Square/
```

每个 `Foo.jack` 会在其所在目录生成：

```
FooT.xml     # tokens 输出
Foo.xml      # parse tree 输出
```

## 实现要点

1. **词法扫描单次完成**：`JackTokenizer._tokenize` 在同一趟扫描里同时处理空白、行注释 `//`、块注释 `/* */` 和 `/** */`、以及字符串常量，避免了“先删注释再切词”在遇到形如 `"hello // world"` 的字符串时误删字符串内容。

2. **符号转义**：`<`, `>`, `&`, `"` 按 XML 规范分别转义为 `&lt;`, `&gt;`, `&amp;`, `&quot;`。输出文件中的字符串常量应不带`"`。

3. **term 的歧义消解**：`compileTerm` 在看到标识符后利用下一个 token（`[`、`(`、`.` 或其他）区分 `varName`、数组访问、无限定子例程调用和带限定子例程调用这四种情形，对应教材 10.2.5 节的要求。

4. **标签规范遵守教材**：输出包含 `class / classVarDec / subroutineDec / parameterList / subroutineBody / varDec / statements / letStatement / ifStatement / whileStatement / doStatement / returnStatement / expression / term / expressionList` 等非终结符标签；`type / className / subroutineName / variableName / statement / subroutineCall` 不单独输出，与 `CompareFiles` 的参考答案一致。

5. **对齐缩进**：每层非终结符缩进两个空格，便于人工阅读（缩进对 `TextComparer` 不敏感）。

6. **处理bug**：课程默认所有source code内没有bug。

## 测试

教材附带的所有样例（`ExpressionLessSquare/`、`Square/`、`ArrayTest/`）均可直接作为本程序输入。对目录调用后，将生成的 `*.xml` 逐一交给 `../tools/TextComparer.sh` 与参考答案比较即可得到 `Comparison ended successfully`。
