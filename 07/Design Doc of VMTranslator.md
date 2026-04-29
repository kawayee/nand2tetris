# Design Doc of VM Translator

## Summary

The documentation is designed to translate VM commands (bytecode) into machine language (assembly) for the computer to execute.

## Problems to Solve

- **Whitespace**: includes blank lines and comments, should be ignored.
- **Pop/Push commands**: `push/pop segment i`
- **Arithmetic/Logical commands**: `add/sub/neg/eq/gt/lt/and/or/not`

## Architecture

- Source program: `xxx.vm`
- Generated code: `xxx.asm`
- Includes three modules (`main`, `parser`, `codewriter`) to deal with specific problems, and three test files to isolate questions for testing.

## Module Specification

### Main (drives the process)

- Initializes I/O files and drives parser process by calling corresponding methods.
- Opens and saves files.

### Parser (reads and parses a VM command)

- `constructor init(arg: raw_commands)`
- `first_run_pass`
  - Ignores heading/trailing whitespace and comments.
  - Saves results to a new list as `first_pass_result`.
- `commandtype`
  - Returns current command type, including `C_arithmetic`, `C_push`, `C_pop`.
- `arg1`
  - For `C_arithmetic`, returns command itself (e.g. `add`).
  - For `C_push` and `C_pop`, returns memory segment name (e.g. `local`).
- `arg2`
  - Only for `C_push` and `C_pop`, returns `int i` (e.g. `2`).
- TODO: `second_pass_result` (total list)
  - Add list from `codewriter` to total list using `"+"`.

### CodeWriter (generates assembly code)

- Gets command from parser.
- Uses `true = -1`, `false = 0`
  - `@SP,A=M,M=-1  // set to true`
- `writearithmetic(arg: command/str) -> list[str]`
  - Writes assembly code for arithmetic commands.
- `writepushpop(push/pop command) -> list[str]`
  - Writes assembly code for push/pop commands.
