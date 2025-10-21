"""
协议策略选择器
Protocol Strategy Selector

基于网络条件和场景自动选择最优协议
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from ..core.models import ProtocolType, TransportStats


class ScenarioType(Enum):
    """应用场景类型"""
    REALTIME_CALL = "realtime_call"  # 实时音视频通话
    LIVE_PUSH = "live_push"  # 直播推流
    LIVE_PULL = "live_pull"  # 直播拉流
    VOD = "vod"  # 点播
    SURVEILLANCE = "surveillance"  # 监控
    SCREEN_SHARE = "screen_share"  # 屏幕共享


class NetworkQuality(Enum):
    """网络质量等级"""
    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"  # 良好
    FAIR = "fair"  # 中等
    POOR = "poor"  # 较差
    VERY_POOR = "very_poor"  # 极差


@dataclass
class NetworkCondition:
    """
    网络条件
    Network Condition
    """
    # RTT往返时延(毫秒)
    rtt: float = 0
    
    # 丢包率(0-1)
    loss_rate: float = 0
    
    # 抖动(毫秒)
    jitter: float = 0
    
    # 带宽(kbps)
    bandwidth: float = 0
    
    # 是否在NAT后
    behind_nat: bool = False
    
    # 是否移动网络
    is_mobile: bool = False
    
    def get_quality(self) -> NetworkQuality:
        """
        评估网络质量
        
        Returns:
            NetworkQuality: 网络质量等级
        """
        score = 100.0
        
        # RTT影响
        if self.rtt > 300:
            score -= 40
        elif self.rtt > 150:
            score -= 20
        elif self.rtt > 50:
            score -= 10
        
        # 丢包率影响
        if self.loss_rate > 0.1:
            score -= 40
        elif self.loss_rate > 0.05:
            score -= 25
        elif self.loss_rate > 0.01:
            score -= 10
        
        # 抖动影响
        if self.jitter > 100:
            score -= 20
        elif self.jitter > 50:
            score -= 10
        
        # 根据评分返回等级
        if score >= 90:
            return NetworkQuality.EXCELLENT
        elif score >= 75:
            return NetworkQuality.GOOD
        elif score >= 60:
            return NetworkQuality.FAIR
        elif score >= 40:
            return NetworkQuality.POOR
        else:
            return NetworkQuality.VERY_POOR


class ProtocolSelector:
    """
    协议选择器
    Protocol Selector
    
    基于场景和网络条件选择最优协议
    """
    
    # 场景-协议映射表
    SCENARIO_PROTOCOL_MAP = {
        ScenarioType.REALTIME_CALL: {
            NetworkQuality.EXCELLENT: ProtocolType.WEBRTC,
            NetworkQuality.GOOD: ProtocolType.WEBRTC,
            NetworkQuality.FAIR: ProtocolType.SRT,
            NetworkQuality.POOR: ProtocolType.SRT,
            NetworkQuality.VERY_POOR: ProtocolType.SRT,
        },
        ScenarioType.LIVE_PUSH: {
            NetworkQuality.EXCELLENT: ProtocolType.RTMP,
            NetworkQuality.GOOD: ProtocolType.RTMP,
            NetworkQuality.FAIR: ProtocolType.SRT,
            NetworkQuality.POOR: ProtocolType.SRT,
            NetworkQuality.VERY_POOR: ProtocolType.SRT,
        },
        ScenarioType.LIVE_PULL: {
            NetworkQuality.EXCELLENT: ProtocolType.HLS,
            NetworkQuality.GOOD: ProtocolType.HLS,
            NetworkQuality.FAIR: ProtocolType.HLS,
            NetworkQuality.POOR: ProtocolType.HLS,
            NetworkQuality.VERY_POOR: ProtocolType.HLS,
        },
        ScenarioType.VOD: {
            NetworkQuality.EXCELLENT: ProtocolType.HLS,
            NetworkQuality.GOOD: ProtocolType.HLS,
            NetworkQuality.FAIR: ProtocolType.HLS,
            NetworkQuality.POOR: ProtocolType.HLS,
            NetworkQuality.VERY_POOR: ProtocolType.HLS,
        },
        ScenarioType.SURVEILLANCE: {
            NetworkQuality.EXCELLENT: ProtocolType.RTSP,
            NetworkQuality.GOOD: ProtocolType.RTSP,
            NetworkQuality.FAIR: ProtocolType.RTSP,
            NetworkQuality.POOR: ProtocolType.HLS,
            NetworkQuality.VERY_POOR: ProtocolType.HLS,
        },
        ScenarioType.SCREEN_SHARE: {
            NetworkQuality.EXCELLENT: ProtocolType.WEBRTC,
            NetworkQuality.GOOD: ProtocolType.WEBRTC,
            NetworkQuality.FAIR: ProtocolType.WEBRTC,
            NetworkQuality.POOR: ProtocolType.SRT,
            NetworkQuality.VERY_POOR: ProtocolType.SRT,
        },
    }
    
    @classmethod
    def select_protocol(cls, scenario: ScenarioType, 
                       network: NetworkCondition) -> ProtocolType:
        """
        选择最优协议
        
        Args:
            scenario: 应用场景
            network: 网络条件
            
        Returns:
            ProtocolType: 推荐的协议类型
        """
        # 获取网络质量
        quality = network.get_quality()
        
        # 从映射表获取推荐协议
        if scenario in cls.SCENARIO_PROTOCOL_MAP:
            protocol_map = cls.SCENARIO_PROTOCOL_MAP[scenario]
            if quality in protocol_map:
                return protocol_map[quality]
        
        # 默认返回RTP
        return ProtocolType.RTP
    
    @classmethod
    def should_switch_protocol(cls, current_protocol: ProtocolType,
                              scenario: ScenarioType,
                              network: NetworkCondition) -> tuple[bool, Optional[ProtocolType]]:
        """
        判断是否需要切换协议
        
        Args:
            current_protocol: 当前使用的协议
            scenario: 应用场景
            network: 网络条件
            
        Returns:
            tuple: (是否需要切换, 推荐的新协议)
        """
        # 获取推荐协议
        recommended = cls.select_protocol(scenario, network)
        
        # 如果推荐协议与当前协议不同，建议切换
        if recommended != current_protocol:
            # 检查网络质量是否达到切换阈值
            quality = network.get_quality()
            
            # 网络质量差时立即切换，好转时延迟切换(避免频繁切换)
            if quality in [NetworkQuality.POOR, NetworkQuality.VERY_POOR]:
                return True, recommended
            
            # 网络质量好转，但需要连续稳定
            # 这里简化处理，实际应用中需要维护历史状态
            return False, None
        
        return False, None
    
    @classmethod
    def get_protocol_priority(cls, scenario: ScenarioType) -> list[ProtocolType]:
        """
        获取指定场景下的协议优先级列表
        
        Args:
            scenario: 应用场景
            
        Returns:
            list: 协议优先级列表(从高到低)
        """
        if scenario not in cls.SCENARIO_PROTOCOL_MAP:
            return []
        
        protocol_map = cls.SCENARIO_PROTOCOL_MAP[scenario]
        
        # 按网络质量从好到差获取协议
        priorities = []
        for quality in [NetworkQuality.EXCELLENT, NetworkQuality.GOOD, 
                       NetworkQuality.FAIR, NetworkQuality.POOR, 
                       NetworkQuality.VERY_POOR]:
            if quality in protocol_map:
                protocol = protocol_map[quality]
                if protocol not in priorities:
                    priorities.append(protocol)
        
        return priorities


def create_network_condition_from_stats(stats: TransportStats, 
                                       behind_nat: bool = False,
                                       is_mobile: bool = False) -> NetworkCondition:
    """
    从传输统计信息创建网络条件
    
    Args:
        stats: 传输统计信息
        behind_nat: 是否在NAT后
        is_mobile: 是否移动网络
        
    Returns:
        NetworkCondition: 网络条件
    """
    return NetworkCondition(
        rtt=stats.rtt,
        loss_rate=stats.loss_rate,
        jitter=stats.jitter,
        bandwidth=stats.bitrate,
        behind_nat=behind_nat,
        is_mobile=is_mobile
    )
