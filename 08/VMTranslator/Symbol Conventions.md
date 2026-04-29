# Symbol Conventions

## Summary

This document explains the symbol naming conventions used by the VM Translator when generating Hack assembly code.

## Problems to Solve

- Avoid naming conflicts across different `.vm` files and functions.
- Ensure labels and return addresses are unique and traceable.
- Keep function-level control flow (`label/goto/if-goto`) scoped correctly.
- Preserve correct stack and segment behavior using predefined pointers.

## Architecture Context

- Input: VM commands from one or multiple `.vm` files.
- Output: assembly symbols injected into generated `.asm` code.
- Symbol design goal: keep generated assembly correct, collision-free, and toolchain-compatible.

## Symbol Specification

### `SP`

- Points to the RAM address just after the current top stack value.
- Works as the stack pointer for `push/pop` and arithmetic/logical operations.
- Semantics: always points to the next writable stack slot.

### `LCL`, `ARG`, `THIS`, `THAT`

- Predefined pointers to base addresses of VM segments:
  - `local`
  - `argument`
  - `this`
  - `that`
- Segment access rule: use `base + offset`.
- Used to maintain segment bases for the currently running function.

### `Xxx.i` (static variables)

- Each `static i` in `Xxx.vm` is translated to assembly symbol `Xxx.i`.
- The Hack assembler allocates these symbolic variables in RAM starting from address `16`.
- File prefix (`Xxx`) prevents collisions between different VM files.

Examples:

- In `Foo.vm`: `push static 0` -> `Foo.0`
- In `Bar.vm`: `push static 0` -> `Bar.0`

### `Xxx.foo$bar` (label destinations inside a function)

- Suppose `foo` is a function in `Xxx.vm`.
- `label bar` inside `foo` becomes assembly label `(Xxx.foo$bar)`.
- `goto bar` and `if-goto bar` inside `foo` must target `Xxx.foo$bar`.
- This enforces function-local label scope and avoids conflicts.

Why this layered name is needed:

- Different files may contain same function name -> isolate by `Xxx.`
- Different functions may contain same label name -> isolate by `foo$`
- Resulting symbols remain unique (for example: `Xxx.foo$LOOP`, `Yyy.foo$LOOP`, `Xxx.bar$LOOP`)

### `Xxx.foo` (function entry point)

- `function foo nVars` in `Xxx.vm` generates function entry label `(Xxx.foo)` in assembly.
- `call Xxx.foo n` can jump to this label.
- The assembler resolves `Xxx.foo` to the physical address where function code begins.

### `Xxx.foo$ret.i` (return address symbols)

- For each `call` command inside function `foo` (in `Xxx.vm`), generate a unique return label:
  - `Xxx.foo$ret.1`
  - `Xxx.foo$ret.2`
  - ...
- The label marks the instruction immediately after that `call`.
- Uniqueness (`i`) is required because one caller function may issue multiple calls.

### `R13` - `R15`

- Predefined registers available for translator-defined temporary usage.
- Commonly used for intermediate addresses or values during multi-step code generation.

## Toolchain Responsibility Note

- In many Jack toolchains, function names in VM code already include class/file prefix (for example `Xxx.foo`).
- Therefore, VM Translator often reuses these names directly when emitting assembly labels.
- The symbol convention describes the expected final assembly form; it does not necessarily require VM Translator to invent the prefix itself.
