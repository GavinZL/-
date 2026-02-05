# Kotlin 完全指南

> 从基础语法到高级特性 - Android 开发首选语言深度解析

## 📑 文章目录

- [一、Kotlin 概述与背景](#一kotlin-概述与背景)
  - [1.1 Kotlin 发展历史](#11-kotlin-发展历史)
  - [1.2 核心特性与优势](#12-核心特性与优势)
  - [1.3 Kotlin vs Java 对比](#13-kotlin-vs-java-对比)
- [二、基础语法](#二基础语法)
  - [2.1 变量与常量](#21-变量与常量)
  - [2.2 基本数据类型](#22-基本数据类型)
  - [2.3 控制流](#23-控制流)
  - [2.4 函数定义](#24-函数定义)
  - [2.5 类与对象](#25-类与对象)
- [三、关键字详解](#三关键字详解)
  - [3.1 修饰符关键字](#31-修饰符关键字)
  - [3.2 控制流关键字](#32-控制流关键字)
  - [3.3 特殊关键字](#33-特殊关键字)
- [四、面向对象编程](#四面向对象编程)
  - [4.1 类与继承](#41-类与继承)
  - [4.2 属性与字段](#42-属性与字段)
  - [4.3 接口](#43-接口)
  - [4.4 数据类](#44-数据类)
  - [4.5 密封类](#45-密封类)
  - [4.6 对象表达式与声明](#46-对象表达式与声明)
- [五、高级特性](#五高级特性)
  - [5.1 空安全](#51-空安全)
  - [5.2 扩展函数与属性](#52-扩展函数与属性)
  - [5.3 Lambda 表达式](#53-lambda-表达式)
  - [5.4 高阶函数](#54-高阶函数)
  - [5.5 泛型](#55-泛型)
  - [5.6 协程](#56-协程)
  - [5.7 委托](#57-委托)
  - [5.8 DSL 构建](#58-dsl-构建)
- [六、集合与序列](#六集合与序列)
- [七、最佳实践与技巧](#七最佳实践与技巧)
- [八、参考资料](#八参考资料)

---

## 一、Kotlin 概述与背景

### 1.1 Kotlin 发展历史

```
Kotlin 发展历程
├─ 2011 年
│  └─ JetBrains 公开发布 Kotlin 项目
├─ 2012 年
│  └─ 开源 Apache 2.0 许可证
├─ 2016 年
│  └─ Kotlin 1.0 正式发布
├─ 2017 年
│  └─ Google I/O 宣布 Kotlin 成为 Android 官方支持语言
├─ 2019 年
│  └─ Google 宣布 Kotlin-first for Android
└─ 2021 年至今
   ├─ Kotlin 1.5+ 持续演进
   ├─ Kotlin Multiplatform 成熟
   └─ Compose Multiplatform 发展
```

> **💡 为什么选择 Kotlin？**
>
> - **简洁性：** 相比 Java 减少约 40% 的代码量
> - **安全性：** 空安全设计，避免 NullPointerException
> - **互操作性：** 100% 兼容 Java，可无缝调用
> - **工具支持：** IntelliJ IDEA 和 Android Studio 原生支持
> - **现代特性：** 协程、扩展函数、DSL 等先进特性

### 1.2 核心特性与优势

```
Kotlin 核心特性
├─ 类型系统
│  ├─ 类型推断
│  ├─ 空安全（Null Safety）
│  └─ 智能类型转换
├─ 函数式编程
│  ├─ Lambda 表达式
│  ├─ 高阶函数
│  ├─ 内联函数
│  └─ 函数类型
├─ 面向对象增强
│  ├─ 数据类（Data Class）
│  ├─ 密封类（Sealed Class）
│  ├─ 单例对象（Object）
│  └─ 伴生对象（Companion Object）
├─ 扩展机制
│  ├─ 扩展函数
│  ├─ 扩展属性
│  └─ 接收者类型
├─ 协程（Coroutines）
│  ├─ 轻量级线程
│  ├─ 结构化并发
│  ├─ Flow 数据流
│  └─ 挂起函数
└─ 委托（Delegation）
   ├─ 类委托
   ├─ 属性委托
   └─ 标准委托（lazy, observable）
```

### 1.3 Kotlin vs Java 对比

| 特性 | Kotlin | Java |
|------|--------|------|
| **空安全** | 编译时空安全检查 | 运行时 NPE |
| **扩展函数** | 原生支持 | 需要工具类 |
| **Lambda** | 简洁的语法 | Java 8+ 支持 |
| **数据类** | 一行声明 | 需要手写 getter/setter/equals/hashCode |
| **协程** | 原生支持 | 需要第三方库 |
| **智能转换** | 自动类型转换 | 需要显式转换 |
| **默认参数** | 支持 | 需要重载 |
| **字符串模板** | $变量、${表达式} | + 拼接 |

---

## 二、基础语法

### 2.1 变量与常量

```kotlin
// val - 只读变量（不可变，类似 Java 的 final）
val name: String = "Kotlin"
val age = 10  // 类型推断

// var - 可变变量
var count: Int = 0
count = 10  // 可以重新赋值

// 延迟初始化
lateinit var message: String
message = "Hello"

// 懒加载
val lazyValue: String by lazy {
    println("计算中...")
    "Hello Lazy"  // 第一次访问时才执行
}

// 编译时常量（必须在顶层或 object 中）
const val MAX_COUNT = 100
```

> **⚠️ val vs var 选择原则**
>
> 优先使用 `val`，这样可以:
> - 提高代码的安全性和可预测性
> - 避免意外修改
> - 便于并发编程
> - 只有当确实需要修改时才使用 `var`

### 2.2 基本数据类型

```
Kotlin 数据类型体系
├─ 数字类型
│  ├─ Byte (8位)
│  ├─ Short (16位)
│  ├─ Int (32位)
│  ├─ Long (64位)
│  ├─ Float (32位浮点)
│  └─ Double (64位浮点)
├─ 字符与字符串
│  ├─ Char - 单个字符
│  └─ String - 字符串
├─ 布尔类型
│  └─ Boolean (true/false)
├─ 数组
│  ├─ Array<T> - 泛型数组
│  ├─ IntArray - 基本类型数组
│  └─ ByteArray, ShortArray, LongArray...
└─ 集合类型
   ├─ List/MutableList
   ├─ Set/MutableSet
   └─ Map/MutableMap
```

```kotlin
// 数字类型
val byteValue: Byte = 127
val intValue: Int = 2_147_483_647  // 下划线分隔符
val longValue: Long = 9_223_372_036_854_775_807L
val hexValue = 0x1F  // 十六进制
val binaryValue = 0b1010  // 二进制

// 浮点数
val pi: Double = 3.14159
val e: Float = 2.71828f

// 字符与字符串
val char: Char = 'A'
val str: String = "Hello Kotlin"

// 字符串模板
val name = "Kotlin"
val greeting = "Hello, $name!"
val length = "Length is ${name.length}"

// 原始字符串（三引号）
val multiLine = """
    |第一行
    |第二行
    |第三行
""".trimMargin()

// 数组
val array = arrayOf(1, 2, 3, 4, 5)
val intArray = intArrayOf(1, 2, 3)
val nullableArray = arrayOfNulls<String>(5)

// 类型转换
val x: Int = 100
val y: Long = x.toLong()  // 显式转换
val z: String = x.toString()
```

### 2.3 控制流

#### if 表达式

```kotlin
// Kotlin 中 if 是表达式，有返回值
val max = if (a > b) a else b

// 多行代码块
val result = if (a > b) {
    println("a 更大")
    a
} else {
    println("b 更大")
    b
}

// 替代三元运算符
val status = if (isValid) "有效" else "无效"
```

#### when 表达式

```kotlin
// 基本用法
when (x) {
    1 -> println("One")
    2 -> println("Two")
    else -> println("Other")
}

// 作为表达式返回值
val result = when (x) {
    0, 1 -> "小于2"  // 多个值
    in 2..10 -> "2到10之间"  // 范围
    !in 10..20 -> "不在10到20之间"
    is String -> "是字符串"  // 类型检查
    else -> "其他"
}

// 无参数形式（替代 if-else 链）
when {
    x.isOdd() -> println("奇数")
    x.isEven() -> println("偶数")
    else -> println("未知")
}

// 密封类匹配（exhaustive）
fun eval(expr: Expr): Int = when (expr) {
    is Expr.Const -> expr.number
    is Expr.Sum -> eval(expr.e1) + eval(expr.e2)
    // 无需 else，编译器知道已覆盖所有情况
}
```

#### 循环

```kotlin
// for 循环
for (i in 1..10) {  // 1 到 10（包含）
    println(i)
}

for (i in 1 until 10) {  // 1 到 9（不包含10）
    println(i)
}

for (i in 10 downTo 1 step 2) {  // 倒序，步长2
    println(i)  // 10, 8, 6, 4, 2
}

// 遍历集合
val list = listOf("A", "B", "C")
for (item in list) {
    println(item)
}

// 带索引遍历
for ((index, value) in list.withIndex()) {
    println("$index: $value")
}

// while 循环
var x = 0
while (x < 10) {
    println(x)
    x++
}

// do-while
do {
    x--
} while (x > 0)
```

### 2.4 函数定义

```kotlin
// 基本函数
fun sum(a: Int, b: Int): Int {
    return a + b
}

// 单表达式函数（可省略返回类型）
fun sum(a: Int, b: Int) = a + b

// 无返回值（Unit，可省略）
fun printSum(a: Int, b: Int): Unit {
    println("Sum is ${a + b}")
}

// 默认参数
fun greet(name: String, prefix: String = "Hello") {
    println("$prefix, $name!")
}
greet("Kotlin")  // 使用默认值
greet("Kotlin", "Hi")  // 覆盖默认值

// 具名参数
fun createUser(name: String, age: Int, email: String) { }
createUser(
    name = "Alice",
    email = "alice@example.com",
    age = 25  // 顺序可以不同
)

// 可变参数
fun printAll(vararg messages: String) {
    for (msg in messages) {
        println(msg)
    }
}
printAll("A", "B", "C")

// 中缀函数
infix fun Int.shl(x: Int): Int {
    // ...
}
val result = 1 shl 2  // 等同于 1.shl(2)

// 局部函数（函数内定义函数）
fun outerFunction() {
    fun innerFunction() {
        println("Inner")
    }
    innerFunction()
}
```

### 2.5 类与对象

```kotlin
// 基本类
class Person {
    var name: String = ""
    var age: Int = 0
}

// 主构造函数
class Person(val name: String, var age: Int)

// 带初始化块
class Person(val name: String) {
    init {
        println("创建了 $name")
    }
}

// 次构造函数
class Person(val name: String) {
    var age: Int = 0
    
    constructor(name: String, age: Int) : this(name) {
        this.age = age
    }
}

// 创建对象（无需 new 关键字）
val person = Person("Alice", 25)
```

---

## 三、关键字详解

### 3.1 修饰符关键字

```
Kotlin 修饰符关键字
├─ 可见性修饰符
│  ├─ public - 公开（默认）
│  ├─ private - 私有
│  ├─ protected - 受保护
│  └─ internal - 模块内可见
├─ 类修饰符
│  ├─ abstract - 抽象类/成员
│  ├─ final - 不可继承/重写（默认）
│  ├─ open - 可继承/重写
│  ├─ sealed - 密封类
│  ├─ data - 数据类
│  ├─ enum - 枚举类
│  ├─ inner - 内部类
│  └─ annotation - 注解类
├─ 成员修饰符
│  ├─ override - 重写
│  ├─ lateinit - 延迟初始化
│  ├─ const - 编译时常量
│  ├─ inline - 内联函数
│  ├─ infix - 中缀函数
│  ├─ operator - 运算符重载
│  ├─ tailrec - 尾递归
│  └─ suspend - 挂起函数
└─ 参数修饰符
   ├─ vararg - 可变参数
   ├─ crossinline - 禁止非局部返回
   └─ noinline - 禁止内联
```

```kotlin
// 可见性修饰符
public class PublicClass  // 默认就是 public
private class PrivateClass
internal class InternalClass  // 模块内可见

// open 允许继承
open class Base {
    open fun method() { }
}

class Derived : Base() {
    override fun method() { }
}

// 内联函数
inline fun performAction(action: () -> Unit) {
    action()
}

// 运算符重载
data class Point(val x: Int, val y: Int) {
    operator fun plus(other: Point) = 
        Point(x + other.x, y + other.y)
}

val p1 = Point(1, 2)
val p2 = Point(3, 4)
val p3 = p1 + p2  // 使用 + 运算符

// 尾递归优化
tailrec fun factorial(n: Int, acc: Int = 1): Int {
    return if (n <= 1) acc
    else factorial(n - 1, n * acc)
}
```

### 3.2 控制流关键字

| 关键字 | 用途 | 示例 |
|--------|------|------|
| `if` | 条件表达式 | val max = if (a > b) a else b |
| `when` | 多分支表达式 | when (x) { 1 -> "one" else -> "other" } |
| `for` | 循环 | for (i in 1..10) { } |
| `while` | 条件循环 | while (condition) { } |
| `break` | 跳出循环 | break |
| `continue` | 继续下一次循环 | continue |
| `return` | 返回 | return value |

```kotlin
// 标签（Label）
loop@for (i in 1..10) {
    for (j in 1..10) {
        if (j == 5) break@loop  // 跳出外层循环
    }
}

// Lambda 中的返回
fun foo() {
    listOf(1, 2, 3).forEach {
        if (it == 2) return@forEach  // 只返回 lambda
        println(it)
    }
    println("Done")  // 会执行
}
```

### 3.3 特殊关键字

```kotlin
// this - 当前接收者
class Person(val name: String) {
    fun introduce() {
        println("I am ${this.name}")
    }
}

// super - 父类
open class Base {
    open fun method() { }
}

class Derived : Base() {
    override fun method() {
        super.method()  // 调用父类方法
    }
}

// in - 类型参数协变、范围检查
interface Consumer<in T>  // 逆变
if (x in 1..10) { }  // 范围检查

// out - 类型参数协变
interface Producer<out T>  // 协变

// is - 类型检查
if (obj is String) {
    println(obj.length)  // 智能转换
}

// as - 类型转换
val str = obj as String  // 不安全转换
val str = obj as? String  // 安全转换，失败返回 null

// object - 单例/匿名对象
object Singleton {
    fun method() { }
}

// companion - 伴生对象
class MyClass {
    companion object {
        fun create(): MyClass = MyClass()
    }
}
```

---

## 四、面向对象编程

### 4.4 数据类（Data Class）

Kotlin 的数据类是一个非常强大的特性，自动生成 `equals()`、`hashCode()`、`toString()`、`copy()` 等方法。

```kotlin
// 简单数据类
data class User(
    val id: Int,
    val name: String,
    val email: String
)

// 使用
val user1 = User(1, "Alice", "alice@example.com")
val user2 = User(1, "Alice", "alice@example.com")

// 自动生成的方法
println(user1 == user2)  // true - equals()
println(user1)  // User(id=1, name=Alice, email=alice@example.com) - toString()

// copy() - 复制并修改部分属性
val user3 = user1.copy(name = "Bob")

// 解构声明
val (id, name, email) = user1
println("ID: $id, Name: $name")
```

> **📝 数据类要求**
>
> - 主构造函数至少有一个参数
> - 所有主构造函数参数必须标记为 `val` 或 `var`
> - 不能是 `abstract`、`open`、`sealed` 或 `inner`

### 4.5 密封类（Sealed Class）

密封类用于表示受限的类层次结构，是枚举类的扩展。

```kotlin
// 定义密封类
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val exception: Exception) : Result<Nothing>()
    object Loading : Result<Nothing>()
}

// 使用 when 进行匹配（穷尽性检查）
fun <T> handleResult(result: Result<T>) {
    when (result) {
        is Result.Success -> println("Success: ${result.data}")
        is Result.Error -> println("Error: ${result.exception}")
        Result.Loading -> println("Loading...")
        // 无需 else，编译器知道已覆盖所有情况
    }
}

// 实际应用
sealed class UIState {
    object Idle : UIState()
    object Loading : UIState()
    data class Success(val data: String) : UIState()
    data class Error(val message: String) : UIState()
}
```

> **✅ 密封类优势**
>
> - **类型安全：** 编译时检查，避免遗漏分支
> - **语义清晰：** 明确表达有限的状态集合
> - **when 表达式：** 无需 else 分支，穷尽性检查

### 4.6 对象表达式与声明

```kotlin
// 1. 对象声明（单例）
object DatabaseConfig {
    const val DB_NAME = "mydb"
    fun connect() { }
}

// 使用
DatabaseConfig.connect()

// 2. 伴生对象（类似 Java 的静态成员）
class MyClass {
    companion object Factory {
        fun create(): MyClass = MyClass()
    }
}

// 使用
val instance = MyClass.create()

// 3. 对象表达式（匿名对象）
val clickListener = object : View.OnClickListener {
    override fun onClick(v: View) {
        println("Clicked")
    }
}

// 4. 带状态的对象表达式
fun countClicks(window: JComponent) {
    var clickCount = 0
    
    window.addMouseListener(object : MouseAdapter() {
        override fun mouseClicked(e: MouseEvent) {
            clickCount++  // 可以访问外部变量
        }
    })
}
```

---

## 五、高级特性

### 5.1 空安全（Null Safety）

Kotlin 的空安全是其最重要的特性之一，从类型系统上消除了 NullPointerException。

```kotlin
// 可空类型 vs 非空类型
var nonNullStr: String = "Hello"
// nonNullStr = null  // 编译错误

var nullableStr: String? = "Hello"
nullableStr = null  // OK

// 1. 安全调用操作符 ?.
val length = nullableStr?.length  // 如果为 null 则返回 null

// 2. Elvis 操作符 ?:
val len = nullableStr?.length ?: 0  // 如果为 null 则返回 0

// 3. !! 操作符（非空断言）
val length2 = nullableStr!!.length  // 如果为 null 则抛出 NPE

// 4. 安全转换 as?
val num: Int? = str as? Int  // 转换失败返回 null

// 5. let 函数配合使用
nullableStr?.let {
    // 只有当 nullableStr 不为 null 时才执行
    println(it.length)
}

// 6. 智能转换
fun process(str: String?) {
    if (str != null) {
        // 在这个作用域内，str 自动转换为非空类型
        println(str.length)
    }
}

// 7. 平台类型
val list = ArrayList<String>()  // 平台类型（Java 互操作）
list.add(null)  // 运行时允许，但不推荐
```

> **⚠️ 空安全最佳实践**
>
> - 优先使用非空类型
> - 避免使用 `!!`，除非确定不为 null
> - 使用 `?.let` 处理可空值
> - 使用 Elvis 操作符提供默认值

### 5.2 扩展函数与属性

扩展函数允许为现有类添加新函数，而无需继承或使用装饰器模式。

```kotlin
// 为 String 添加扩展函数
fun String.removeWhitespace(): String {
    return this.replace(" ", "")
}

// 使用
val str = "Hello World"
println(str.removeWhitespace())  // "HelloWorld"

// 泛型扩展函数
fun <T> List<T>.secondOrNull(): T? {
    return if (this.size >= 2) this[1] else null
}

// 扩展属性
val String.lastChar: Char
    get() = this[length - 1]

println("Kotlin".lastChar)  // 'n'

// 可空接收者的扩展
fun Any?.toString(): String {
    if (this == null) return "null"
    return toString()
}

// 伴生对象扩展
class MyClass {
    companion object { }
}

fun MyClass.Companion.create(): MyClass {
    return MyClass()
}
```

> **📝 扩展函数原理**
>
> 扩展函数实际上是静态解析的，并不会修改原有类。编译后会转换为静态方法调用。
>
> ```kotlin
> // Kotlin
> fun String.last(): Char = this[length - 1]
> 
> // 编译后的 Java 代码（简化）
> public static char last(String $this) {
>     return $this.charAt($this.length() - 1);
> }
> ```

### 5.3 Lambda 表达式

```kotlin
// 基本 Lambda
val sum = { x: Int, y: Int -> x + y }
println(sum(1, 2))  // 3

// 类型推断
val list = listOf(1, 2, 3)
list.filter { it > 1 }  // it 是隐式参数名

// 显式参数名
list.filter { num -> num > 1 }

// 多行 Lambda
val process = { x: Int ->
    val doubled = x * 2
    println("Processing $x")
    doubled  // 最后一行作为返回值
}

// 闭包（捕获外部变量）
var sum = 0
list.forEach { sum += it }

// 带接收者的 Lambda
val stringBuilder = StringBuilder()
stringBuilder.apply {
    append("Hello ")
    append("World")
}

// 匿名函数
fun(x: Int, y: Int): Int = x + y

// Lambda 作为参数
fun calculate(x: Int, y: Int, operation: (Int, Int) -> Int): Int {
    return operation(x, y)
}

val result = calculate(5, 3) { a, b -> a + b }
```

### 5.4 高阶函数

高阶函数是以函数为参数或返回函数的函数。

```kotlin
// 接收函数作为参数
fun operateOnNumbers(
    x: Int, 
    y: Int, 
    operation: (Int, Int) -> Int
): Int {
    return operation(x, y)
}

// 使用
val sum = operateOnNumbers(5, 3) { a, b -> a + b }
val product = operateOnNumbers(5, 3) { a, b -> a * b }

// 返回函数
fun makeMultiplier(factor: Int): (Int) -> Int {
    return { x -> x * factor }
}

val double = makeMultiplier(2)
println(double(5))  // 10

// 内联函数（优化性能）
inline fun measureTime(block: () -> Unit) {
    val start = System.currentTimeMillis()
    block()
    val end = System.currentTimeMillis()
    println("Time: ${end - start}ms")
}

measureTime {
    // 一些耗时操作
}

// 带接收者的函数类型
fun buildString(builderAction: StringBuilder.() -> Unit): String {
    val sb = StringBuilder()
    sb.builderAction()
    return sb.toString()
}

val result = buildString {
    append("Hello")
    append(" ")
    append("World")
}
```

#### 标准库中的高阶函数

```kotlin
// let - 在对象上执行 lambda
val name: String? = "Kotlin"
name?.let {
    println(it.length)
}

// apply - 配置对象，返回对象本身
val person = Person().apply {
    name = "Alice"
    age = 25
}

// also - 执行额外操作，返回对象
val list = mutableListOf(1, 2, 3).also {
    println("List: $it")
}

// run - 执行 lambda 并返回结果
val result = "Kotlin".run {
    length + 10
}

// with - 在对象上执行多个操作
val numbers = mutableListOf(1, 2, 3)
with(numbers) {
    add(4)
    add(5)
    println(this)
}
```

### 5.6 协程（Coroutines）

Kotlin 协程是一种轻量级的并发方案，可以简化异步编程。

```kotlin
import kotlinx.coroutines.*

// 启动协程
fun main() = runBlocking {
    launch {
        delay(1000L)
        println("World!")
    }
    println("Hello")
}

// 挂起函数
suspend fun fetchData(): String {
    delay(1000L)  // 模拟网络请求
    return "Data"
}

// async/await 模式
suspend fun loadData() = coroutineScope {
    val deferred1 = async { fetchData() }
    val deferred2 = async { fetchData() }
    
    val result1 = deferred1.await()
    val result2 = deferred2.await()
    
    println("$result1, $result2")
}

// 协程上下文
GlobalScope.launch(Dispatchers.IO) {
    // IO 线程执行
}

GlobalScope.launch(Dispatchers.Main) {
    // 主线程执行（Android）
}

// Flow - 异步数据流
fun simpleFlow(): Flow<Int> = flow {
    for (i in 1..3) {
        delay(100)
        emit(i)  // 发送数据
    }
}

fun main() = runBlocking {
    simpleFlow().collect { value ->
        println(value)
    }
}
```

> **✅ 协程优势**
>
> - **轻量级：** 可以启动成千上万个协程
> - **结构化并发：** 通过 coroutineScope 管理生命周期
> - **异常处理：** 支持 try-catch
> - **取消支持：** 可以取消正在执行的协程

### 5.7 委托（Delegation）

```kotlin
// 1. 类委托
interface Base {
    fun print()
}

class BaseImpl(val x: Int) : Base {
    override fun print() { println(x) }
}

// 将接口实现委托给 b
class Derived(b: Base) : Base by b

val b = BaseImpl(10)
Derived(b).print()  // 10

// 2. 属性委托

// lazy - 延迟初始化
val lazyValue: String by lazy {
    println("计算中...")
    "Hello"
}

// observable - 观察属性变化
import kotlin.properties.Delegates

class User {
    var name: String by Delegates.observable("<no name>") { 
        prop, old, new ->
        println("$old -> $new")
    }
}

// vetoable - 拦截属性修改
var age: Int by Delegates.vetoable(0) { prop, old, new ->
    new >= 0  // 只允许非负数
}

// 自定义委托
class Delegate {
    operator fun getValue(thisRef: Any?, property: KProperty<*>): String {
        return "Delegated value"
    }
    
    operator fun setValue(thisRef: Any?, property: KProperty<*>, value: String) {
        println("Setting value: $value")
    }
}

var delegated: String by Delegate()

// Map 委托（常用于 JSON 解析）
class User(val map: Map<String, Any?>) {
    val name: String by map
    val age: Int by map
}

val user = User(mapOf(
    "name" to "Alice",
    "age" to 25
))
```

---

## 六、集合与序列

```kotlin
// 只读集合
val list = listOf(1, 2, 3)
val set = setOf("a", "b", "c")
val map = mapOf("key" to "value")

// 可变集合
val mutableList = mutableListOf(1, 2, 3)
mutableList.add(4)

// 常用操作
val numbers = listOf(1, 2, 3, 4, 5)

// filter - 过滤
val even = numbers.filter { it % 2 == 0 }

// map - 转换
val doubled = numbers.map { it * 2 }

// flatMap - 展开并合并
val nested = listOf(listOf(1, 2), listOf(3, 4))
val flattened = nested.flatMap { it }  // [1, 2, 3, 4]

// groupBy - 分组
val grouped = numbers.groupBy { it % 2 }

// fold/reduce - 聚合
val sum = numbers.fold(0) { acc, num -> acc + num }
val product = numbers.reduce { acc, num -> acc * num }

// 序列（懒求值）
val seq = numbers.asSequence()
    .filter { it % 2 == 0 }
    .map { it * 2 }
    .toList()  // 终端操作才开始计算
```

---

## 七、最佳实践与技巧

> **✅ Kotlin 编码规范**
>
> - 优先使用 `val` 而非 `var`
> - 使用数据类而非普通类来表示值对象
> - 使用密封类表示有限的类型层次
> - 避免使用 `!!`，使用安全调用 `?.`
> - 利用扩展函数提高代码可读性
> - 使用作用域函数（apply, let, run, with）
> - 适当使用内联函数优化性能
> - 使用协程而非线程处理异步任务

> **💡 性能优化技巧**
>
> - 使用序列处理大型集合
> - 内联函数减少 Lambda 开销
> - 使用基本类型数组（IntArray）而非泛型数组
> - 合理使用 `lazy` 委托

---

## 八、参考资料

- [Kotlin 官方文档](https://kotlinlang.org/docs/home.html)
- [Kotlin 语言参考](https://kotlinlang.org/docs/reference/)
- [Android Kotlin 指南](https://developer.android.com/kotlin)
- [Kotlin GitHub 仓库](https://github.com/JetBrains/kotlin)
- [Kotlin Tour](https://kotlinlang.org/docs/kotlin-tour-welcome.html)
- [Kotlin Playground](https://play.kotlinlang.org/)

---

© 2025 Kotlin 完全指南 | 持续更新中...
