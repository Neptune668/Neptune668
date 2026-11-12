# Java SE 阶段一学习笔记 · 环境与语法基础

> 对应大纲阶段一：开发环境 → 编译运行 → 变量与类型 → 运算符 → 流程控制 → 数组 → 方法
> 学习方式：每个知识点先看说明，再亲手敲一遍示例，最后做文末练习。

---

## 0. 为什么学 Java

- 掌握一个新的工具，扩展能力的边界，增加职场的选择范围。
- 核心能力：**工程化** —— 分析问题、设计方案、编码落地、测试上线、运行监控与维护。

---

## 1. 开发环境搭建

### 1.1 简介：Java 是什么

Java 是一门**静态强类型、面向对象**的通用编程语言。

- 静态：变量必须先声明类型，编译期就做类型检查。
- 强类型：不同类型之间不能随意混用，转换有严格规则（见 3.5）。
- 面向对象：以类 / 对象为基本组织单位（阶段二展开）。

### 1.2 JVM 跨平台原理

严格说：**JVM 本身并不跨平台，跨平台的是 Java 字节码；JVM 是平台相关的“适配层”**。不同 OS / CPU 有各自的 JVM 实现，但它们都遵循同一套 JVM 规范。

> **Java 源码编译成平台无关的字节码；各平台提供平台相关的 JVM；JVM 负责把统一字节码解释或编译成当前平台的机器码。因此跨平台的是字节码，JVM 是实现适配的关键中间层。**

#### 从开发到运行的完整流程

```text
Hello.java
   ↓ javac，由 JDK 提供
Hello.class
   ↓ java，由 JRE / JVM 提供
JVM 执行字节码
   ↓
当前平台的机器码
```

### 1.3 JDK / JRE / JVM 的关系

这三者是**包含关系**：JDK ⊃ JRE ⊃ JVM

| 名称 | 全称 | 作用 | 关系 |
|------|------|------|------|
| JVM | Java Virtual Machine | 执行字节码，是 Java 跨平台的核心 | 最底层 |
| JRE | Java Runtime Environment | JVM + 核心类库，只能**运行**程序，给运行者用 | JRE ⊃ JVM |
| JDK | Java Development Kit | JRE + 编译器等**开发**工具，开发者用 | JDK ⊃ JRE ⊃ JVM |

> 记忆：开发装 **JDK**，运行装 **JRE**。现在基本直接装 JDK。

### 1.4 安装与配置（Windows）

1. 下载 JDK 17 或 21（LTS 长期支持版），推荐 Adoptium / Oracle / 华为毕昇。
2. 配置环境变量：
   - `JAVA_HOME` = JDK 安装目录，如 `C:\Program Files\Java\jdk-21`
   - **注意**：`JAVA_HOME` 指向「能看到 `bin` 的那一层」目录，即**不包含 `bin`**（这是 `JAVA_HOME` 的规定写法）。
   - `Path` 中追加 `%JAVA_HOME%\bin`
3. 验证：

```bash
java -version    # 验证运行时
javac -version   # 验证编译器
```

两条命令都能输出对应版本号，说明配置成功。

> **小坑**：Path 环境变量打开后只有一行，这通常是 Windows 的正常现象，**不影响功能，只影响查看和编辑的便利性**。原因是 Path 的第一个值是以 `%` 开头的相对路径（如 `%SystemRoot%`），系统没能把它展开成多行列表。

### 1.5 IDEA 关键设置

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

Java 是「先编译成字节码，再由 JVM 解释 / JIT 执行」的语言，所以能跨平台（一次编写，到处运行）。

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
| `boolean` | - | true / false | false | 逻辑判断 |

> 除以上 8 种，其余都是**引用类型**（类、接口、数组、String、枚举等）。

几处细节：

- `char` 是 **16 位无符号**整数，能表示一个 Unicode 字符，写法是**单引号且只能包一个字符**（`'a'` 合法，`'ab'` 不合法）。
- `boolean` 在 Java 规范中**没有精确规定字节数**，通常按 1 字节实现，所以表中字节列留空。

### 3.2 变量声明与初始化

语法：`数据类型 变量名 = 初始值;`

需要掌握的六个要素：**类型、名称、值、作用域、默认值、`final` 与 `var`**。

要点：

- 必须**先声明类型**，类型确定后不能再存不兼容类型的值。
- **读取局部变量前必须初始化**（成员变量才有默认值）（`注意`）
- 变量有**作用域**，出了作用域即失效。
- 语句末尾记得**分号**。
- `final` 修饰的局部变量**只能赋值一次**，不可二次修改。

### 3.3 字面量写法

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

### 3.4 String 类型（非常常用，重点）

Java 中 `String` 用来保存字符串，它是**实打实的引用类型**，不是基本类型。但因为用得太频繁，JDK 给了它特殊待遇——**字符串常量池**。

```java
String s1 = "hello";
String s2 = "hello";
String s3 = new String("hello");

System.out.println(s1 == s2);       // true  （都指向常量池中的同一个对象）
System.out.println(s1 == s3);       // false （new 出来的是堆中的新对象）
System.out.println(s1.equals(s3));  // true  （equals 比较的是内容）
```

> **重点**：Java 中比较字符串**内容**必须用 `.equals()`；`==` 比较的是**内存地址**。

### 3.5 类型转换

Java 是强类型语言，不同类型之间的转换有严格规则。总体分三类。

