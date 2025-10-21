# 音视频传输协议框架

## 项目简介

这是一个**灵活、可扩展的音视频传输协议框架**，实现了协议层与业务层的解耦，支持多种主流传输协议的统一接口调用和动态切换。

### 核心特性

✨ **协议抽象** - 统一的媒体传输接口，屏蔽协议差异  
🔌 **插件化架构** - 支持协议热插拔，轻松扩展新协议  
🎯 **智能选择** - 基于场景和网络条件自动选择最优协议  
📊 **QoS优化** - 自适应码率控制、动态FEC、统一质量监控  
🔄 **无缝切换** - 支持协议动态切换，保持传输连续性  
🛡️ **安全可靠** - 支持多种加密方案，传输安全可控

### 支持的协议

| 协议 | 状态 | 适用场景 |
|------|------|---------|
| **RTP/RTCP** | ✅ 已实现 | 实时音视频通话、低延迟传输 |
| **RTMP** | ✅ 已实现 | 直播推流、CDN分发 |
| **SRT** | ✅ 已实现 | 弱网环境、远距离传输 |
| **WebRTC** | ✅ 已实现 | P2P通话、浏览器通信 |
| **RTSP** | 📋 待实现 | 监控摄像头、点播 |
| **HLS** | 📋 待实现 | 大规模直播分发 |

## 快速开始

### 安装依赖

```bash
# Python 3.8+
pip install -r requirements.txt
```

### 基础示例

#### 1. 使用RTP发送视频流

```python
from core.models import (
    MediaPacket, MediaType, CodecType,
    TransportConfig, ProtocolType, TransportMode
)
from core.protocol_factory import ProtocolFactory

# 1. 创建配置
config = TransportConfig(
    protocol_type=ProtocolType.RTP,
    transport_mode=TransportMode.UDP,
    server_address="127.0.0.1",
    server_port=5004,
    local_port=5000
)

# 2. 创建适配器
adapter = ProtocolFactory.create(ProtocolType.RTP, config)

# 3. 发送数据
packet = MediaPacket(
    payload=b'video_data',
    timestamp=1234567,
    media_type=MediaType.VIDEO,
    codec_type=CodecType.H264,
    is_key_frame=True
)

adapter.send_media_data(packet)

# 4. 获取统计
stats = adapter.get_transport_stats()
print(f"发送包数: {stats.packets_sent}")
print(f"丢包率: {stats.loss_rate:.2%}")
```

#### 2. 协议自动选择

```python
from core.protocol_selector import (
    ProtocolSelector, ScenarioType, NetworkCondition
)

# 定义网络条件
network = NetworkCondition(
    rtt=50.0,
    loss_rate=0.02,
    jitter=10.0,
    bandwidth=3000.0
)

# 自动选择协议
protocol = ProtocolSelector.select_protocol(
    ScenarioType.REALTIME_CALL,
    network
)

print(f"推荐协议: {protocol.value}")
```

#### 3. QoS自适应优化

```python
from core.models import QoSConfig
from qos import QoSManager

# 创建QoS配置
qos_config = QoSConfig(
    enable_adaptive_bitrate=True,
    target_bitrate=2000,
    min_bitrate=500,
    max_bitrate=4000,
    enable_dynamic_fec=True
)

# 创建QoS管理器
qos_manager = QoSManager(adapter, qos_config)

# 设置回调
def on_bitrate_change(bitrate):
    print(f"码率调整为: {bitrate} kbps")

qos_manager.set_bitrate_change_callback(on_bitrate_change)

# 启动QoS监控
qos_manager.start()
```

### 运行示例

```bash
# 示例1: RTP视频流传输
python examples/example_rtp_streaming.py

# 示例2: 协议选择与QoS优化
python examples/example_protocol_selection.py

# 示例3: 所有协议演示
python examples/example_all_protocols.py
```

## 架构设计

### 分层架构

```
┌─────────────────────────────────────┐
│         应用层 (Application)         │
│    业务逻辑、UI交互、场景控制        │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│     协议抽象层 (Protocol Abstract)   │
│  IMediaTransport | ISignaling | ICodec│
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│     协议适配层 (Protocol Adapters)   │
│  RTP | RTMP | SRT | WebRTC | RTSP   │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│       传输层 (Transport Layer)       │
│      UDP | TCP | QUIC | WebSocket   │
└─────────────────────────────────────┘
```

### 核心模块

#### 1. 接口层 (core/interfaces)
- **IMediaTransport**: 媒体传输接口
- **ISignaling**: 信令接口
- **ICodec**: 编解码器接口

