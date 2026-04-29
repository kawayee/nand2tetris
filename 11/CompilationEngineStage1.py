"""
CompilationEngine module
========================
Jack 语言递归下降语法分析器。依据 Jack 文法逐条匹配非终结符，
并将解析结果按照 nand2tetris 教材规定的 XML 格式输出到文件。
Gets its input from a JackTokenizer, and emits its output to an output file, using
parsing routines. Each parsing routine compilexxx is responsible for handling all 
the tokens that make up xxx, advancing the tokenizer exactly beyond these tokens, 
and outputting the parsing of xxx.

Routine:
Constructor/Initializer(input stream/file, output stream/file) -> None
Creates a new compilation engine with the given input and output. 
The next routine called (by the JackAnalyzer module) must be compileClass.

compileClass() -> None
Compiles a complete class.

compileClassVarDec() -> None
Compiles a static variable declaration, or a field declaration.

compileSubroutine() -> None
Compiles a complete method, function, or constructor.

compileParameterList() -> None
Compiles a (possibly empty) parameter list. Does not handle the enclosing parentheses tokens ( and ).

compileSubroutineBody() -> None
Compiles a subroutine's body.

compileVarDec() -> None
Compiles a var declaration.

compileStatements() -> None
Compiles a sequence of statements. Does not handle the enclosing curly bracket tokens { and }.

compileLet() -> None
Compiles a let statement.

compileIf() -> None
Compiles an if statement, possibly with a trailing else clause.

compileWhile() -> None
Compiles a while statement.

compileDo() -> None
Compiles a do statement.

compileReturn() -> None
Compiles a return statement.

compileExpression() -> None
Compiles an expression.

compileTerm() -> None
Compiles a *term*. If the current token is an *identifier*, the routine must resolve it 
into a *variable*, an *array entry*, or a *subroutine call*. A single lookahead token, 
which may be [, (, or ., suffices to distinguish between the possibilities. Any other 
token is not part of this term and should not be advanced over.

compileExpressionList() -> int
Compiles a (possibly empty) comma-separated list of expressions. Returns the number of 
expressions in the list.

Parsing tip 8:
Six nonterminal grammar elements (subroutineCall, subroutineName, varName, className, 
type, statement) have no corresponding compilexxx methods. 

In our proposed API these terminals are parsed directly, by other parsing methods that 
handle them. This makes the analyzer's implementation simpler.
"""
from SymbolTable import SymbolTable

