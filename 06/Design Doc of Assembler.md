# Design Doc of Assembler

## Summary

This documentation describes how to translate an assembly program into binary code for computer execution.

## Problems to Solve

- **Whitespace**: includes blank lines and comments; ignore them.
- **Instruction**: translate A/C instructions one by one based on specific rules.
- **Symbol**: support pre-defined symbols, labels, and variables.

## Architecture

- **Source program**: `xxx.asm`
- **Generated code**: `xxx.hack`
- The translator contains four modules (`main`, `parser`, `code`, `symboltable`) to isolate concerns and simplify testing.
- Considering symbol complexity, implementation and testing start without symbol handling, then add symbols after base translation is stable.

## Module Specification

- **Main** (overall flow)
  - Drives the translation process.
- **Parser** (line by line)
  - Reads and parses an instruction.
- **Code**
  - Generates binary codes.
- **SymbolTable** (class)
  - Handles symbols.

## TBD

1. Where should whitespace skipping be added?
2. Where should `SymbolTable` be added?

```python
# first pass
for r in reader:
    processed_r
    if len(processed_r) > 0:
        rows.append(processed_r)
    else:
        print(f"ignored {r}")

# second pass
for r in rows:
    binary_string = parser.parse(r)
    result.append(binary_string)

outfile.save(result)
```

```java
// example of parsing and coding
String c = parser.comp();
String d = parser.dest();
String j = parser.jump();

String cc = code.comp(c);
String dd = code.dest(d);
String jj = code.jump(j);

String out = "111" + cc + dd + jj;
```
