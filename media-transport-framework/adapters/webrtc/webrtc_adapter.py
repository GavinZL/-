"""
WebRTC协议适配器
WebRTC Protocol Adapter
"""
import json
import time
import threading
from typing import Callable, Optional, Dict, List
from enum import Enum
from ...core.interfaces import IMediaTransport, ISignaling, SessionDescription, IceCandidate
from ...core.models import MediaPacket, TransportStats, TransportConfig, MediaType


class ICEConnectionState(Enum):
    """ICE连接状态"""
    NEW = "new"
    CHECKING = "checking"
    CONNECTED = "connected"
    COMPLETED = "completed"
    FAILED = "failed"
    DISCONNECTED = "disconnected"
    CLOSED = "closed"


class ICECandidateType(Enum):
    """ICE候选类型"""
    HOST = "host"           # 本地候选
    SRFLX = "srflx"        # 服务器反射候选(STUN)
    RELAY = "relay"        # 中继候选(TURN)


class STUNMessage:
    """
    STUN消息
    Session Traversal Utilities for NAT
    """
    
    # STUN消息类型
    BINDING_REQUEST = 0x0001
    BINDING_RESPONSE = 0x0101
    
    # STUN属性
    ATTR_MAPPED_ADDRESS = 0x0001
    ATTR_XOR_MAPPED_ADDRESS = 0x0020
    
    # STUN Magic Cookie
    MAGIC_COOKIE = 0x2112A442
    
    def __init__(self):
        self.message_type = self.BINDING_REQUEST
        self.transaction_id = b'\x00' * 12
        self.attributes = {}
    
    def pack(self) -> bytes:
        """打包STUN消息"""
        import struct
        import random
        
        # 生成随机事务ID
        self.transaction_id = bytes([random.randint(0, 255) for _ in range(12)])
        
        # STUN消息头 (20字节)
        # Type (2) + Length (2) + Magic Cookie (4) + Transaction ID (12)
        header = struct.pack(
            '>HHI',
            self.message_type,
            0,  # 暂时为0，后面计算
            self.MAGIC_COOKIE
        ) + self.transaction_id
        
        return header
    
    @staticmethod
    def unpack(data: bytes) -> 'STUNMessage':
        """解包STUN消息"""
        import struct
        
        if len(data) < 20:
            raise ValueError("Invalid STUN message size")
        
        msg = STUNMessage()
        msg_type, length, magic_cookie = struct.unpack('>HHI', data[:8])
        msg.transaction_id = data[8:20]
        
        msg.message_type = msg_type
        
        return msg


