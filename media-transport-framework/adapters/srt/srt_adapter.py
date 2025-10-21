"""
SRT协议适配器
SRT (Secure Reliable Transport) Protocol Adapter
"""
import socket
import struct
import threading
import time
import hashlib
from typing import Callable, Optional, Dict
from ...core.interfaces import IMediaTransport
from ...core.models import MediaPacket, TransportStats, TransportConfig, MediaType


class SRTHandshake:
    """
    SRT握手处理器
    SRT Handshake Handler
    """
    
    # SRT版本
    SRT_VERSION = 0x00010400  # 1.4.0
    
    # 握手类型
    UDT_HANDSHAKE = 0x00000000
    SRT_HANDSHAKE = 0x00000001
    
    # 握手阶段
    INDUCTION = 1
    CONCLUSION = -1
    
    def __init__(self):
        self.socket_id = 0
        self.peer_socket_id = 0
        self.initial_seq = 0
        self.crypto_key = None
    
    def create_handshake_packet(self, handshake_type: int) -> bytes:
        """
        创建握手包
        
        Args:
            handshake_type: 握手类型
            
        Returns:
            bytes: 握手包数据
        """
        # SRT握手包结构
        # Version (4) + Extension (2) + Initial Packet Sequence (4)
        # Maximum Transmission Unit (4) + Maximum Flow Window (4)
        # Handshake Type (4) + Socket ID (4) + SYN Cookie (4)
        # IP Address (16)
        
        packet = struct.pack(
            '>IHHIIIII',
            self.SRT_VERSION,           # Version
            0,                          # Extension Field
            0,                          # Extension
            self.initial_seq,           # Initial Packet Sequence
            1500,                       # MTU
            8192,                       # Flow Window Size
            handshake_type,             # Handshake Type
            self.socket_id              # Socket ID
        )
        
        # SYN Cookie (4 bytes)
        syn_cookie = int(time.time()) & 0xFFFFFFFF
        packet += struct.pack('>I', syn_cookie)
        
        # IP Address (16 bytes, IPv4用前4字节)
        packet += b'\x00' * 16
        
        return packet
    
    def parse_handshake_packet(self, data: bytes) -> Dict:
        """解析握手包"""
        if len(data) < 48:
            raise ValueError("Invalid SRT handshake packet size")
        
        version, ext_field, ext, init_seq, mtu, flow_win, hs_type, sock_id = \
            struct.unpack('>IHHIIIII', data[:32])
        
        syn_cookie, = struct.unpack('>I', data[32:36])
        
        return {
            'version': version,
            'initial_seq': init_seq,
            'mtu': mtu,
            'flow_window': flow_win,
            'handshake_type': hs_type,
            'socket_id': sock_id,
            'syn_cookie': syn_cookie
        }


class SRTPacket:
    """
    SRT数据包
    SRT Data Packet
    """
    
    # 控制包类型
    CONTROL_HANDSHAKE = 0x0000
    CONTROL_KEEPALIVE = 0x0001
    CONTROL_ACK = 0x0002
    CONTROL_NAK = 0x0003
    CONTROL_SHUTDOWN = 0x0005
    
    def __init__(self):
        self.is_control = False
        self.packet_seq = 0
        self.message_number = 0
        self.timestamp = 0
        self.destination_socket_id = 0
        self.payload = b''
    
    def pack(self) -> bytes:
        """打包SRT数据包"""
        # 数据包头 (16 字节)
        # Flags (4) + Packet Sequence (4) + Message Number (4) + Timestamp (4)
        # Destination Socket ID (4)
        
        flags = 0x80000000 if self.is_control else 0x00000000
        
        header = struct.pack(
            '>IIIII',
            flags,
            self.packet_seq,
            self.message_number,
            self.timestamp,
            self.destination_socket_id
        )
        
        return header + self.payload
    
    @staticmethod
    def unpack(data: bytes) -> 'SRTPacket':
        """解包SRT数据包"""
        if len(data) < 16:
            raise ValueError("Invalid SRT packet size")
        
        packet = SRTPacket()
        
        flags, seq, msg_num, ts, dst_id = struct.unpack('>IIIII', data[:20])
        
        packet.is_control = (flags & 0x80000000) != 0
        packet.packet_seq = seq & 0x7FFFFFFF
        packet.message_number = msg_num
        packet.timestamp = ts
        packet.destination_socket_id = dst_id
        packet.payload = data[20:]
        
        return packet


