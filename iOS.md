
##1. runtime

###1.1 概念：什么是runtime？
    Runtime（运行时）是iOS/macOS系统的底层C/C++库​（开源地址：objc4），负责程序运行时的动态行为​：
    1. 对于Objective-C：它是「动态语言」的核心——类的创建、方法调用、消息传递都不是编译时固定的，而是运行时由Runtime决定的；
    2. 对于Swift：虽然Swift更强调静态类型安全，但仍依赖Runtime实现部分动态特性（如@objc修饰的方法、反射等）。


###1.2 底层运行时原理：核心机制
    1. 核心数据结构：类、对象与元类​ --> objc_object, objc_class, metaclass
    2. 消息传递：objc_msgSend
    3. 消息转发
        forwardingTargetForSelector
        methodSignatureForSelector
        forwardInvocation

###1.3 关键实现：Runtime的核心API与应用
    1. 动态添加方法​
    2. 方法交换（Method Swizzling）
    3. 关联对象（Associated Objects）
    4. 反射与动态调用​
        // 通过类名字符串创建类
        Class className = NSClassFromString(@"UIViewController");
        if (className) {
            UIViewController *vc = [[className alloc] init];
            
            // 通过方法名字符串调用方法
            SEL selector = NSSelectorFromString(@"viewDidLoad");
            if ([vc respondsToSelector:selector]) {
                [vc performSelector:selector];
            }
        }


##2. Runloop

###2.1 概念：什么是Runloop？
    RunLoop（运行循环）是iOS/macOS中管理线程生命周期与事件处理的核心机制，其本质是一个基于事件驱动的无限循环，负责在「有任务时执行任务，无任务时休眠」的循环逻辑.
    解决了两个关键问题：
        ​线程保活​：防止线程执行完任务后立即退出，保持活跃状态以响应后续事件。
        ​资源优化​：无任务时休眠，避免CPU空转浪费资源。

###2.2 底层运行机制：Runloop的组成