#### （1）基本数据类型转换

```java
// 自动转换（小容量 → 大容量，安全，即隐式转换）
byte b = 10;
int i = b;        // byte -> int，自动
long l = i;       // int -> long，自动
float f = l;      // long -> float，自动，但可能丢失精度
double d = f;     // float -> double，自动

// 强制转换（大容量 → 小容量，可能丢精度）
double pi = 3.99;
int n = (int) pi;        // 结果 3，直接截断小数

int a2 = 200;
byte b2 = (byte) a2;     // 结果 -56，数据溢出

int i2 = 128;
byte b3 = (byte) i2;
System.out.println(b3);  // -128，溢出，符号位改变

// 想四舍五入，用 Math.round
long round = Math.round(3.99);  // 4

// 混合运算会向“大”的类型提升
System.out.println(1 + 2.0);    // 3.0，int 被提升为 double
```

转换方向大致是：

```text
byte -> short -> int -> long -> float -> double
                  char  -> int
```

> 陷阱：`char` 参与算术运算时会自动提升为 `int`。
> `'a' + 1` 得到的是数字 98，而不是字符 `'b'`，需要 `(char)('a' + 1)`。

##### 表达式中的类型提升

当不同类型参与运算时，Java 会自动提升为范围更大的类型。规则：

- `byte`、`short`、`char` 参与运算时，**先提升为 `int`**；
- 有一个操作数是 `long`，结果就是 `long`；
- 有一个操作数是 `float`，结果就是 `float`；
- 有一个操作数是 `double`，结果就是 `double`。

```java
byte x = 1;
byte y = 2;
// byte z = x + y;  // 编译错误，x + y 结果是 int
int z = x + y;      // 正确

long l2 = 10L;
double d3 = l2 + 1.5;  // 结果是 double
```

**复合赋值运算符隐含强制转换**：

```java
short s = 1;
s += 1;                      // 等价于 s = (short)(s + 1);
System.out.println(s);       // 2
```

但下面这样写会编译错误：

```java
short s2 = 1;
// s2 = s2 + 1;  // 错误，s2 + 1 已经是 int
```

##### 常量优化

如果赋值的是**编译期常量**，且值在目标类型范围内，可以直接赋值。

```java
byte b4 = 100;    // 正确，100 在 byte 范围内
// byte b5 = 128; // 错误，128 超出 byte 范围

final int X = 100;
byte b6 = X;      // 正确，X 是编译期常量
```

#### （2）引用数据类型转换

##### 向上转型（自动）

子类对象赋给父类引用，安全，自动完成。

```java
class Animal {}
class Dog extends Animal {}

Animal a = new Dog();   // 向上转型，自动
```

##### 向下转型（强制）

父类引用赋给子类引用，必须强制转换。

```java
Animal a = new Dog();
Dog d = (Dog) a;        // 向下转型，强制
```

如果实际对象类型不匹配，会抛出 `ClassCastException`：

```java
Animal a = new Animal();
// Dog d = (Dog) a;     // 运行时错误：ClassCastException
```

安全做法：先用 `instanceof` 判断。

```java
if (a instanceof Dog) {
    Dog d = (Dog) a;
    System.out.println("是 Dog");
}
```

Java 16+ 支持模式匹配写法，更简洁：

```java
if (a instanceof Dog d) {
    System.out.println("是 Dog");
}
```

#### （3）包装类与字符串转换

##### 自动装箱与拆箱

基本类型和包装类之间可以自动转换。

```java
Integer i = 100;   // 自动装箱：int -> Integer
int n = i;         // 自动拆箱：Integer -> int
```

注意：包装类对象为 `null` 时拆箱会抛 `NullPointerException`。

```java
Integer i = null;
// int n = i;      // NullPointerException
```

##### 字符串转基本类型

使用包装类的 `parseXxx` 方法：

```java
int i = Integer.parseInt("123");
double d = Double.parseDouble("3.14");
boolean b = Boolean.parseBoolean("true");
```

##### 基本类型转字符串

```java
String s1 = String.valueOf(123);
String s2 = Integer.toString(123);
String s3 = 123 + "";   // 简单写法，但可读性差
```

> **核心原则**：小转大自动，大转小强制；`boolean` 不参与；浮点转整数直接舍去小数；引用向上安全，向下要判断；字符串转数字用 `parse`，数字转字符串用 `valueOf`。

### 3.6 常量与 var

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

| 类别 | 运算符 | 注意 |
|------|--------|------|
| 算术 | `+ - * / %` | `/` 整除陷阱、`%` 取余 |
| 自增自减 | `++ --` | 前置先加后用，后置先用后加 |
| 关系 | `> < >= <= == !=` | 结果是 boolean |
| 逻辑 | `&&  ||!`或与非 | `&&` `\|\|` 有短路特性 |
| 位运算 | `& \| ^ ~ << >> >>>` | 二进制层面操作 |
| 赋值 | `= += -= *= /= %=` | 复合赋值隐含强制转换 |
| 三元 | `条件 ? A : B` | 简化 if-else |

### 4.2 位运算补充：异或 `^`

**按位异或（XOR）**规则：**相同为 0，不同为 1**。

```java
System.out.println(5 ^ 3);   // 0101 ^ 0011 = 0110 = 6
```

### 4.3 高频陷阱

