"""
配置参数模型
Configuration Models
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum


class ProtocolType(Enum):
    """协议类型枚举"""
    RTP = "rtp"
    RTCP = "rtcp"
    RTMP = "rtmp"
    HLS = "hls"
    DASH = "dash"
    SIP = "sip"
    RTSP = "rtsp"
    SRT = "srt"
    WEBRTC = "webrtc"


class TransportMode(Enum):
    """传输模式"""
    UDP = "udp"
    TCP = "tcp"
    QUIC = "quic"
    WEBSOCKET = "websocket"


@dataclass
class TransportConfig:
    """
    传输配置参数
    Transport Configuration
    """
    
    # 协议类型
    protocol_type: ProtocolType
    
    # 传输模式
    transport_mode: TransportMode = TransportMode.UDP
    
    # 服务器地址
    server_address: str = "localhost"
    
    # 服务器端口
    server_port: int = 0
    
    # 本地端口
    local_port: int = 0
    
    # 是否启用加密
    enable_encryption: bool = False
    
    # 加密密钥
    encryption_key: Optional[str] = None
    
    # 最大重传次数
    max_retransmit: int = 3
    
    # 超时时间(毫秒)
    timeout_ms: int = 5000
    
    # 缓冲区大小(字节)
    buffer_size: int = 65536
    
    # 协议特定参数
    protocol_params: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """验证配置参数"""
        if self.server_port <= 0 or self.server_port > 65535:
            return False
        if self.local_port < 0 or self.local_port > 65535:
            return False
        if self.timeout_ms <= 0:
            return False
        if self.buffer_size <= 0:
            return False
        return True


@dataclass
class RTPConfig:
    """RTP协议配置"""
    
    # 载荷类型
    payload_type: int = 96
    
    # SSRC标识符
    ssrc: int = 0
    
    # 时钟频率(Hz)
    clock_rate: int = 90000
    
    # 抖动缓冲大小(毫秒)
    jitter_buffer_size: int = 100
    
    # 是否启用NACK
    enable_nack: bool = True
    
    # 是否启用FEC
    enable_fec: bool = False
    
    # FEC冗余率(0-1)
    fec_redundancy: float = 0.1


@dataclass
class RTMPConfig:
    """RTMP协议配置"""
    
    # 应用名称
    app_name: str = "live"
    
    # 流名称
    stream_name: str = "stream"
    
    # 块大小
    chunk_size: int = 128
    
    # 窗口确认大小
    window_ack_size: int = 2500000
    
    # 是否启用GOP缓存
    enable_gop_cache: bool = True
    
    # GOP缓存大小(秒)
    gop_cache_size: int = 2


@dataclass
class SRTConfig:
    """SRT协议配置"""
    
    # 延迟(毫秒)
    latency: int = 120
    
    # 最大带宽(bps, -1表示无限制)
    max_bandwidth: int = -1
    
    # 密钥长度(0/16/24/32)
    pbkeylen: int = 16
    
    # 预共享密钥
    passphrase: str = ""
    
    # 是否丢弃过时数据包
    tlpktdrop: bool = True
    
    # 发送缓冲区大小(字节)
    send_buffer_size: int = 8192000
    
    # 接收缓冲区大小(字节)
    recv_buffer_size: int = 8192000


@dataclass
class WebRTCConfig:
    """WebRTC协议配置"""
    
    # STUN服务器列表
    stun_servers: list = field(default_factory=lambda: ["stun:stun.l.google.com:19302"])
    
    # TURN服务器列表
    turn_servers: list = field(default_factory=list)
    
    # 是否启用Simulcast
    enable_simulcast: bool = False
    
    # Simulcast层数
    simulcast_layers: int = 3
    
    # 是否强制中继
    force_relay: bool = False
    
    # ICE候选超时(毫秒)
    ice_candidate_timeout: int = 5000
    
    # DTLS角色 (auto/client/server)
    dtls_role: str = "auto"


@dataclass
class QoSConfig:
    """QoS配置"""
    
    # 是否启用自适应码率
    enable_adaptive_bitrate: bool = True
    
    # 目标码率(kbps)
    target_bitrate: int = 2000
    
    # 最小码率(kbps)
    min_bitrate: int = 500
    
    # 最大码率(kbps)
    max_bitrate: int = 4000
    
    # 是否启用动态FEC
    enable_dynamic_fec: bool = True
    
    # 统计更新间隔(秒)
    stats_update_interval: int = 1
    
    # 网络质量阈值
    network_quality_threshold: float = 60.0
