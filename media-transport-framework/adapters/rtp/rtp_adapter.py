"""
RTP/RTCP协议适配器
RTP/RTCP Protocol Adapter
"""
import socket
import struct
import threading
import time
from typing import Callable, Optional, Dict
from ...core.interfaces import IMediaTransport
from ...core.models import MediaPacket, TransportStats, TransportConfig, MediaType


class RTPPacket:
    """RTP数据包结构"""
    
    # RTP固定头长度
    FIXED_HEADER_SIZE = 12
    
    def __init__(self):
        self.version = 2
        self.padding = 0
        self.extension = 0
        self.csrc_count = 0
        self.marker = 0
        self.payload_type = 96
        self.sequence_number = 0
        self.timestamp = 0
        self.ssrc = 0
        self.payload = b''
    
    def pack(self) -> bytes:
        """打包RTP数据包"""
        # 构建第一个字节: V(2) + P(1) + X(1) + CC(4)
        byte0 = (self.version << 6) | (self.padding << 5) | \
                (self.extension << 4) | self.csrc_count
        
        # 构建第二个字节: M(1) + PT(7)
        byte1 = (self.marker << 7) | self.payload_type
        
        # 打包固定头
        header = struct.pack(
            '!BBHII',
            byte0,
            byte1,
            self.sequence_number,
            self.timestamp,
            self.ssrc
        )
        
        return header + self.payload
    
    @staticmethod
    def unpack(data: bytes) -> 'RTPPacket':
        """解包RTP数据包"""
        if len(data) < RTPPacket.FIXED_HEADER_SIZE:
            raise ValueError("Invalid RTP packet size")
        
        packet = RTPPacket()
        
        # 解析固定头
        byte0, byte1, seq, ts, ssrc = struct.unpack('!BBHII', data[:12])
        
        packet.version = (byte0 >> 6) & 0x03
        packet.padding = (byte0 >> 5) & 0x01
        packet.extension = (byte0 >> 4) & 0x01
        packet.csrc_count = byte0 & 0x0F
        packet.marker = (byte1 >> 7) & 0x01
        packet.payload_type = byte1 & 0x7F
        packet.sequence_number = seq
        packet.timestamp = ts
        packet.ssrc = ssrc
        packet.payload = data[12:]
        
        return packet


class RTCPPacket:
    """RTCP数据包结构"""
    
    # RTCP包类型
    SR = 200  # Sender Report
    RR = 201  # Receiver Report
    SDES = 202  # Source Description
    BYE = 203  # Goodbye
    APP = 204  # Application Defined
    
    def __init__(self, packet_type: int):
        self.version = 2
        self.padding = 0
        self.count = 0
        self.packet_type = packet_type
        self.length = 0
        self.ssrc = 0
        self.payload = b''


class JitterBuffer:
    """
    抖动缓冲器
    Jitter Buffer
    
    用于平滑网络抖动，重排乱序数据包
    """
    
    def __init__(self, size_ms: int = 100):
        self.size_ms = size_ms
        self.buffer: Dict[int, RTPPacket] = {}
        self.last_seq = -1
        self.lock = threading.Lock()
    
    def add_packet(self, packet: RTPPacket) -> bool:
        """添加数据包到缓冲区"""
        with self.lock:
            self.buffer[packet.sequence_number] = packet
            return True
    
    def get_next_packet(self) -> Optional[RTPPacket]:
        """获取下一个有序数据包"""
        with self.lock:
            if not self.buffer:
                return None
            
            # 查找下一个期望的序列号
            expected_seq = (self.last_seq + 1) & 0xFFFF
            
            if expected_seq in self.buffer:
                packet = self.buffer.pop(expected_seq)
                self.last_seq = expected_seq
                return packet
            
            # 如果缓冲区过大，跳过丢失的包
            if len(self.buffer) > 10:
                min_seq = min(self.buffer.keys())
                packet = self.buffer.pop(min_seq)
                self.last_seq = min_seq
                return packet
            
            return None


