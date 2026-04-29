'''
• Handles the parsing of a single .vm file
• Reads a VM command, parses the command into its lexical components,
and provides convenient access to these components
• Ignores white space and comments

Routines
• Constructor / initializer: Creates a Parser and opens the input (source VM code) file
• Getting the current instruction:
    hasMoreLines() -> boolean: 
        Checks if there is more work to do (boolean)
    advance(): 
        Gets the next command and makes it the current instruction (string)
• Parsing the current instruction:
    commandType() -> string constant: 
        Returns the type of the current command (a string constant):
        C_ARITHMETIC if the current command is an arithmetic-logical command;
        C_PUSH, C_POP if the current command is one of these command types;
        C_LABEL, C_GOTO, C_IF if the current command is branching command type;
        C_FUNCTION, C_RETURN, C_CALL if the current command is function command type;
    arg1() -> string: 
        Returns the first argument of the current command;
        In the case of C_ARITHMETIC, the command itself is returned (string)
    arg2() -> int: 
        Returns the second argument of the current command (int);
        Called only if the current command is C_PUSH, C-POP, C_FUNCTION, or C_CALL
'''

class Parser:
    # 命令类型常量
    C_ARITHMETIC = "C_ARITHMETIC"
    C_PUSH = "C_PUSH"
    C_POP = "C_POP"
    # Project 8 的命令类型（此处先预留，Project 7 用不到）
    C_LABEL = "C_LABEL"
    C_GOTO = "C_GOTO"
    C_IF = "C_IF"
    C_FUNCTION = "C_FUNCTION"
    C_RETURN = "C_RETURN"
    C_CALL = "C_CALL"

    ARITHMETIC_COMMANDS = {
        "add", "sub", "neg",
        "eq", "gt", "lt",
        "and", "or", "not"
    }

    _KEYWORD_COMMAND_TYPE = {
        "push": C_PUSH,
        "pop": C_POP,
        "label": C_LABEL,
        "goto": C_GOTO,
        "if-goto": C_IF,
        "function": C_FUNCTION,
        "return": C_RETURN,
        "call": C_CALL,
    }

    def __init__(self, input_file: str):
        """打开输入文件，预处理所有行（去注释、去空行）。"""
        with open(input_file, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
        self.commands = [s for s in (self._clean(ln) for ln in raw_lines) if s]
        self.current_index = -1
        self._tokens: list[str] = []

    @staticmethod
    def _clean(line: str) -> str:
        # nand2tetris VM 只有 // 行尾注释；从首个 // 起截断即可
        idx = line.find("//")
        if idx != -1:
            line = line[:idx]
        return line.strip()

    def hasMoreCommands(self) -> bool:
        """是否还有未处理的命令。"""
        return self.current_index + 1 < len(self.commands)

    def advance(self) -> None:
        """读取下一条命令，使其成为当前命令。"""
        self.current_index += 1
        self._tokens = self.commands[self.current_index].split()

    def commandType(self) -> str:
        """返回当前命令的类型。"""
        if not self._tokens:
            raise ValueError("空命令")
        head = self._tokens[0]
        if head in self.ARITHMETIC_COMMANDS:
            return self.C_ARITHMETIC
        try:
            return self._KEYWORD_COMMAND_TYPE[head]
        except KeyError as e:
            raise ValueError(f"未知命令: {head}") from e

    def arg1(self) -> str:
        """
        若当前命令是 C_ARITHMETIC，返回命令本身（如 add）。
        否则返回第一个参数（如 push local 2 的 local）。
        C_RETURN 不应调用此方法。
        """
        ctype = self.commandType()
        if ctype == self.C_RETURN:
            raise ValueError("C_RETURN 没有 arg1")
        if ctype == self.C_ARITHMETIC:
            return self._tokens[0]
        return self._tokens[1]

    def arg2(self) -> int:
        """
        返回第二个参数（整数）。
        仅当命令为 C_PUSH、C_POP、C_FUNCTION、C_CALL 时调用。
        """
        ctype = self.commandType()
        if ctype not in (self.C_PUSH, self.C_POP, self.C_FUNCTION, self.C_CALL):
            raise ValueError(f"{ctype} 没有 arg2")
        return int(self._tokens[2])