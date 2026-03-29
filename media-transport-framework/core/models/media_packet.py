"""
媒体数据包模型定义
Media Packet Model Definition
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


class MediaType(Enum):
    """媒体类型枚举"""
    AUDIO = "audio"
    VIDEO = "video"
    DATA = "data"


class CodecType(Enum):
    """编解码器类型枚举"""
    # 视频编解码器
    H264 = "H264"
    H265 = "H265"
    VP8 = "VP8"
    VP9 = "VP9"
    AV1 = "AV1"
    
    # 音频编解码器
    OPUS = "OPUS"
    AAC = "AAC"
    G711 = "G711"
    PCMU = "PCMU"
    PCMA = "PCMA"


@dataclass
class MediaPacket:
    """
    统一的媒体数据包结构
    Unified Media Packet Structure
    
    设计目标：
    1. 协议无关的媒体数据封装
    2. 支持音频、视频、数据通道
    3. 包含必要的时间戳和序列号信息
    """
    
    # 媒体载荷数据
    payload: bytes
    
    # 时间戳(微秒)
    timestamp: int
    
    # 媒体类型
    media_type: MediaType
    
    # 编解码器类型
    codec_type: CodecType
    
    # 是否关键帧
    is_key_frame: bool = False
    
    # 序列号
    sequence_number: int = 0
    
    # 扩展元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # SSRC标识符(用于RTP等协议)
    ssrc: Optional[int] = None
    
    # 载荷类型(用于RTP)
    payload_type: Optional[int] = None
    
    def __post_init__(self):
        """数据包创建后的验证"""
        if not self.payload:
            raise ValueError("Media payload cannot be empty")
        if self.timestamp < 0:
            raise ValueError("Timestamp must be non-negative")
    
    @property
    def size(self) -> int:
        """获取载荷大小(字节)"""
        return len(self.payload)
    
    def clone(self) -> 'MediaPacket':
        """克隆数据包"""
        return MediaPacket(
            payload=self.payload,
            timestamp=self.timestamp,
            media_type=self.media_type,
            codec_type=self.codec_type,
            is_key_frame=self.is_key_frame,
            sequence_number=self.sequence_number,
            metadata=self.metadata.copy(),
            ssrc=self.ssrc,
            payload_type=self.payload_type
        )