```java
// 1. 整数除法
System.out.println(5 / 2);      // 2，不是 2.5！（整数相除，结果还是整数）
System.out.println(5 / 2.0);    // 2.5

// 2. 浮点精度
System.out.println(0.1 + 0.2);  // 0.30000000000000004
// 结论：金额计算用 BigDecimal，不要用 double

// 3. 自增顺序
// ++ 在后面：先取值，后自增
// ++ 在前面：先自增，后取值
int a = 5;
System.out.println(a++);        // 输出 5，之后 a = 6
System.out.println(++a);        // a 先变 7，输出 7

// 4. 短路求值
// && ：左边为假，右边不执行
// || ：左边为真，右边不执行
// & 、| ：两边都执行，不短路
int x = 0;
if (x != 0 && 10 / x > 1) { }   // 左边 false，右边不执行，不会除以 0
```

### 4.4 三元运算符

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

> 注意：`case` 的值**不能重复**；`default` 分支用来覆盖其他情况（兜底）。

### 5.2 循环结构

```java
// for：已知次数
for (int i = 0; i < 5; i++) {
    System.out.print(i + " ");
}

// 增强 for：遍历数组 / 集合，只读遍历首选
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
    if (i % 2 == 0) continue;   // 跳过偶数
    if (i > 7) break;           // 大于 7 就结束
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

Java 数组核心点：**固定长度、同类型、下标从 0 开始、用 `length` 获取长度、通过 `Arrays` 工具类操作**。

### 6.1 声明与初始化

```java
// 静态初始化：声明时直接给值
int[] a = {1, 2, 3};
int[] b = new int[]{1, 2, 3};

// 动态初始化：只给长度，元素为默认值
int[] c = new int[5];               // {0,0,0,0,0}
boolean[] flags = new boolean[3];   // {false,false,false}
String[] names = new String[3];     // {null,null,null}
```

通过下标读写数组元素，下标不能超过数组长度：

```java
int[] nums = {65, 78, 92};

// 读取某个下标元素
System.out.println(nums[2]);   // 92

// 向某个下标位置赋值
nums[2] = 96;
System.out.println(nums[2]);   // 96
```

**数组下标越界**会抛出：

```text
java.lang.ArrayIndexOutOfBoundsException
```

### 6.2 遍历与长度

```java
int[] nums = {10, 20, 30};
System.out.println(nums.length);   // 3，注意 length 是属性不是方法

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

Arrays.sort(arr);                          // 升序排序：[1,1,3,4,5]
int idx = Arrays.binarySearch(arr, 4);     // 二分查找（需先排序）
boolean eq = Arrays.equals(arr, arr);      // 比较内容
System.out.println(Arrays.toString(arr));  // 快速打印：[1, 1, 3, 4, 5]
```

### 6.5 可变参数

```java
// 本质是 int[]；必须是最后一个参数；同一个方法内，可变参数只能有一组
public static int sum(int... nums) {
    int total = 0;
    for (int n : nums) total += n;
    return total;
}

sum();                 // 0
sum(1, 2, 3);          // 6
sum(new int[]{1, 2});  // 也可传数组
```

---

## 7. 方法

### 7.1 定义与调用

语法：

```java
修饰符 返回值类型 方法名(参数列表) {
    方法体;
    return 返回值;
}

public static int add(int a, int b) {
    return a + b;
}
```

**静态与实例的访问规则（高频考点）**：

- 静态方法**可以通过类名直接调用**，不需要创建对象。
- **实例方法**可以直接访问静态成员和实例成员。
- **静态方法**只能直接访问静态成员（不能直接访问实例成员）。

### 7.2 方法重载

核心原则：**同一个行为、不同参数形式，用重载；语义不同，用不同的方法名。**

```java
// 同名、不同参数列表（类型 / 个数 / 顺序不同），与返回值无关
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

static void changeInt(int v)       { v = 99; }        // 改的是副本
static void changeArray(int[] a)   { a[0] = 99; }     // 副本指向同一个数组对象
static void changeString(String v) { v = "changed"; } // 副本重新指向新对象
```

一句话记忆：

- 参数是**基本类型** → 改形参不影响实参。
- 参数是**引用类型** → 改形参指向的对象**内容**会影响实参；但让形参**重新指向**新对象不影响实参。

---

## 8. 编码规范与常见陷阱

### 8.1 命名规范

| 元素 | 规范 | 示例 |
|------|------|------|
| 类名 / 接口 | 大驼峰 | `StudentScore` |
| 方法名 / 变量名 | 小驼峰 | `getScore`、`totalCount` |
| 常量 | 全大写下划线 | `MAX_SIZE` |
| 包名 | 全小写 | `com.example.demo` |

标识符由 **字母、数字、下划线 `_`、美元符 `$`** 组成，**不能以数字开头**，**不能是 Java 关键字或保留字**，**区分大小写**；`public` 类名必须与文件名一致。

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
- [ ] 能解释“跨平台的是字节码，不是 JVM”
- [ ] 能独立编译并运行一个 `.java` 文件
- [ ] 背下 8 种基本类型的字节数
- [ ] 会区分自动转换与强制转换，知道精度丢失
- [ ] 理解 `++i` 与 `i++` 的区别
- [ ] 知道 `&&` 的短路特性
- [ ] 理解 String 常量池与 `==`、`equals` 的区别
- [ ] 会写 if / switch / for / while / do-while
- [ ] 能用 Arrays 工具类排序和打印数组
- [ ] 理解方法重载与值传递机制
- [ ] 完成阶段验收项目

---

# Java SE 阶段二 · 面向对象与核心类库

> 对应大纲阶段二：类与对象 → 封装 / 继承 / 多态 → 抽象类与接口 → 内部类 → Object 类 → 字符串 → 包装类 → 枚举 → 日期时间 → 正则
> 学习方式：先理解概念与规则，再手敲示例，最后完成文末的图书管理系统项目。

## 1. 类与对象

### 1.1 什么是类与对象

> **Java 面向对象 = 用类描述事物，用对象干活；封装保护数据，继承复用代码，多态统一调用，抽象定义规范**

- **类（class）**：抽象的模板，描述一类事物的属性（成员变量）和行为（方法）。
- **对象（object）**：类的具体实例，通过 `new` 创建，存在于堆内存中。

```java
public class Student {
    // 成员变量（属性）
    String name;
    int age;