#### 2. 模型层 (core/models)
- **MediaPacket**: 统一媒体数据包
- **TransportStats**: 传输统计信息
- **QoSMetrics**: QoS质量指标
- **TransportConfig**: 传输配置

#### 3. 协议工厂 (core/protocol_factory.py)
- 协议注册与管理
- 协议实例创建
- 插件化扩展

#### 4. 协议选择器 (core/protocol_selector.py)
- 基于场景的协议选择
- 网络质量评估
- 协议切换决策

#### 5. QoS管理器 (qos/qos_manager.py)
- 自适应码率控制
- 动态FEC调整
- 质量监控与报告

#### 6. 协议适配器 (adapters/)
- **RTP适配器**: RTP/RTCP协议实现
- **RTMP适配器**: RTMP协议实现
- 更多协议扩展中...

## 目录结构

```
media-transport-framework/
├── core/                       # 核心模块
│   ├── interfaces/             # 抽象接口
│   │   ├── media_transport.py  # 媒体传输接口
│   │   ├── signaling.py        # 信令接口
│   │   └── codec.py            # 编解码器接口
│   ├── models/                 # 数据模型
│   │   ├── media_packet.py     # 媒体数据包
│   │   ├── statistics.py       # 统计信息
│   │   └── config.py           # 配置参数
│   ├── protocol_factory.py     # 协议工厂
│   └── protocol_selector.py    # 协议选择器
├── adapters/                   # 协议适配器
│   ├── rtp/                    # RTP适配器
│   │   └── rtp_adapter.py
│   ├── rtmp/                   # RTMP适配器
│   │   └── rtmp_adapter.py
│   ├── srt/                    # SRT适配器 (计划中)
│   └── webrtc/                 # WebRTC适配器 (计划中)
├── qos/                        # QoS管理
│   └── qos_manager.py          # QoS管理器
├── examples/                   # 示例代码
│   ├── example_rtp_streaming.py
│   └── example_protocol_selection.py
└── docs/                       # 文档
    ├── PROTOCOL_COMPARISON.md  # 协议对比分析
    └── API_REFERENCE.md        # API参考手册
```

## 协议对比

详细的协议对比分析请参考: [协议对比文档](docs/PROTOCOL_COMPARISON.md)

### 场景推荐

| 应用场景 | 推荐协议 | 延迟 | 特点 |
|---------|---------|------|------|
| 实时音视频通话 | WebRTC | <300ms | P2P、NAT穿透 |
| 直播推流 | RTMP/SRT | 1-3s | 稳定、CDN友好 |
| 大规模直播分发 | HLS | 10-30s | HTTP、CDN优化 |
| 监控录像 | RTSP | <500ms | 回放支持 |
| 弱网环境 | SRT | 可配置 | ARQ重传、加密 |

## 扩展开发

### 添加新协议

1. **实现协议适配器**

```python
from core.interfaces import IMediaTransport
from core.models import MediaPacket, TransportStats, TransportConfig

class MyProtocolAdapter(IMediaTransport):
    def initialize(self, config: TransportConfig) -> bool:
        # 初始化协议
        pass
    
    def send_media_data(self, packet: MediaPacket) -> bool:
        # 发送数据
        pass
    
    # 实现其他接口方法...
```

2. **注册协议**

```python
from core.protocol_factory import ProtocolFactory
from core.models import ProtocolType

# 注册新协议
ProtocolFactory.register(ProtocolType.MY_PROTOCOL, MyProtocolAdapter)
```

3. **使用新协议**

```python
adapter = ProtocolFactory.create(ProtocolType.MY_PROTOCOL, config)
```

## 性能优化

### RTP优化
- 启用NACK重传 (RTT<100ms)
- FEC冗余率: 5-15%
- 抖动缓冲: 动态调整

### RTMP优化
- TCP_NODELAY: 禁用Nagle算法
- GOP缓存: 1-2秒
- 增大发送缓冲区

### 通用优化
- 零拷贝技术
- 异步I/O
- 连接池复用
- 硬件加速

## 测试

```bash
# 运行单元测试
python -m pytest tests/

# 运行性能测试
python tests/performance_test.py
```

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

项目维护者: Media Transport Framework Team

## 致谢

- FFmpeg: 多媒体处理
- WebRTC: 实时通信技术
- SRT Alliance: SRT协议标准

---

**⭐ 如果这个项目对您有帮助，请给我们一个Star！**
