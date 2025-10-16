# iOS Runtime 完整知识体系

## 目录
1. [概念：什么是 Runtime](#1-概念什么是-runtime)
2. [原理：Runtime 底层机制](#2-原理runtime-底层机制)
3. [实现：Runtime 核心 API](#3-实现runtime-核心-api)
4. [应用：Runtime 实战场景](#4-应用runtime-实战场景)
5. [Swift 中的 Runtime](#5-swift-中的-runtime)

---

## 1. 概念：什么是 Runtime？

### 1.1 定义
Runtime（运行时）是 iOS/macOS 系统的底层 C/C++ 库（开源地址：[objc4](https://opensource.apple.com/source/objc4/)），负责程序运行时的动态行为。

### 1.2 核心特性
- **对于 Objective-C**：它是「动态语言」的核心——类的创建、方法调用、消息传递都不是编译时固定的，而是运行时由 Runtime 决定的
- **对于 Swift**：虽然 Swift 更强调静态类型安全，但仍依赖 Runtime 实现部分动态特性（如 `@objc` 修饰的方法、反射等）

### 1.3 为什么需要 Runtime？
1. **动态性**：运行时决定调用哪个方法，而非编译时
2. **灵活性**：可以在运行时动态添加、替换、交换方法
3. **扩展性**：可以为已有类添加属性和方法，无需修改源码
4. **调试能力**：可以在运行时检查对象类型、方法列表等信息

---

## 2. 原理：Runtime 底层机制

### 2.1 核心数据结构

#### 2.1.1 对象结构（objc_object）
```c
struct objc_object {
    Class isa;  // 指向类对象的指针（现在使用 isa_t 联合体优化）
};
```

**isa 指针的作用**：
- 实例对象的 `isa` 指向类对象（Class）
- 类对象的 `isa` 指向元类对象（Meta-Class）
- 元类对象的 `isa` 指向根元类（Root Meta-Class）

#### 2.1.2 类结构（objc_class）
```c
struct objc_class : objc_object {
    Class superclass;           // 父类指针
    cache_t cache;             // 方法缓存（提高性能）
    class_data_bits_t bits;    // 类的详细信息
};

struct class_ro_t {
    const char * name;         // 类名
    method_list_t * baseMethodList;  // 方法列表
    protocol_list_t * baseProtocols; // 协议列表
    const ivar_list_t * ivars;       // 成员变量列表
    property_list_t *baseProperties; // 属性列表
};
```

#### 2.1.3 元类（Meta-Class）
- **元类是类对象的类**
- 类方法存储在元类中
- 所有元类的 `isa` 最终指向根元类（NSObject 的元类）
- 根元类的 `isa` 指向自己

**isa 和 superclass 指向关系**：
```
Instance (实例对象)
  isa ──> Class (类对象)
            isa ──> Meta-Class (元类)
                      isa ──> Root Meta-Class
                                isa ──> Root Meta-Class (指向自己)
  
Class
  superclass ──> Superclass ──> ... ──> NSObject ──> nil
  
Meta-Class
  superclass ──> Super Meta-Class ──> ... ──> Root Meta-Class
                                                superclass ──> NSObject (类对象)
```

### 2.2 消息传递机制（objc_msgSend）

#### 2.2.1 消息发送流程
当执行 `[receiver message]` 时，编译器会转换为：
```c
objc_msgSend(receiver, @selector(message))
```

**消息发送步骤**：
1. **快速查找**：通过对象的 `isa` 指针找到类对象，在缓存（cache）中查找方法
2. **慢速查找**：如果缓存未命中，在类的方法列表（method_list）中查找
3. **父类查找**：如果当前类没有找到，沿着 `superclass` 链向上查找
4. **动态解析**：如果仍未找到，进入动态方法解析阶段
5. **消息转发**：如果动态解析也失败，进入消息转发流程
6. **报错崩溃**：如果消息转发也失败，抛出 `unrecognized selector` 异常

#### 2.2.2 方法缓存机制
```c
struct cache_t {
    bucket_t *_buckets;  // 哈希表
    mask_t _mask;        // 哈希表大小-1
    mask_t _occupied;    // 已占用数量
};
```

- 使用**哈希表**存储最近调用的方法
- 通过 `SEL & mask` 计算索引位置
- 缓存命中率极高，大幅提升性能

### 2.3 消息转发机制

当方法查找失败后，Runtime 提供三次拯救机会：

#### 2.3.1 动态方法解析（Dynamic Method Resolution）
```objective-c
// 实例方法
+ (BOOL)resolveInstanceMethod:(SEL)sel {
    if (sel == @selector(dynamicMethod)) {
        // 动态添加方法实现
        class_addMethod([self class], sel, 
                       (IMP)dynamicMethodIMP, 
                       "v@:");
        return YES;
    }
    return [super resolveInstanceMethod:sel];
}

void dynamicMethodIMP(id self, SEL _cmd) {
    NSLog(@"动态添加的方法被调用");
}

// 类方法
+ (BOOL)resolveClassMethod:(SEL)sel {
    // 类方法存储在元类中，需要向元类添加方法
    if (sel == @selector(classMethod)) {
        Class metaClass = object_getClass(self);
        class_addMethod(metaClass, sel, 
                       (IMP)classMethodIMP, 
                       "v@:");
        return YES;
    }
    return [super resolveClassMethod:sel];
}
```

#### 2.3.2 快速转发（Fast Forwarding）
```objective-c
- (id)forwardingTargetForSelector:(SEL)aSelector {
    if (aSelector == @selector(unknownMethod)) {
        // 将消息转发给其他对象处理
        return [[OtherClass alloc] init];
    }
    return [super forwardingTargetForSelector:aSelector];
}
```

#### 2.3.3 完整转发（Normal Forwarding）
```objective-c
// 1. 返回方法签名
- (NSMethodSignature *)methodSignatureForSelector:(SEL)aSelector {
    if (aSelector == @selector(unknownMethod:)) {
        // 返回方法签名：v@:@（void, id, SEL, id）
        return [NSMethodSignature signatureWithObjCTypes:"v@:@"];
    }
    return [super methodSignatureForSelector:aSelector];
}

// 2. 完整的消息转发
- (void)forwardInvocation:(NSInvocation *)anInvocation {
    SEL selector = [anInvocation selector];
    
    // 可以修改参数、返回值、目标对象等
    if ([anotherObject respondsToSelector:selector]) {
        [anInvocation invokeWithTarget:anotherObject];
    } else {
        [super forwardInvocation:anInvocation];
    }
}
```

**完整消息转发流程图**：
```
[obj message]
    ↓
objc_msgSend
    ↓
缓存查找 → 方法列表查找 → 父类查找
    ↓ (未找到)
+ resolveInstanceMethod: (动态方法解析)
    ↓ (返回 NO)
- forwardingTargetForSelector: (快速转发)
    ↓ (返回 nil)
- methodSignatureForSelector: (获取方法签名)
    ↓
- forwardInvocation: (完整转发)
    ↓ (未处理)
doesNotRecognizeSelector: (抛出异常)
```

### 2.4 方法（Method）结构
```c
struct method_t {
    SEL name;           // 方法名（选择器）
    const char *types;  // 方法类型编码
    IMP imp;            // 方法实现（函数指针）
};
```

- **SEL**：方法选择器，是方法名的唯一标识符
- **IMP**：函数指针，指向方法的具体实现
- **Types**：方法的参数和返回值类型编码（Type Encoding）

**Type Encoding 示例**：
- `v@:` → void (id self, SEL _cmd)
- `@@:@` → id (id self, SEL _cmd, id arg)
- `i@:i` → int (id self, SEL _cmd, int arg)

---

## 3. 实现：Runtime 核心 API

### 3.1 类相关操作

#### 3.1.1 获取类信息
```objective-c
// 获取类对象
Class cls = [NSObject class];
Class cls2 = object_getClass(obj);  // 获取对象的类

// 获取类名
const char *className = class_getName(cls);
NSString *name = NSStringFromClass(cls);

// 获取父类
Class superCls = class_getSuperclass(cls);

// 判断是否是元类
BOOL isMeta = class_isMetaClass(cls);

// 获取实例大小
size_t instanceSize = class_getInstanceSize(cls);
```

#### 3.1.2 动态创建类
```objective-c
// 创建类
Class newClass = objc_allocateClassPair([NSObject class], "MyClass", 0);

// 添加成员变量（必须在注册前）
class_addIvar(newClass, "_name", sizeof(NSString *), 
             log2(sizeof(NSString *)), @encode(NSString *));

// 添加方法
class_addMethod(newClass, @selector(sayHello), 
               (IMP)sayHelloIMP, "v@:");

// 注册类
objc_registerClassPair(newClass);

// 使用类
id instance = [[newClass alloc] init];
[instance sayHello];

// 销毁类（确保没有实例存在）
objc_disposeClassPair(newClass);
```

### 3.2 方法相关操作

#### 3.2.1 获取方法信息
```objective-c
// 获取实例方法
Method method = class_getInstanceMethod([MyClass class], @selector(myMethod));

// 获取类方法
Method classMethod = class_getClassMethod([MyClass class], @selector(classMethod));

// 获取方法实现
IMP imp = method_getImplementation(method);

// 获取方法名
SEL selector = method_getName(method);

// 获取方法类型编码
const char *types = method_getTypeEncoding(method);

// 获取所有方法
unsigned int methodCount;
Method *methods = class_copyMethodList([MyClass class], &methodCount);
for (unsigned int i = 0; i < methodCount; i++) {
    Method method = methods[i];
    NSLog(@"方法名：%@", NSStringFromSelector(method_getName(method)));
}
free(methods);  // 注意释放内存
```

#### 3.2.2 动态添加方法
```objective-c
void dynamicMethodIMP(id self, SEL _cmd, NSString *param) {
    NSLog(@"动态方法被调用，参数：%@", param);
}

+ (BOOL)resolveInstanceMethod:(SEL)sel {
    if (sel == @selector(dynamicMethod:)) {
        class_addMethod([self class], sel, 
                       (IMP)dynamicMethodIMP, 
                       "v@:@");  // void, id, SEL, NSString*
        return YES;
    }
    return [super resolveInstanceMethod:sel];
}
```

#### 3.2.3 方法交换（Method Swizzling）

**标准实现**：
```objective-c
@implementation UIViewController (Tracking)

+ (void)load {
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        Class class = [self class];
        
        SEL originalSelector = @selector(viewWillAppear:);
        SEL swizzledSelector = @selector(swizzled_viewWillAppear:);
        
        Method originalMethod = class_getInstanceMethod(class, originalSelector);
        Method swizzledMethod = class_getInstanceMethod(class, swizzledSelector);
        
        // 先尝试添加原方法，如果已存在则添加失败
        BOOL didAddMethod = class_addMethod(class,
                                           originalSelector,
                                           method_getImplementation(swizzledMethod),
                                           method_getTypeEncoding(swizzledMethod));
        
        if (didAddMethod) {
            // 添加成功说明原方法不存在，替换 swizzled 方法实现为原实现
            class_replaceMethod(class,
                              swizzledSelector,
                              method_getImplementation(originalMethod),
                              method_getTypeEncoding(originalMethod));
        } else {
            // 原方法已存在，直接交换
            method_exchangeImplementations(originalMethod, swizzledMethod);
        }
    });
}

- (void)swizzled_viewWillAppear:(BOOL)animated {
    // 执行自定义逻辑
    NSLog(@"页面将要出现：%@", NSStringFromClass([self class]));
    
    // 调用原方法（因为方法已交换，这里实际调用的是原始的 viewWillAppear:）
    [self swizzled_viewWillAppear:animated];
}

@end
```

**为什么调用 `[self swizzled_viewWillAppear:animated]` 不会死循环？**

交换前：
```
viewWillAppear:          → 原始实现 A
swizzled_viewWillAppear: → 自定义实现 B
```

交换后：
```
viewWillAppear:          → 自定义实现 B
swizzled_viewWillAppear: → 原始实现 A
```

执行流程：
1. 系统调用 `viewWillAppear:` → 实际执行自定义实现 B
2. 在 B 中调用 `swizzled_viewWillAppear:` → 实际执行原始实现 A
3. 不会递归，因为方法实现已经互换

**Method Swizzling 最佳实践**：
1. 在 `+load` 方法中执行（而非 `+initialize`）
2. 使用 `dispatch_once` 确保只交换一次
3. 使用 `class_addMethod` + `class_replaceMethod` 组合（更安全）
4. 在 swizzled 方法中调用原方法（保持原有功能）
5. 谨慎使用，避免影响系统稳定性

### 3.3 成员变量（Ivar）操作

```objective-c
// 获取所有成员变量
unsigned int ivarCount;
Ivar *ivars = class_copyIvarList([MyClass class], &ivarCount);
for (unsigned int i = 0; i < ivarCount; i++) {
    Ivar ivar = ivars[i];
    const char *name = ivar_getName(ivar);
    const char *type = ivar_getTypeEncoding(ivar);
    NSLog(@"成员变量：%s, 类型：%s", name, type);
}
free(ivars);

// 获取指定成员变量
Ivar ivar = class_getInstanceVariable([MyClass class], "_name");

// 获取/设置成员变量的值
id obj = [[MyClass alloc] init];
object_setIvar(obj, ivar, @"新值");
id value = object_getIvar(obj, ivar);
```

### 3.4 属性（Property）操作

```objective-c
// 获取所有属性
unsigned int propertyCount;
objc_property_t *properties = class_copyPropertyList([MyClass class], &propertyCount);
for (unsigned int i = 0; i < propertyCount; i++) {
    objc_property_t property = properties[i];
    const char *name = property_getName(property);
    const char *attributes = property_getAttributes(property);
    NSLog(@"属性：%s, 特性：%s", name, attributes);
}
free(properties);
```

**属性特性（Attributes）说明**：
- `T` - 类型（Type）
- `V` - 成员变量名（iVar name）
- `C` - copy
- `&` - strong/retain
- `N` - nonatomic
- `R` - readonly
- `W` - weak
- `D` - dynamic

### 3.5 关联对象（Associated Objects）

#### 3.5.1 基本使用
```objective-c
// 为分类添加"属性"
@interface UIView (Tag)
@property (nonatomic, strong) NSString *customTag;
@end

@implementation UIView (Tag)

static const void *kCustomTagKey = &kCustomTagKey;

- (void)setCustomTag:(NSString *)customTag {
    objc_setAssociatedObject(self, 
                            kCustomTagKey, 
                            customTag, 
                            OBJC_ASSOCIATION_RETAIN_NONATOMIC);
}

- (NSString *)customTag {
    return objc_getAssociatedObject(self, kCustomTagKey);
}

@end
```

#### 3.5.2 关联策略（Association Policy）
```objective-c
typedef OBJC_ENUM(uintptr_t, objc_AssociationPolicy) {
    OBJC_ASSOCIATION_ASSIGN = 0,           // assign（不推荐用于对象）
    OBJC_ASSOCIATION_RETAIN_NONATOMIC = 1, // strong, nonatomic
    OBJC_ASSOCIATION_COPY_NONATOMIC = 3,   // copy, nonatomic
    OBJC_ASSOCIATION_RETAIN = 01401,       // strong, atomic
    OBJC_ASSOCIATION_COPY = 01403          // copy, atomic
};
```

### 3.6 反射与动态调用

```objective-c
// 字符串 → 类
Class cls = NSClassFromString(@"UIViewController");
id obj = [[cls alloc] init];

// 类 → 字符串
NSString *className = NSStringFromClass([UIViewController class]);

// 字符串 → SEL
SEL selector = NSSelectorFromString(@"viewDidLoad");

// SEL → 字符串
NSString *selectorName = NSStringFromSelector(@selector(viewDidLoad));

// 使用 performSelector（简单场景）
id result = [obj performSelector:@selector(methodName)];
[obj performSelector:@selector(methodWithParam:) withObject:@"参数"];

// 使用 NSInvocation（复杂场景，支持多参数、返回值）
NSMethodSignature *signature = [obj methodSignatureForSelector:@selector(method:param2:)];
NSInvocation *invocation = [NSInvocation invocationWithMethodSignature:signature];
[invocation setTarget:obj];
[invocation setSelector:@selector(method:param2:)];

NSString *param1 = @"参数1";
NSInteger param2 = 42;
[invocation setArgument:&param1 atIndex:2];  // 索引从2开始（0是self，1是_cmd）
[invocation setArgument:&param2 atIndex:3];

[invocation invoke];

// 获取返回值
NSString *returnValue;
[invocation getReturnValue:&returnValue];
```

---

## 4. 应用：Runtime 实战场景

### 4.1 字典转模型（JSON 解析）

```objective-c
@implementation NSObject (Model)

+ (instancetype)modelWithDictionary:(NSDictionary *)dict {
    id obj = [[self alloc] init];
    
    unsigned int propertyCount;
    objc_property_t *properties = class_copyPropertyList([self class], &propertyCount);
    
    for (unsigned int i = 0; i < propertyCount; i++) {
        objc_property_t property = properties[i];
        NSString *propertyName = @(property_getName(property));
        
        id value = dict[propertyName];
        if (value) {
            [obj setValue:value forKey:propertyName];
        }
    }
    
    free(properties);
    return obj;
}

@end
```

### 4.2 防止按钮重复点击

```objective-c
@implementation UIControl (PreventRepeatedClick)

+ (void)load {
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        Class class = [self class];
        
        SEL originalSelector = @selector(sendAction:to:forEvent:);
        SEL swizzledSelector = @selector(swizzled_sendAction:to:forEvent:);
        
        Method originalMethod = class_getInstanceMethod(class, originalSelector);
        Method swizzledMethod = class_getInstanceMethod(class, swizzledSelector);
        
        method_exchangeImplementations(originalMethod, swizzledMethod);
    });
}

static const void *kAcceptEventIntervalKey = &kAcceptEventIntervalKey;

- (NSTimeInterval)acceptEventInterval {
    return [objc_getAssociatedObject(self, kAcceptEventIntervalKey) doubleValue];
}

- (void)setAcceptEventInterval:(NSTimeInterval)acceptEventInterval {
    objc_setAssociatedObject(self, kAcceptEventIntervalKey, 
                            @(acceptEventInterval), 
                            OBJC_ASSOCIATION_RETAIN_NONATOMIC);
}

- (void)swizzled_sendAction:(SEL)action to:(id)target forEvent:(UIEvent *)event {
    if (self.acceptEventInterval > 0) {
        NSNumber *lastTime = objc_getAssociatedObject(self, @selector(setAcceptEventInterval:));
        NSTimeInterval currentTime = [[NSDate date] timeIntervalSince1970];
        
        if (lastTime && currentTime - [lastTime doubleValue] < self.acceptEventInterval) {
            return;  // 忽略重复点击
        }
        
        objc_setAssociatedObject(self, @selector(setAcceptEventInterval:), 
                                @(currentTime), 
                                OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    }
    
    [self swizzled_sendAction:action to:target forEvent:event];
}

@end
```

### 4.3 全局页面统计

```objective-c
@implementation UIViewController (Tracking)

+ (void)load {
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        Class class = [self class];
        
        SEL originalSelector = @selector(viewDidAppear:);
        SEL swizzledSelector = @selector(swizzled_viewDidAppear:);
        
        Method originalMethod = class_getInstanceMethod(class, originalSelector);
        Method swizzledMethod = class_getInstanceMethod(class, swizzledSelector);
        
        method_exchangeImplementations(originalMethod, swizzledMethod);
    });
}

- (void)swizzled_viewDidAppear:(BOOL)animated {
    [self swizzled_viewDidAppear:animated];
    
    // 统计页面访问
    NSString *className = NSStringFromClass([self class]);
    NSLog(@"📊 页面统计：%@", className);
}

@end
```

---

## 5. Swift 中的 Runtime

### 5.1 Swift 与 Objective-C Runtime 的关系

Swift 是一门静态类型语言，但在与 Objective-C 混编时，仍然依赖 Objective-C Runtime。

**Swift 使用 Runtime 的场景**：
1. `@objc` 修饰的类、方法、属性
2. 继承自 NSObject 的类
3. KVO、KVC
4. 动态方法调用（`perform(_:with:)`）
5. Selector

**Swift 不使用 Runtime 的场景**：
1. 纯 Swift 类（不继承 NSObject）
2. 值类型（struct、enum）
3. 泛型
4. 命名空间

### 5.2 Swift 中使用 Runtime API

#### 5.2.1 获取类信息
```swift
import ObjectiveC

class Person: NSObject {
    @objc var name: String = ""
    @objc var age: Int = 0
}

let person = Person()

// 获取类名
let className = NSStringFromClass(type(of: person))

// 获取所有属性
var propertyCount: UInt32 = 0
let properties = class_copyPropertyList(Person.self, &propertyCount)

for i in 0..<Int(propertyCount) {
    if let property = properties?[i] {
        let propertyName = String(cString: property_getName(property))
        print("属性：\(propertyName)")
    }
}

free(properties)
```

#### 5.2.2 Method Swizzling in Swift
```swift
import UIKit

extension UIViewController {
    @objc func swizzled_viewWillAppear(_ animated: Bool) {
        // 调用原方法
        self.swizzled_viewWillAppear(animated)
        
        // 自定义逻辑
        print("页面将要出现：\(type(of: self))")
    }
    
    static func swizzleViewWillAppear() {
        guard let originalMethod = class_getInstanceMethod(UIViewController.self, 
                                                           #selector(viewWillAppear(_:))),
              let swizzledMethod = class_getInstanceMethod(UIViewController.self, 
                                                           #selector(swizzled_viewWillAppear(_:))) else {
            return
        }
        
        method_exchangeImplementations(originalMethod, swizzledMethod)
    }
}

// 在 AppDelegate 中调用
UIViewController.swizzleViewWillAppear()
```

#### 5.2.3 关联对象 in Swift
```swift
import ObjectiveC

extension UIView {
    private static var customTagKey: UInt8 = 0
    
    var customTag: String? {
        get {
            return objc_getAssociatedObject(self, &UIView.customTagKey) as? String
        }
        set {
            objc_setAssociatedObject(self, 
                                    &UIView.customTagKey, 
                                    newValue, 
                                    .OBJC_ASSOCIATION_RETAIN_NONATOMIC)
        }
    }
}
```

### 5.3 Swift 的反射（Mirror）

Swift 提供了自己的反射机制 `Mirror`，用于纯 Swift 类型：

```swift
struct Person {
    var name: String
    var age: Int
}

let person = Person(name: "李四", age: 30)

// 使用 Mirror 反射
let mirror = Mirror(reflecting: person)

for case let (label?, value) in mirror.children {
    print("\(label): \(value)")
}
```

**Mirror vs Runtime**：

| 特性 | Mirror（Swift） | Runtime（ObjC） |
|------|----------------|----------------|
| 支持类型 | 所有 Swift 类型 | NSObject 子类 |
| 性能 | 较慢 | 较快 |
| 功能 | 只读反射 | 可读可写，可动态修改 |
| 动态性 | 有限 | 强大 |

### 5.4 Swift 中的 KVO

```swift
class Person: NSObject {
    @objc dynamic var name: String = ""  // 必须使用 @objc dynamic
    @objc dynamic var age: Int = 0
}

class Observer: NSObject {
    var person: Person
    var observation: NSKeyValueObservation?
    
    init(person: Person) {
        self.person = person
        super.init()
        
        // 使用 observe
        observation = person.observe(\.name, options: [.new, .old]) { person, change in
            print("name 改变了")
        }
    }
}
```

---

## 总结

### Runtime 核心要点

1. **概念层面**：
   - Runtime 是 ObjC 动态语言的核心机制
   - 负责运行时的类型检查、方法调用、消息转发
   - Swift 部分依赖 Runtime（@objc 修饰）

2. **原理层面**：
   - 核心数据结构：objc_object、objc_class、Meta-Class
   - 消息传递：objc_msgSend → 缓存查找 → 方法列表查找 → 父类查找
   - 消息转发：动态方法解析 → 快速转发 → 完整转发

3. **实现层面**：
   - 类操作：获取类信息、动态创建类
   - 方法操作：获取方法、动态添加方法、Method Swizzling
   - 属性操作：获取属性、修改私有属性
   - 关联对象：为分类添加"属性"
   - 反射：字符串与类/方法互转

4. **应用层面**：
   - 字典转模型（JSON 解析）
   - 防止按钮重复点击
   - 全局页面统计
   - AOP（面向切面编程）

5. **Swift 特殊性**：
   - 需要 @objc 修饰才能使用 Runtime
   - 值类型不支持 Runtime
   - Swift 有自己的反射机制 Mirror
   - KVO 需要 @objc dynamic 修饰

### 注意事项

⚠️ **Method Swizzling 风险**：
- 可能与系统或第三方库冲突
- 影响性能（增加调用链）
- 难以调试
- 建议在 +load 方法中使用 dispatch_once

⚠️ **关联对象注意**：
- 会增加内存开销
- 需要注意内存管理策略
- dealloc 时会自动释放

⚠️ **性能考虑**：
- Runtime 方法比直接调用慢
- 缓存机制能大幅优化性能
- 不要在热点路径中频繁使用 Runtime API
```