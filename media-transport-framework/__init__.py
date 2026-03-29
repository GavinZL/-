"""
媒体传输框架
Media Transport Framework

一个灵活、可扩展的音视频传输协议框架
"""

__version__ = "1.0.0"
__author__ = "Media Transport Framework Team"

from .core.interfaces import IMediaTransport, ISignaling, ICodec
from .core.models import (
    MediaPacket, MediaType, CodecType,
    TransportStats, QoSMetrics,
    TransportConfig, ProtocolType, TransportMode
)
from .core.protocol_factory import ProtocolFactory
from .core.protocol_selector import ProtocolSelector, ScenarioType, NetworkCondition
from .qos import QoSManager

__all__ = [
    # 接口
    'IMediaTransport', 'ISignaling', 'ICodec',
    
    # 模型
    'MediaPacket', 'MediaType', 'CodecType',
    'TransportStats', 'QoSMetrics',
    'TransportConfig', 'ProtocolType', 'TransportMode',
    
    # 核心类
    'ProtocolFactory', 'ProtocolSelector', 'QoSManager',
    
    # 枚举
    'ScenarioType', 'NetworkCondition',
]
