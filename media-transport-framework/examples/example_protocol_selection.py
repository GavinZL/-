"""
示例2: 协议自动选择和QoS优化
Example 2: Auto Protocol Selection and QoS Optimization
"""
import sys
import os
import time

# 添加框架路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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


def print_section(title):
    """打印章节标题"""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}\n")


def main():
    print_section("Example 2: 协议自动选择与QoS优化")
    
    # ===== 场景1: 优秀网络 - 实时通话 =====
    print("场景1: 优秀网络环境下的实时通话")
    print("-" * 60)
    
    network_excellent = NetworkCondition(
        rtt=30.0,
        loss_rate=0.005,
        jitter=5.0,
        bandwidth=5000.0,
        behind_nat=True,
        is_mobile=False
    )
    
    quality = network_excellent.get_quality()
    print(f"网络质量: {quality.value}")
    print(f"  - RTT: {network_excellent.rtt}ms")
    print(f"  - 丢包率: {network_excellent.loss_rate:.2%}")
    print(f"  - 抖动: {network_excellent.jitter}ms")
    print(f"  - 带宽: {network_excellent.bandwidth}kbps")
    
    # 选择协议
    selected_protocol = ProtocolSelector.select_protocol(
        ScenarioType.REALTIME_CALL,
        network_excellent
    )
    print(f"\n推荐协议: {selected_protocol.value.upper()}")
    
    # ===== 场景2: 较差网络 - 直播推流 =====
    print_section("场景2: 较差网络环境下的直播推流")
    
    network_poor = NetworkCondition(
        rtt=200.0,
        loss_rate=0.08,
        jitter=80.0,
        bandwidth=1500.0,
        behind_nat=False,
        is_mobile=True
    )
    
    quality = network_poor.get_quality()
    print(f"网络质量: {quality.value}")
    print(f"  - RTT: {network_poor.rtt}ms")
    print(f"  - 丢包率: {network_poor.loss_rate:.2%}")
    print(f"  - 抖动: {network_poor.jitter}ms")
    print(f"  - 带宽: {network_poor.bandwidth}kbps")
    
    selected_protocol = ProtocolSelector.select_protocol(
        ScenarioType.LIVE_PUSH,
        network_poor
    )
    print(f"\n推荐协议: {selected_protocol.value.upper()}")
    
    # ===== 场景3: QoS自适应优化 =====
    print_section("场景3: QoS自适应优化演示")
    
    # 创建RTP传输
    config = TransportConfig(
        protocol_type=ProtocolType.RTP,
        transport_mode=TransportMode.UDP,
        server_address="127.0.0.1",
        server_port=5004,
        local_port=5000
    )
    
    print("1. 创建RTP传输...")
    transport = ProtocolFactory.create(ProtocolType.RTP, config)
    if not transport:
        print("   ✗ 创建失败")
        return
    print("   ✓ 创建成功")
    
    # 创建QoS管理器
    print("\n2. 创建QoS管理器...")
    qos_config = QoSConfig(
        enable_adaptive_bitrate=True,
        target_bitrate=2000,
        min_bitrate=500,
        max_bitrate=4000,
        enable_dynamic_fec=True,
        stats_update_interval=1
    )
    
    qos_manager = QoSManager(transport, qos_config)
    
    # 设置回调
    def on_quality_change(metrics):
        print(f"\n   [QoS] 网络评分: {metrics.network_score:.1f}, "
              f"MOS: {metrics.mos_score:.1f}")
    
    def on_bitrate_change(bitrate):
        print(f"   [码率] 调整为: {bitrate} kbps")
    
    qos_manager.set_quality_change_callback(on_quality_change)
    qos_manager.set_bitrate_change_callback(on_bitrate_change)
    
    print("   ✓ QoS管理器已创建")
    print(f"   - 目标码率: {qos_config.target_bitrate} kbps")
    print(f"   - 码率范围: {qos_config.min_bitrate}-{qos_config.max_bitrate} kbps")
    print(f"   - 自适应码率: {'启用' if qos_config.enable_adaptive_bitrate else '禁用'}")
    print(f"   - 动态FEC: {'启用' if qos_config.enable_dynamic_fec else '禁用'}")
    
    # 启动QoS监控
    print("\n3. 启动QoS监控 (模拟5秒)...")
    qos_manager.start()
    
    # 模拟传输
    for i in range(5):
        packet = MediaPacket(
            payload=bytes([i % 256 for _ in range(1000)]),
            timestamp=i * 40000,
            media_type=MediaType.VIDEO,
            codec_type=CodecType.H264,
            is_key_frame=(i % 30 == 0),
            sequence_number=i
        )
        transport.send_media_data(packet)
        time.sleep(1)
    
    # 获取QoS报告
    print("\n4. QoS报告:")
    report = qos_manager.get_report()
    print(f"   网络评分: {report['network_score']:.1f}")
    print(f"   MOS评分: {report['mos_score']:.1f}")
    print(f"   当前码率: {report['current_bitrate']} kbps")
    print(f"   发送包数: {report['stats']['packets_sent']}")
    print(f"   发送字节: {report['stats']['bytes_sent']}")
    
    # 停止QoS管理
    qos_manager.stop()
    transport.close()
    print("\n   ✓ QoS管理器已停止")
    
    # ===== 场景4: 协议切换决策 =====
    print_section("场景4: 协议切换决策")
    
    current_protocol = ProtocolType.RTMP
    scenario = ScenarioType.LIVE_PUSH
    
    print(f"当前协议: {current_protocol.value.upper()}")
    print(f"应用场景: {scenario.value}")
    
    # 测试不同网络条件下的切换决策
    test_networks = [
        ("优秀网络", NetworkCondition(rtt=30, loss_rate=0.005, jitter=5, bandwidth=5000)),
        ("良好网络", NetworkCondition(rtt=80, loss_rate=0.02, jitter=20, bandwidth=3000)),
        ("较差网络", NetworkCondition(rtt=200, loss_rate=0.08, jitter=80, bandwidth=1000)),
    ]
    
    for name, network in test_networks:
        should_switch, new_protocol = ProtocolSelector.should_switch_protocol(
            current_protocol, scenario, network
        )
        
        quality = network.get_quality()
        print(f"\n{name} ({quality.value}):")
        print(f"  是否切换: {'是' if should_switch else '否'}")
        if should_switch and new_protocol:
            print(f"  推荐协议: {new_protocol.value.upper()}")
    
    # ===== 场景5: 协议优先级 =====
    print_section("场景5: 不同场景的协议优先级")
    
    scenarios = [
        ScenarioType.REALTIME_CALL,
        ScenarioType.LIVE_PUSH,
        ScenarioType.SURVEILLANCE,
        ScenarioType.SCREEN_SHARE
    ]
    
    for scenario in scenarios:
        priorities = ProtocolSelector.get_protocol_priority(scenario)
        print(f"\n{scenario.value}:")
        for i, protocol in enumerate(priorities, 1):
            print(f"  {i}. {protocol.value.upper()}")
    
    print_section("示例完成")


if __name__ == "__main__":
    main()
