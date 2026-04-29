"""
SymbolTable: 管理类作用域和子程序作用域两层符号表。

Implementation notes
• symbol table = instance of a SymbolTable class (next slide)
• When compiling a Jack class, we need one class-level symbol table and one
subroutine-level symbol table
• When we start compiling a subroutine, we reset the latter table
• Each variable is assigned a running index within its scope (table) and kind.
The index starts at 0, increments by 1 after each time a new symbol is added
to the table, and is reset to 0 when starting a new scope (table)
• When compiling an error-free Jack code, each identifier not found in the symbol
tables can be assumed to be either a subroutine name or a class name.

Routine
Constructor(): -> SymbolTable
Creates a new empty symbol table.

reset(): -> void
Empties the symbol table, and resets the four indexes to 0. Should be called when
starting to compile a subroutine declaration.

define(name: String, type: String, kind: STATIC/FIELD/ARG/VAR): -> void 
Defines(adds to the table) a new variable of the given name, type, and kind. Assigns 
to it the index value of that kind, and adds 1 to the index.

varCount(kind: STATIC/FIELD/ARG/VAR): -> int 
Returns the number of variables of the given kind already defined in the table.

kindOf(name: String): -> STATIC/FIELD/ARG/VAR/NONE 
Returns the kind of the named identifier in the current scope. If the identifier is 
not found, returns NONE.

typeOf(name: String): -> String 
Returns the type of the named identifier in the current scope.

indexOf(name: String): -> int 
Returns the index of the named identifier.
"""

class SymbolTable:
    # 变量种类（kind）
    STATIC = 'static'
    FIELD = 'field'
    ARG = 'arg'
    VAR = 'var'
    NONE = 'none'

    def __init__(self):
        # name -> (type, kind, index)
        self.class_table = {}
        self.subroutine_table = {}
        self.counts = {self.STATIC: 0, self.FIELD: 0, self.ARG: 0, self.VAR: 0}

    def reset(self):
        """开始一个新的子程序，重置子程序作用域和相应计数。未严格遵守文档要求。"""
        self.subroutine_table = {}
        self.counts[self.ARG] = 0
        self.counts[self.VAR] = 0

    def define(self, name, type_, kind):
        """定义一个新的标识符，分配下一个可用 index。"""
        if kind in (self.STATIC, self.FIELD):
            self.class_table[name] = (type_, kind, self.counts[kind])
        else:  # ARG, VAR
            self.subroutine_table[name] = (type_, kind, self.counts[kind])
        self.counts[kind] += 1

    def varCount(self, kind):
        return self.counts[kind]

    def kindOf(self, name):
        if name in self.subroutine_table:
            return self.subroutine_table[name][1]
        if name in self.class_table:
            return self.class_table[name][1]
        return self.NONE

    def typeOf(self, name):
        if name in self.subroutine_table:
            return self.subroutine_table[name][0]
        if name in self.class_table:
            return self.class_table[name][0]
        return None

    def indexOf(self, name):
        if name in self.subroutine_table:
            return self.subroutine_table[name][2]
        if name in self.class_table:
            return self.class_table[name][2]
        return -1
