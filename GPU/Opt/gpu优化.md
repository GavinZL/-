# 移动端OpenGL ES GPU优化技术详解

> GPU端Shader优化：顶点着色器、片元着色器、渲染管线优化

## 目录

1. [GPU优化概述](#1-gpu优化概述)
2. [顶点Shader优化](#2-顶点shader优化)
3. [片元Shader优化](#3-片元shader优化)
4. [渲染管线优化](#4-渲染管线优化)
5. [移动GPU架构适配](#5-移动gpu架构适配)
6. [性能分析与调优](#6-性能分析与调优)
7. [优化检查清单](#7-优化检查清单)

---

## 1. GPU优化概述

### 1.1 GPU性能指标

**关键性能指标**

| 指标 | 定义 | 目标值 | 获取方式 |
|------|------|--------|---------|
| cycles/pixel | 每像素处理周期 | <1.0 | Mali Offline Compiler |
| 寄存器使用 | 工作寄存器数量 | <16 | Shader编译器 |
| 纹理采样数 | 每着色器采样次数 | <8 | 代码审查 |
| FP16利用率 | 16位浮点使用比例 | >70% | Mali分析报告 |
| 分支发散度 | 线程执行路径差异 | 0% | 性能分析 |

### 1.2 优化优先级

```
GPU优化优先级金字塔：

        ┌────────────┐
        │ 平台特定   │ 5%收益
        │  优化      │
      ┌─┴────────────┴─┐
      │  渲染管线优化   │ 15%收益
      │ Early-Z/混合   │
    ┌─┴────────────────┴─┐
    │   纹理采样优化      │ 20%收益
    │ 减少采样/压缩纹理   │
  ┌─┴────────────────────┴─┐
  │    算术运算优化         │ 25%收益
  │  避免昂贵运算/向量化    │
┌─┴────────────────────────┴─┐
│      精度优化（最重要）      │ 35%收益
│   lowp/mediump/预计算       │
└──────────────────────────────┘
```

---

## 2. 顶点Shader优化

### 2.1 顶点处理原则

顶点着色器每顶点执行一次，相比片元着色器（每像素执行）计算量小得多，但仍需优化。

**顶点vs片元执行频率**

```
场景示例：1080p全屏四边形
├── 顶点数：4个
├── 片元数：1920 × 1080 = 2,073,600个
├── 比例：1:518,400
└── 结论：将计算从片元移至顶点可获得巨大收益

场景示例：10万三角形模型
├── 顶点数：约50,000个（共享顶点）
├── 片元数：约500,000个（假设50%屏幕覆盖）
├── 比例：1:10
└── 结论：顶点计算仍比片元便宜10倍
```

### 2.2 顶点预计算

**将复杂计算从片元移至顶点**

```glsl
// ❌ Bad: 在Fragment Shader计算（每像素执行）
// Vertex Shader
attribute vec3 a_position;
attribute vec3 a_normal;

uniform mat4 u_mvpMatrix;
uniform mat4 u_modelMatrix;

varying vec3 v_worldPos;     // 传递世界坐标
varying vec3 v_worldNormal;  // 传递世界法线

void main() {
    vec4 worldPos = u_modelMatrix * vec4(a_position, 1.0);
    v_worldPos = worldPos.xyz;
    v_worldNormal = a_normal;
    gl_Position = u_mvpMatrix * vec4(a_position, 1.0);
}

// Fragment Shader（性能差）
precision highp float;

varying vec3 v_worldPos;
varying vec3 v_worldNormal;

uniform vec3 u_lightPos;
uniform vec3 u_cameraPos;

void main() {
    // ❌ 每像素计算归一化和方向
    vec3 normal = normalize(v_worldNormal);
    vec3 lightDir = normalize(u_lightPos - v_worldPos);
    vec3 viewDir = normalize(u_cameraPos - v_worldPos);
    vec3 halfVec = normalize(lightDir + viewDir);
    
    float diffuse = max(dot(normal, lightDir), 0.0);
    float specular = pow(max(dot(normal, halfVec), 0.0), 32.0);
    
    gl_FragColor = vec4(vec3(diffuse + specular), 1.0);
}

// Mali分析：Fragment Shader 2.1 cycles/pixel
```

```glsl
// ✅ Good: 在Vertex Shader预计算（每顶点执行）
// Vertex Shader
attribute vec3 a_position;
attribute vec3 a_normal;

uniform mat4 u_mvpMatrix;
uniform mat4 u_modelMatrix;
uniform mat3 u_normalMatrix;
uniform vec3 u_lightPos;
uniform vec3 u_cameraPos;

varying mediump vec3 v_normal;      // 已归一化
varying mediump vec3 v_lightDir;    // 已归一化
varying mediump vec3 v_halfVec;     // 已归一化
varying mediump float v_attenuation;

void main() {
    vec4 worldPos = u_modelMatrix * vec4(a_position, 1.0);
    gl_Position = u_mvpMatrix * vec4(a_position, 1.0);
    
    // ✅ 在顶点着色器预计算
    v_normal = normalize(u_normalMatrix * a_normal);
    
    vec3 toLight = u_lightPos - worldPos.xyz;
    float lightDist = length(toLight);
    v_lightDir = toLight / lightDist;  // 归一化
    
    vec3 viewDir = normalize(u_cameraPos - worldPos.xyz);
    v_halfVec = normalize(v_lightDir + viewDir);
    
    // 预计算衰减
    v_attenuation = 1.0 / (1.0 + lightDist * lightDist * 0.01);
}

// Fragment Shader（性能优秀）
precision mediump float;

varying mediump vec3 v_normal;
varying mediump vec3 v_lightDir;
varying mediump vec3 v_halfVec;
varying mediump float v_attenuation;

void main() {
    // ✅ 直接使用预计算结果
    float diffuse = max(dot(v_normal, v_lightDir), 0.0);
    float specular = pow(max(dot(v_normal, v_halfVec), 0.0), 32.0);
    
    vec3 color = vec3(diffuse + specular) * v_attenuation;
    gl_FragColor = vec4(color, 1.0);
}

// Mali分析：Fragment Shader 0.7 cycles/pixel
// 性能提升：200%
```

### 2.3 顶点格式优化

**减少顶点数据大小**

```cpp
// ❌ Bad: 冗余顶点格式（48字节/顶点）
struct BadVertex {
    float position[3];   // 12字节
    float normal[3];     // 12字节
    float tangent[4];    // 16字节（含手性）
    float texCoord[2];   // 8字节
};  // 总计48字节

// ✅ Good: 压缩顶点格式（24字节/顶点）
struct GoodVertex {
    int16_t position[3]; // 6字节（归一化到模型空间）
    int16_t padding;     // 2字节（对齐）
    int8_t normal[4];    // 4字节（归一化，SNORM）
    int8_t tangent[4];   // 4字节（归一化，SNORM）
    uint16_t texCoord[2];// 4字节（UNORM）
};  // 总计20字节（对齐到24）

// 设置压缩顶点属性
void SetupCompressedVertexAttributes() {
    // 位置：16位有符号整数，需在着色器中缩放
    glVertexAttribPointer(0, 3, GL_SHORT, GL_FALSE, 
                          sizeof(GoodVertex), (void*)0);
    
    // 法线：8位有符号归一化
    glVertexAttribPointer(1, 4, GL_BYTE, GL_TRUE,  // GL_TRUE归一化
                          sizeof(GoodVertex), (void*)8);
    
    // 切线：8位有符号归一化
    glVertexAttribPointer(2, 4, GL_BYTE, GL_TRUE,
                          sizeof(GoodVertex), (void*)12);
    
    // UV：16位无符号归一化
    glVertexAttribPointer(3, 2, GL_UNSIGNED_SHORT, GL_TRUE,
                          sizeof(GoodVertex), (void*)16);
}

// 顶点着色器中处理压缩数据
const char* compressedVertexShader = R"(
attribute vec3 a_position;    // 归一化后的位置（-1到1）
attribute vec4 a_normal;      // 已归一化（GL_TRUE）
attribute vec4 a_tangent;     // 已归一化（GL_TRUE）
attribute vec2 a_texCoord;    // 已归一化（GL_TRUE）

uniform mat4 u_mvpMatrix;
uniform vec3 u_posScale;      // 模型空间缩放
uniform vec3 u_posOffset;     // 模型空间偏移

void main() {
    // 还原位置（从归一化值）
    vec3 position = a_position * u_posScale + u_posOffset;
    gl_Position = u_mvpMatrix * vec4(position, 1.0);
    
    // 法线和切线已经是归一化的，直接使用
    v_normal = a_normal.xyz;
    v_tangent = a_tangent;
    v_texCoord = a_texCoord;
}
)";
```

**顶点格式优化收益**

| 格式 | 大小 | 带宽（10万顶点） | 缓存效率 |
|------|------|-----------------|---------|
| 原始（Float） | 48B | 4.8 MB/帧 | 低 |
| 压缩（Int16/8） | 24B | 2.4 MB/帧 | 高 |
| 收益 | 50%减少 | 50%减少 | 2x |

### 2.4 避免冗余Varying

**精简Varying变量**

```glsl
// ❌ Bad: 过多Varying（带宽浪费）
varying highp vec3 v_position;      // 很少需要片元位置
varying highp vec3 v_worldPos;      // 冗余
varying mediump vec3 v_normal;
varying mediump vec3 v_tangent;
varying mediump vec3 v_bitangent;   // 可在片元计算
varying mediump vec2 v_texCoord;
varying mediump vec2 v_texCoord2;   // 第二UV常不需要
varying lowp vec4 v_color;
varying mediump float v_fogFactor;
// 总计：11个vec3/vec4 = 44个浮点数 = 176字节/顶点

// ✅ Good: 精简Varying
varying mediump vec3 v_normal;
varying mediump vec4 v_tangent;     // w存储手性
varying mediump vec2 v_texCoord;
varying lowp vec4 v_color;
// 总计：4个变量 = 13个浮点数 = 52字节/顶点

// 在Fragment Shader中计算bitangent
// Fragment Shader
vec3 bitangent = cross(v_normal, v_tangent.xyz) * v_tangent.w;
```

---

## 3. 片元Shader优化

片元着色器是移动GPU性能优化的核心，每帧可能执行数百万到数千万次。

### 3.1 精度优化

**精度类型选择规则**

| 数据类型 | 推荐精度 | 原因 |
|---------|---------|------|
| 颜色值 | `lowp` | 显示器8位，足够 |
| 纹理坐标 | `mediump` | 通常足够 |
| 归一化向量 | `mediump` | 方向精度OK |
| 世界坐标 | `highp` | 大范围需要 |
| 深度值 | `highp` | 精度敏感 |
| 临时计算 | `mediump` | 默认选择 |

**精度优化代码示例**

```glsl
// ❌ Bad: 全部使用highp
precision highp float;

varying highp vec2 v_texCoord;
varying highp vec3 v_normal;
varying highp vec4 v_color;

uniform highp sampler2D u_texture;
uniform highp vec3 u_lightDir;
uniform highp vec3 u_lightColor;

void main() {
    highp vec4 texColor = texture2D(u_texture, v_texCoord);
    highp vec3 normal = normalize(v_normal);
    highp float diffuse = max(dot(normal, u_lightDir), 0.0);
    highp vec3 lit = texColor.rgb * u_lightColor * diffuse;
    
    gl_FragColor = vec4(lit, texColor.a) * v_color;
}

// Mali分析：
// - cycles/pixel: 1.8
// - 16-bit arithmetic: 12%
// - 寄存器使用: 14
```

```glsl
// ✅ Good: 按需选择精度
precision mediump float;

varying mediump vec2 v_texCoord;      // 纹理坐标
varying mediump vec3 v_normal;        // 法线
varying lowp vec4 v_color;            // 颜色

uniform sampler2D u_texture;
uniform mediump vec3 u_lightDir;      // 方向
uniform lowp vec3 u_lightColor;       // 颜色

void main() {
    lowp vec4 texColor = texture2D(u_texture, v_texCoord);
    mediump vec3 normal = normalize(v_normal);
    mediump float diffuse = max(dot(normal, u_lightDir), 0.0);
    
    // 颜色计算用lowp
    lowp vec3 lit = texColor.rgb * u_lightColor * diffuse;
    
    gl_FragColor = vec4(lit, texColor.a) * v_color;
}

// Mali分析：
// - cycles/pixel: 0.7
// - 16-bit arithmetic: 89%
// - 寄存器使用: 7
// 性能提升：157%
```

### 3.2 算术计算优化

**运算成本参考**

| 运算 | 近似周期 | 优化建议 |
|------|---------|---------|
| +, -, * | 1 | 基准 |
| / | 4-8 | 用乘法倒数替代 |
| sqrt() | 4-6 | 使用inversesqrt |
| pow() | 16-32 | 展开或查表 |
| sin(), cos() | 8-16 | 查表或近似 |
| exp(), log() | 8-16 | 避免或查表 |
| normalize() | 4 | 使用内置函数 |
| reflect() | 6 | 考虑替代方案 |

**除法优化**

```glsl
// ❌ Bad: 频繁除法
void main() {
    float a = value / 2.0;           // 除法
    float b = value / 3.0;           // 除法
    float c = value / (1.0 + x);     // 除法
    float d = length(v) / maxLen;    // 除法
}

// ✅ Good: 乘以倒数
void main() {
    float a = value * 0.5;           // 乘法
    float b = value * 0.333333;      // 乘法
    float invDenom = 1.0 / (1.0 + x);// 仅1次除法
    float c = value * invDenom;      // 复用倒数
    float d = length(v) * u_invMaxLen; // CPU预计算倒数
}
```

**平方根优化**

```glsl
// ❌ Bad: 手动归一化
vec3 dir = targetPos - currentPos;
float len = sqrt(dot(dir, dir));    // sqrt
dir = dir / len;                     // 除法

// ✅ Good: 使用内置函数或inversesqrt
// 方案1：使用normalize
vec3 dir = normalize(targetPos - currentPos);

// 方案2：需要同时获得长度和方向
vec3 diff = targetPos - currentPos;
float invLen = inversesqrt(dot(diff, diff));
vec3 dir = diff * invLen;           // 归一化方向
float len = 1.0 / invLen;           // 长度（如果需要）

// ✅ 距离比较优化
// ❌ Bad: 计算距离再比较
float dist = length(pos - target);
if (dist < 100.0) { ... }

// ✅ Good: 比较平方距离
float distSq = dot(pos - target, pos - target);
if (distSq < 10000.0) { ... }  // 100² = 10000
```

**指数函数优化**

```glsl
// ❌ Bad: 使用pow（昂贵）
float specular = pow(NdotH, 32.0);     // 16-32周期

// ✅ Good: 手动展开或近似
// 对于2的幂次，连续乘法
float specular = NdotH;
specular *= specular;  // ^2
specular *= specular;  // ^4
specular *= specular;  // ^8
specular *= specular;  // ^16
specular *= specular;  // ^32
// 仅5次乘法 vs pow的16-32周期

// 或使用exp2/log2组合（比pow快）
float specular = exp2(32.0 * log2(max(NdotH, 0.0001)));
```

**三角函数优化**

```glsl
// ❌ Bad: 直接使用sin/cos
float wave = sin(u_time * 3.14159);
float wave2 = cos(u_time * 3.14159);

// ✅ Good: 使用查找表
uniform sampler2D u_sinCosLUT;  // 预计算的sin/cos表
vec2 sc = texture2D(u_sinCosLUT, vec2(u_time, 0.5)).rg;
float wave = sc.x;   // sin
float wave2 = sc.y;  // cos

// ✅ Good: 泰勒级数近似（适用于小角度）
// sin(x) ≈ x - x³/6 + x⁵/120
float fastSin(float x) {
    float x2 = x * x;
    float x3 = x2 * x;
    float x5 = x3 * x2;
    return x - x3 * 0.166667 + x5 * 0.00833;
}
```

### 3.3 分支优化

移动GPU的SIMD架构对分支非常敏感。

**分支发散问题**

```
SIMD执行模型：

Warp/Wave内16-64个线程执行相同指令
├── 无分支：所有线程同步执行
│   执行时间 = N条指令
│
└── 有分支：分支发散
    if (condition) {
        A指令  // 部分线程执行
    } else {
        B指令  // 其他线程执行
    }
    执行时间 = A指令 + B指令（串行执行两个分支）
```

**分支消除技术**

```glsl
// ❌ Bad: 条件分支
void main() {
    vec4 color;
    if (v_isHighlighted > 0.5) {
        color = texture2D(u_highlightTex, v_texCoord);
    } else {
        color = texture2D(u_normalTex, v_texCoord);
    }
    gl_FragColor = color;
}

// ✅ Good: 使用mix替代
void main() {
    vec4 normalColor = texture2D(u_normalTex, v_texCoord);
    vec4 highlightColor = texture2D(u_highlightTex, v_texCoord);
    // mix(a, b, t) = a * (1-t) + b * t
    vec4 color = mix(normalColor, highlightColor, v_isHighlighted);
    gl_FragColor = color;
}

// ✅ Good: 使用step替代简单条件
// ❌ Bad
if (value > threshold) {
    result = 1.0;
} else {
    result = 0.0;
}

// ✅ Good
result = step(threshold, value);  // value >= threshold ? 1.0 : 0.0

// ✅ Good: 使用smoothstep实现软过渡
// 在edge0和edge1之间平滑插值
result = smoothstep(edge0, edge1, value);
```

**条件采样优化**

```glsl
// ❌ Bad: 条件纹理采样
void main() {
    vec4 color;
    if (u_useDetailMap) {
        vec4 detail = texture2D(u_detailMap, v_texCoord * 4.0);
        color = texture2D(u_diffuseMap, v_texCoord) * detail;
    } else {
        color = texture2D(u_diffuseMap, v_texCoord);
    }
    gl_FragColor = color;
}

// ✅ Good: 使用Shader变体
// 编译时条件（无运行时开销）
#ifdef USE_DETAIL_MAP
    vec4 detail = texture2D(u_detailMap, v_texCoord * 4.0);
    vec4 color = texture2D(u_diffuseMap, v_texCoord) * detail;
#else
    vec4 color = texture2D(u_diffuseMap, v_texCoord);
#endif
gl_FragColor = color;

// C++端管理Shader变体
class ShaderVariantManager {
public:
    GLuint GetShader(bool useDetailMap, bool useShadow) {
        int key = (useDetailMap ? 1 : 0) | (useShadow ? 2 : 0);
        
        if (variants.find(key) == variants.end()) {
            std::string defines;
            if (useDetailMap) defines += "#define USE_DETAIL_MAP\n";
            if (useShadow) defines += "#define USE_SHADOW\n";
            
            variants[key] = CompileShader(baseSource, defines);
        }
        
        return variants[key];
    }
    
private:
    std::map<int, GLuint> variants;
    std::string baseSource;
};
```

**循环优化**

```glsl
// ❌ Bad: 动态循环（GPU难以优化）
uniform int u_lightCount;  // 运行时确定

void main() {
    vec3 totalLight = vec3(0.0);
    for (int i = 0; i < u_lightCount; ++i) {
        totalLight += calculateLight(i);
    }
    gl_FragColor = vec4(totalLight, 1.0);
}

// ✅ Good: 固定循环或展开
// 方案1：固定最大数量
#define MAX_LIGHTS 4

void main() {
    vec3 totalLight = vec3(0.0);
    for (int i = 0; i < MAX_LIGHTS; ++i) {
        // 使用uniform控制实际使用的灯光
        totalLight += u_lightEnabled[i] * calculateLight(i);
    }
    gl_FragColor = vec4(totalLight, 1.0);
}

// 方案2：完全展开
void main() {
    vec3 totalLight = vec3(0.0);
    totalLight += u_light0Enabled * calculateLight(0);
    totalLight += u_light1Enabled * calculateLight(1);
    totalLight += u_light2Enabled * calculateLight(2);
    totalLight += u_light3Enabled * calculateLight(3);
    gl_FragColor = vec4(totalLight, 1.0);
}

// 方案3：Shader变体
#if LIGHT_COUNT == 1
    totalLight = calculateLight(0);
#elif LIGHT_COUNT == 2
    totalLight = calculateLight(0) + calculateLight(1);
#elif LIGHT_COUNT == 3
    // ...
#endif
```

### 3.4 纹理采样优化

**减少采样次数**

```glsl
// ❌ Bad: 9次采样的模糊
void main() {
    vec4 color = vec4(0.0);
    for (int y = -1; y <= 1; ++y) {
        for (int x = -1; x <= 1; ++x) {
            vec2 offset = vec2(float(x), float(y)) * u_texelSize;
            color += texture2D(u_texture, v_texCoord + offset);
        }
    }
    gl_FragColor = color / 9.0;
}

// ✅ Good: 分离卷积（3+3=6次采样）
// Pass 1: 水平模糊
void main() {
    vec4 color = texture2D(u_texture, v_texCoord) * 0.4;
    color += texture2D(u_texture, v_texCoord + vec2(-u_texelSize.x, 0.0)) * 0.3;
    color += texture2D(u_texture, v_texCoord + vec2( u_texelSize.x, 0.0)) * 0.3;
    gl_FragColor = color;
}

// Pass 2: 垂直模糊
void main() {
    vec4 color = texture2D(u_texture, v_texCoord) * 0.4;
    color += texture2D(u_texture, v_texCoord + vec2(0.0, -u_texelSize.y)) * 0.3;
    color += texture2D(u_texture, v_texCoord + vec2(0.0,  u_texelSize.y)) * 0.3;
    gl_FragColor = color;
}
```

**利用硬件双线性插值**

```glsl
// ✅ 利用GL_LINEAR采样实现4采样模糊（只需1次采样）
// 当采样位置在4个texel中心之间时，硬件自动混合4个值

void main() {
    // 偏移0.5 texel，让硬件双线性采样混合4个texel
    vec2 offset = u_texelSize * 0.5;
    
    vec4 tl = texture2D(u_texture, v_texCoord + vec2(-offset.x, -offset.y));
    vec4 tr = texture2D(u_texture, v_texCoord + vec2( offset.x, -offset.y));
    vec4 bl = texture2D(u_texture, v_texCoord + vec2(-offset.x,  offset.y));
    vec4 br = texture2D(u_texture, v_texCoord + vec2( offset.x,  offset.y));
    
    // 16个texel的平均值，仅4次采样
    gl_FragColor = (tl + tr + bl + br) * 0.25;
}
```

**避免Dependent Texture Read**

```glsl
// ❌ Bad: 依赖纹理读取
void main() {
    // 第1次采样
    vec2 distortion = texture2D(u_distortionMap, v_texCoord).rg;
    
    // 第2次采样依赖第1次结果（GPU必须等待）
    vec2 distortedUV = v_texCoord + distortion * 0.1;
    vec4 color = texture2D(u_colorMap, distortedUV);
    
    gl_FragColor = color;
}

// ✅ Good: 在顶点着色器预计算或使用固定偏移
// 方案1：顶点着色器预计算扭曲UV
// Vertex Shader
varying mediump vec2 v_texCoord;
varying mediump vec2 v_distortedUV;

void main() {
    // ... 
    vec2 distortion = texture2D(u_distortionMap, a_texCoord).rg;
    v_distortedUV = a_texCoord + distortion * 0.1;
}

// Fragment Shader
void main() {
    // 两次采样独立，可并行
    vec4 color = texture2D(u_colorMap, v_distortedUV);
    gl_FragColor = color;
}

// 方案2：使用固定偏移模式
void main() {
    // 固定偏移，无依赖
    vec2 uv = v_texCoord;
    vec2 offset1 = vec2(0.01, 0.0);
    vec2 offset2 = vec2(0.0, 0.01);
    
    vec4 c0 = texture2D(u_texture, uv);
    vec4 c1 = texture2D(u_texture, uv + offset1);
    vec4 c2 = texture2D(u_texture, uv + offset2);
    
    gl_FragColor = (c0 + c1 + c2) / 3.0;
}
```

**纹理压缩格式使用**

```cpp
// 压缩纹理格式选择
struct TextureFormatSelector {
    GLenum SelectFormat(Platform platform, TextureType type, 
                        bool hasAlpha, Quality quality) {
        if (platform == Platform::Android) {
            if (hasAlpha) {
                if (quality == Quality::High) {
                    return GL_COMPRESSED_RGBA_ASTC_4x4_KHR;  // 最高质量
                } else {
                    return GL_COMPRESSED_RGBA8_ETC2;          // 通用
                }
            } else {
                return GL_COMPRESSED_RGB8_ETC2;               // 无Alpha
            }
        } else if (platform == Platform::iOS) {
            if (hasAlpha) {
                return GL_COMPRESSED_RGBA_ASTC_4x4_KHR;
            } else {
                return GL_COMPRESSED_RGB_PVRTC_4BPPV1_IMG;
            }
        }
        return GL_RGBA8;  // 后备
    }
};

// 压缩格式带宽对比
/**
 * 1920x1080纹理单帧带宽：
 * 
 * | 格式 | 每像素位数 | 大小 | 带宽(@60fps) |
 * |------|-----------|------|--------------|
 * | RGBA8 | 32 | 8.3 MB | 498 MB/s |
 * | RGB8 | 24 | 6.2 MB | 372 MB/s |
 * | ETC2 RGBA | 8 | 2.1 MB | 126 MB/s |
 * | ETC2 RGB | 4 | 1.0 MB | 60 MB/s |
 * | ASTC 4x4 | 8 | 2.1 MB | 126 MB/s |
 * | ASTC 8x8 | 2 | 0.5 MB | 30 MB/s |
 */
```

### 3.5 向量化与SIMD

**向量操作优化**

```glsl
// ❌ Bad: 标量操作
float r = color.r * 0.299;
float g = color.g * 0.587;
float b = color.b * 0.114;
float gray = r + g + b;

// ✅ Good: 向量操作
const vec3 grayWeight = vec3(0.299, 0.587, 0.114);
float gray = dot(color.rgb, grayWeight);  // 单条指令

// ❌ Bad: 分开计算
vec3 a = vec3(1.0, 2.0, 3.0);
vec3 b = vec3(4.0, 5.0, 6.0);
float x = a.x * b.x;
float y = a.y * b.y;
float z = a.z * b.z;
vec3 result = vec3(x, y, z);

// ✅ Good: 向量乘法
vec3 result = a * b;  // 单条指令
```

**Swizzle零成本**

```glsl
// Swizzle操作是免费的（硬件支持）
vec4 color = texture2D(u_texture, uv);

// 以下操作都是0周期：
vec3 rgb = color.rgb;
vec3 bgr = color.bgr;
float alpha = color.a;
vec4 aaaa = color.aaaa;  // 广播
vec2 rg = color.rg;

// ❌ 不要这样写
vec3 rgb = vec3(color.r, color.g, color.b);  // 有开销

// ✅ 使用swizzle
vec3 rgb = color.rgb;  // 零成本
```

**MAD指令融合**

```glsl
// GPU会将乘加运算融合为单条MAD指令
// result = a * b + c  →  MAD(a, b, c)

// ✅ 这些会自动融合：
vec3 result = v1 * v2 + v3;        // 1条MAD
vec3 result = v1 + v2 * v3;        // 1条MAD
vec4 color = texColor * factor + bias;  // 1条MAD

// ❌ 分开写可能无法融合：
vec3 temp = v1 * v2;   // MUL
vec3 result = temp + v3; // ADD
// 可能是2条指令
```

---

## 4. 渲染管线优化

### 4.1 Early-Z优化

Early-Z允许在片元着色器执行前进行深度测试，丢弃不可见片元。

**启用Early-Z的条件**

- 深度测试已启用
- 深度写入已启用
- 片元着色器不写入`gl_FragDepth`
- 片元着色器不使用`discard`（部分GPU）
- 无alpha测试（部分GPU）

**Early-Z友好写法**

```glsl
// ❌ Bad: 使用discard破坏Early-Z
void main() {
    vec4 color = texture2D(u_texture, v_texCoord);
    
    // discard可能禁用Early-Z
    if (color.a < 0.5) {
        discard;
    }
    
    gl_FragColor = color;
}

// ✅ Good: 使用alpha test替代discard
// 依赖渲染顺序，先渲染不透明物体

// 对于需要alpha test的情况，分两个Pass：
// Pass 1: 仅深度写入（alpha test）
void mainDepthPass() {
    float alpha = texture2D(u_texture, v_texCoord).a;
    if (alpha < 0.5) discard;
    // 不写颜色，仅深度
}

// Pass 2: 颜色渲染（深度测试通过的才执行）
void mainColorPass() {
    gl_FragColor = texture2D(u_texture, v_texCoord);
}
```

**渲染顺序优化**

```cpp
// 前后排序优化Early-Z效率
void RenderScene() {
    // 1. 渲染不透明物体（前到后）
    SortFrontToBack(opaqueObjects);
    
    glEnable(GL_DEPTH_TEST);
    glDepthMask(GL_TRUE);
    glDisable(GL_BLEND);
    
    for (const auto& obj : opaqueObjects) {
        RenderObject(obj);
    }
    
    // 2. 渲染透明物体（后到前）
    SortBackToFront(transparentObjects);
    
    glDepthMask(GL_FALSE);  // 不写深度
    glEnable(GL_BLEND);
    
    for (const auto& obj : transparentObjects) {
        RenderObject(obj);
    }
}

// 排序函数
void SortFrontToBack(std::vector<RenderObject>& objects) {
    Vec3 cameraPos = GetCameraPosition();
    
    std::sort(objects.begin(), objects.end(),
              [&cameraPos](const RenderObject& a, const RenderObject& b) {
                  float distA = LengthSquared(a.position - cameraPos);
                  float distB = LengthSquared(b.position - cameraPos);
                  return distA < distB;  // 近的先渲染
              });
}
```

### 4.2 模板测试优化

模板测试可以用于实现复杂效果，但需要谨慎使用。

```cpp
// 模板遮罩优化示例
class StencilMask {
public:
    // 绘制遮罩区域
    void RenderMask(const Mesh& maskMesh) {
        // 配置模板写入
        glEnable(GL_STENCIL_TEST);
        glStencilFunc(GL_ALWAYS, 1, 0xFF);
        glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE);
        glStencilMask(0xFF);
        
        // 禁用颜色和深度写入
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE);
        glDepthMask(GL_FALSE);
        
        // 绘制遮罩（只写模板）
        DrawMesh(maskMesh, maskShader);
        
        // 恢复状态
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE);
        glDepthMask(GL_TRUE);
    }
    
    // 使用遮罩渲染
    void RenderWithMask() {
        // 仅在模板值为1的区域渲染
        glStencilFunc(GL_EQUAL, 1, 0xFF);
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP);
        glStencilMask(0x00);  // 不再修改模板
        
        // 渲染场景
        RenderScene();
        
        glDisable(GL_STENCIL_TEST);
    }
};
```

### 4.3 混合优化

混合操作消耗带宽和ALU。

**混合模式性能**

| 混合模式 | 性能影响 | 说明 |
|---------|---------|------|
| 无混合 | 最快 | 直接写入 |
| Alpha混合 | 中等 | 需读取帧缓冲 |
| 加法混合 | 中等 | 需读取帧缓冲 |
| 乘法混合 | 较慢 | 更复杂的计算 |
| 预乘Alpha | 较快 | 简化混合公式 |

**预乘Alpha优化**

```glsl
// 标准Alpha混合公式：
// result = src.rgb * src.a + dst.rgb * (1 - src.a)

// 预乘Alpha：存储时已经乘以alpha
// src.rgb_premul = src.rgb * src.a
// 混合公式简化为：
// result = src.rgb_premul + dst.rgb * (1 - src.a)

// C++端：使用预乘alpha纹理
void LoadPremultipliedTexture(const char* path) {
    // 加载并预乘
    Image img = LoadImage(path);
    for (int i = 0; i < img.width * img.height; ++i) {
        float alpha = img.pixels[i * 4 + 3] / 255.0f;
        img.pixels[i * 4 + 0] *= alpha;
        img.pixels[i * 4 + 1] *= alpha;
        img.pixels[i * 4 + 2] *= alpha;
    }
    
    // 上传纹理
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 
                 img.width, img.height, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, img.pixels);
}

// 渲染时使用预乘混合
void RenderWithPremultipliedAlpha() {
    glEnable(GL_BLEND);
    // 预乘alpha混合模式
    glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA);
    
    // Shader中不需要额外乘alpha
    // gl_FragColor = texColor;  // 已经是预乘的
}
```

**减少混合区域**

```cpp
// 透明物体使用紧凑包围盒
void RenderTransparentSprite(const Sprite& sprite) {
    // 计算实际不透明区域（避免绘制完全透明部分）
    Rect visibleRect = CalculateTrimmedRect(sprite);
    
    // 仅绘制可见区域
    DrawRect(visibleRect, sprite.texture, sprite.uvRect);
}
```

### 4.4 多采样抗锯齿优化

MSAA在移动端需要谨慎使用。

```cpp
// MSAA配置
class MSAARenderer {
public:
    void Initialize(int width, int height, int samples) {
        // 创建MSAA帧缓冲
        glGenFramebuffers(1, &msaaFBO);
        glBindFramebuffer(GL_FRAMEBUFFER, msaaFBO);
        
        // 创建MSAA渲染缓冲
        glGenRenderbuffers(1, &msaaColorRBO);
        glBindRenderbuffer(GL_RENDERBUFFER, msaaColorRBO);
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, samples,
                                         GL_RGBA8, width, height);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                                  GL_RENDERBUFFER, msaaColorRBO);
        
        glGenRenderbuffers(1, &msaaDepthRBO);
        glBindRenderbuffer(GL_RENDERBUFFER, msaaDepthRBO);
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, samples,
                                         GL_DEPTH24_STENCIL8, width, height);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT,
                                  GL_RENDERBUFFER, msaaDepthRBO);
        
        // 创建解析目标
        glGenFramebuffers(1, &resolveFBO);
        // ...
    }
    
    void BeginFrame() {
        glBindFramebuffer(GL_FRAMEBUFFER, msaaFBO);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    }
    
    void EndFrame() {
        // 解析MSAA到普通纹理
        glBindFramebuffer(GL_READ_FRAMEBUFFER, msaaFBO);
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, resolveFBO);
        glBlitFramebuffer(0, 0, width, height,
                          0, 0, width, height,
                          GL_COLOR_BUFFER_BIT, GL_NEAREST);
    }
    
private:
    GLuint msaaFBO, resolveFBO;
    GLuint msaaColorRBO, msaaDepthRBO;
    int width, height;
};

// MSAA性能建议
/**
 * | 采样数 | 内存开销 | 带宽开销 | 建议使用场景 |
 * |--------|---------|---------|--------------|
 * | 2x | 2x | ~1.5x | 移动端可接受 |
 * | 4x | 4x | ~2x | 旗舰设备 |
 * | 8x | 8x | ~3x | 不推荐移动端 |
 * 
 * 替代方案：
 * - FXAA：后处理AA，性能较好
 * - TAA：时间抗锯齿，需要历史帧
 * - 超采样后下采样：某些场景效果好
 */
```

**后处理FXAA**

```glsl
// 简化FXAA实现
precision mediump float;

varying vec2 v_texCoord;
uniform sampler2D u_texture;
uniform vec2 u_texelSize;

void main() {
    // 采样相邻像素
    vec3 rgbNW = texture2D(u_texture, v_texCoord + vec2(-1.0, -1.0) * u_texelSize).rgb;
    vec3 rgbNE = texture2D(u_texture, v_texCoord + vec2( 1.0, -1.0) * u_texelSize).rgb;
    vec3 rgbSW = texture2D(u_texture, v_texCoord + vec2(-1.0,  1.0) * u_texelSize).rgb;
    vec3 rgbSE = texture2D(u_texture, v_texCoord + vec2( 1.0,  1.0) * u_texelSize).rgb;
    vec3 rgbM  = texture2D(u_texture, v_texCoord).rgb;
    
    // 计算亮度
    vec3 luma = vec3(0.299, 0.587, 0.114);
    float lumaNW = dot(rgbNW, luma);
    float lumaNE = dot(rgbNE, luma);
    float lumaSW = dot(rgbSW, luma);
    float lumaSE = dot(rgbSE, luma);
    float lumaM  = dot(rgbM, luma);
    
    // 计算边缘方向
    float lumaMin = min(lumaM, min(min(lumaNW, lumaNE), min(lumaSW, lumaSE)));
    float lumaMax = max(lumaM, max(max(lumaNW, lumaNE), max(lumaSW, lumaSE)));
    
    vec2 dir;
    dir.x = -((lumaNW + lumaNE) - (lumaSW + lumaSE));
    dir.y =  ((lumaNW + lumaSW) - (lumaNE + lumaSE));
    
    float dirReduce = max((lumaNW + lumaNE + lumaSW + lumaSE) * 0.25 * 0.25, 0.0001);
    float rcpDirMin = 1.0 / (min(abs(dir.x), abs(dir.y)) + dirReduce);
    
    dir = min(vec2(8.0), max(vec2(-8.0), dir * rcpDirMin)) * u_texelSize;
    
    vec3 rgbA = 0.5 * (
        texture2D(u_texture, v_texCoord + dir * (1.0/3.0 - 0.5)).rgb +
        texture2D(u_texture, v_texCoord + dir * (2.0/3.0 - 0.5)).rgb);
    
    vec3 rgbB = rgbA * 0.5 + 0.25 * (
        texture2D(u_texture, v_texCoord + dir * -0.5).rgb +
        texture2D(u_texture, v_texCoord + dir *  0.5).rgb);
    
    float lumaB = dot(rgbB, luma);
    
    if (lumaB < lumaMin || lumaB > lumaMax) {
        gl_FragColor = vec4(rgbA, 1.0);
    } else {
        gl_FragColor = vec4(rgbB, 1.0);
    }
}
```

---

## 5. 移动GPU架构适配

### 5.1 TBDR友好写法

**避免强制刷新Tile**

```glsl
// ❌ Bad: 在片元着色器中读取帧缓冲
// 某些效果需要读取当前像素值（如软粒子）
uniform sampler2D u_depthTexture;  // 需要先渲染到纹理

void main() {
    // 读取深度可能导致Tile刷新
    float sceneDepth = texture2D(u_depthTexture, v_screenUV).r;
    // ...
}

// ✅ Good: 使用frameBuffer Fetch扩展（如果支持）
#extension GL_EXT_shader_framebuffer_fetch : enable

void main() {
    // 直接访问Tile内存，无需刷新
    vec4 lastColor = gl_LastFragData[0];
    // ...
}
```

**充分利用Tile内存**

```cpp
// 确保Tile内数据不被不必要地写回
void ConfigureFramebuffer() {
    // 使用glInvalidateFramebuffer告知驱动丢弃不需要的附件
    GLenum attachments[] = { GL_DEPTH_ATTACHMENT, GL_STENCIL_ATTACHMENT };
    glInvalidateFramebuffer(GL_FRAMEBUFFER, 2, attachments);
    
    // 或在渲染开始时清除（让驱动知道旧数据不重要）
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
}
```

### 5.2 各GPU架构特点

**Mali GPU (ARM)**

```glsl
// Mali优化要点：
// 1. 使用mediump作为默认精度
precision mediump float;

// 2. 避免在Fragment中使用highp除非必要
// 3. 使用Mali Offline Compiler验证
// 4. 关注"16-bit arithmetic"指标

// Mali特有优化：Forward Pixel Kill
// - 隐藏不可见片元，无需Early-Z
// - 但discard仍会影响效率
```

**Adreno GPU (Qualcomm)**

```glsl
// Adreno优化要点：
// 1. Adreno支持FlexRender（混合IMR/TBR）
// 2. 对分支相对宽容
// 3. 寄存器文件较大

// Adreno特有功能：Binning Pass
// - 先进行低精度几何处理确定可见性
// - 再进行完整渲染
```

**PowerVR GPU (Imagination)**

```glsl
// PowerVR优化要点：
// 1. 硬件HSR（Hidden Surface Removal）
// 2. 延迟着色器编译
// 3. 对Overdraw非常敏感

// 最佳实践：不排序不透明物体（硬件处理）
// 但透明物体仍需排序
```

**Apple GPU (A系列)**

```swift
// Apple GPU优化（Metal为主，但OpenGL ES仍适用）：
// 1. Tile Memory访问优化
// 2. SIMD Group大小为32
// 3. 支持Tile Shading

// 使用Metal可获得更好的优化空间
```

---

## 6. 性能分析与调优

### 6.1 性能分析工具

**Mali Offline Compiler使用**

```bash
# 分析Fragment Shader
malioc --core Mali-G78 --fragment shader.frag

# 输出示例：
# Fragment shader for Mali-G78:
#   Work registers: 8
#   Uniform registers: 4
#   Stack spilling: false
#   16-bit arithmetic: 87%
#   Arithmetic: 65%
#   Load/Store: 20%
#   Texture: 15%
#   Performance: 0.8 cycles/pixel
```

**性能指标解读**

| 指标 | 优秀 | 良好 | 需优化 |
|------|------|------|--------|
| cycles/pixel | <0.5 | 0.5-1.0 | >1.0 |
| 16-bit arithmetic | >80% | 50-80% | <50% |
| Work registers | <8 | 8-12 | >12 |
| Stack spilling | false | - | true |

### 6.2 GPU时间测量

```cpp
// 使用Timer Query测量GPU时间
class GPUTimer {
public:
    void Initialize() {
        if (HasExtension("GL_EXT_disjoint_timer_query")) {
            glGenQueries = GetExtProc<PFNGLGENQUERIESEXTPROC>("glGenQueriesEXT");
            glBeginQuery = GetExtProc<PFNGLBEGINQUERYEXTPROC>("glBeginQueryEXT");
            glEndQuery = GetExtProc<PFNGLENDQUERYEXTPROC>("glEndQueryEXT");
            glGetQueryObjectui64v = GetExtProc<PFNGLGETQUERYOBJECTUI64VEXTPROC>(
                "glGetQueryObjectui64vEXT");
            
            glGenQueries(2, queries);
            supported = true;
        }
    }
    
    void BeginMeasure() {
        if (!supported) return;
        currentQuery = (currentQuery + 1) % 2;
        glBeginQuery(GL_TIME_ELAPSED_EXT, queries[currentQuery]);
    }
    
    void EndMeasure() {
        if (!supported) return;
        glEndQuery(GL_TIME_ELAPSED_EXT);
    }
    
    float GetLastTimeMs() {
        if (!supported) return 0.0f;
        
        GLuint64 timeNs = 0;
        glGetQueryObjectui64v(queries[(currentQuery + 1) % 2],
                              GL_QUERY_RESULT, &timeNs);
        return timeNs / 1000000.0f;
    }
    
private:
    GLuint queries[2];
    int currentQuery = 0;
    bool supported = false;
    
    PFNGLGENQUERIESEXTPROC glGenQueries;
    PFNGLBEGINQUERYEXTPROC glBeginQuery;
    PFNGLENDQUERYEXTPROC glEndQuery;
    PFNGLGETQUERYOBJECTUI64VEXTPROC glGetQueryObjectui64v;
};

// 使用示例
GPUTimer timer;
timer.Initialize();

void RenderFrame() {
    timer.BeginMeasure();
    
    // 渲染代码...
    RenderScene();
    
    timer.EndMeasure();
    
    // 获取上一帧的GPU时间
    float gpuTime = timer.GetLastTimeMs();
    LOG("GPU Time: %.2f ms", gpuTime);
}
```

### 6.3 着色器变体管理

```cpp
// Shader变体系统
class ShaderVariantSystem {
public:
    struct VariantKey {
        uint32_t features;  // 位标志
        
        bool operator==(const VariantKey& other) const {
            return features == other.features;
        }
    };
    
    enum Feature : uint32_t {
        FEATURE_NONE = 0,
        FEATURE_NORMAL_MAP = 1 << 0,
        FEATURE_SHADOW = 1 << 1,
        FEATURE_FOG = 1 << 2,
        FEATURE_SKINNING = 1 << 3,
        FEATURE_INSTANCING = 1 << 4,
    };
    
    GLuint GetShader(uint32_t features) {
        VariantKey key = { features };
        
        auto it = shaderCache.find(key.features);
        if (it != shaderCache.end()) {
            return it->second;
        }
        
        // 编译新变体
        std::string defines = GenerateDefines(features);
        GLuint shader = CompileShader(vertexSource, fragmentSource, defines);
        shaderCache[key.features] = shader;
        
        return shader;
    }
    
    // 预编译常用变体
    void WarmupShaders() {
        std::vector<uint32_t> commonVariants = {
            FEATURE_NONE,
            FEATURE_NORMAL_MAP,
            FEATURE_SHADOW,
            FEATURE_NORMAL_MAP | FEATURE_SHADOW,
            FEATURE_FOG,
            // ...
        };
        
        for (auto features : commonVariants) {
            GetShader(features);
        }
    }
    
private:
    std::string GenerateDefines(uint32_t features) {
        std::string defines;
        if (features & FEATURE_NORMAL_MAP) defines += "#define USE_NORMAL_MAP\n";
        if (features & FEATURE_SHADOW) defines += "#define USE_SHADOW\n";
        if (features & FEATURE_FOG) defines += "#define USE_FOG\n";
        if (features & FEATURE_SKINNING) defines += "#define USE_SKINNING\n";
        if (features & FEATURE_INSTANCING) defines += "#define USE_INSTANCING\n";
        return defines;
    }
    
    std::unordered_map<uint32_t, GLuint> shaderCache;
    std::string vertexSource;
    std::string fragmentSource;
};
```

---

## 7. 优化检查清单

### 7.1 精度优化检查

| 检查项 | 判定标准 | 验证方式 |
|--------|---------|---------|
| 默认精度 | Fragment使用mediump | 代码审查 |
| 颜色变量 | 使用lowp | 代码审查 |
| 纹理坐标 | 使用mediump | 代码审查 |
| FP16利用率 | >70% | Mali分析 |
| 精度转换 | 最小化隐式转换 | 代码审查 |

### 7.2 算术优化检查

| 检查项 | 判定标准 | 验证方式 |
|--------|---------|---------|
| 除法使用 | 用乘法倒数替代 | 代码审查 |
| pow使用 | 展开或使用exp2 | 代码审查 |
| 三角函数 | 查表或近似 | 代码审查 |
| normalize | 使用内置函数 | 代码审查 |
| 向量化 | 使用向量操作 | 代码审查 |

### 7.3 分支优化检查

| 检查项 | 判定标准 | 验证方式 |
|--------|---------|---------|
| 动态分支 | 用mix/step替代 | 代码审查 |
| 循环展开 | 固定迭代次数 | 代码审查 |
| Shader变体 | 编译时条件 | 架构审查 |
| discard使用 | 最小化或分Pass | 代码审查 |

### 7.4 纹理优化检查

| 检查项 | 判定标准 | 验证方式 |
|--------|---------|---------|
| 采样次数 | Fragment <8次 | 代码审查 |
| Dependent Read | 避免依赖采样 | 代码审查 |
| 纹理压缩 | 使用ASTC/ETC2 | 资源审查 |
| Mipmap | 3D纹理启用 | 资源审查 |
| 图集使用 | 2D资源使用图集 | 资源审查 |

### 7.5 管线优化检查

| 检查项 | 判定标准 | 验证方式 |
|--------|---------|---------|
| Early-Z | 不透明物体前到后 | 运行时验证 |
| Overdraw | <2.0平均值 | 可视化工具 |
| 混合优化 | 使用预乘Alpha | 代码审查 |
| FBO切换 | 最小化切换 | 代码审查 |
| 分辨率 | 合理的渲染分辨率 | 配置审查 |

---

## 总结

GPU端优化是移动端渲染性能提升的核心环节。通过精度选择、算术优化、分支消除、纹理采样优化和渲染管线优化，可以显著提升Shader执行效率。

**核心优化原则**：
1. **精度优先**：使用最低可接受精度
2. **预计算转移**：复杂计算移至CPU或顶点着色器
3. **减少采样**：纹理采样是最大开销之一
4. **消除分支**：利用mix/step替代条件判断
5. **利用硬件**：使用内置函数和硬件特性

**优化验证流程**：
1. 使用Mali Offline Compiler分析Shader
2. 使用GPU Timer测量实际执行时间
3. 在目标设备验证实际效果
4. 持续监控性能回归

详细的CPU/GPU数据同步优化技术请参考数据同步优化.md文档。