    // 构造器
    public Student() {}

    public Student(String name, int age) {
        this.name = name;
        this.age = age;
    }

    // 方法（行为）
    public void study() {
        System.out.println(name + " 正在学习");//字符串拼接
    }
}

// 使用
Student s = new Student("张三", 18);
// 1、创建 Student类的对象
// 底层行为说明：
// [1]new Soldier() 是在堆内存中开辟一块空间
// [2]Soldier soldier 是声明一个 Soldier 类型的变量
// [3]赋值是把 Soldier 对象在堆空间中的地址赋值给 soldier 变量
// [4]所在内存空间：对象在堆内存中，局部变量在栈内存中
// [5]堆内存中的对象必须通过指向它的变量才能被找到
System.out.println(s)//打印的是全类名@hash码，重新类的toString打印完整信息
s.study();//调用对象的方法
```

### 1.2 成员变量 vs 局部变量

| 对比项   | 成员变量                    | 局部变量               |
| -------- | --------------------------- | ---------------------- |
| 定义位置 | 类中、方法外                | 方法 / 代码块 / 参数中 |
| 内存位置 | 堆（对象里）(Heap)          | 栈(Stack)              |
| 默认值   | 有（int=0，引用=null）      | 无，必须先赋值         |
| 生命周期 | 随对象                      | 随方法调用             |
| 修饰符   | 可用 public/static/final 等 | 只能用 final           |

### 1.3 构造器（Constructor）

```java
public class User {
    String name;
    int age;

    public User() { // 无参构造
        this("未知", 0);// 调用本类其他构造器，必须放第一行
    }

    public User(String name, int age) {   // 有参构造
        this.name = name;
        this.age = age;
    }
}
```

- 构造器名与类名相同、无返回值类型（连 void 都不写）
- 不写构造器时，编译器自动给一个**无参构造器**；一旦写了有参构造器，无参的就没了。
- 构造器**不能被子类继承**，但子类构造器会默认调用父类无参构造器。

### 1.4 this 关键字

| 用法             | 说明                                |
| ---------------- | ----------------------------------- |
| `this.字段`      | 区分成员变量与同名的局部变量 / 参数 |
| `this.方法()`    | 调用本类其他方法                    |
| `this()`         | 调用本类其他构造器（必须在第一行）  |
| `this` 作为参数  | 把当前对象传给别的方法              |
| `this`作为返回值 | 实现链式调用                        |

### 1.5 static 关键字

psf快捷生成全局常量

```java
public class Counter {
    static int count = 0;      // 静态变量：全类共享，属于类不属于对象
    int id;                    // 实例变量：每个对象一份

    public Counter() {
        count++;
        id = count;
    }

    static void show() {       // 静态方法：通过类名调用
        System.out.println("共创建 " + count + " 个对象");
        // System.out.println(id);  // 错误：静态方法不能直接访问实例变量
    }

    static {                   // 静态代码块：类加载时执行一次，用于初始化，非静态代码块随着对象创建加载
        System.out.println("类被加载");
    }
}//静态上下文不能访问非静态的资源
//核心原因：静态上下文属于“类”，非静态资源属于“对象”。静态上下文没有当前对象引用 this，而实例字段、实例方法必须通过某个对象来访问。
Counter c1 = new Counter();
Counter c2 = new Counter();
Counter.show();                // 共创建 2 个对象
```

> 关键结论：**静态成员属于类，随类加载而存在；实例成员属于对象。** 静态方法中不能使用 `this`，也不能直接访问实例成员。

### 1.6 对象的内存布局

```java
Student s = new Student("张三", 18);
```

- `s` 这个引用变量在**栈**中；
- `new Student(...)` 创建的对象在**堆**中；
- 类的方法代码、静态变量在**方法区**。

---

## 2. 封装

封装 = 隐藏内部细节，只暴露必要接口。

```java
public class Account {
    private double balance;          // 私有，外部不能直接改

    public double getBalance() {     // 提供受控的访问
        return balance;
    }

