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

class CompilationEngine:
    OPS = set('+-*/&|<>=')
    UNARY_OPS = {'-', '~'}
    XML_ESCAPE = {'<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;'}

    def __init__(self, tokenizer, outputPath):
        self.tk = tokenizer
        self.out = open(outputPath, 'w', encoding='utf-8')
        self.indent = 0
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

    # 当前待写的 token
    def _cur(self):
        return self.tk.currentToken

    # ----------------------------------------------------------------
    # 程序结构
    # ----------------------------------------------------------------
    def compileClass(self):
        self._open('class')
        self._writeToken()  # 'class'
        self._writeToken()  # className
        self._writeToken()  # '{'
        while self._cur() in ('static', 'field'):
            self.compileClassVarDec()
        while self._cur() in ('constructor', 'function', 'method'):
            self.compileSubroutine()
        self._writeToken()  # '}'
        self._close('class')

    def compileClassVarDec(self):
        self._open('classVarDec')
        self._writeToken()  # static/field
        self._writeToken()  # type
        self._writeToken()  # varName
        while self._cur() == ',':
            self._writeToken()  # ','
            self._writeToken()  # varName
        self._writeToken()  # ';'
        self._close('classVarDec')

    def compileSubroutine(self):
        self._open('subroutineDec')
        self._writeToken()  # constructor/function/method
        self._writeToken()  # void|type
        self._writeToken()  # subroutineName
        self._writeToken()  # '('
        self.compileParameterList()
        self._writeToken()  # ')'
        self.compileSubroutineBody()
        self._close('subroutineDec')

    def compileParameterList(self):
        self._open('parameterList')
        if self._cur() != ')':
            self._writeToken()  # type
            self._writeToken()  # varName
            while self._cur() == ',':
                self._writeToken()  # ','
                self._writeToken()  # type
                self._writeToken()  # varName
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
        self._writeToken()  # type
        self._writeToken()  # varName
        while self._cur() == ',':
            self._writeToken()  # ','
            self._writeToken()  # varName
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
        self._writeToken()  # varName
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
        # subroutineCall 展开（这里不包围 subroutineCall 标签，与教材一致）
        self._writeToken()  # identifier（subroutineName 或 className/varName）
        if self._cur() == '.':
            self._writeToken()  # '.'
            self._writeToken()  # subroutineName
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
            # 标识符，需要看下一个 token 判断是哪种 term
            nxt = self.tk.peek()    # 未使用nxt，此处仅做提示LL(2)用途
            self._writeToken()  # identifier
            if self._cur() == '[':
                # varName '[' expression ']'
                self._writeToken()  # '['
                self.compileExpression()
                self._writeToken()  # ']'
            elif self._cur() == '(':
                # subroutineName '(' expressionList ')'
                self._writeToken()  # '('
                self.compileExpressionList()
                self._writeToken()  # ')'
            elif self._cur() == '.':
                # (className|varName) '.' subroutineName '(' expressionList ')'
                self._writeToken()  # '.'
                self._writeToken()  # subroutineName
                self._writeToken()  # '('
                self.compileExpressionList()
                self._writeToken()  # ')'
            # 否则就是单独的 varName，什么也不做
            _ = nxt  # 仅作文档化意图
        self._close('term')

    def compileExpressionList(self):
        self._open('expressionList')
        if self._cur() != ')':      # ExpressionList只在subroutineCall中出现
            self.compileExpression()
            while self._cur() == ',':
                self._writeToken()  # ','
                self.compileExpression()
        self._close('expressionList')
