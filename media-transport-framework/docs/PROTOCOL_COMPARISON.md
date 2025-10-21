# 音视频传输协议深度对比分析

## 概述

本文档提供主流音视频传输协议的深度对比分析，帮助开发者根据应用场景选择最优协议。

## 协议分类

### 1. 媒体传输协议
- **RTP** (Real-time Transport Protocol) - 实时传输协议
- **RTCP** (RTP Control Protocol) - 控制协议
- **SRTP** (Secure RTP) - 安全RTP

### 2. 信令控制协议
- **SIP** (Session Initiation Protocol) - 会话发起协议
- **SDP** (Session Description Protocol) - 会话描述协议
- **WebSocket** - 双向通信协议

### 3. 流媒体协议
- **RTMP** (Real-Time Messaging Protocol) - 实时消息协议
- **HLS** (HTTP Live Streaming) - HTTP直播流
- **DASH** (Dynamic Adaptive Streaming) - 动态自适应流
- **RTSP** (Real-Time Streaming Protocol) - 实时流协议
- **SRT** (Secure Reliable Transport) - 安全可靠传输

## 核心协议详解

### RTP/RTCP

#### 技术特性
| 特性 | 描述 |
|------|------|
| **传输层** | UDP |
| **可靠性** | 不保证可靠传输 |
| **延迟** | 极低 (<100ms) |
| **用途** | 实时音视频传输 |

#### RTP报文结构
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|V=2|P|X|  CC   |M|     PT      |       Sequence Number         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           Timestamp                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           SSRC (Synchronization Source Identifier)            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                          Payload Data                         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

#### 关键机制
- **时间戳**: 用于播放同步和抖动计算
- **序列号**: 检测丢包和乱序
- **SSRC**: 标识同步源
- **抖动缓冲**: 平滑网络抖动

#### 适用场景
✓ 实时音视频通话  
✓ WebRTC通信  
✓ IPTV直播  
✗ 公网环境无重传机制

---

### RTMP

#### 技术特性
| 特性 | 描述 |
|------|------|
| **传输层** | TCP |
| **可靠性** | 可靠传输 |
| **延迟** | 低 (1-3s) |
| **默认端口** | 1935 |

#### 握手流程
```
Client                          Server
  |                               |
  |------ C0 + C1 ------------->  |
  |<----- S0 + S1 + S2 ----------|
  |------ C2 ------------------>  |
  |                               |
  |------ Connect -------------->  |
  |<----- Connect Result --------|
  |------ CreateStream --------->  |
  |<----- Stream ID -------------|
  |------ Publish -------------->  |
  |<----- Publish Start ---------|
  |                               |
  |------ Media Data ----------->  |
```

#### 关键特性
- **分块传输**: 默认128字节，避免大消息阻塞
- **GOP缓存**: 缓存关键帧，新观众快速加入
- **AMF编码**: 元数据格式
- **CDN友好**: 行业标准推流协议

#### 适用场景
✓ 直播推流 (OBS → CDN)  
✓ 稳定网络环境  
✗ 移动网络切换易断流  
✗ 浏览器原生不支持

---

### SRT

#### 技术特性
| 特性 | 描述 |
|------|------|
| **传输层** | UDP (基于UDT) |
| **可靠性** | ARQ选择性重传 |
| **延迟** | 可配置 (120ms-8s) |
| **加密** | AES-128/256 |

#### 核心技术
1. **ARQ重传**: 选择性重传，类似TCP SACK
2. **FEC纠错**: 可选冗余编码
3. **拥塞控制**: 基于延迟的算法
4. **加密**: 内置端到端加密

#### 配置参数
| 参数 | 默认值 | 说明 |
|------|-------|------|
| latency | 120ms | 目标延迟 |
| maxbw | -1 | 最大带宽 |
| pbkeylen | 16 | 密钥长度 |
| tlpktdrop | true | 丢弃过时包 |

#### 适用场景
✓ 弱网环境传输  
✓ 远距离直播  
✓ 移动网络  
✓ 贡献级传输  
✗ 高并发分发

---

### WebRTC

#### 技术架构
```
应用层: 浏览器API (getUserMedia, RTCPeerConnection)
   ↓
信令层: 自定义 (WebSocket + SDP)
   ↓
媒体层: RTP/RTCP + SRTP
   ↓
传输层: ICE (STUN + TURN)
   ↓
网络层: UDP
```

#### 连接建立流程
```
用户A                信令服务器              用户B
  |                      |                     |
  |--- Offer (SDP) ----->|-------------------->|
  |                      |                     |
  |<------------------- Answer (SDP) ----------|
  |                      |                     |
  |--- ICE Candidate --->|-------------------->|
  |<---------------- ICE Candidate ------------|
  |                      |                     |
  |<========== P2P媒体连接建立 ===============>|
```