    public void deposit(double amount) {
        if (amount <= 0) {
            System.out.println("金额非法");
            return;
        }
        this.balance += amount;      // 在方法内做校验
    }
}
```

### 2.1 访问修饰符

| 修饰符       | 本类 | 同包 | 子类 | 其他 |
| ------------ | :--: | :--: | :--: | :--: |
| `private`    |  ✔   |  ✘   |  ✘   |  ✘   |
| 默认（不写） |  ✔   |  ✔   |  ✘   |  ✘   |
| `protected`  |  ✔   |  ✔   |  ✔   |  ✘   |
| `public`     |  ✔   |  ✔   |  ✔   |  ✔   |

> 封装实践：**成员变量私有（private），通过 getter / setter 访问**。

---

## 3. 继承

子类无需重复编写父类已有的代码，直接“拿来即用”。同时，子类还能在此基础上增加独有的属性和方法，实现功能的灵活扩展。

### 3.0 super关键字

① 访问父类字段：`super.字段`，`super.方法()`

② 调用父类构造器：`super(参数)`

```java
public class Animal {
    protected String name;

    public Animal(String name) {
        this.name = name;
    }
    public void eat() {
        System.out.println(name + " 在吃东西");
    }
}

public class Dog extends Animal {
    public Dog(String name) {
        super(name);            // 调用父类构造器，必须第一行
    }
    @Override
    public void eat() {         // 方法重写
        super.eat();            // 也可调用父类原实现
        System.out.println("狗吃骨头");
    }
}
```

### 3.1 继承要点

- Java 是**单继承**：一个类只能 `extends` 一个父类（但可以多层继承）。
- 所有类默认继承 `Object`。
- 子类拥有父类的非私有成员；父类私有成员**不能直接访问**。
- 构造子类对象时，会**先调用父类构造器**（默认调无参，没有无参则必须显式 `super(...)`）。
- `final` 修饰的类不能被继承，`final` 修饰的方法不能被重写。

### 3.2 方法重写（Override）规则

| 规则     | 说明                                 |
| -------- | ------------------------------------ |
| 方法签名 | 方法名、参数列表必须相同             |
| 返回类型 | 相同或是父类返回值的子类（协变）     |
| 访问权限 | 不能比父类更严格                     |
| 异常     | 不能抛出更宽泛的受检异常             |
| 建议     | 一律加 `@Override`，让编译器帮你检查 |

> 重写 vs 重载：**重写是子类覆盖父类同名同参方法；重载是同类中同名不同参方法。** 重写看运行期，重载看编译期。

---

## 4. 多态

### 4.1 三个前提

1. 有**继承**（或接口实现）关系
2. 子类**重写**了父类方法
3. 父类引用**指向**子类对象（向上转型）

```java
Animal a = new Dog("旺财");   // 向上转型：父类引用指向子类对象
a.eat();                      // 实际执行 Dog 的 eat()
```

### 4.2 核心口诀：编译看左边，运行看右边

- **编译期**：看变量声明类型（左边）——`Animal` 里必须有这个方法，否则编译不过。
- **运行期**：看实际对象类型（右边）——真正执行的是 `Dog` 重写后的方法。

```java
Animal a = new Dog("旺财");
a.eat();          // ✔ 编译通过（Animal 有 eat），运行执行 Dog.eat()

// a.bark();      // ✘ 编译失败：Animal 里没有 bark 方法
```

### 4.3 向下转型与 instanceof

解决上面4.2不能调用子类特有的方法

```java
Animal a = new Dog("旺财");

if (a instanceof Dog) {//判断哪个类型转哪个类型
    Dog d = (Dog) a;        // 向下转型：父类引用 → 子类引用
    d.bark();
}
//向上转型为了统一处理，向下转型为了使用子类特有功能
// Java 16+ 模式匹配写法，自动完成强转
if (a instanceof Dog d) {
    d.bark();
}
```

> 陷阱：不能把「本来就是猫」的对象强转成狗，运行时抛 `ClassCastException`。转型前先用 `instanceof` 判断。

### 4.4 多态的典型用法

```java
public static void feed(Animal a) {   // 参数用父类类型
    a.eat();                           // 传入 Dog、Cat 都能工作
}

feed(new Dog("旺财"));
feed(new Cat("咪咪"));
```

> 多态的价值：**面向父类/接口编程**，新增子类时无需修改调用方代码。

---

## 5. 抽象类与接口

### 5.1 抽象类（abstract）

final被修饰常量不能修改，修饰方法禁止重写，修饰类禁止继承

```java
public abstract class Shape {
    protected String name;

    public abstract double area();     // 抽象方法：只有声明，没有实现

    public void print() {              // 抽象类也可以有普通方法
        System.out.println(name + " 面积 = " + area());
    }
}

public class Circle extends Shape {
    private double r;

    public Circle(double r) {
        this.name = "圆形";
        this.r = r;
    }

    @Override
    public double area() {
        return Math.PI * r * r;
    }
}
```

- 抽象类**不能实例化**（不能 `new`）。
- 有抽象方法的类必须是抽象类；抽象类可以没有抽象方法。
- 子类必须实现所有抽象方法，否则子类也得声明为抽象类。
- 抽象类中的抽象方法只是声明，不包含方法体，就是不给出方法的具体实现也就是方法的具体功能。
- 构造方法，类方法（用 static 修饰的方法）不能声明为抽象方法。

### 5.2 接口（interface）

类的多继承是不合法，但接口允许多继承。

```java
public interface Flyable {
    int MAX_SPEED = 100;               // 常量：默认 public static final默认赋值，不能修改

    void fly();                         // 抽象方法：默认 public abstract

    default void show() {                      // 默认方法（Java 8+）实现这个接口可以实现也可以不实现
        System.out.println("飞行能力");
    }

