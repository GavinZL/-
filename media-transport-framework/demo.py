#!/usr/bin/env python3
"""
框架功能演示脚本
Framework Demo Script

快速展示框架的核心功能
"""
import sys
import os

# 添加框架路径
sys.path.insert(0, os.path.dirname(__file__))

from core.models import (
    MediaPacket, MediaType, CodecType,
    TransportConfig, ProtocolType, TransportMode,
    QoSConfig
)
from core.protocol_factory import ProtocolFactory
from core.protocol_selector import (
    ProtocolSelector, ScenarioType, NetworkCondition, NetworkQuality
)
from qos import QoSManager


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_protocol_factory():
    """演示协议工厂"""
    print_header("功能1: 协议工厂 - 插件化协议管理")
    
    # 查看已注册的协议
    protocols = ProtocolFactory.get_registered_protocols()
    print("✓ 已注册的协议:")
    for protocol in protocols:
        print(f"  - {protocol.value.upper()}")
    
    # 创建RTP适配器
    print("\n✓ 创建RTP适配器:")
    config = TransportConfig(
        protocol_type=ProtocolType.RTP,
        transport_mode=TransportMode.UDP,
        server_address="127.0.0.1",
        server_port=5004
    )
    
    adapter = ProtocolFactory.create(ProtocolType.RTP, config)
    if adapter:
        print(f"  协议名称: {adapter.get_protocol_name()}")
        print(f"  连接状态: {'已连接' if adapter.is_connected() else '未连接'}")
        adapter.close()


def demo_protocol_selector():
    """演示协议选择器"""
    print_header("功能2: 智能协议选择 - 基于场景和网络条件")
    
    scenarios = [
        ("实时通话", ScenarioType.REALTIME_CALL),
        ("直播推流", ScenarioType.LIVE_PUSH),
        ("监控系统", ScenarioType.SURVEILLANCE)
    ]
    
    networks = [
        ("优秀网络", NetworkCondition(rtt=30, loss_rate=0.005, jitter=5, bandwidth=5000)),
        ("较差网络", NetworkCondition(rtt=200, loss_rate=0.08, jitter=80, bandwidth=1000))
    ]
    
    print("✓ 协议选择矩阵:\n")
    print(f"{'场景':<12} {'网络质量':<12} {'推荐协议':<12}")
    print("-" * 40)
    
    for scenario_name, scenario in scenarios:
        for network_name, network in networks:
            quality = network.get_quality()
            protocol = ProtocolSelector.select_protocol(scenario, network)
            print(f"{scenario_name:<12} {quality.value:<12} {protocol.value.upper():<12}")


def demo_network_quality():
    """演示网络质量评估"""
    print_header("功能3: 网络质量评估 - 5级评分体系")
    
    test_cases = [
        ("办公网络", NetworkCondition(rtt=20, loss_rate=0.001, jitter=3, bandwidth=10000)),
        ("家庭WiFi", NetworkCondition(rtt=50, loss_rate=0.01, jitter=10, bandwidth=5000)),
        ("4G移动网", NetworkCondition(rtt=100, loss_rate=0.03, jitter=30, bandwidth=3000)),
        ("3G弱网", NetworkCondition(rtt=250, loss_rate=0.08, jitter=100, bandwidth=1000)),
        ("极差网络", NetworkCondition(rtt=500, loss_rate=0.15, jitter=200, bandwidth=500))
    ]
    
    print("✓ 网络质量评估结果:\n")
    print(f"{'网络类型':<12} {'RTT(ms)':<10} {'丢包率':<10} {'抖动(ms)':<10} {'质量等级':<12}")
    print("-" * 70)
    
    for name, network in test_cases:
        quality = network.get_quality()
        print(f"{name:<12} {network.rtt:<10.0f} {network.loss_rate*100:<10.2f}% "
              f"{network.jitter:<10.0f} {quality.value:<12}")


