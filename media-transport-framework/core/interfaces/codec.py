"""
编解码器接口定义
Codec Interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass
from ..models import MediaPacket, CodecType


@dataclass
class VideoFrame:
    """
    原始视频帧
    Raw Video Frame
    """
    # 视频数据
    data: bytes
    
    # 宽度
    width: int
    
    # 高度
    height: int
    
    # 时间戳(微秒)
    timestamp: int
    
    # 像素格式 (YUV420P, NV12, etc.)
    pixel_format: str = "YUV420P"
    
    # 是否关键帧
    is_key_frame: bool = False


@dataclass
class AudioFrame:
    """
    原始音频帧
    Raw Audio Frame
    """
    # 音频数据
    data: bytes
    
    # 采样率
    sample_rate: int
    
    # 声道数
    channels: int
    
    # 时间戳(微秒)
    timestamp: int
    
    # 采样格式 (S16, F32, etc.)
    sample_format: str = "S16"


@dataclass
class CodecInfo:
    """编解码器信息"""
    name: str
    codec_type: CodecType
    profile: str = ""
    level: str = ""
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class ICodec(ABC):
    """
    编解码器抽象接口
    Codec Abstract Interface
    """
    
    @abstractmethod
    def encode_video(self, frame: VideoFrame) -> MediaPacket:
        """
        编码视频帧
        
        Args:
            frame: 原始视频帧
            
        Returns:
            MediaPacket: 编码后的媒体包
        """
        pass
    
    @abstractmethod
    def decode_video(self, packet: MediaPacket) -> VideoFrame:
        """
        解码视频包
        
        Args:
            packet: 编码的媒体包
            
        Returns:
            VideoFrame: 解码后的视频帧
        """
        pass
    
    @abstractmethod
    def encode_audio(self, frame: AudioFrame) -> MediaPacket:
        """
        编码音频帧
        
        Args:
            frame: 原始音频帧
            
        Returns:
            MediaPacket: 编码后的媒体包
        """
        pass
    
    @abstractmethod
    def decode_audio(self, packet: MediaPacket) -> AudioFrame:
        """
        解码音频包
        
        Args:
            packet: 编码的媒体包
            
        Returns:
            AudioFrame: 解码后的音频帧
        """
        pass
    
    @abstractmethod
    def set_bitrate(self, target_bitrate: int) -> bool:
        """
        设置目标码率
        
        Args:
            target_bitrate: 目标码率(kbps)
            
        Returns:
            bool: 设置是否成功
        """
        pass
    
    @abstractmethod
    def set_framerate(self, fps: int) -> bool:
        """
        设置帧率
        
        Args:
            fps: 目标帧率
            
        Returns:
            bool: 设置是否成功
        """
        pass
    
    @abstractmethod
    def request_key_frame(self) -> bool:
        """
        请求关键帧
        
        Returns:
            bool: 请求是否成功
        """
        pass
    
    @abstractmethod
    def get_codec_info(self) -> CodecInfo:
        """
        获取编解码器信息
        
        Returns:
            CodecInfo: 编解码器信息
        """
        pass
