"""
传输统计信息模型
Transport Statistics Model
"""
from dataclasses import dataclass, field
from typing import Dict, Any
import time


@dataclass
class TransportStats:
    """
    传输层统计信息
    Transport Layer Statistics
    
    用于QoS监控和自适应优化决策
    """
    
    # 已发送字节数
    bytes_sent: int = 0
    
    # 已接收字节数
    bytes_received: int = 0
    
    # 已发送包数
    packets_sent: int = 0
    
    # 已接收包数
    packets_received: int = 0
    
    # 丢包数
    packets_lost: int = 0
    
    # 抖动(毫秒)
    jitter: float = 0.0
    
    # 往返时延RTT(毫秒)
    rtt: float = 0.0
    
    # 实时码率(kbps)
    bitrate: float = 0.0
    
    # 丢包率(0-1)
    loss_rate: float = 0.0
    
    # 统计开始时间戳
    start_time: float = field(default_factory=time.time)
    
    # 最后更新时间戳
    last_update_time: float = field(default_factory=time.time)
    
    # 扩展统计信息
    extended_stats: Dict[str, Any] = field(default_factory=dict)
    
    def update_loss_rate(self):
        """更新丢包率"""
        total_packets = self.packets_sent + self.packets_lost
        if total_packets > 0:
            self.loss_rate = self.packets_lost / total_packets
        else:
            self.loss_rate = 0.0
    
    def update_bitrate(self):
        """更新实时码率"""
        time_elapsed = self.last_update_time - self.start_time
        if time_elapsed > 0:
            # 计算平均码率 (bytes * 8 / 1000 / seconds)
            self.bitrate = (self.bytes_sent * 8) / (time_elapsed * 1000)
        else:
            self.bitrate = 0.0
    
    def reset(self):
        """重置统计信息"""
        self.bytes_sent = 0
        self.bytes_received = 0
        self.packets_sent = 0
        self.packets_received = 0
        self.packets_lost = 0
        self.jitter = 0.0
        self.rtt = 0.0
        self.bitrate = 0.0
        self.loss_rate = 0.0
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.extended_stats.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "packets_lost": self.packets_lost,
            "jitter": self.jitter,
            "rtt": self.rtt,
            "bitrate": self.bitrate,
            "loss_rate": self.loss_rate,
            "duration": self.last_update_time - self.start_time,
            "extended_stats": self.extended_stats
        }


@dataclass
class QoSMetrics:
    """
    QoS质量指标
    Quality of Service Metrics
    """
    
    # 网络质量评分 (0-100)
    network_score: float = 100.0
    
    # MOS评分 (1-5)
    mos_score: float = 5.0
    
    # 卡顿次数
    stall_count: int = 0
    
    # 卡顿总时长(秒)
    stall_duration: float = 0.0
    
    # 首帧延迟(毫秒)
    first_frame_delay: float = 0.0
    
    # 当前帧率
    current_fps: float = 0.0
    
    # 目标帧率
    target_fps: float = 30.0
    
    # 当前分辨率
    current_resolution: str = "1280x720"
    
    # 清晰度切换次数
    quality_switch_count: int = 0
    
    def calculate_network_score(self, stats: TransportStats) -> float:
        """
        计算网络质量评分
        基于丢包率、RTT、抖动的综合评估
        """
        score = 100.0
        
        # 丢包率影响 (最多扣50分)
        if stats.loss_rate > 0:
            score -= min(50, stats.loss_rate * 500)
        
        # RTT影响 (最多扣30分)
        if stats.rtt > 100:
            score -= min(30, (stats.rtt - 100) / 10)
        
        # 抖动影响 (最多扣20分)
        if stats.jitter > 20:
            score -= min(20, (stats.jitter - 20) / 5)
        
        self.network_score = max(0, score)
        return self.network_score
    
    def calculate_mos_score(self) -> float:
        """
        计算MOS评分 (Mean Opinion Score)
        基于网络质量评分的映射
        """
        if self.network_score >= 90:
            self.mos_score = 5.0  # 优秀
        elif self.network_score >= 80:
            self.mos_score = 4.0  # 良好
        elif self.network_score >= 60:
            self.mos_score = 3.0  # 中等
        elif self.network_score >= 40:
            self.mos_score = 2.0  # 较差
        else:
            self.mos_score = 1.0  # 极差
        
        return self.mos_score
