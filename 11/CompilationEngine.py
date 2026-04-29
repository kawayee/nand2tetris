"""
CompilationEngine: 递归下降编译，直接生成 VM 代码。

• Gets its input from a Jacktk and writes its output using the VMWriter
• Organized as a set of compilexxx routines, xxx being a syntactic element in the
Jack grammar:
    1. Each compilexxx routine should read xxx from the input, advance() the input exactly
       beyond xxx, and emit to the output VM code effecting the semantics of xxx.
    2. compilexxx is called only if xxx is the current syntactic element.
    3. If xxx is part of an expression and thus has a value, the emitted VM code will end up
       computing the value and leaving it at the top of the VM’s stack

Routine
The CompilationEngine of the compiler (project 11) and the syntax analyzer (project 10)
have the same design and API: a set of compilexxx methods
However, the compilexxx methods generate different outputs.
"""
from JackTokenizer import JackTokenizer
from SymbolTable import SymbolTable
from VMWriter import VMWriter

class CompilationEngine:
    # kind -> VM segment
    KIND_TO_SEGMENT = {
        SymbolTable.STATIC: VMWriter.STATIC,
        SymbolTable.FIELD:  VMWriter.THIS,
        SymbolTable.ARG:    VMWriter.ARG,
        SymbolTable.VAR:    VMWriter.LOCAL,
    }

    # 二元运算符（直接对应 VM 命令）
    OP_TO_VM = {
        '+': VMWriter.ADD,
        '-': VMWriter.SUB,
        '&': VMWriter.AND,
        '|': VMWriter.OR,
        '<': VMWriter.LT,
        '>': VMWriter.GT,
        '=': VMWriter.EQ,
    }

    UNARY_OPS = {
        '-': VMWriter.NEG,
        '~': VMWriter.NOT,
    }

    BINARY_OPS = {'+', '-', '*', '/', '&', '|', '<', '>', '='}

    def __init__(self, tokenizer, vm_writer):
        self.tk = tokenizer
        self.vm = vm_writer
        self.symbols = SymbolTable()
        self.class_name = ''
        self.label_counter = 0

    # ---------- 工具方法 ----------

    def _new_label(self, prefix):
        label = f'{prefix}_{self.label_counter}'
        self.label_counter += 1
        return label

    def _eat(self, expected=None):
        """消费当前 token；如果 expected 给定就校验。"""
        cur_token = self.tk.peek()
        self.tk.advance()
        if expected is not None and cur_token != expected:
            raise SyntaxError(f"Expected '{expected}', got '{cur_token}'")
        return cur_token

    # ---------- 类 ----------
    def compileClass(self):
        if self.tk.hasMoreTokens():
            self._eat('class')              # class
            self.class_name = self._eat()   # className
            self._eat('{')                  # {
            while self.tk.peek() in ('static', 'field'):
                self.compileClassVarDec()
            while self.tk.peek() in ('constructor', 'function', 'method'):
                self.compileSubroutine()
            self._eat('}')                  # }

    def compileClassVarDec(self):
        kind_kw = self._eat()               # 'static' / 'field'
        kind = SymbolTable.STATIC if kind_kw == 'static' else SymbolTable.FIELD
        type_ = self._eat()                 # type
        name = self._eat()
        self.symbols.define(name, type_, kind) # varName
        while self.tk.peek() == ',':
            self._eat(',')                  # ','
            name = self._eat()
            self.symbols.define(name, type_, kind)  # varName
        self._eat(';')                      # ';'

    # ---------- 子程序 ----------
    def compileSubroutine(self):
        self.symbols.reset()
        self.label_counter = 0
        sub_kind = self._eat()              # constructor / function / method
        sub_ret = self._eat()               # void|type
        sub_name = self._eat()              # subroutineName

        # method 需要把 this 放在 argument 0
        if sub_kind == 'method':
            self.symbols.define('this', self.class_name, SymbolTable.ARG)

        self._eat('(')                      # '('
        self.compileParameterList()
        self._eat(')')                      # ')'
        self.compileSubroutineBody(sub_kind, sub_name, sub_ret)

    def compileParameterList(self):
        if self.tk.peek() != ')':
            type_ = self._eat()             # type
            name = self._eat()
            self.symbols.define(name, type_, SymbolTable.ARG)   # varName
            while self.tk.peek() == ',':
                self._eat(',')              # ','
                type_ = self._eat()         # type
                name = self._eat()
                self.symbols.define(name, type_, SymbolTable.ARG)   # varName

    def compileSubroutineBody(self, sub_kind, sub_name, sub_ret):
        self._eat('{')                      # '{'
        while self.tk.peek() == 'var':
            self.compileVarDec()
        
        # 写 function 头：本地变量数 = var 计数
        n_locals = self.symbols.varCount(SymbolTable.VAR)
        self.vm.writeFunction(f'{self.class_name}.{sub_name}', n_locals) 
        # 根据子程序类型生成入口代码
        if sub_kind == 'constructor':
            n_fields = self.symbols.varCount(SymbolTable.FIELD)
            self.vm.writePush(VMWriter.CONST, n_fields)
            self.vm.writeCall('Memory.alloc', 1)
            self.vm.writePop(VMWriter.POINTER, 0)   # this = 分配地址
        elif sub_kind == 'method':
            self.vm.writePush(VMWriter.ARG, 0)
            self.vm.writePop(VMWriter.POINTER, 0)   # this = arg 0

        self.compileStatements()
        self._eat('}')                      # '}'
    
    def compileVarDec(self):
        self._eat('var')                    # var
        type_ = self._eat()                 # type
        name = self._eat()
        self.symbols.define(name, type_, SymbolTable.VAR)   # varName
        while self.tk.peek() == ',':
            self._eat(',')                  # ','
            name = self._eat()
            self.symbols.define(name, type_, SymbolTable.VAR)   # varName
        self._eat(';')                      # ';'

    # ---------- 语句 ----------
    def compileStatements(self):
        while self.tk.peek() in ('let', 'if', 'while', 'do', 'return'):
            tok = self.tk.peek()
            if tok == 'let':
                self.compileLet()
            elif tok == 'if':
                self.compileIf()
            elif tok == 'while':
                self.compileWhile()
            elif tok == 'do':
                self.compileDo()
            elif tok == 'return':
                self.compileReturn()

    def compileLet(self):
        self._eat('let')                    # let
        var_name = self._eat()
        kind = self.symbols.kindOf(var_name)
        index = self.symbols.indexOf(var_name)
        segment = self.KIND_TO_SEGMENT[kind]

        is_array = (self.tk.peek() == '[')

        if is_array:
            # let arr[expr1] = expr2;
            self._eat('[')
            self.compileExpression()           # 栈顶: expr1
            self._eat(']')
            self.vm.writePush(segment, index)  # 栈顶: arr 基地址
            self.vm.writeArithmetic(VMWriter.ADD)  # 栈顶: arr + expr1

            self._eat('=')
            self.compileExpression()           # 计算 expr2，栈顶: 值
            self._eat(';')

            # 此时栈顶为右值，下面是目标地址
            self.vm.writePop(VMWriter.TEMP, 0)      # temp 0 = 右值
            self.vm.writePop(VMWriter.POINTER, 1)   # THAT = arr + expr1
            self.vm.writePush(VMWriter.TEMP, 0)     # stack top = 右值
            self.vm.writePop(VMWriter.THAT, 0)      # *(arr+expr1) = 右值
        else:
            # let var = expr;
            self._eat('=')
            self.compileExpression()
            self._eat(';')
            self.vm.writePop(segment, index)

    def compileIf(self):
        else_label = self._new_label('IF_L1')
        end_label = self._new_label('IF_L2')

        self._eat('if')
        self._eat('(')
        self.compileExpression()                # if expression
        self._eat(')')

        self.vm.writeArithmetic(VMWriter.NOT)   # not
        self.vm.writeIf(else_label)             # if-goto L1

        self._eat('{')
        self.compileStatements()                # statements1
        self._eat('}')

        self.vm.writeGoto(end_label)            # goto L2
        self.vm.writeLabel(else_label)          # lable L1

        if self.tk.peek() == 'else':
            self._eat('else')
            self._eat('{')
            self.compileStatements()            # statements2
            self._eat('}')

        self.vm.writeLabel(end_label)           # label L2

    def compileWhile(self):
        start_label = self._new_label('WHILE_START')
        end_label = self._new_label('WHILE_END')

        self.vm.writeLabel(start_label)         # lable L1

        self._eat('while')
        self._eat('(')
        self.compileExpression()                # while expression
        self._eat(')')

        self.vm.writeArithmetic(VMWriter.NOT)   # not
        self.vm.writeIf(end_label)              # if-goto L2

        self._eat('{')
        self.compileStatements()                # statements
        self._eat('}')

        self.vm.writeGoto(start_label)          # goto L1
        self.vm.writeLabel(end_label)           # label L2

    def compileDo(self):
        self._eat('do')
        name = self._eat()
        self._compileSubroutineCall(name)
        self._eat(';')
        # 调用结果是 void，但 VM 仍然返回值，需弹出丢弃
        self.vm.writePop(VMWriter.TEMP, 0)

    def compileReturn(self):
        self._eat('return')
        if self.tk.peek() != ';':
            self.compileExpression()
        else:
            # void 函数：必须 push 一个占位返回值
            self.vm.writePush(VMWriter.CONST, 0)
        self._eat(';')
        self.vm.writeReturn()

    # ---------- 表达式 ----------
    def compileExpression(self):
        self.compileTerm()
        while self.tk.peek() in self.BINARY_OPS:
            op = self._eat()
            self.compileTerm()
            if op in self.OP_TO_VM:
                self.vm.writeArithmetic(self.OP_TO_VM[op])
            elif op == '*':
                self.vm.writeCall('Math.multiply', 2)
            elif op == '/':
                self.vm.writeCall('Math.divide', 2)

    def compileTerm(self):
        name = self._eat()
        tt = self.tk.tokenType()
        # 整数常量
        if tt == self.tk.INT_CONST:
            self.vm.writePush(VMWriter.CONST, self.tk.intVal())
            return
        # 字符串常量
        if tt == self.tk.STRING_CONST:
            s = self.tk.stringVal()
            self.vm.writePush(VMWriter.CONST, len(s))
            self.vm.writeCall('String.new', 1)
            for ch in s:
                self.vm.writePush(VMWriter.CONST, ord(ch))
                self.vm.writeCall('String.appendChar', 2)
            return
        # 关键字常量
        if tt == self.tk.KEYWORD and name in ('true', 'false', 'null', 'this'):
            kw = self.tk.keyword()
            if kw == 'true':
                self.vm.writePush(VMWriter.CONST, 0)
                self.vm.writeArithmetic(VMWriter.NOT)   # -1
            elif kw in ('false', 'null'):
                self.vm.writePush(VMWriter.CONST, 0)
            elif kw == 'this':
                self.vm.writePush(VMWriter.POINTER, 0)
            return
        # 括号表达式
        if name == '(':
            self.compileExpression()
            self._eat(')')
            return
        # 一元运算
        if name in self.UNARY_OPS:
            self.compileTerm()
            self.vm.writeArithmetic(self.UNARY_OPS[name])
            return

        # identifier：数组访问 / 子程序调用 / 普通变量
        nxt = self.tk.peek()
        if nxt == '[':
            # varName '[' expression ']'
            kind = self.symbols.kindOf(name)
            index = self.symbols.indexOf(name)
            segment = self.KIND_TO_SEGMENT[kind]
            self._eat('[')
            self.compileExpression()                # stack top = exp
            self._eat(']')
            self.vm.writePush(segment, index)       # stack top = addr
            self.vm.writeArithmetic(VMWriter.ADD)   # stack top = addr + exp 
            self.vm.writePop(VMWriter.POINTER, 1)   # that = addr + exp
            self.vm.writePush(VMWriter.THAT, 0)     # push that 0
        elif nxt in ('(', '.'):
            # subroutineCall
            self._compileSubroutineCall(name)
        else:
            # varName
            kind = self.symbols.kindOf(name)
            index = self.symbols.indexOf(name)
            segment = self.KIND_TO_SEGMENT[kind]
            self.vm.writePush(segment, index)

    def _compileSubroutineCall(self, name):
        """name 已经被 _eat 消费过，处理三种调用形式。"""
        nxt = self.tk.peek()

        if nxt == '(':
            # subroutineName '(' expressionList ')'
            # 形式 1：this.foo(...)
            self.vm.writePush(VMWriter.POINTER, 0)   # push this
            self._eat('(')
            n_args = 1 + self.compileExpressionList()
            self._eat(')')
            self.vm.writeCall(f'{self.class_name}.{name}', n_args)

        elif nxt == '.':
            # (className|varName) '.' subroutineName '(' expressionList ')'
            self._eat('.')
            sub_name = self._eat()
            kind = self.symbols.kindOf(name)

            if kind == SymbolTable.NONE:
                # 形式 2：ClassName.foo(...)  —— 函数 / 构造器调用
                self._eat('(')
                n_args = self.compileExpressionList()
                self._eat(')')
                self.vm.writeCall(f'{name}.{sub_name}', n_args)
            else:
                # 形式 3：obj.foo(...)  —— 实例方法调用
                type_ = self.symbols.typeOf(name)
                index = self.symbols.indexOf(name)
                segment = self.KIND_TO_SEGMENT[kind]
                self.vm.writePush(segment, index)    # push obj, inspect symbol table
                self._eat('(')
                n_args = 1 + self.compileExpressionList()
                self._eat(')')
                # JackCompiler把所有的 obj.method(arg1, arg2) 都强行转换成了 Class.method(obj, arg1, arg2)
                self.vm.writeCall(f'{type_}.{sub_name}', n_args)

    def compileExpressionList(self) -> int:
        """编译以逗号分隔的表达式列表，返回参数个数。"""
        count = 0
        if self.tk.peek() != ')':
            self.compileExpression()
            count += 1
            while self.tk.peek() == ',':
                self._eat(',')
                self.compileExpression()
                count += 1
        return count