class ICEAgent:
    """
    ICE代理
    Interactive Connectivity Establishment Agent
    
    负责收集候选、执行连通性检查
    """
    
    def __init__(self, stun_servers: List[str]):
        self.stun_servers = stun_servers
        self.local_candidates: List[Dict] = []
        self.remote_candidates: List[Dict] = []
        self.connection_state = ICEConnectionState.NEW
        self.selected_candidate_pair = None
    
    def gather_candidates(self) -> List[Dict]:
        """
        收集ICE候选
        
        Returns:
            List[Dict]: 候选列表
        """
        candidates = []
        
        # 1. 收集Host候选（本地网络接口）
        host_candidate = self._gather_host_candidates()
        candidates.extend(host_candidate)
        
        # 2. 收集Server Reflexive候选（STUN）
        srflx_candidate = self._gather_srflx_candidates()
        candidates.extend(srflx_candidate)
        
        # 3. 收集Relay候选（TURN）- 简化实现中跳过
        
        self.local_candidates = candidates
        return candidates
    
    def _gather_host_candidates(self) -> List[Dict]:
        """收集本地候选"""
        import socket
        
        candidates = []
        
        try:
            # 获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            candidate = {
                'type': ICECandidateType.HOST.value,
                'protocol': 'udp',
                'address': local_ip,
                'port': 0,  # 动态分配
                'priority': self._calculate_priority(ICECandidateType.HOST, 65535),
                'foundation': self._calculate_foundation(ICECandidateType.HOST, local_ip)
            }
            
            candidates.append(candidate)
            
        except Exception as e:
            print(f"Failed to gather host candidates: {e}")
        
        return candidates
    
    def _gather_srflx_candidates(self) -> List[Dict]:
        """收集服务器反射候选（通过STUN）"""
        candidates = []
        
        if not self.stun_servers:
            return candidates
        
        try:
            # 简化实现：向STUN服务器发送请求获取公网地址
            # 实际应解析STUN服务器地址并发送STUN Binding Request
            
            for stun_server in self.stun_servers[:1]:  # 只用第一个
                # 解析STUN服务器地址
                if ':' in stun_server:
                    stun_server = stun_server.replace('stun:', '')
                    parts = stun_server.split(':')
                    stun_host = parts[0]
                    stun_port = int(parts[1]) if len(parts) > 1 else 3478
                else:
                    stun_host = stun_server.replace('stun:', '')
                    stun_port = 3478
                
                # 简化：假设通过STUN获取到了公网地址
                candidate = {
                    'type': ICECandidateType.SRFLX.value,
                    'protocol': 'udp',
                    'address': '203.0.113.1',  # 示例公网IP
                    'port': 54321,
                    'priority': self._calculate_priority(ICECandidateType.SRFLX, 65535),
                    'foundation': self._calculate_foundation(ICECandidateType.SRFLX, '203.0.113.1')
                }
                
                candidates.append(candidate)
                break
                
        except Exception as e:
            print(f"Failed to gather srflx candidates: {e}")
        
        return candidates
    
    def _calculate_priority(self, candidate_type: ICECandidateType, local_pref: int) -> int:
        """
        计算候选优先级
        priority = (2^24)*(type preference) + (2^8)*(local preference) + (2^0)*(256 - component ID)
        """
        type_pref = {
            ICECandidateType.HOST: 126,
            ICECandidateType.SRFLX: 100,
            ICECandidateType.RELAY: 0
        }
        
        pref = type_pref.get(candidate_type, 0)
        component_id = 1  # RTP组件
        
        priority = (pref << 24) + (local_pref << 8) + (256 - component_id)
        return priority
    
    def _calculate_foundation(self, candidate_type: ICECandidateType, address: str) -> str:
        """计算候选Foundation"""
        import hashlib
        
        # Foundation用于标识相同传输地址的候选
        foundation_str = f"{candidate_type.value}:{address}"
        return hashlib.md5(foundation_str.encode()).hexdigest()[:8]
    
    def add_remote_candidate(self, candidate: Dict):
        """添加远端候选"""
        self.remote_candidates.append(candidate)
    
    def start_connectivity_checks(self):
        """开始连通性检查"""
        self.connection_state = ICEConnectionState.CHECKING
        
        # 简化实现：直接选择优先级最高的候选对
        if self.local_candidates and self.remote_candidates:
            local_best = max(self.local_candidates, key=lambda c: c['priority'])
            remote_best = max(self.remote_candidates, key=lambda c: c['priority'])
            
            self.selected_candidate_pair = (local_best, remote_best)
            self.connection_state = ICEConnectionState.CONNECTED
            
            return True
        
        self.connection_state = ICEConnectionState.FAILED
        return False


class DTLSHandler:
    """
    DTLS处理器
    Datagram Transport Layer Security
    
    负责密钥协商和SRTP密钥派生
    """
    
    def __init__(self):
        self.role = "auto"  # auto, client, server
        self.fingerprint = ""
        self.remote_fingerprint = ""
        self.srtp_key = None
    
    def generate_fingerprint(self) -> str:
        """生成证书指纹"""
        import hashlib
        import random
        
        # 简化实现：生成随机指纹
        random_data = bytes([random.randint(0, 255) for _ in range(32)])
        fingerprint = hashlib.sha256(random_data).hexdigest()
        
        # 格式化为标准格式
        formatted = ':'.join([fingerprint[i:i+2].upper() for i in range(0, len(fingerprint), 2)])
        self.fingerprint = formatted
        
        return formatted
    
    def perform_handshake(self) -> bool:
        """执行DTLS握手"""
        # 简化实现：假设握手成功
        self._derive_srtp_keys()
        return True
    
    def _derive_srtp_keys(self):
        """派生SRTP密钥"""
        import hashlib
        
        # 简化实现：从指纹派生密钥
        key_material = hashlib.sha256(self.fingerprint.encode()).digest()
        self.srtp_key = key_material[:16]  # AES-128需要16字节


