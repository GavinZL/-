"""
信令接口定义
Signaling Interface
"""
from abc import ABC, abstractmethod
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SessionDescription:
    """
    会话描述 (SDP)
    Session Description Protocol
    """
    type: str  # offer / answer
    sdp: str  # SDP内容
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "type": self.type,
            "sdp": self.sdp
        }


@dataclass
class IceCandidate:
    """
    ICE候选
    Interactive Connectivity Establishment Candidate
    """
    candidate: str
    sdp_mid: str
    sdp_mline_index: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate": self.candidate,
            "sdpMid": self.sdp_mid,
            "sdpMLineIndex": self.sdp_mline_index
        }


class ISignaling(ABC):
    """
    信令抽象接口
    Signaling Abstract Interface
    
    用于WebRTC、SIP等需要信令交换的协议
    """
    
    @abstractmethod
    def connect(self, server_url: str, auth_token: Optional[str] = None) -> bool:
        """
        连接信令服务器
        
        Args:
            server_url: 服务器URL
            auth_token: 认证令牌
            
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def send_offer(self, sdp: SessionDescription) -> bool:
        """
        发送会话邀请(Offer)
        
        Args:
            sdp: 会话描述
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @abstractmethod
    def send_answer(self, sdp: SessionDescription) -> bool:
        """
        发送会话应答(Answer)
        
        Args:
            sdp: 会话描述
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @abstractmethod
    def send_candidate(self, candidate: IceCandidate) -> bool:
        """
        发送ICE候选
        
        Args:
            candidate: ICE候选信息
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @abstractmethod
    def on_signal_received(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        注册信令接收回调
        
        Args:
            callback: 回调函数 (signal_type, data)
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        断开信令连接
        
        Returns:
            bool: 断开是否成功
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