class RTPAdapter(IMediaTransport):
    """
    RTP/RTCP协议适配器实现
    RTP/RTCP Protocol Adapter Implementation
    """
    
    def __init__(self):
        self.config: Optional[TransportConfig] = None
        self.rtp_socket: Optional[socket.socket] = None
        self.rtcp_socket: Optional[socket.socket] = None
        self.running = False
        self.receive_thread: Optional[threading.Thread] = None
        self.rtcp_thread: Optional[threading.Thread] = None
        
        # RTP状态
        self.sequence_number = 0
        self.ssrc = int(time.time() * 1000) & 0xFFFFFFFF
        self.timestamp_offset = 0
        
        # 统计信息
        self.stats = TransportStats()
        
        # 抖动缓冲
        self.jitter_buffer = JitterBuffer(100)
        
        # 回调函数
        self.media_callback: Optional[Callable[[MediaPacket], None]] = None
        
        # 锁
        self.lock = threading.Lock()
    
    def initialize(self, config: TransportConfig) -> bool:
        """初始化RTP传输"""
        try:
            self.config = config
            
            # 创建RTP socket (UDP)
            self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.rtp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 绑定本地端口
            if config.local_port > 0:
                self.rtp_socket.bind(('0.0.0.0', config.local_port))
            else:
                self.rtp_socket.bind(('0.0.0.0', 0))
            
            # 创建RTCP socket (RTP端口 + 1)
            self.rtcp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            rtcp_port = self.rtp_socket.getsockname()[1] + 1
            self.rtcp_socket.bind(('0.0.0.0', rtcp_port))
            
            # 从协议参数中读取RTP配置
            rtp_config = config.protocol_params.get('rtp', {})
            self.ssrc = rtp_config.get('ssrc', self.ssrc)
            
            # 启动接收线程
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            # 启动RTCP线程
            self.rtcp_thread = threading.Thread(target=self._rtcp_loop)
            self.rtcp_thread.daemon = True
            self.rtcp_thread.start()
            
            return True
            
        except Exception as e:
            print(f"RTP initialization failed: {e}")
            return False
    
    def send_media_data(self, packet: MediaPacket) -> bool:
        """发送媒体数据"""
        try:
            if not self.rtp_socket or not self.config:
                return False
            
            # 创建RTP包
            rtp_packet = RTPPacket()
            rtp_packet.payload_type = packet.payload_type or 96
            rtp_packet.sequence_number = self.sequence_number
            rtp_packet.timestamp = int(packet.timestamp / 1000 * 90)  # 转换为90kHz
            rtp_packet.ssrc = self.ssrc
            rtp_packet.marker = 1 if packet.is_key_frame else 0
            rtp_packet.payload = packet.payload
            
            # 打包并发送
            data = rtp_packet.pack()
            self.rtp_socket.sendto(
                data,
                (self.config.server_address, self.config.server_port)
            )
            
            # 更新统计
            with self.lock:
                self.stats.packets_sent += 1
                self.stats.bytes_sent += len(data)
                self.sequence_number = (self.sequence_number + 1) & 0xFFFF
                self.stats.last_update_time = time.time()
            
            return True
            
        except Exception as e:
            print(f"RTP send failed: {e}")
            return False
    
    def _receive_loop(self):
        """接收循环"""
        self.rtp_socket.settimeout(1.0)
        
        while self.running:
            try:
                data, addr = self.rtp_socket.recvfrom(65536)
                
                # 解析RTP包
                rtp_packet = RTPPacket.unpack(data)
                
                # 添加到抖动缓冲
                self.jitter_buffer.add_packet(rtp_packet)
                
                # 从缓冲区获取有序包
                ordered_packet = self.jitter_buffer.get_next_packet()
                while ordered_packet:
                    self._process_rtp_packet(ordered_packet)
                    ordered_packet = self.jitter_buffer.get_next_packet()
                
                # 更新统计
                with self.lock:
                    self.stats.packets_received += 1
                    self.stats.bytes_received += len(data)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"RTP receive error: {e}")
    
    def _process_rtp_packet(self, rtp_packet: RTPPacket):
        """处理RTP数据包"""
        if self.media_callback:
            # 转换为MediaPacket
            media_packet = MediaPacket(
                payload=rtp_packet.payload,
                timestamp=int(rtp_packet.timestamp / 90 * 1000),  # 转回微秒
                media_type=MediaType.VIDEO,  # 根据payload_type判断
                codec_type=self._get_codec_type(rtp_packet.payload_type),
                is_key_frame=(rtp_packet.marker == 1),
                sequence_number=rtp_packet.sequence_number,
                ssrc=rtp_packet.ssrc,
                payload_type=rtp_packet.payload_type
            )
            
            self.media_callback(media_packet)
    
    def _rtcp_loop(self):
        """RTCP循环 - 定期发送Sender Report"""
        while self.running:
            try:
                time.sleep(5)  # 每5秒发送一次SR
                self._send_sender_report()
            except Exception as e:
                if self.running:
                    print(f"RTCP error: {e}")
    
    def _send_sender_report(self):
        """发送RTCP Sender Report"""
        # 简化实现，实际应按RFC 3550构建完整SR包
        pass
    
    def _get_codec_type(self, payload_type: int):
        """根据payload type获取codec类型"""
        from ...core.models import CodecType
        
        # 标准RTP payload types
        codec_map = {
            96: CodecType.H264,
            97: CodecType.H265,
            98: CodecType.VP8,
            99: CodecType.VP9,
        }
        
        return codec_map.get(payload_type, CodecType.H264)
    
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
        # RTP层不直接控制编码参数，需通过上层编码器
        return True
    
    def close(self) -> bool:
        """关闭连接"""
        self.running = False
        
        if self.receive_thread:
            self.receive_thread.join(timeout=2)
        
        if self.rtcp_thread:
            self.rtcp_thread.join(timeout=2)
        
        if self.rtp_socket:
            self.rtp_socket.close()
        
        if self.rtcp_socket:
            self.rtcp_socket.close()
        
        return True
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.running and self.rtp_socket is not None
    
    def get_protocol_name(self) -> str:
        """获取协议名称"""
        return "RTP/RTCP"