    static Flyable of() {                      // 静态方法（Java 8+）通过接口名直接调用
        return () -> System.out.println("默认飞行");
    }//接口中的方法是不能在接口中实现的，只能由实现接口的类来实现接口中的方法。
}

public class Bird implements Flyable {
    @Override
    public void fly() {
        System.out.println("鸟在飞");
    }
}
```

- 接口可以**多实现**：`class A implements X, Y, Z`。
- 接口中的字段都是常量，方法默认 `public abstract`。
- 一个类可以同时「继承父类 + 实现多个接口」：`class A extends B implements C, D`。

### 5.3 抽象类 vs 接口

| 对比项   | 抽象类             | 接口                    |
| -------- | ------------------ | ----------------------- |
| 关键字   | `extends`          | `implements`            |
| 数量     | 单继承             | 多实现                  |
| 成员变量 | 可以有普通变量     | 只能是常量              |
| 构造器   | 有                 | 无                      |
| 方法     | 抽象 + 普通        | 抽象 + default + static |
| 设计意图 | **是什么**（is-a） | **能做什么**（can-do）  |

---

### 5.4.函数式接口

一个有且仅有一个抽象方法，但是可以有多个非抽象方法的接口。

**lambda 表达式可以隐式转换成函数式接口的实例。**

```java
@FunctionalInterface
interface GreetingService 
{
    void sayMessage(String message);
}
GreetingService greetService1 = message -> System.out.println("Hello " + message);
```

| 接口            | 抽象方法            | 含义                   |
| :-------------- | :------------------ | :--------------------- |
| `Consumer<T>`   | `void accept(T t)`  | 消费一个值，不返回     |
| `Supplier<T>`   | `T get()`           | 不传参，返回一个值     |
| `Function<T,R>` | `R apply(T t)`      | 传一个值，返回另一个值 |
| `Predicate<T>`  | `boolean test(T t)` | 传一个值，返回布尔值   |

## 6. 内部类
将一个类定义在另一个类里面或者一个方法里面，这样的类称为内部类

| 类型       | 定义位置        | 特点                        |
| ---------- | --------------- | --------------------------- |
| 成员内部类 | 类中方法外      | 可访问外部类所有成员        |
| 静态内部类 | 类中，加 static | 不能直接访问外部实例成员    |
| 局部内部类 | 方法内          | 作用范围仅限该方法          |
| 匿名内部类 | 使用时定义      | 一次性使用，常配接口/抽象类 |

**内部类能方便地访问外部类成员，但要注意静态、实例引用、作用域和内存泄漏问题。**

```java
// 成员内部类
public class Outer {
    private int x = 10;

    class Inner {
        void show() {
            System.out.println(x);      // 可直接访问外部类私有成员
        }
    }
}

// 匿名内部类：最常用
Flyable f = new Flyable() {
    @Override
    public void fly() {
        System.out.println("匿名实现");
    }
};
f.fly();

// Lambda 替代匿名内部类（接口是函数式接口时）
Flyable f2 = () -> System.out.println("Lambda 实现");
```

---

## 7. Object 类

所有类都直接或间接继承 `Object`，因此都拥有它的方法。

### 7.1 常用方法

| 方法             | 作用               | 建议                   |
| ---------------- | ------------------ | ---------------------- |
| `toString()`     | 返回对象字符串表示 | 重写，便于打印调试     |
| `equals(Object)` | 判断内容是否相等   | 重写，配合 hashCode    |
| `hashCode()`     | 返回哈希值         | 重写 equals 必须重写它 |
| `getClass()`     | 获取运行时类       | 反射用                 |
| `clone()`        | 浅拷贝             | 需实现 Cloneable       |

### 7.2 == 与 equals 的区别

- `==`：基本类型比**值**，引用类型比**地址**。
- `equals()`：`Object` 默认也是比地址，重写后比**内容**。

```java
String s1 = new String("abc");
String s2 = new String("abc");
System.out.println(s1 == s2);        // false，地址不同
System.out.println(s1.equals(s2));   // true，内容相同
```

### 7.3 equals 与 hashCode 契约

> **规则：两个对象 equals 为 true，则 hashCode 必须相同；反之不要求。**

```java
public class Person {
    private String id;
    private String name;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Person p = (Person) o;
        return Objects.equals(id, p.id) && Objects.equals(name, p.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, name);   // 用 Objects.hash 简化
    }

    @Override
    public String toString() {
        return "Person{id='" + id + "', name='" + name + "'}";
    }
}
```

> 为什么必须配对重写？因为 `HashSet` / `HashMap` 先用 hashCode 定位桶，再用 equals 比较。只重写一个会导致去重失效。

---

## 8. 字符串

### 8.1 String 的不可变性

`String` 是**不可变**的，每次修改都会产生新对象。

```java
String s = "hello";
s = s + " world";        // 并非修改原对象，而是新建了 "hello world"
```

```java
String a = "abc";              // 存在字符串常量池
String b = "abc";              // 复用常量池中的同一个对象
String c = new String("abc");  // 强制在堆中新建对象