def demo_media_packet():
    """演示媒体数据包"""
    print_header("功能4: 统一媒体数据包 - 协议无关封装")
    
    # 创建视频帧
    video_packet = MediaPacket(
        payload=b'\x00\x00\x00\x01\x65' + bytes(100),  # 模拟H.264 IDR帧
        timestamp=1234567890,
        media_type=MediaType.VIDEO,
        codec_type=CodecType.H264,
        is_key_frame=True,
        sequence_number=1
    )
    
    print("✓ 视频数据包:")
    print(f"  媒体类型: {video_packet.media_type.value}")
    print(f"  编码格式: {video_packet.codec_type.value}")
    print(f"  关键帧: {'是' if video_packet.is_key_frame else '否'}")
    print(f"  时间戳: {video_packet.timestamp}")
    print(f"  序列号: {video_packet.sequence_number}")
    print(f"  数据大小: {video_packet.size} 字节")
    
    # 创建音频帧
    audio_packet = MediaPacket(
        payload=bytes(200),
        timestamp=1234567890,
        media_type=MediaType.AUDIO,
        codec_type=CodecType.OPUS,
        sequence_number=1
    )
    
    print("\n✓ 音频数据包:")
    print(f"  媒体类型: {audio_packet.media_type.value}")
    print(f"  编码格式: {audio_packet.codec_type.value}")
    print(f"  数据大小: {audio_packet.size} 字节")


def demo_qos_config():
    """演示QoS配置"""
    print_header("功能5: QoS自适应优化 - 智能码率控制")
    
    qos_config = QoSConfig(
        enable_adaptive_bitrate=True,
        target_bitrate=2000,
        min_bitrate=500,
        max_bitrate=4000,
        enable_dynamic_fec=True,
        stats_update_interval=1
    )
    
    print("✓ QoS配置参数:")
    print(f"  自适应码率: {'启用' if qos_config.enable_adaptive_bitrate else '禁用'}")
    print(f"  目标码率: {qos_config.target_bitrate} kbps")
    print(f"  码率范围: {qos_config.min_bitrate} - {qos_config.max_bitrate} kbps")
    print(f"  动态FEC: {'启用' if qos_config.enable_dynamic_fec else '禁用'}")
    print(f"  更新间隔: {qos_config.stats_update_interval} 秒")
    
    print("\n✓ 自适应策略:")
    print("  - 丢包率 > 5%  → 快速降低码率 (×0.8)")
    print("  - 丢包率 3-5%  → 缓慢降低码率 (×0.9)")
    print("  - 丢包率 < 1%  → 尝试提升码率 (×1.05)")
    print("  - RTT > 300ms  → 降低码率减少延迟")


def demo_protocol_priority():
    """演示协议优先级"""
    print_header("功能6: 协议优先级 - 场景化配置")
    
    scenarios = [
        ("实时通话", ScenarioType.REALTIME_CALL),
        ("直播推流", ScenarioType.LIVE_PUSH),
        ("屏幕共享", ScenarioType.SCREEN_SHARE)
    ]
    
    print("✓ 各场景协议优先级:\n")
    
    for name, scenario in scenarios:
        priorities = ProtocolSelector.get_protocol_priority(scenario)
        print(f"{name}:")
        for i, protocol in enumerate(priorities, 1):
            print(f"  {i}. {protocol.value.upper()}")
        print()


def main():
    """主函数"""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  音视频传输协议框架 - 功能演示".center(66) + "  █")
    print("█" + "  Media Transport Framework Demo".center(66) + "  █")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    try:
        # 演示各项功能
        demo_protocol_factory()
        demo_protocol_selector()
        demo_network_quality()
        demo_media_packet()
        demo_qos_config()
        demo_protocol_priority()
        
        # 总结
        print_header("演示完成")
        print("✓ 框架核心功能已全部展示")
        print("✓ 协议工厂: 插件化管理")
        print("✓ 协议选择: 智能推荐")
        print("✓ 网络评估: 5级评分")
        print("✓ 数据封装: 协议无关")
        print("✓ QoS优化: 自适应控制")
        print("✓ 场景配置: 优先级排序")
        
        print("\n" + "█" * 70)
        print("█" + " " * 68 + "█")
        print("█" + "  感谢使用音视频传输协议框架！".center(62) + "  █")
        print("█" + " " * 68 + "█")
        print("█" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