#### 核心技术
- **ICE**: NAT穿透
- **DTLS**: 密钥协商
- **SRTP**: 媒体加密
- **GCC**: Google拥塞控制
- **Simulcast**: 大小流

#### 适用场景
✓ 1v1视频通话  
✓ 多人会议 (SFU)  
✓ 屏幕共享  
✓ 云游戏  
✗ 大规模直播分发

---

## 协议对比矩阵

### 技术特性对比

| 协议 | 传输层 | 可靠性 | 延迟 | NAT穿透 | 加密 | 标准化 |
|------|-------|--------|------|---------|------|--------|
| RTP/RTCP | UDP | 不可靠 | <100ms | 需ICE | 需SRTP | IETF |
| RTMP | TCP | 可靠 | 1-3s | 困难 | 弱 | 事实标准 |
| HLS | HTTP/TCP | 可靠 | 10-30s | 优秀 | HTTPS | IETF |
| DASH | HTTP/TCP | 可靠 | 10-30s | 优秀 | HTTPS | ISO |
| RTSP | TCP | 可靠 | <500ms | 困难 | 部分 | IETF |
| SRT | UDP | 可靠 | 0.12-8s | 较好 | AES | 开源 |
| WebRTC | UDP | 选择性 | <300ms | 优秀 | 强制 | W3C |

### 应用场景适配

| 场景 | 首选协议 | 备选方案 | 不推荐 |
|------|---------|---------|--------|
| 超低延迟通话 | WebRTC | RTP/RTCP | HLS, RTMP |
| 直播推流 | RTMP/SRT | WebRTC | HLS |
| 大规模分发 | HLS/DASH | RTMP(CDN) | WebRTC |
| 监控视频 | RTSP | HLS | RTMP |
| 会议信令 | SIP/WebSocket | 自定义 | - |
| 远距离传输 | SRT | RTMP | WebRTC |
| 移动网络 | WebRTC/SRT | HLS | RTSP |
| 弱网环境 | SRT | WebRTC | RTMP |

### 性能指标对比

| 协议 | 首包延迟 | 端到端延迟 | 丢包容忍 | CPU占用 | 带宽效率 |
|------|---------|-----------|---------|---------|---------|
| RTP/RTCP | 低 | <200ms | 低 | 低 | 高 |
| RTMP | 中 | 1-3s | 高 | 中 | 中 |
| HLS | 高 | 10-30s | 高 | 低 | 低 |
| SRT | 中 | 0.5-3s | 极高 | 中 | 高 |
| WebRTC | 低 | <500ms | 中 | 高 | 高 |

## 协议选择决策树

```
开始
  │
  ├─ 实时通话场景?
  │   ├─ 是 → 公网NAT环境? → 是 → WebRTC
  │   │                    → 否 → RTP/RTCP
  │   └─ 否 ↓
  │
  ├─ 直播场景?
  │   ├─ 推流端? 
  │   │   ├─ 稳定网络 → RTMP
  │   │   └─ 弱网环境 → SRT
  │   └─ 拉流端?
  │       ├─ 延迟要求<3s → RTMP/SRT
  │       └─ 延迟可接受 → HLS/DASH
  │
  └─ 监控场景?
      ├─ 局域网 → RTSP
      └─ 公网 → HLS
```

## 优化建议

### RTP优化
- 启用NACK重传 (RTT<100ms时)
- FEC冗余率: 5-15%
- 抖动缓冲: 20-200ms动态调整

### RTMP优化
- TCP_NODELAY: 禁用Nagle算法
- 增大发送缓冲区
- GOP缓存: 1-2秒

### SRT优化
- 延迟设置: 网络RTT的3-4倍
- 密钥长度: 至少16字节
- 带宽限制: 根据实际网络容量

### WebRTC优化
- Simulcast: 多码率适配
- SVC: 可伸缩编码
- Jitter Buffer: 动态调整

## 参考资料

### 标准文档
- [RFC 3550] RTP: A Transport Protocol for Real-Time Applications
- [RFC 3261] SIP: Session Initiation Protocol
- [RFC 8216] HTTP Live Streaming (HLS)
- [W3C] WebRTC 1.0: Real-Time Communication Between Browsers

### 开源项目
- **FFmpeg**: 全协议支持
- **WebRTC Native**: Google官方实现
- **SRS**: 高性能流媒体服务器
- **libsrt**: SRT协议官方库

---

*本文档基于设计文档生成，持续更新中...*