class CompilationEngine:
    OPS = set('+-*/&|<>=')
    UNARY_OPS = {'-', '~'}
    XML_ESCAPE = {'<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;'}

    def __init__(self, tokenizer, outputPath):
        self.tk = tokenizer
        self.out = open(outputPath, 'w', encoding='utf-8')
        self.indent = 0
        self.symbols = SymbolTable()
        self.className = ''
        # 读入第一个 token 后即进入顶层 class 解析
        if(self.tk.hasMoreTokens()):
            self.tk.advance()
            self.compileClass()
        self.out.close()

    # ----------------------------------------------------------------
    # 输出辅助
    # ----------------------------------------------------------------
    def _emit(self, line):
        self.out.write('  ' * self.indent + line + '\n')

    def _open(self, tag):
        self._emit(f'<{tag}>')
        self.indent += 1

    def _close(self, tag):
        self.indent -= 1
        self._emit(f'</{tag}>')

    def _writeToken(self):
        """将当前 token 以正确的 XML 标签写出，然后前移。"""
        tt = self.tk.tokenType()
        if tt == self.tk.KEYWORD:
            self._emit(f'<keyword> {self.tk.keyword()} </keyword>')
        elif tt == self.tk.SYMBOL:
            sym = self.XML_ESCAPE.get(self.tk.symbol(), self.tk.symbol())
            self._emit(f'<symbol> {sym} </symbol>')
        elif tt == self.tk.IDENTIFIER:
            self._emit(f'<identifier> {self.tk.identifier()} </identifier>')
        elif tt == self.tk.INT_CONST:
            self._emit(f'<integerConstant> {self.tk.intVal()} </integerConstant>')
        elif tt == self.tk.STRING_CONST:
            self._emit(f'<stringConstant> {self.tk.stringVal()} </stringConstant>')
        if self.tk.hasMoreTokens():
            self.tk.advance()

    def _writeIdentifier(self, category, usage, index=None):
        """输出 identifier 并附带 category / usage / index 属性。"""
        name = self.tk.identifier()
        attrs = f' category="{category}" usage="{usage}"'
        if index is not None:
            attrs += f' index="{index}"'
        self._emit(f'<identifier{attrs}> {name} </identifier>')
        if self.tk.hasMoreTokens():
            self.tk.advance()

    def _writeType(self):
        """输出 type token：keyword类型直接写出，class类型作为 class/used 输出。"""
        if self.tk.tokenType() == self.tk.KEYWORD:
            self._writeToken()          # int / char / boolean / void
        else:
            self._writeIdentifier('class', 'used')  # 用户自定义类型（类名）

    def _writeVarUse(self):
        """输出一个"正在被使用"的变量标识符，自动从符号表查找信息。"""
        name = self._cur()
        kind = self.symbols.kindOf(name)
        if kind != SymbolTable.NONE:
            self._writeIdentifier(kind, 'used', self.symbols.indexOf(name))
        else:
            # 无错误 Jack 代码中，查不到说明是类名（理论上不应出现在纯变量位置）
            self._writeIdentifier('class', 'used')

    # 当前待写的 token
    def _cur(self):
        return self.tk.currentToken

    # ----------------------------------------------------------------
    # 程序结构
    # ----------------------------------------------------------------
    def compileClass(self):
        self._open('class')
        self._writeToken()  # 'class'
        self.className = self._cur()
        self._writeIdentifier('class', 'defined')  # className
        self._writeToken()  # '{'
        while self._cur() in ('static', 'field'):
            self.compileClassVarDec()
        while self._cur() in ('constructor', 'function', 'method'):
            self.compileSubroutine()
        self._writeToken()  # '}'
        self._close('class')

    def compileClassVarDec(self):
        self._open('classVarDec')
        kind = self._cur() 
        self._writeToken()  # static/field
        type_ = self._cur()
        self._writeType()  # type
        name = self._cur()
        self.symbols.define(name, type_, kind)
        self._writeIdentifier(kind, 'defined', self.symbols.indexOf(name))  # varName
        while self._cur() == ',':
            self._writeToken()  # ','
            name = self._cur()
            self.symbols.define(name, type_, kind)
            self._writeIdentifier(kind, 'defined', self.symbols.indexOf(name))  # varName
        self._writeToken()  # ';'
        self._close('classVarDec')

    def compileSubroutine(self):
        self._open('subroutineDec')
        self.symbols.reset()
        funcType = self._cur()
        if funcType == 'method':
            self.symbols.define('this', self.className, SymbolTable.ARG)
        self._writeToken()  # constructor/function/method
        self._writeType()  # void|type
        self._writeIdentifier('subroutine', 'defined')  # subroutineName
        self._writeToken()  # '('
        self.compileParameterList()
        self._writeToken()  # ')'
        self.compileSubroutineBody()
        self._close('subroutineDec')

    def compileParameterList(self):
        self._open('parameterList')
        if self._cur() != ')':
            type_ = self._cur()
            self._writeType()  # type
            name = self._cur()
            self.symbols.define(name, type_, SymbolTable.ARG)
            self._writeIdentifier('arg', 'defined', self.symbols.indexOf(name))  # varName
            while self._cur() == ',':
                self._writeToken()  # ','
                type_ = self._cur()
                self._writeType()  # type
                name = self._cur()
                self.symbols.define(name, type_, SymbolTable.ARG)
                self._writeIdentifier('arg', 'defined', self.symbols.indexOf(name))  # varName
        self._close('parameterList')

    def compileSubroutineBody(self):
        self._open('subroutineBody')
        self._writeToken()  # '{'
        while self._cur() == 'var':
            self.compileVarDec()
        self.compileStatements()
        self._writeToken()  # '}'
        self._close('subroutineBody')

    def compileVarDec(self):
        self._open('varDec')
        self._writeToken()  # 'var'
        type_ = self._cur()
        self._writeType()  # type
        name = self._cur()
        self.symbols.define(name, type_, SymbolTable.VAR)
        self._writeIdentifier('var', 'defined', self.symbols.indexOf(name))  # varName
        while self._cur() == ',':
            self._writeToken()  # ','
            name = self._cur()
            self.symbols.define(name, type_, SymbolTable.VAR)
            self._writeIdentifier('var', 'defined', self.symbols.indexOf(name))  # varName
        self._writeToken()  # ';'
        self._close('varDec')

    # ----------------------------------------------------------------
    # 语句
    # ----------------------------------------------------------------
    def compileStatements(self):
        self._open('statements')
        while self._cur() in ('let', 'if', 'while', 'do', 'return'):
            kw = self._cur()
            if kw == 'let':
                self.compileLet()
            elif kw == 'if':
                self.compileIf()
            elif kw == 'while':
                self.compileWhile()
            elif kw == 'do':
                self.compileDo()
            elif kw == 'return':
                self.compileReturn()
        self._close('statements')

    def compileLet(self):
        self._open('letStatement')
        self._writeToken()  # 'let'
        self._writeVarUse()  # varName
        if self._cur() == '[':
            self._writeToken()  # '['
            self.compileExpression()
            self._writeToken()  # ']'
        self._writeToken()  # '='
        self.compileExpression()
        self._writeToken()  # ';'
        self._close('letStatement')

    def compileIf(self):
        self._open('ifStatement')
        self._writeToken()  # 'if'
        self._writeToken()  # '('
        self.compileExpression()
        self._writeToken()  # ')'
        self._writeToken()  # '{'
        self.compileStatements()
        self._writeToken()  # '}'
        if self._cur() == 'else':
            self._writeToken()  # 'else'
            self._writeToken()  # '{'
            self.compileStatements()
            self._writeToken()  # '}'
        self._close('ifStatement')

    def compileWhile(self):
        self._open('whileStatement')
        self._writeToken()  # 'while'
        self._writeToken()  # '('
        self.compileExpression()
        self._writeToken()  # ')'
        self._writeToken()  # '{'
        self.compileStatements()
        self._writeToken()  # '}'
        self._close('whileStatement')

    def compileDo(self):
        self._open('doStatement')
        self._writeToken()  # 'do'
        # 处理两种形式的 subroutineCall:
        # subroutineName '(' expressionList ')'
        # (className|varName) '.' subroutineName '(' expressionList ')'
        name = self._cur()
        if self.tk.peek() == '.':
            # 先输出 '.' 前面的标识符
            kind = self.symbols.kindOf(name)
            if kind != SymbolTable.NONE:
                # 在符号表中 → 是对象变量（被使用）
                self._writeIdentifier(kind, 'used', self.symbols.indexOf(name))
            else:
                # 不在符号表 → 是类名
                self._writeIdentifier('class', 'used')
            self._writeToken()                        # '.'
            self._writeIdentifier('subroutine', 'used')  # subroutineName
        else:
            # 直接调用本类方法
            self._writeIdentifier('subroutine', 'used')
        self._writeToken()  # '('
        self.compileExpressionList()
        self._writeToken()  # ')'
        self._writeToken()  # ';'
        self._close('doStatement')

    def compileReturn(self):
        self._open('returnStatement')
        self._writeToken()  # 'return'
        if self._cur() != ';':
            self.compileExpression()
        self._writeToken()  # ';'
        self._close('returnStatement')

    # ----------------------------------------------------------------
    # 表达式
    # ----------------------------------------------------------------
    def compileExpression(self):
        self._open('expression')
        self.compileTerm()
        while self._cur() in self.OPS:
            self._writeToken()  # op
            self.compileTerm()
        self._close('expression')

    def compileTerm(self):
        self._open('term')
        tt = self.tk.tokenType()
        tok = self._cur()

        if tt == self.tk.INT_CONST or tt == self.tk.STRING_CONST:
            self._writeToken()
        elif tt == self.tk.KEYWORD:
            # 预留容错位置，仅true | false | null | this合法
            self._writeToken()
        elif tok == '(':
            self._writeToken()  # '('
            self.compileExpression()
            self._writeToken()  # ')'
        elif tok in self.UNARY_OPS:
            self._writeToken()  # unaryOp
            self.compileTerm()
        else:
            # identifier 分支：根据 peek 判断类型
            nxt = self.tk.peek()    # project10未使用，仅做提示LL(2)用途，project11使用
            if nxt == '[':
                # varName '[' expression ']'
                self._writeVarUse()
                self._writeToken()  # '['
                self.compileExpression()
                self._writeToken()  # ']'
            elif nxt == '(':
                # subroutineName '(' expressionList ')'
                self._writeIdentifier('subroutine', 'used')
                self._writeToken()  # '('
                self.compileExpressionList()
                self._writeToken()  # ')'
            elif nxt == '.':
                # (className|varName) '.' subroutineName '(' expressionList ')'
                name = self._cur()
                kind = self.symbols.kindOf(name)
                if kind != SymbolTable.NONE:
                    # 在符号表中 → 是对象变量（被使用）
                    self._writeIdentifier(kind, 'used', self.symbols.indexOf(name))
                else:
                    # 不在符号表 → 是类名
                    self._writeIdentifier('class', 'used')
                self._writeToken()  # '.'
                self._writeIdentifier('subroutine', 'used')  # subroutineName
                self._writeToken()  # '('
                self.compileExpressionList()
                self._writeToken()  # ')'
            else:
            # 否则就是单独的 varName
                self._writeVarUse()
        self._close('term')

    def compileExpressionList(self) -> int:
        self._open('expressionList')
        count = 0
        if self._cur() != ')':      # ExpressionList只在subroutineCall中出现
            self.compileExpression()
            count += 1
            while self._cur() == ',':
                self._writeToken()  # ','
                self.compileExpression()
                count += 1
        self._close('expressionList')