System.out.println(a == b);    // true
System.out.println(a == c);    // false
System.out.println(a.equals(c)); // true（永远用 equals 比较内容）
```

### 8.2 StringBuilder / StringBuffer

| 对比项   | String       | StringBuilder | StringBuffer         |
| -------- | ------------ | ------------- | -------------------- |
| 可变性   | 不可变       | 可变          | 可变                 |
| 线程安全 | —            | 不安全        | 安全（synchronized） |
| 性能     | 拼接慢       | 最快          | 稍慢                 |
| 适用场景 | 少量、不常改 | 单线程拼接    | 多线程拼接           |

```java
StringBuilder sb = new StringBuilder();
sb.append("Hello").append(", ").append("Java");
String result = sb.toString();      // "Hello, Java"

// 注意：循环里拼接字符串一定要用 StringBuilder
```

### 8.3 常用方法速查

```java
String s = "Hello, Java";
s.length();                  // 12
s.charAt(0);                 // 'H'
s.indexOf("Java");           // 7
s.substring(7);              // "Java"
s.substring(0, 5);           // "Hello"（左闭右开）
s.toUpperCase();             // "HELLO, JAVA"
s.contains("Java");          // true
s.startsWith("Hello");       // true
s.replace("Java", "World");  // "Hello, World"
s.split(", ");               // ["Hello", "Java"]
s.trim();                    // 去首尾空格
s.isEmpty();                 // false
"".isBlank();                // true（Java 11+，判断是否空白）
```

> 补充：`String.format` 与文本块（Java 15+ `"""..."""`）也值得掌握。

---

## 9. 包装类

每个基本类型都有对应的包装类：`byte→Byte`、`int→Integer`、`char→Character`、`boolean→Boolean` 等。

### 9.1 装箱与拆箱

```java
Integer i = 10;        // 自动装箱：int → Integer
int j = i;             // 自动拆箱：Integer → int

// 与 String 互转
String s = String.valueOf(123);      // int → String
String s2 = Integer.toString(123);
int n = Integer.parseInt("123");     // String → int（可能抛 NumberFormatException）
```

### 9.2 Integer 缓存陷阱（高频）

```java
Integer a = 127, b = 127;
Integer c = 128, d = 128;

System.out.println(a == b);   // true，127 在缓存范围内复用同一对象
System.out.println(c == d);   // false，128 超出缓存，各新建对象

// 结论：包装类比较一律用 equals()
System.out.println(c.equals(d));   // true
```

> `Integer` 缓存范围：**-128 ~ 127**。这是「用 == 比较包装类」翻车的根本原因。

---

## 10. 枚举

```java
public enum Season {
    SPRING("春天", 1),
    SUMMER("夏天", 2),
    AUTUMN("秋天", 3),
    WINTER("冬天", 4);

    private final String cn;
    private final int code;

    Season(String cn, int code) {     // 枚举构造器默认 private
        this.cn = cn;
        this.code = code;
    }

    public String getCn() { return cn; }

    public boolean isHot() {
        return this == SUMMER;
    }
}
```

```java
Season s = Season.SUMMER;
System.out.println(s.getCn());        // 夏天

Season[] all = Season.values();       // 遍历所有枚举常量
Season s2 = Season.valueOf("AUTUMN"); // 按名字获取
System.out.println(s.name());         // "SUMMER"
System.out.println(s.ordinal());      // 2（从 0 开始的序号）

// switch 中使用
switch (s) {
    case SUMMER -> System.out.println("热");
    default -> System.out.println("其他");
}
```

> 枚举适合替代「魔法值」，类型安全、可读性强。枚举也可实现接口、定义抽象方法。

---

## 11. 日期时间 API

Java 8 引入 `java.time`，**替代有线程安全问题的 `Date` / `SimpleDateFormat`**。

```java
import java.time.*;
import java.time.format.DateTimeFormatter;

LocalDate date = LocalDate.now();              // 2026-09-11
LocalTime time = LocalTime.now();              // 14:52:32.123
LocalDateTime dt = LocalDateTime.now();        // 日期 + 时间

// 构造指定时间
LocalDate birthday = LocalDate.of(2000, 1, 1);
LocalDateTime meeting = LocalDateTime.of(2026, 9, 11, 15, 30);

// 计算与加减
LocalDate nextWeek = date.plusWeeks(1);
LocalDate lastMonth = date.minusMonths(1);
int year = date.getYear();
boolean before = date.isBefore(nextWeek);

// 格式化与解析（线程安全，可缓存复用）
DateTimeFormatter fmt = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
String text = dt.format(fmt);                  // "2026-09-11 14:52:32"
LocalDateTime parsed = LocalDateTime.parse("2026-09-11 15:30:00", fmt);

// 时间间隔
Duration d = Duration.between(time, time.plusHours(2));   // 2 小时
Period p = Period.between(birthday, date);                // 年/月/日差

// 时间戳
Instant instant = Instant.now();
long epochMilli = instant.toEpochMilli();
```

| 旧 API             | 新 API                        | 说明                    |
| ------------------ | ----------------------------- | ----------------------- |
| `Date`             | `LocalDateTime` / `Instant`   | 新 API 不可变、线程安全 |
| `SimpleDateFormat` | `DateTimeFormatter`           | 新类线程安全            |
| `Calendar`         | `LocalDate` / `ZonedDateTime` | 更直观的加减            |

---

## 12. 正则表达式

```java
String regex = "^1[3-9]\\d{9}$";        // 手机号
String phone = "13812345678";
System.out.println(phone.matches(regex));   // true
```

```java
// String 中的三个常用方法
String s = "a1b2c3";
System.out.println(s.replaceAll("\\d", "#"));   // "a#b#c#"
System.out.println(s.replaceAll("\\D", ""));    // "123"
System.out.println("a,b,,c".split(",").length); // 4

