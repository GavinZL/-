"""
媒体传输接口定义
Media Transport Interface
"""
from abc import ABC, abstractmethod
from typing import Callable, Optional
from ..models import MediaPacket, TransportStats, TransportConfig


class IMediaTransport(ABC):
    """
    媒体传输抽象接口
    Media Transport Abstract Interface
    
    设计目标：
    1. 协议无关的统一传输接口
    2. 支持多种传输协议的适配
    3. 提供统一的QoS统计和控制
    """
    
    @abstractmethod
    def initialize(self, config: TransportConfig) -> bool:
        """
        初始化传输层
        
        Args:
            config: 传输配置参数
            
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    def send_media_data(self, packet: MediaPacket) -> bool:
        """
        发送媒体数据包
        
        Args:
            packet: 媒体数据包
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @abstractmethod
    def on_media_data_received(self, callback: Callable[[MediaPacket], None]) -> None:
        """
        注册媒体数据接收回调
        
        Args:
            callback: 接收回调函数
        """
        pass
    
    @abstractmethod
    def get_transport_stats(self) -> TransportStats:
        """
        获取传输统计信息
        
        Returns:
            TransportStats: 传输统计数据
        """
        pass
    
    @abstractmethod
    def update_qos(self, bitrate: Optional[int] = None, 
                   framerate: Optional[int] = None,
                   resolution: Optional[str] = None) -> bool:
        """
        更新服务质量参数
        
        Args:
            bitrate: 目标码率(kbps)
            framerate: 目标帧率(fps)
            resolution: 目标分辨率(widthxheight)
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    def close(self) -> bool:
        """
        关闭传输连接
        
        Returns:
            bool: 关闭是否成功
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        检查连接状态
        
        Returns:
            bool: 是否已连接
        """
        pass
    
    @abstractmethod
    def get_protocol_name(self) -> str:
        """
        获取协议名称
        
        Returns:
            str: 协议名称
        """
        pass
