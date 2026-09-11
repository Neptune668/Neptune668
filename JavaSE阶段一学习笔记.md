# Java SE 阶段一学习笔记 · 环境与语法基础

> 对应大纲阶段一：开发环境 → 编译运行 → 变量与类型 → 运算符 → 流程控制 → 数组 → 方法
> 学习方式：每个知识点先看说明，再亲手敲一遍示例，最后做文末练习。

---

## 目录

掌握一个新的工具，扩展能力的边界，增加职场的选择范围

核心能力：工程化——分析问题、设计方案、编码落地、测试上线、运行监控与维护

1. [开发环境搭建](#1-开发环境搭建)
2. [第一个程序与编译运行](#2-第一个程序与编译运行)
3. [变量与数据类型](#3-变量与数据类型)
4. [运算符](#4-运算符)
5. [流程控制](#5-流程控制)
6. [数组](#6-数组)
7. [方法](#7-方法)
8. [编码规范与常见陷阱](#8-编码规范与常见陷阱)
9. [阶段验收练习](#9-阶段验收练习)

---

## 1. 开发环境搭建

### 1.0 简介

简介：Java是一门静态强类型、面向对象的通用编程语言。

#### 1.01 JVM跨平台原理

严格说：**JVM 本身并不跨平台，跨平台的是 Java 字节码；JVM 是平台相关的“适配层”**。不同 OS/CPU 有不同 JVM 实现，但它们都遵循同一套 JVM 规范

> **Java 源码编译成平台无关的字节码；各平台提供平台相关的 JVM；JVM 负责把统一字节码解释或编译成当前平台的机器码。因此跨平台的是字节码，JVM 是实现适配的关键中间层。**

### 1.1 JDK / JRE / JVM 的关系

这三者是**包含关系**：JDK  ⊃  JRE  ⊃  JVM

| 名称 | 全称 | 作用 | 关系 |
|------|------|------|------|
| JVM | Java Virtual Machine | 执行字节码，是 Java 跨平台的核心 | 最底层 |
| JRE | Java Runtime Environment | JVM + 核心类库，只能**运行**程序,给运行者用 | JRE ⊃ JVM |
| JDK | Java Development Kit | JRE + 编译器等**开发**工具，开发者用 | JDK ⊃ JRE ⊃ JVM |

> 记忆：开发装 **JDK**，运行装 **JRE**。现在基本直接装 JDK。

#### 开发到运行流程

```
Hello.java
   ↓ javac，JDK 提供
Hello.class
   ↓ java，JRE/JVM 提供
JVM 执行字节码
   ↓
当前平台的机器码
```

### 1.2 安装与配置（Windows）

1. 下载 JDK 17 或 21（LTS 长期支持版），推荐 Adoptium / Oracle / 华为毕昇。

2. 配置环境变量：
   - `JAVA_HOME` = JDK 安装目录，如 `C:\Program Files\Java\jdk-21`\
   - 配置JAVA_HOME=看到bin的目录，目录不包含bin,(JAVA_HOME规定好的！)
   
   - `Path` 中追加 `%JAVA_HOME%\bin`

```bash
java -version#验证
javac -version#两条命令都能输出对应版本号，说明配置成功。
```

> 注意:Path 环境变量打开只有一行，这通常是 Windows 系统的一个正常“Bug”，**不影响功能，只是影响查看和编辑的便利性**。它通常是因为 Path 变量的第一个值是 `%` 开头的相对路径（如 `%SystemRoot%`），系统就没能把它展开成多行列表

### 1.3 IDEA 关键设置

- Project SDK 选择已安装的 JDK 21
- 语言级别（Language Level）与 SDK 保持一致
- 编码统一设置为 **UTF-8**（避免中文乱码）
- 开启自动导包、自动编译

---

## 2. 第一个程序与编译运行

### 2.1 HelloWorld

```java
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, Java!");
    }
}
```

### 2.2 编译与运行

```bash
javac HelloWorld.java   # 编译：生成 HelloWorld.class（字节码）
java HelloWorld         # 运行：由 JVM 解释执行字节码
```

Java 是「先编译成字节码，再由 JVM 解释/JIT 执行」的语言，所以能跨平台（一次编写，到处运行）。

### 2.3 三条必记规则

| 规则 | 说明 |
|------|------|
| 文件与类名 | 一个源文件中 `public` 类的名字必须和文件名一致 |
| 一个文件多个类 | 可以写多个类，但只能有一个 `public` 类 |
| main 方法签名 | `public static void main(String[] args)` 是程序入口，签名不能改 |

> `main` 拆开看：`public` 权限最大；`static` 无需创建对象即可调用；`void` 无返回值；`String[] args` 接收命令行参数。

---

## 3. 变量与数据类型

### 3.1 八种基本类型（必背）

| 类型 | 字节 | 取值范围 | 默认值 | 典型用途 |
|------|------|----------|--------|----------|
| `byte` | 1 | -128 ~ 127 | 0 | 字节数据、文件流 |
| `short` | 2 | -32768 ~ 32767 | 0 | 少见 |
| `int` | 4 | -2^31 ~ 2^31-1 | 0 | **整数默认类型** |
| `long` | 8 | -2^63 ~ 2^63-1 | 0L | 时间戳、大整数（需加 `L`） |
| `float` | 4 | 约 ±3.4e38 | 0.0f | 精度要求低（需加 `f`） |
| `double` | 8 | 约 ±1.7e308 | 0.0d | **小数默认类型** |
| `char` | 2 | 0 ~ 65535（Unicode） | '\u0000' | 单个字符 |
| `boolean` | 1 | true / false | false | 逻辑判断 |

> 除以上 8 种，其余都是**引用类型**（类、接口、数组、String、枚举等）。

- `char` 是 16 位无符号，能表示一个 Unicode 字符。
- `boolean` 在 Java 规范中没有精确规定字节数，通常按 1 字节实现。

先声明，char只能''一个字符（单引号只能引用一个字符）

#### 声明与初始化

语法：数据类型 变量名 = 初始值;****

> final修饰的局部变量仅能赋值一次，不可二次修改

必须指定类型，指定类型后不兼容其他类型，读取局部变量的时候必须初始化，变量有作用域，末尾有分号；

Java 变量主要掌握**类型、名称、值、作用域、默认值、`final` 和 `var`** 即可

### 3.2 字面量写法

```java
int a = 100;
int bin = 0b1010;        // 二进制，值为 10
int oct = 012;           // 八进制，值为 10
int hex = 0x1F;          // 十六进制，值为 31
int big = 1_000_000;     // 下划线分隔，便于阅读
long time = 1699999999L; // long 必须加 L
double d1 = 3.14;
double d2 = 3.14e2;      // 科学计数法 = 314.0
float f = 3.14f;         // float 必须加 f
char c1 = 'A';
char c2 = '\n';          // 转义字符：换行
char c3 = '\u0041';      // Unicode，也是 'A'
String s = "hello";      // 字符串是引用类型，用双引号
```

常见转义字符：`\n` 换行、`\t` 制表、`\\` 反斜杠、`\"` 双引号、`\'` 单引号。

#### String类型（非常常用,重点）

•Java中String类型用来保存字符串，它是一个实打实的**引用类型**！

•String虽然不是基本类型，但用得太频繁，JDK 给了特殊待遇——常量池。

```java
String s1 = "hello";
String s2 = "hello";
String s3 = new String("hello");

System.out.println(s1 == s2);          // true （字符串常量池）
System.out.println(s1 == s3);          // false （new 出来的新对象）
System.out.println(s1.equals(s3));     // true （比较内容要用 equals）
```

>   结论：**重点**：Java 中比较字符串内容必须用.equals()，==比较的是内存地址！

String类型（非常常用）

### 3.3 类型转换

Java 是强类型语言，不同类型之间转换有严格规则。总体分两类：

#### 1   **基本数据类型转换**

```java
// 自动转换（小容量 → 大容量，安全）（隐式转换）
byte b = 10;
int i = b;        // byte -> int，自动
long l = i;       // int -> long，自动
float f = l;      // long -> float，自动，但可能丢失精度
double d = f;     // float -> double，自动（隐式转换）

// 强制转换（大容量 → 小容量，可能丢精度）
double pi = 3.99;
int n = (int) pi;        // 结果 3，直接截断小数

int big = 200;
byte b = (byte) big;     // 结果 -56，  数据溢出

int i = 128;
byte b = (byte) i;
System.out.println(b); // -128，溢出，符号改变

// 如果想四舍五入，用：
long round = Math.round(3.99); //4
// 混合运算会向"大"的类型提升
System.out.println(1 + 2.0);   // 3.0，int 被提升为 double
```

转换方向大致是：

byte -> short -> int -> long -> float -> double
        char  -> int

> 陷阱：`char` 参与算术运算时会自动提升为 `int`。
> `'a' + 1` 得到的是数字 98，而不是字符 'b'，需要 `(char)('a' + 1)`。

##### 表达式中的类型提升

当不同类型参与运算时，Java 会自动提升为范围更大的类型。

规则：

- `byte、short、char` 参与运算时，先提升为 `int`
- 有一个操作数是 `long`，结果就是 `long`
- 有一个操作数是 `float`，结果就是 `float`
- 有一个操作数是 `double`，结果就是 `double`

```java
byte a = 1;
byte b = 2;
// byte c = a + b; // 编译错误，a + b 结果是 int
int c = a + b;     // 正确

long l = 10L;
double d = l + 1.5; // 结果是 double
```

复合赋值运算符隐含强制转换：

```java
short s = 1;
s += 1;        // 等价于 s = (short)(s + 1);
System.out.println(s); // 2
```

但下面这样写会编译错误：

```java
short s = 1;
// s = s + 1; // 错误，s + 1 是 int
```

##### 常量优化

如果赋值的是编译期常量，并且值在目标类型范围内，可以直接赋值。

```java
byte b = 100;    // 正确，100 在 byte 范围内
// byte b2 = 128; // 错误，128 超出 byte 范围

final int x = 100;
byte b3 = x;     // 正确，x 是编译期常量
```

---

#### 2. 引用数据类型转换(略)

##### 1. 向上转型（自动）

子类对象赋给父类引用，安全，自动完成。

```java
class Animal {}
class Dog extends Animal {}

Animal a = new Dog(); // 向上转型，自动
```

##### 2. 向下转型（强制）

父类引用赋给子类引用，必须强制转换。

```java
Animal a = new Dog();
Dog d = (Dog) a; // 向下转型，强制
```

如果实际对象类型不匹配，会抛出 `ClassCastException`。

```java
Animal a = new Animal();
// Dog d = (Dog) a; // 运行时错误：ClassCastException
```

安全做法：先用 `instanceof` 判断。

```java
if (a instanceof Dog) {
    Dog d = (Dog) a;
    System.out.println("是 Dog");
}
```

Java 16+ 支持模式匹配：

```java
if (a instanceof Dog d) {
    System.out.println("是 Dog");
}
```

---

#### 3.  包装类与字符串转换（略）

##### 1. 自动装箱与拆箱

基本类型和包装类之间可以自动转换。

```java
Integer i = 100;   // 自动装箱：int -> Integer
int n = i;         // 自动拆箱：Integer -> int
```

注意：包装类对象为 `null` 时拆箱会抛 `NullPointerException`。

```java
Integer i = null;
// int n = i; // NullPointerException
```

##### 2. 字符串转基本类型

使用包装类的 `parseXxx` 方法。

```java
int i = Integer.parseInt("123");
double d = Double.parseDouble("3.14");
boolean b = Boolean.parseBoolean("true");
```

##### 3. 基本类型转字符串

```java
String s1 = String.valueOf(123);
String s2 = Integer.toString(123);
String s3 = 123 + "";x
```

> **核心原则**：***小转大自动*，大转小强制；boolean 不参与；浮点转整数直接舍去小数；引用向上安全，向下要判断；字符串转数字用 parse，数字转字符串用 valueOf。**

### 3.4 常量与 var

```java
final double PI = 3.14159;   // final 修饰常量，赋值后不可改
final int MAX;

var count = 10;              // Java 10+：局部变量类型推断，等价于 int count = 10;
var name = "Java";           // 推断为 String
```

> `var` 只能用于**局部变量**，且必须**声明时初始化**。

---

## 4. 运算符

### 4.1 分类速查

**按位异或  `^`（XOR**:异或规则是：**相同为 0，不同为 1**）:``

| 类别 | 运算符 | 注意 |
|------|--------|------|
| 算术 | `+ - * / %` | `/` 整除陷阱、`%` 取余 |
| 自增自减 | `++ --` | 前置先加后用，后置先用后加 |
| 关系 | `> < >= <= == !=` | 结果是 boolean |
| 逻辑 | `&&  ||  !`或与非 | `&&` `\|\|` 有短路特性 |
| 位运算 | `& \| ^ ~ << >> >>>` | 二进制层面操作 |
| 赋值 | `= += -= *= /= %=` | 复合赋值隐含强制转换 |
| 三元 | `条件 ? A : B` | 简化 if-else |

### 4.2 高频陷阱

```java
// 1. 整数除法
System.out.println(5 / 2);      // 2，不是 2.5！（整数相除，结果还是整数！
System.out.println(5 / 2.0);    // 2.5

// 2. 浮点精度
System.out.println(0.1 + 0.2);  // 0.30000000000000004
// 结论：金额计算用 BigDecimal，不要用 double

// 3. 自增顺序
// ++在后面，先取值后++,
// ++在前面，先++后取值
int a = 5;
System.out.println(a++);        // 输出 5，之后 a=6
System.out.println(++a);        // a 先变 7，输出 7

// 4. 短路求值
//  `&&`：左边假，右边不看
//  `||`：左边真，右边不看
//  `&`、`|`：两边都看，不短路
int x = 0;
if (x != 0 && 10 / x > 1) { }   // 左边 false，右边不执行，不会除以 0
```

### 4.3 三元运算符

```java
int score = 75;
String result = score >= 60 ? "及格" : "不及格";
```

---

## 5. 流程控制

### 5.1 分支结构

```java
// if - else if - else
int score = 85;
if (score >= 90) {
    System.out.println("优秀");
} else if (score >= 60) {
    System.out.println("及格");
} else {
    System.out.println("不及格");
}
```

```java
// 传统 switch（注意 break 贯穿）
String day = "Mon";
switch (day) {
    case "Mon":
    case "Tue":
        System.out.println("工作日");
        break;
    default:
        System.out.println("其他");
}
```

```java
// 增强 switch 表达式（Java 14+，推荐）
int day = 3;
String type = switch (day) {
    case 1, 2, 3, 4, 5 -> "工作日";
    case 6, 7 -> "周末";
    default -> "非法";
};
```

注意:case的值不能重复，default分支覆盖其他情况(兜底)

### 5.2 循环结构

```java
// for：已知次数
for (int i = 0; i < 5; i++) {
    System.out.print(i + " ");
}

// 增强 for：遍历数组/集合，只读遍历首选
int[] nums = {1, 2, 3};
for (int n : nums) {
    System.out.println(n);
}

// while：条件驱动
int i = 0;
while (i < 5) {
    i++;
}

// do-while：至少执行一次
int j = 10;
do {
    System.out.println(j);   // 即使条件不成立也会执行一次
} while (j < 5);
```

### 5.3 break / continue / 标签

```java
// break：跳出当前循环
// continue：跳过本次，进入下一次
for (int i = 1; i <= 10; i++) {
    if (i % 2 == 0) continue;  // 跳过偶数
    if (i > 7) break;          // 大于 7 就结束
    System.out.print(i + " ");  // 1 3 5 7
}

// 标签：跳出嵌套外层循环
outer:
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
        if (j == 2) break outer;
    }
}
```

---

## 6. 数组

Java 数组核心点就是：**固定长度、同类型、下标从 0 开始、用 length 获取长度、通过 Arrays 工具类操作**

### 6.1 声明与初始化

```java
// 静态初始化：声明时直接给值
int[] a = {1, 2, 3};
int[] b = new int[]{1, 2, 3};

// 动态初始化：只给长度，元素为默认值
int[] c = new int[5];        // {0,0,0,0,0}
boolean[] flags = new boolean[3];  // {false,false,false}
String[] names = new String[3];    // {null,null,null}
//通过下标读写数组元素，下标不能超过数组长度
// 读取某个下标元素
System.out.println(nums[2]);

//向某个下标位置赋值
nums[2] = 92;
System.out.println(nums[2]);

```

**数组下标越界**会抛出：

```
java.lang.ArrayIndexOutOfBoundsException
```

### 6.2 遍历与长度

```java
int[] nums = {10, 20, 30};
System.out.println(nums.length);   // 3，注意是属性不是方法

for (int i = 0; i < nums.length; i++) {
    System.out.println(nums[i]);
}
for (int n : nums) {
    System.out.println(n);
}
```

> 数组一旦创建，长度**固定不可变**；需要动态长度请用集合（阶段三）。

### 6.3 二维数组

```java
int[][] matrix = {
    {1, 2, 3},
    {4, 5, 6}
};
System.out.println(matrix[1][2]);   // 6

// 不规则二维数组
int[][] jagged = new int[2][];
jagged[0] = new int[1];
jagged[1] = new int[3];
```

### 6.4 Arrays 工具类

```java
import java.util.Arrays;

int[] arr = {3, 1, 4, 1, 5};

Arrays.sort(arr);                       // 升序排序：[1,1,3,4,5]
int idx = Arrays.binarySearch(arr, 4);  // 二分查找（需先排序）
boolean eq = Arrays.equals(arr, arr);   // 比较内容
System.out.println(Arrays.toString(arr)); // 打印：[1, 1, 3, 4, 5]Arrays.toString 快速打印
```

### 6.5 可变参数

```java
public static int sum(int... nums) {// 本质是 int[]，必须是最后一个参数，同一个方法内，可变参数只能有一组

    int total = 0;
    for (int n : nums) total += n;
    return total;
}

sum();              // 0
sum(1, 2, 3);       // 6
sum(new int[]{1, 2}); // 也可传数组
```

---

## 7. 方法🐤

### 7.1 定义与调用

静态方法可以通过类调用

**实例方法可以直接访问静态成员和实例成员；静态方法只能直接访问静态成员**

```java
修饰符 返回值类型 方法名(参数列表) {
    方法体;
    return 返回值;
}

public static int add(int a, int b) {
    return a + b;
}
```

### 7.2 方法重载

核心原则：**同一个行为，不同参数形式，用重载；语义不同，用不同方法名。**

```java
// 同名不同参数列表（类型/个数/顺序不同），与返回值无关
public static int add(int a, int b)          { return a + b; }
public static double add(double a, double b) { return a + b; }
public static int add(int a, int b, int c)   { return a + b + c; }
```

### 7.3 递归

```java
// 计算阶乘：自己调用自己，必须有终止条件
public static int factorial(int n) {
    if (n <= 1) return 1;        // 终止条件
    return n * factorial(n - 1);
}
```

> 递归三要素：**终止条件 + 向终止靠近 + 自己调用自己**。注意栈溢出风险。

### 7.4 值传递机制（重点难点）

**Java 只有值传递，没有引用传递。** 传对象时，传的是引用的**副本**。

```java
public static void main(String[] args) {
    int x = 10;
    changeInt(x);
    System.out.println(x);        // 10，基本类型不变

    int[] arr = {1, 2, 3};
    changeArray(arr);
    System.out.println(arr[0]);   // 99，数组内容被改了

    String s = "hi";
    changeString(s);
    System.out.println(s);        // hi，String 不可变
}

static void changeInt(int v)      { v = 99; }        // 改的是副本
static void changeArray(int[] a)  { a[0] = 99; }     // 副本指向同一个数组对象
static void changeString(String v){ v = "changed"; } // 副本重新指向新对象
```

一句话记忆：
- 参数是**基本类型** → 改形参不影响实参。
- 参数是**引用类型** → 改形参指向的对象**内容**会影响实参；但让形参**重新指向**新对象不影响实参。

---

## 8. 编码规范与常见陷阱

### 8.1 命名规范

| 元素 | 规范 | 示例 |
|------|------|------|
| 类名/接口 | 大驼峰 | `StudentScore` |
| 方法名 / 变量名 | 小驼峰 | `getScore`、`totalCount` |
| 常量 | 全大写下划线 | `MAX_SIZE` |
| 包名 | 全小写 | `com.example.demo` |

由 **字母、数字、下划线 `_`、美元符 `$`** 组成,**不能以数字开头**,**不能是 Java 关键字或保留字**。**区分大小写**，`public` 类名必须与文件名一致。

### 8.2 常见陷阱清单

| 陷阱 | 说明 | 规避 |
|------|------|------|
| 整数除法 | `5/2 = 2` | 至少一侧转 double |
| 浮点精度 | `0.1+0.2 != 0.3` | 金额用 BigDecimal |
| 数组越界 | 下标 0 ~ length-1 | 循环用 `<` 而非 `<=` |
| == 比字符串 | 比较的是地址 | 用 `equals()` |
| switch 漏 break | 会贯穿执行 | 用增强 switch |
| 死循环 | 循环变量未更新 | 检查退出条件 |
| 空指针 | 引用为 null 时调用方法 | 判空后再使用 |

---

## 9. 阶段验收练习

### 练习 1 · 基础语法
写一个程序，输出 1~100 中所有能被 3 或 5 整除的数，并统计个数。

### 练习 2 · 数组
给定一个整数数组，实现：求最大值、最小值、平均值、以及倒序输出。

```java
int[] data = {72, 89, 65, 90, 58, 77, 95};
// 提示：一次遍历即可同时求出 max/min/sum
```

### 练习 3 · 方法与重载
写一组计算器方法，支持 `int` 和 `double` 两种入参的加、减、乘、除（除数为 0 时返回提示）。

### 练习 4 · 综合 · 学生成绩统计（阶段验收项目）

需求：
1. 用数组存储 N 个学生成绩（可先写死）
2. 计算平均分、最高分、最低分
3. 按分数段输出等级：≥90 优秀、≥80 良好、≥60 及格、否则不及格
4. 将成绩从高到低排序输出
5. 拆分为多个方法（求平均、求等级、排序），练习方法抽取

**完成标准**：程序能运行、结果正确、代码有方法拆分和注释。

---

## 学习检查清单

- [ ] 能说清 JDK / JRE / JVM 的区别
- [ ] 能独立编译并运行一个 `.java` 文件
- [ ] 背下 8 种基本类型的字节数
- [ ] 会区分自动转换与强制转换，知道精度丢失
- [ ] 理解 `++i` 与 `i++` 的区别
- [ ] 知道 `&&` 的短路特性
- [ ] 会写 if / switch / for / while / do-while
- [ ] 能用 Arrays 工具类排序和打印数组
- [ ] 理解方法重载与值传递机制
- [ ] 完成阶段验收项目
