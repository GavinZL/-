"""
RTMP协议适配器
RTMP Protocol Adapter
"""
import socket
import struct
import threading
import time
import random
from typing import Callable, Optional, Dict
from ...core.interfaces import IMediaTransport
from ...core.models import MediaPacket, TransportStats, TransportConfig, MediaType


class RTMPHandshake:
    """
    RTMP握手处理器
    RTMP Handshake Handler
    """
    
    # 握手包大小
    C0_SIZE = 1
    C1_SIZE = 1536
    C2_SIZE = 1536
    
    @staticmethod
    def create_c0() -> bytes:
        """创建C0包 - RTMP版本号"""
        return bytes([0x03])  # RTMP版本3
    
    @staticmethod
    def create_c1() -> bytes:
        """创建C1包 - 1536字节随机数据"""
        timestamp = int(time.time())
        zero = 0
        random_bytes = bytes([random.randint(0, 255) for _ in range(1528)])
        
        return struct.pack('>II', timestamp, zero) + random_bytes
    
    @staticmethod
    def create_c2(s1: bytes) -> bytes:
        """创建C2包 - 回显S1"""
        return s1
    
    @staticmethod
    def parse_s0(data: bytes) -> int:
        """解析S0 - 服务器版本"""
        if len(data) < 1:
            raise ValueError("Invalid S0 size")
        return data[0]
    
    @staticmethod
    def parse_s1(data: bytes) -> tuple:
        """解析S1"""
        if len(data) < 1536:
            raise ValueError("Invalid S1 size")
        
        timestamp, zero = struct.unpack('>II', data[:8])
        random_bytes = data[8:]
        
        return timestamp, zero, random_bytes


class RTMPChunk:
    """
    RTMP分块
    RTMP Chunk
    """
    
    # 消息类型
    MSG_SET_CHUNK_SIZE = 1
    MSG_ABORT = 2
    MSG_ACK = 3
    MSG_USER_CONTROL = 4
    MSG_WINDOW_ACK_SIZE = 5
    MSG_SET_PEER_BANDWIDTH = 6
    MSG_AUDIO = 8
    MSG_VIDEO = 9
    MSG_DATA_AMF3 = 15
    MSG_DATA_AMF0 = 18
    MSG_COMMAND_AMF3 = 17
    MSG_COMMAND_AMF0 = 20
    
    # 分块类型
    FMT_TYPE_0 = 0  # 11字节头
    FMT_TYPE_1 = 1  # 7字节头
    FMT_TYPE_2 = 2  # 3字节头
    FMT_TYPE_3 = 3  # 0字节头
    
    def __init__(self):
        self.fmt = 0
        self.chunk_stream_id = 0
        self.timestamp = 0
        self.message_length = 0
        self.message_type_id = 0
        self.message_stream_id = 0
        self.payload = b''


class AMF0Encoder:
    """
    AMF0编码器
    AMF0 Encoder - Action Message Format
    """
    
    # AMF0数据类型
    NUMBER = 0x00
    BOOLEAN = 0x01
    STRING = 0x02
    OBJECT = 0x03
    NULL = 0x05
    UNDEFINED = 0x06
    ARRAY = 0x08
    
    @staticmethod
    def encode_number(value: float) -> bytes:
        """编码数字"""
        return struct.pack('>Bd', AMF0Encoder.NUMBER, value)
    
    @staticmethod
    def encode_string(value: str) -> bytes:
        """编码字符串"""
        encoded = value.encode('utf-8')
        return struct.pack('>BH', AMF0Encoder.STRING, len(encoded)) + encoded
    
    @staticmethod
    def encode_boolean(value: bool) -> bytes:
        """编码布尔值"""
        return struct.pack('>BB', AMF0Encoder.BOOLEAN, 1 if value else 0)
    
    @staticmethod
    def encode_null() -> bytes:
        """编码NULL"""
        return bytes([AMF0Encoder.NULL])
    
    @staticmethod
    def encode_object(obj: Dict) -> bytes:
        """编码对象"""
        result = bytes([AMF0Encoder.OBJECT])
        
        for key, value in obj.items():
            # 编码属性名 (不带类型标记)
            encoded_key = key.encode('utf-8')
            result += struct.pack('>H', len(encoded_key)) + encoded_key
            
            # 编码属性值
            if isinstance(value, str):
                result += AMF0Encoder.encode_string(value)
            elif isinstance(value, (int, float)):
                result += AMF0Encoder.encode_number(float(value))
            elif isinstance(value, bool):
                result += AMF0Encoder.encode_boolean(value)
            elif value is None:
                result += AMF0Encoder.encode_null()
        
        # 对象结束标记
        result += bytes([0x00, 0x00, 0x09])
        
        return result