class WebRTCAdapter(IMediaTransport):
    """
    WebRTC协议适配器实现
    WebRTC Protocol Adapter Implementation
    
    注意：这是简化的实现，生产环境建议使用aiortc等成熟库
    """
    
    def __init__(self):
        self.config: Optional[TransportConfig] = None
        self.running = False
        self.connected = False
        
        # WebRTC组件
        self.ice_agent: Optional[ICEAgent] = None
        self.dtls_handler = DTLSHandler()
        
        # SDP
        self.local_description: Optional[SessionDescription] = None
        self.remote_description: Optional[SessionDescription] = None
        
        # 统计信息
        self.stats = TransportStats()
        
        # 回调函数
        self.media_callback: Optional[Callable[[MediaPacket], None]] = None
        self.signaling_callback: Optional[Callable[[str, Dict], None]] = None
        
        # 锁
        self.lock = threading.Lock()
    
    def initialize(self, config: TransportConfig) -> bool:
        """初始化WebRTC传输"""
        try:
            self.config = config
            
            # 从协议参数中读取WebRTC配置
            webrtc_config = config.protocol_params.get('webrtc', {})
            stun_servers = webrtc_config.get('stun_servers', ['stun:stun.l.google.com:19302'])
            
            # 创建ICE代理
            self.ice_agent = ICEAgent(stun_servers)
            
            # 生成DTLS证书指纹
            self.dtls_handler.generate_fingerprint()
            
            # 收集ICE候选
            candidates = self.ice_agent.gather_candidates()
            print(f"Gathered {len(candidates)} ICE candidates")
            
            return True
            
        except Exception as e:
            print(f"WebRTC initialization failed: {e}")
            return False
    
    def create_offer(self) -> SessionDescription:
        """
        创建Offer SDP
        
        Returns:
            SessionDescription: SDP描述
        """
        # 构建简化的SDP
        sdp_lines = [
            "v=0",
            f"o=- {int(time.time())} {int(time.time())} IN IP4 127.0.0.1",
            "s=-",
            "t=0 0",
            # 音频媒体描述
            "m=audio 9 UDP/TLS/RTP/SAVPF 111",
            "c=IN IP4 0.0.0.0",
            "a=rtcp:9 IN IP4 0.0.0.0",
            "a=ice-ufrag:abc123",
            "a=ice-pwd:xyz789",
            f"a=fingerprint:sha-256 {self.dtls_handler.fingerprint}",
            "a=setup:actpass",
            "a=mid:0",
            "a=sendrecv",
            "a=rtcp-mux",
            "a=rtpmap:111 opus/48000/2",
            # 视频媒体描述
            "m=video 9 UDP/TLS/RTP/SAVPF 96",
            "c=IN IP4 0.0.0.0",
            "a=rtcp:9 IN IP4 0.0.0.0",
            "a=ice-ufrag:abc123",
            "a=ice-pwd:xyz789",
            f"a=fingerprint:sha-256 {self.dtls_handler.fingerprint}",
            "a=setup:actpass",
            "a=mid:1",
            "a=sendrecv",
            "a=rtcp-mux",
            "a=rtpmap:96 H264/90000",
        ]
        
        # 添加ICE候选
        if self.ice_agent:
            for candidate in self.ice_agent.local_candidates:
                sdp_lines.append(
                    f"a=candidate:{candidate['foundation']} 1 {candidate['protocol']} "
                    f"{candidate['priority']} {candidate['address']} {candidate['port']} "
                    f"typ {candidate['type']}"
                )
        
        sdp = '\n'.join(sdp_lines)
        
        self.local_description = SessionDescription(type="offer", sdp=sdp)
        return self.local_description
    
    def create_answer(self, offer: SessionDescription) -> SessionDescription:
        """
        创建Answer SDP
        
        Args:
            offer: 远端Offer
            
        Returns:
            SessionDescription: Answer SDP
        """
        self.remote_description = offer
        
        # 解析Offer中的候选
        self._parse_remote_candidates(offer.sdp)
        
        # 创建Answer（简化：与Offer类似）
        answer_sdp = offer.sdp.replace("a=setup:actpass", "a=setup:active")
        
        self.local_description = SessionDescription(type="answer", sdp=answer_sdp)
        return self.local_description
    
    def _parse_remote_candidates(self, sdp: str):
        """解析远端候选"""
        # 简化实现：提取candidate行
        for line in sdp.split('\n'):
            if line.startswith('a=candidate:'):
                # 解析候选信息
                parts = line.replace('a=candidate:', '').split()
                if len(parts) >= 7:
                    candidate = {
                        'foundation': parts[0],
                        'protocol': parts[2],
                        'priority': int(parts[3]),
                        'address': parts[4],
                        'port': int(parts[5]),
                        'type': parts[7] if len(parts) > 7 else 'host'
                    }
                    
                    if self.ice_agent:
                        self.ice_agent.add_remote_candidate(candidate)
    
    def set_remote_description(self, description: SessionDescription):
        """设置远端描述"""
        self.remote_description = description
        self._parse_remote_candidates(description.sdp)
    
    def add_ice_candidate(self, candidate: IceCandidate):
        """添加ICE候选"""
        if self.ice_agent:
            # 解析候选字符串
            parts = candidate.candidate.split()
            if len(parts) >= 7:
                cand_dict = {
                    'foundation': parts[0],
                    'protocol': parts[2],
                    'priority': int(parts[3]),
                    'address': parts[4],
                    'port': int(parts[5]),
                    'type': parts[7] if len(parts) > 7 else 'host'
                }
                
                self.ice_agent.add_remote_candidate(cand_dict)
    
    def connect(self) -> bool:
        """建立连接"""
        if not self.ice_agent:
            return False
        
        # 开始ICE连通性检查
        if self.ice_agent.start_connectivity_checks():
            # 执行DTLS握手
            if self.dtls_handler.perform_handshake():
                self.connected = True
                self.running = True
                return True
        
        return False
    
    def send_media_data(self, packet: MediaPacket) -> bool:
        """发送媒体数据"""
        try:
            if not self.connected:
                return False
            
            # 简化实现：实际应通过SRTP发送
            # 这里仅更新统计
            with self.lock:
                self.stats.packets_sent += 1
                self.stats.bytes_sent += packet.size
                self.stats.last_update_time = time.time()
            
            return True
            
        except Exception as e:
            print(f"WebRTC send failed: {e}")
            return False
    
    def on_media_data_received(self, callback: Callable[[MediaPacket], None]) -> None:
        """注册接收回调"""
        self.media_callback = callback
    
    def get_transport_stats(self) -> TransportStats:
        """获取传输统计"""
        with self.lock:
            self.stats.update_loss_rate()
            self.stats.update_bitrate()
            return self.stats
    
    def update_qos(self, bitrate: Optional[int] = None,
                   framerate: Optional[int] = None,
                   resolution: Optional[str] = None) -> bool:
        """更新QoS参数"""
        # WebRTC层可以通过调整编码参数来适配
        return True
    
    def close(self) -> bool:
        """关闭连接"""
        self.running = False
        self.connected = False
        
        if self.ice_agent:
            self.ice_agent.connection_state = ICEConnectionState.CLOSED
        
        return True
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected
    
    def get_protocol_name(self) -> str:
        """获取协议名称"""
        return "WebRTC"