class ARQController:
    """
    ARQ自动重传控制器
    Automatic Repeat reQuest Controller
    """
    
    def __init__(self):
        self.send_buffer: Dict[int, bytes] = {}
        self.ack_seq = 0
        self.loss_list = []
        self.rto = 100  # 重传超时(ms)
    
    def add_to_buffer(self, seq: int, data: bytes):
        """添加到发送缓冲区"""
        self.send_buffer[seq] = data
    
    def on_ack_received(self, ack_seq: int):
        """处理ACK"""
        # 清理已确认的包
        to_remove = [seq for seq in self.send_buffer.keys() if seq <= ack_seq]
        for seq in to_remove:
            del self.send_buffer[seq]
        
        self.ack_seq = ack_seq
    
    def on_nak_received(self, nak_list: list):
        """处理NAK - 重传丢失的包"""
        self.loss_list.extend(nak_list)
    
    def get_retransmit_packets(self) -> list:
        """获取需要重传的包"""
        packets = []
        for seq in self.loss_list:
            if seq in self.send_buffer:
                packets.append((seq, self.send_buffer[seq]))
        
        self.loss_list.clear()
        return packets


class SRTEncryption:
    """
    SRT加密模块
    SRT Encryption Module
    """
    
    def __init__(self, passphrase: str = "", key_length: int = 16):
        self.passphrase = passphrase
        self.key_length = key_length
        self.key = None
        
        if passphrase:
            self._generate_key()
    
    def _generate_key(self):
        """生成加密密钥"""
        # 使用SHA256派生密钥
        hash_obj = hashlib.sha256(self.passphrase.encode('utf-8'))
        self.key = hash_obj.digest()[:self.key_length]
    
    def encrypt(self, data: bytes) -> bytes:
        """
        加密数据
        简化实现：实际应使用AES-CTR
        """
        if not self.key:
            return data
        
        # 简化实现：XOR加密（实际应使用AES）
        encrypted = bytearray(data)
        key_len = len(self.key)
        for i in range(len(encrypted)):
            encrypted[i] ^= self.key[i % key_len]
        
        return bytes(encrypted)
    
    def decrypt(self, data: bytes) -> bytes:
        """
        解密数据
        XOR加密的解密与加密相同
        """
        return self.encrypt(data)