class RTMPAdapter(IMediaTransport):
    """
    RTMP协议适配器实现
    RTMP Protocol Adapter Implementation
    """
    
    def __init__(self):
        self.config: Optional[TransportConfig] = None
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.connected = False
        self.receive_thread: Optional[threading.Thread] = None
        
        # RTMP状态
        self.chunk_size = 128
        self.window_ack_size = 2500000
        self.transaction_id = 1
        self.stream_id = 0
        
        # 统计信息
        self.stats = TransportStats()
        
        # 回调函数
        self.media_callback: Optional[Callable[[MediaPacket], None]] = None
        
        # 锁
        self.lock = threading.Lock()
    
    def initialize(self, config: TransportConfig) -> bool:
        """初始化RTMP传输"""
        try:
            self.config = config
            
            # 创建TCP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # 连接服务器
            self.socket.connect((config.server_address, config.server_port))
            
            # 执行RTMP握手
            if not self._do_handshake():
                return False
            
            # 发送Connect命令
            if not self._send_connect():
                return False
            
            # 启动接收线程
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"RTMP initialization failed: {e}")
            return False
    
    def _do_handshake(self) -> bool:
        """执行RTMP握手"""
        try:
            # 发送 C0 + C1
            c0 = RTMPHandshake.create_c0()
            c1 = RTMPHandshake.create_c1()
            self.socket.sendall(c0 + c1)
            
            # 接收 S0 + S1 + S2
            s0 = self.socket.recv(1)
            RTMPHandshake.parse_s0(s0)
            
            s1 = self.socket.recv(1536)
            s2 = self.socket.recv(1536)
            
            # 发送 C2
            c2 = RTMPHandshake.create_c2(s1)
            self.socket.sendall(c2)
            
            return True
            
        except Exception as e:
            print(f"RTMP handshake failed: {e}")
            return False
    
    def _send_connect(self) -> bool:
        """发送Connect命令"""
        try:
            # 获取RTMP配置
            rtmp_config = self.config.protocol_params.get('rtmp', {})
            app_name = rtmp_config.get('app_name', 'live')
            
            # 构建Connect命令
            command = AMF0Encoder.encode_string("connect")
            transaction_id = AMF0Encoder.encode_number(1)
            
            # 命令对象
            command_obj = {
                "app": app_name,
                "type": "nonprivate",
                "flashVer": "FMLE/3.0",
                "tcUrl": f"rtmp://{self.config.server_address}:{self.config.server_port}/{app_name}"
            }
            command_obj_encoded = AMF0Encoder.encode_object(command_obj)
            
            payload = command + transaction_id + command_obj_encoded
            
            # 发送消息块
            self._send_chunk(RTMPChunk.MSG_COMMAND_AMF0, payload, 3)
            
            return True
            
        except Exception as e:
            print(f"RTMP connect failed: {e}")
            return False
    
    def _send_chunk(self, message_type: int, payload: bytes, chunk_stream_id: int = 3):
        """发送RTMP消息块"""
        try:
            # 简化实现：使用Format 0 (完整头)
            fmt = RTMPChunk.FMT_TYPE_0
            
            # 基本头 (1字节)
            basic_header = bytes([(fmt << 6) | chunk_stream_id])
            
            # 消息头 (11字节)
            timestamp = 0
            message_length = len(payload)
            message_stream_id = self.stream_id
            
            message_header = struct.pack(
                '>I',
                timestamp & 0xFFFFFF  # 24位时间戳
            )[1:]  # 取后3字节
            
            message_header += struct.pack('>I', message_length)[1:]  # 3字节长度
            message_header += bytes([message_type])  # 1字节类型
            message_header += struct.pack('<I', message_stream_id)  # 4字节小端stream id
            
            # 分块发送payload
            header = basic_header + message_header
            self.socket.sendall(header + payload)
            
            # 更新统计
            with self.lock:
                self.stats.packets_sent += 1
                self.stats.bytes_sent += len(header) + len(payload)
                self.stats.last_update_time = time.time()
            
        except Exception as e:
            print(f"RTMP send chunk failed: {e}")
    
    def send_media_data(self, packet: MediaPacket) -> bool:
        """发送媒体数据"""
        try:
            if not self.socket or not self.connected:
                return False
            
            # 根据媒体类型选择消息类型
            if packet.media_type == MediaType.VIDEO:
                message_type = RTMPChunk.MSG_VIDEO
            elif packet.media_type == MediaType.AUDIO:
                message_type = RTMPChunk.MSG_AUDIO
            else:
                return False
            
            # 构建FLV标签格式的payload
            # 简化实现：直接发送payload
            self._send_chunk(message_type, packet.payload)
            
            return True
            
        except Exception as e:
            print(f"RTMP send media data failed: {e}")
            return False
    
    def _receive_loop(self):
        """接收循环"""
        self.socket.settimeout(1.0)
        
        while self.running:
            try:
                # 简化实现：读取基本头
                basic_header = self.socket.recv(1)
                if not basic_header:
                    continue
                
                # 更新统计
                with self.lock:
                    self.stats.packets_received += 1
                    self.stats.bytes_received += len(basic_header)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"RTMP receive error: {e}")
                    break
    
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
        # RTMP层不直接控制编码参数
        return True
    
    def close(self) -> bool:
        """关闭连接"""
        self.running = False
        self.connected = False
        
        if self.receive_thread:
            self.receive_thread.join(timeout=2)
        
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
        return "RTMP"