// Pattern / Matcher：需要重复使用或提取分组时
import java.util.regex.*;

Pattern p = Pattern.compile("(\\d+)-(\\d+)");
Matcher m = p.matcher("订单 2026-09");
if (m.find()) {
    System.out.println(m.group(1));   // 2026
    System.out.println(m.group(2));   // 09
}
```

### 常用元字符

| 符号            | 含义          | 符号    | 含义           |
| --------------- | ------------- | ------- | -------------- |
| `.`             | 任意字符      | `\d`    | 数字 `[0-9]`   |
| `*`             | 0 次或多次    | `\D`    | 非数字         |
| `+`             | 1 次或多次    | `\w`    | 字母数字下划线 |
| `?`             | 0 次或 1 次   | `\s`    | 空白字符       |
| `{n}` / `{n,m}` | n 次 / n~m 次 | `^` `$` | 行首 / 行尾    |
| `[]`            | 字符集合      | `()`    | 分组           |
| `\|`            | 或            | `\\.`   | 转义点号       |

> 注意：Java 字符串里写正则，反斜杠要**双写**，如 `\\d`。

---

## 13. 编码规范与常见陷阱

### 13.1 常见陷阱清单

| 陷阱                        | 后果                     | 正确做法         |
| --------------------------- | ------------------------ | ---------------- |
| 重写 equals 不重写 hashCode | HashSet/HashMap 去重失效 | 两者成对重写     |
| 用 == 比较 String / 包装类  | 结果不符预期             | 用 `equals()`    |
| 循环里用 `+=` 拼 String     | 性能极差                 | 用 StringBuilder |
| 静态方法访问实例成员        | 编译错误                 | 先创建对象       |
| 忘记调 `super(...)`         | 父类无无参构造时编译错误 | 构造器第一行调用 |
| 父类构造器里调用可重写方法  | 子类字段尚未初始化       | 避免这种设计     |
| 向下转型不做判断            | ClassCastException       | 先 `instanceof`  |
| 抽象类被 `new`              | 编译错误                 | 用子类实例化     |

### 13.2 设计规范

- 成员变量用 `private`，暴露 getter/setter。
- 集合、工具类优先面向**接口**编程（`List<String> list = new ArrayList<>()`）。
- `toString()` 建议重写，便于日志排查。
- 能用枚举就别用 int 魔法值。

---

## 14. 阶段验收练习

### 练习 1 · 类与封装

设计 `BankAccount` 类：私有余额、开户人；提供存钱、取钱、查询方法，取钱金额超余额时给出提示。

### 练习 2 · 继承与多态

定义抽象类 `Shape`（含抽象方法 `area()`），派生出 `Circle`、`Rectangle`、`Triangle`，参数为 `Shape`，遍历数组打印各自面积。

### 练习 3 · 接口

定义接口 `Playable`（方法 `play()`），让 `Guitar`、`Piano` 实现它；再写 `default` 方法 `describe()` 输出乐器说明。

### 练习 4 · 字符串与包装类

输入一段文本，统计其中字母、数字、空格、其他字符的个数（提示：`Character.isLetter` / `isDigit`）。

### 练习 5 · 综合 · 图书管理系统（阶段验收项目）

需求：

1. 定义 `Book` 类：ISBN、书名、作者、价格、是否借出。重写 `equals` 与 `hashCode`（按 ISBN 去重）、`toString`。
2. 用 `ArrayList<Book>` 管理图书，实现增、删、按书名查询、按价格排序。
3. 用 `HashMap<String, Book>` 按 ISBN 快速检索。
4. 抽取 `Library` 类封装增删改查操作，用接口 `BookService` 定义行为。
5. 使用枚举 `Category` 给图书分类（如 `TECH`、`NOVEL`、`HISTORY`）。
6. 借阅日期用 `LocalDate` 记录，格式化输出。

**完成标准**：类划分清晰、有封装、用到继承/接口/枚举/集合至少各一次、代码带注释。

---

## 15. 学习检查清单

- [ ] 能说清类与对象、成员变量与局部变量的区别
- [ ] 会用 `this`、理解 `static` 的意义和限制
- [ ] 会用 private + getter/setter 做封装
- [ ] 理解继承的规则、会调用 `super`
- [ ] 能默写多态的「编译看左边、运行看右边」
- [ ] 会用 `instanceof` 做安全的向下转型
- [ ] 说得清抽象类与接口的区别与各自适用场景
- [ ] 会写匿名内部类，理解其与 Lambda 的关系
- [ ] 能正确重写 `equals` / `hashCode` / `toString`
- [ ] 知道 String 不可变与字符串常量池
- [ ] 背下 Integer 缓存范围（-128~127）
- [ ] 会用 `java.time` 做日期计算与格式化
- [ ] 能写基本正则并用 `Pattern` / `Matcher` 提取内容
- [ ] 完成图书管理系统项目

---

【强制】所有的相同类型的包装类对象之间值的比较,全部使用equals方法比较。 说明:对于Integer var=?在-128至127之间的赋值, Integer对象是在IntegerCache. cache产生,会复用已有对象,这个区间内的Integer值可以直接使用==进行判断,但是这个区间之外的所有数据，都会在堆上产生，并不会复用已有对象，这是一个大坑，推荐使用 equals 方法进行判断。