class SRTAdapter(IMediaTransport):
    """
    SRT协议适配器实现
    SRT Protocol Adapter Implementation
    """
    
    def __init__(self):
        self.config: Optional[TransportConfig] = None
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.connected = False
        self.receive_thread: Optional[threading.Thread] = None
        self.keepalive_thread: Optional[threading.Thread] = None
        
        # SRT状态
        self.socket_id = int(time.time() * 1000) & 0xFFFFFFFF
        self.peer_socket_id = 0
        self.packet_seq = 0
        self.message_number = 0
        
        # 控制器
        self.arq_controller = ARQController()
        self.encryption: Optional[SRTEncryption] = None
        
        # 统计信息
        self.stats = TransportStats()
        
        # 回调函数
        self.media_callback: Optional[Callable[[MediaPacket], None]] = None
        
        # 锁
        self.lock = threading.Lock()
    
    def initialize(self, config: TransportConfig) -> bool:
        """初始化SRT传输"""
        try:
            self.config = config
            
            # 创建UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 绑定本地端口
            if config.local_port > 0:
                self.socket.bind(('0.0.0.0', config.local_port))
            else:
                self.socket.bind(('0.0.0.0', 0))
            
            # 从协议参数中读取SRT配置
            srt_config = config.protocol_params.get('srt', {})
            
            # 初始化加密
            passphrase = srt_config.get('passphrase', '')
            key_length = srt_config.get('pbkeylen', 16)
            if passphrase:
                self.encryption = SRTEncryption(passphrase, key_length)
            
            # 执行SRT握手
            if not self._do_handshake():
                return False
            
            # 启动接收线程
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            # 启动保活线程
            self.keepalive_thread = threading.Thread(target=self._keepalive_loop)
            self.keepalive_thread.daemon = True
            self.keepalive_thread.start()
            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"SRT initialization failed: {e}")
            return False
    
    def _do_handshake(self) -> bool:
        """执行SRT握手"""
        try:
            handshake = SRTHandshake()
            handshake.socket_id = self.socket_id
            handshake.initial_seq = self.packet_seq
            
            # 发送Induction握手
            hs_packet = handshake.create_handshake_packet(SRTHandshake.INDUCTION)
            self.socket.sendto(
                hs_packet,
                (self.config.server_address, self.config.server_port)
            )
            
            # 接收响应（简化实现）
            # 实际应等待并解析握手响应
            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"SRT handshake failed: {e}")
            return False
    
    def send_media_data(self, packet: MediaPacket) -> bool:
        """发送媒体数据"""
        try:
            if not self.socket or not self.connected:
                return False
            
            # 创建SRT数据包
            srt_packet = SRTPacket()
            srt_packet.is_control = False
            srt_packet.packet_seq = self.packet_seq
            srt_packet.message_number = self.message_number
            srt_packet.timestamp = int(packet.timestamp / 1000)  # 转换为毫秒
            srt_packet.destination_socket_id = self.peer_socket_id
            srt_packet.payload = packet.payload
            
            # 加密
            if self.encryption:
                srt_packet.payload = self.encryption.encrypt(srt_packet.payload)
            
            # 打包并发送
            data = srt_packet.pack()
            self.socket.sendto(
                data,
                (self.config.server_address, self.config.server_port)
            )
            
            # 添加到ARQ缓冲区
            self.arq_controller.add_to_buffer(self.packet_seq, data)
            
            # 更新统计
            with self.lock:
                self.stats.packets_sent += 1
                self.stats.bytes_sent += len(data)
                self.packet_seq = (self.packet_seq + 1) & 0x7FFFFFFF
                self.message_number = (self.message_number + 1) & 0xFFFFFFFF
                self.stats.last_update_time = time.time()
            
            return True
            
        except Exception as e:
            print(f"SRT send failed: {e}")
            return False
    
    def _receive_loop(self):
        """接收循环"""
        self.socket.settimeout(1.0)
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(65536)
                
                # 解析SRT包
                srt_packet = SRTPacket.unpack(data)
                
                if srt_packet.is_control:
                    # 处理控制包
                    self._process_control_packet(srt_packet)
                else:
                    # 处理数据包
                    self._process_data_packet(srt_packet)
                
                # 更新统计
                with self.lock:
                    self.stats.packets_received += 1
                    self.stats.bytes_received += len(data)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"SRT receive error: {e}")
    
    def _process_control_packet(self, packet: SRTPacket):
        """处理控制包"""
        # 简化实现：处理ACK和NAK
        pass
    
    def _process_data_packet(self, packet: SRTPacket):
        """处理数据包"""
        if self.media_callback:
            # 解密
            payload = packet.payload
            if self.encryption:
                payload = self.encryption.decrypt(payload)
            
            # 转换为MediaPacket
            media_packet = MediaPacket(
                payload=payload,
                timestamp=packet.timestamp * 1000,  # 转回微秒
                media_type=MediaType.VIDEO,
                codec_type=self._guess_codec_type(payload),
                sequence_number=packet.packet_seq
            )
            
            self.media_callback(media_packet)
    
    def _keepalive_loop(self):
        """保活循环"""
        while self.running:
            try:
                time.sleep(1)  # 每秒发送保活
                # 发送保活包（简化实现）
            except Exception as e:
                if self.running:
                    print(f"SRT keepalive error: {e}")
    
    def _guess_codec_type(self, payload: bytes):
        """推测编码类型"""
        from ...core.models import CodecType
        
        # 简单的启发式判断
        if len(payload) > 4 and payload[:4] == b'\x00\x00\x00\x01':
            return CodecType.H264
        
        return CodecType.H264  # 默认
    
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
        # SRT层可以通过调整发送速率来适配
        return True
    
    def close(self) -> bool:
        """关闭连接"""
        self.running = False
        self.connected = False
        
        if self.receive_thread:
            self.receive_thread.join(timeout=2)
        
        if self.keepalive_thread:
            self.keepalive_thread.join(timeout=2)
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        return True
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected
    
    def get_protocol_name(self) -> str:
        """获取协议名称"""
        return "SRT"
