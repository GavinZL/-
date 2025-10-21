"""
协议工厂
Protocol Factory

实现协议的注册、创建和管理
"""
from typing import Dict, Type, Optional
from ..core.interfaces import IMediaTransport
from ..core.models import ProtocolType, TransportConfig


class ProtocolFactory:
    """
    协议工厂类
    Protocol Factory Class
    
    实现协议的插件化注册和创建
    """
    
    # 协议注册表
    _registry: Dict[ProtocolType, Type[IMediaTransport]] = {}
    
    @classmethod
    def register(cls, protocol_type: ProtocolType, adapter_class: Type[IMediaTransport]) -> None:
        """
        注册协议适配器
        
        Args:
            protocol_type: 协议类型
            adapter_class: 适配器类
        """
        cls._registry[protocol_type] = adapter_class
        print(f"Protocol registered: {protocol_type.value} -> {adapter_class.__name__}")
    
    @classmethod
    def create(cls, protocol_type: ProtocolType, config: Optional[TransportConfig] = None) -> Optional[IMediaTransport]:
        """
        创建协议适配器实例
        
        Args:
            protocol_type: 协议类型
            config: 传输配置
            
        Returns:
            IMediaTransport: 协议适配器实例，失败返回None
        """
        if protocol_type not in cls._registry:
            print(f"Protocol not registered: {protocol_type.value}")
            return None
        
        try:
            adapter_class = cls._registry[protocol_type]
            adapter = adapter_class()
            
            # 如果提供了配置，立即初始化
            if config:
                if not adapter.initialize(config):
                    print(f"Failed to initialize protocol: {protocol_type.value}")
                    return None
            
            return adapter
            
        except Exception as e:
            print(f"Failed to create protocol adapter: {e}")
            return None
    
    @classmethod
    def get_registered_protocols(cls) -> list:
        """
        获取已注册的协议列表
        
        Returns:
            list: 协议类型列表
        """
        return list(cls._registry.keys())
    
    @classmethod
    def is_registered(cls, protocol_type: ProtocolType) -> bool:
        """
        检查协议是否已注册
        
        Args:
            protocol_type: 协议类型
            
        Returns:
            bool: 是否已注册
        """
        return protocol_type in cls._registry
    
    @classmethod
    def unregister(cls, protocol_type: ProtocolType) -> bool:
        """
        注销协议
        
        Args:
            protocol_type: 协议类型
            
        Returns:
            bool: 是否成功注销
        """
        if protocol_type in cls._registry:
            del cls._registry[protocol_type]
            print(f"Protocol unregistered: {protocol_type.value}")
            return True
        return False


def register_builtin_protocols():
    """注册内置协议"""
    try:
        # 注册RTP协议
        from ..adapters.rtp import RTPAdapter
        ProtocolFactory.register(ProtocolType.RTP, RTPAdapter)
    except ImportError as e:
        print(f"Failed to register RTP: {e}")
    
    try:
        # 注册RTMP协议
        from ..adapters.rtmp import RTMPAdapter
        ProtocolFactory.register(ProtocolType.RTMP, RTMPAdapter)
    except ImportError as e:
        print(f"Failed to register RTMP: {e}")
    
    try:
        # 注册SRT协议
        from ..adapters.srt import SRTAdapter
        ProtocolFactory.register(ProtocolType.SRT, SRTAdapter)
    except ImportError as e:
        print(f"Failed to register SRT: {e}")
    
    try:
        # 注册WebRTC协议
        from ..adapters.webrtc import WebRTCAdapter
        ProtocolFactory.register(ProtocolType.WEBRTC, WebRTCAdapter)
    except ImportError as e:
        print(f"Failed to register WebRTC: {e}")


# 自动注册内置协议
register_builtin_protocols()
