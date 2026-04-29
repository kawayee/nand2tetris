"""
JackTokenizer module
====================
Jack 语言词法分析器。读取 .jack 源文件，去掉注释与空白，
将剩余字符流切分为一连串 token，并按 API 提供访问接口。
Provides routines that skip comments and white space, get the next token, and advance
the input exactly beyond it. Other routines return the type of the current token, and 
its value.

Token 类型：
    KEYWORD, SYMBOL, IDENTIFIER, INT_CONST, STRING_CONST

Routine:
Constructor/Initializer(input file/stream) -> None
Opens the input .jack file / stream and gets ready to tokenize it.

hasMoreTokens() -> bool
Are there more tokens in the input?

advance() -> None
Gets the next token from the input, and makes it the current token. This method should 
be called only if hasMoreTokens is true. Initially there is no current token.

tokenType() -> {KEYWORD, SYMBOL, IDENTIFIER, INT_CONST, STRING_CONST}
Returns the type of the current token, as a constant.

keyWord() -> {CLASS, METHOD, FUNCTION, CONSTRUCTOR, INT, BOOLEAN, CHAR, VOID, VAR, 
              STATIC, FIELD, LET, DO, IF, ELSE, WHILE, RETURN, TRUE, FALSE, NULL, THIS}
Returns the keyword which is the current token, as a constant. This method should be 
called only if tokenType is KEYWORD.

symbol() -> str
Returns the character which is the current token. Should be called only if tokenType is SYMBOL.

identifier() -> str
Returns the string which is the current token. Should be called only if tokenType is IDENTIFIER.

intVal() -> int
Returns the integer value of the current token. Should be called only if tokenType is INT_CONST.

stringVal() -> str
Returns the string value of the current token, without the opening and closing double quotes.
Should be called only if tokenType is STRING_CONST.
"""

import re

class JackTokenizer:
    # Jack 语言关键字
    KEYWORDS = {
        'class', 'constructor', 'function', 'method', 'field', 'static',
        'var', 'int', 'char', 'boolean', 'void', 'true', 'false', 'null',
        'this', 'let', 'do', 'if', 'else', 'while', 'return'
    }

    # Token 类型常量
    KEYWORD = 'KEYWORD'
    SYMBOL = 'SYMBOL'
    IDENTIFIER = 'IDENTIFIER'
    INT_CONST = 'INT_CONST'
    STRING_CONST = 'STRING_CONST'

    # ----------------------------------------------------------------
    # Token 正则规范
    # ----------------------------------------------------------------
    # 顺序即优先级：
    #   1. 块注释 /* ... */（含 /** ... */）必须先于 SYM 的 `/`
    #   2. 行注释 // ... 同理
    #   3. 字符串放在注释之后，其内部不会再被注释规则扫一次
    #      （因为 finditer 以"最前位置 + 最长可匹配"为单位推进，
    #      一旦 STRING 命中，整段连同内部的 // 一起被消耗）
    #   4. SYM 放最后，避免它抢走 `/` 导致注释匹配失效
    #   5. MISMATCH 兜底，方便将来需要报错时定位非法字符
    _TOKEN_SPEC = [
        ('BLOCK_CMT', r'/\*[\s\S]*?\*/'),            # /* ... */ 与 /** ... */
        ('LINE_CMT',  r'//[^\n]*'),                  # // ...
        ('SKIP',      r'\s+'),                       # 空白
        ('STRING',    r'"[^"\n]*"'),                 # 字符串常量（Jack 不允许跨行）
        ('INT',       r'\d+'),                       # 整数常量
        ('IDENT',     r'[A-Za-z_]\w*'),              # 标识符或关键字
        ('SYM',       r'[{}()\[\].,;+\-*/&|<>=~]'),  # 符号
        ('MISMATCH',  r'.'),                         # 未知字符（兜底）
    ]
    _TOKEN_RE = re.compile(
        '|'.join(f'(?P<{name}>{pat})' for name, pat in _TOKEN_SPEC)
    )

    _SKIP_KINDS = {'BLOCK_CMT', 'LINE_CMT', 'SKIP', 'MISMATCH'}

    def __init__(self, inputPath):
        """读取源文件并完成一次性词法扫描。"""
        with open(inputPath, 'r', encoding='utf-8') as f:
            source = f.read()
        self.tokens, self.types = self._tokenize(source)
        self.index = -1
        self.currentToken = None
        self.currentType = None

    # ----------------------------------------------------------------
    # 扫描：用一条正则 + 命名组一次做完切分和分类
    # ----------------------------------------------------------------
    def _tokenize(self, src):
        tokens, types = [], []
        for m in self._TOKEN_RE.finditer(src):
            kind = m.lastgroup
            text = m.group()
            if kind in self._SKIP_KINDS:
                continue
            if kind == 'IDENT':
                tok_type = self.KEYWORD if text in self.KEYWORDS else self.IDENTIFIER
            elif kind == 'INT':
                tok_type = self.INT_CONST
            elif kind == 'STRING':
                tok_type = self.STRING_CONST
            else:  # 'SYM'
                tok_type = self.SYMBOL
            tokens.append(text)
            types.append(tok_type)
        return tokens, types

    # ----------------------------------------------------------------
    # API：遵循 nand2tetris 教材规范
    # ----------------------------------------------------------------
    def hasMoreTokens(self):
        return self.index < len(self.tokens) - 1

    def advance(self):
        """将当前 token 前移一位。仅当 hasMoreTokens() 为真时调用。"""
        self.index += 1
        self.currentToken = self.tokens[self.index]
        self.currentType = self.types[self.index]

    def tokenType(self):
        return self.currentType

    def keyword(self):
        return self.currentToken

    def symbol(self):
        return self.currentToken

    def identifier(self):
        return self.currentToken

    def intVal(self):
        return int(self.currentToken)

    def stringVal(self):
        # 去掉首尾双引号
        return self.currentToken[1:-1]

    def peek(self):
        """偷看下一个 token 但不前移，处理 term 中的歧义需要用到。"""
        if self.hasMoreTokens():
            return self.tokens[self.index + 1]
        return None

    def reset(self):
        """将游标复位，用于重复扫描（例如先输出 T.xml 再给解析器使用）。"""
        self.index = -1
        self.currentToken = None
        self.currentType = None