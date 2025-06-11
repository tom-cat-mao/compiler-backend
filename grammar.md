# Pascal 子集语法文法总结
---

# 🧮 Pascal 子集语法文法总结

该文法实现了一个简化版的 Pascal 编程语言子集，支持程序结构、变量声明、赋值语句、条件判断、循环控制、数组类型以及 `writeln` 输出语句。

---

## 1️⃣ 程序结构（Program Structure）

```ebnf
program → PROGRAM ID SEMICOLON var_declarations BEGIN statements END DOT
```

- 整个程序以 `program` 关键字开头，后跟程序名。
- 包含变量声明和主语句块（`begin ... end.`）。
- 程序以句号 `.` 结尾。

---

## 2️⃣ 变量声明（Variable Declaration）

```ebnf
var_declarations → VAR var_list | ε
var_list → var_declaration | var_list var_declaration
var_declaration → id_list COLON type SEMICOLON
id_list → ID | id_list COMMA ID
type → INTEGER | BOOLEAN | REAL | CHAR | array_type_definition
```

- 使用 `var` 声明变量。
- 支持多个变量同时声明，使用逗号 `,` 分隔。
- 类型包括基本类型（整数、布尔、实数、字符）和数组类型。

---

## 3️⃣ 数组类型定义（Array Type Definition）

```ebnf
array_type_definition → ARRAY LSQUARE index_range RSQUARE OF type
index_range → NUMBER DOTDOT NUMBER
```

- 示例：`array [1..5] of integer`
- 支持固定范围的数组定义。

---

## 4️⃣ 语句部分（Statements）

```ebnf
statements → statement SEMICOLON | statements statement SEMICOLON | statement | statements statement
statement → assignment | if_statement | while_statement | writeln_statement
```

- 多条语句用分号 `;` 分隔。
- 支持赋值语句、条件语句、循环语句和输出语句。

---

## 5️⃣ 赋值语句（Assignment Statement）

```ebnf
assignment → variable ASSIGN expression
variable → ID | ID LSQUARE expression RSQUARE
```

- 支持普通变量赋值，也支持数组元素赋值（如 `a[1] := 2`）。

---

## 6️⃣ 表达式（Expressions）

### 📌 算术表达式结构

```ebnf
expression → simple_expression | simple_expression relop simple_expression
simple_expression → term | simple_expression addop term
term → factor | term mulop factor
factor → LPAREN expression RPAREN | NUMBER | REAL_NUMBER | STRING | variable
```

- 支持括号、加减乘除运算。
- 比较运算符包括 `<`, `>`, `=`, `<=`, `>=`。
- 支持数字、浮点数、字符串和变量作为因子。

### 📌 逻辑运算

```ebnf
expression → expression AND expression
```

- 支持逻辑与 (`and`) 运算。

---

## 7️⃣ 控制结构（Control Structures）

### ✅ `if` 条件语句

```ebnf
if_statement → IF expression THEN statement
             | IF expression THEN statement ELSE statement
             | IF expression THEN BEGIN statements END
             | IF expression THEN BEGIN statements END ELSE BEGIN statements END
```

### 🔁 `while` 循环语句

```ebnf
while_statement → WHILE expression DO BEGIN statements END
```

---

## 8️⃣ 输出语句（Writeln Statement）

```ebnf
writeln_statement → WRITELN LPAREN expression_list RPAREN
expression_list → expression | expression_list COMMA expression
```

- 支持打印多个表达式，用逗号 `,` 分隔。

---

## 9️⃣ 词法分析 Token 列表（Lexer Tokens）

| 类别   | 内容                                                                                                                              |
| ------ | --------------------------------------------------------------------------------------------------------------------------------- |
| 数字   | `NUMBER`, `REAL_NUMBER`                                                                                                           |
| 标识符 | `ID`（变量名），关键字自动识别                                                                                                    |
| 操作符 | `+`, `-`, `*`, `/`, `:=`, `<`, `>`, `=`, `<=`, `>=`                                                                               |
| 分隔符 | `;`, `:`, `,`, `.`, `(`, `)`, `[`, `]`                                                                                            |
| 字符串 | `'abc'`（单引号包裹）                                                                                                             |
| 关键字 | `program`, `var`, `integer`, `real`, `char`, `begin`, `end`, `if`, `then`, `else`, `while`, `do`, `writeln`, `array`, `of`, `and` |

---

## 🔚 总结

该文法描述了一个可用于构建编译器或解释器前端的简单 Pascal 子集。它实现了以下核心功能：

- ✅ 完整的程序结构定义
- ✅ 支持多种数据类型的变量声明（包括数组）
- ✅ 赋值语句与数组访问
- ✅ 基本的算术、比较和逻辑表达式
- ✅ 控制流语句（`if` 和 `while`）
- ✅ 输出语句（`writeln`）
