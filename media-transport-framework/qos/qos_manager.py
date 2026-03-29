"""
QoS管理器
QoS Manager

统一的服务质量管理和自适应优化
"""
import time
import threading
from typing import Optional, Callable, Dict, Any
from ..core.interfaces import IMediaTransport
from ..core.models import TransportStats, QoSMetrics, QoSConfig


class BitrateController:
    """
    码率控制器
    Bitrate Controller
    
    基于网络状况的自适应码率控制
    """
    
    def __init__(self, config: QoSConfig):
        self.config = config
        self.current_bitrate = config.target_bitrate
        self.target_bitrate = config.target_bitrate
        
        # 码率调整状态
        self.last_adjust_time = time.time()
        self.adjust_interval = 1.0  # 调整间隔(秒)
        
        # 带宽探测状态
        self.probing = False
        self.probe_bitrate = 0
    
    def calculate_target_bitrate(self, stats: TransportStats) -> int:
        """
        计算目标码率
        
        Args:
            stats: 传输统计信息
            
        Returns:
            int: 目标码率(kbps)
        """
        current_time = time.time()
        
        # 检查是否到调整时间
        if current_time - self.last_adjust_time < self.adjust_interval:
            return self.current_bitrate
        
        self.last_adjust_time = current_time
        
        # 基于丢包率调整
        if stats.loss_rate > 0.05:
            # 丢包率>5%，快速降低码率
            self.target_bitrate = int(self.current_bitrate * 0.8)
            self.adjust_interval = 0.5  # 加快调整频率
        elif stats.loss_rate > 0.03:
            # 丢包率3-5%，缓慢降低码率
            self.target_bitrate = int(self.current_bitrate * 0.9)
        elif stats.loss_rate < 0.01:
            # 丢包率<1%，尝试提升码率
            if not self.probing:
                self.target_bitrate = int(self.current_bitrate * 1.05)
                self.adjust_interval = 2.0  # 降低调整频率
        
        # 基于RTT调整
        if stats.rtt > 300:
            # RTT过高，降低码率减少延迟
            self.target_bitrate = int(self.target_bitrate * 0.95)
        
        # 限制在配置范围内
        self.target_bitrate = max(self.config.min_bitrate, 
                                 min(self.config.max_bitrate, self.target_bitrate))
        
        self.current_bitrate = self.target_bitrate
        return self.target_bitrate
    
    def reset(self):
        """重置控制器"""
        self.current_bitrate = self.config.target_bitrate
        self.target_bitrate = self.config.target_bitrate
        self.last_adjust_time = time.time()


class FECController:
    """
    FEC前向纠错控制器
    Forward Error Correction Controller
    """
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.redundancy_rate = 0.0  # 冗余率(0-1)
    
    def calculate_redundancy(self, stats: TransportStats) -> float:
        """
        计算FEC冗余率
        
        Args:
            stats: 传输统计信息
            
        Returns:
            float: 冗余率(0-1)
        """
        if not self.enabled:
            return 0.0
        
        loss_rate = stats.loss_rate
        
        # 根据丢包率动态调整FEC冗余
        if loss_rate < 0.01:
            self.redundancy_rate = 0.0
        elif loss_rate < 0.03:
            self.redundancy_rate = 0.05
        elif loss_rate < 0.05:
            self.redundancy_rate = 0.10
        elif loss_rate < 0.10:
            self.redundancy_rate = 0.15
        else:
            self.redundancy_rate = 0.20
        
        return self.redundancy_rate


class QoSManager:
    """
    QoS管理器
    Quality of Service Manager
    
    统一管理传输质量，执行自适应优化
    """
    
    def __init__(self, transport: IMediaTransport, config: QoSConfig):
        self.transport = transport
        self.config = config
        
        # 统计信息
        self.stats = TransportStats()
        self.metrics = QoSMetrics()
        
        # 控制器
        self.bitrate_controller = BitrateController(config)
        self.fec_controller = FECController(config.enable_dynamic_fec)
        
        # 监控线程
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # 回调函数
        self.quality_change_callback: Optional[Callable[[QoSMetrics], None]] = None
        self.bitrate_change_callback: Optional[Callable[[int], None]] = None
    
    def start(self):
        """启动QoS管理"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("QoS Manager started")
    
    def stop(self):
        """停止QoS管理"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("QoS Manager stopped")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 获取传输统计
                self.stats = self.transport.get_transport_stats()
                
                # 计算质量指标
                self.metrics.calculate_network_score(self.stats)
                self.metrics.calculate_mos_score()
                
                # 自适应码率控制
                if self.config.enable_adaptive_bitrate:
                    target_bitrate = self.bitrate_controller.calculate_target_bitrate(self.stats)
                    
                    # 如果码率发生变化，更新传输层
                    if abs(target_bitrate - self.bitrate_controller.current_bitrate) > 100:
                        self.transport.update_qos(bitrate=target_bitrate)
                        
                        # 触发回调
                        if self.bitrate_change_callback:
                            self.bitrate_change_callback(target_bitrate)
                
                # 动态FEC控制
                if self.config.enable_dynamic_fec:
                    redundancy = self.fec_controller.calculate_redundancy(self.stats)
                    # FEC参数更新需要协议层支持
                
                # 触发质量变化回调
                if self.quality_change_callback:
                    self.quality_change_callback(self.metrics)
                
                # 按配置的间隔更新
                time.sleep(self.config.stats_update_interval)
                
            except Exception as e:
                print(f"QoS monitor error: {e}")
    
    def get_metrics(self) -> QoSMetrics:
        """
        获取QoS指标
        
        Returns:
            QoSMetrics: QoS质量指标
        """
        return self.metrics
    
    def get_stats(self) -> TransportStats:
        """
        获取传输统计
        
        Returns:
            TransportStats: 传输统计信息
        """
        return self.stats
    
    def set_quality_change_callback(self, callback: Callable[[QoSMetrics], None]):
        """设置质量变化回调"""
        self.quality_change_callback = callback
    
    def set_bitrate_change_callback(self, callback: Callable[[int], None]):
        """设置码率变化回调"""
        self.bitrate_change_callback = callback
    
    def force_bitrate(self, bitrate: int):
        """
        强制设置码率
        
        Args:
            bitrate: 目标码率(kbps)
        """
        self.bitrate_controller.current_bitrate = bitrate
        self.bitrate_controller.target_bitrate = bitrate
        self.transport.update_qos(bitrate=bitrate)
    
    def get_report(self) -> Dict[str, Any]:
        """
        生成QoS报告
        
        Returns:
            dict: QoS报告
        """
        return {
            "timestamp": time.time(),
            "network_score": self.metrics.network_score,
            "mos_score": self.metrics.mos_score,
            "current_bitrate": self.bitrate_controller.current_bitrate,
            "stats": self.stats.to_dict(),
            "stall_count": self.metrics.stall_count,
            "stall_duration": self.metrics.stall_duration,
            "quality_switch_count": self.metrics.quality_switch_count
        }
