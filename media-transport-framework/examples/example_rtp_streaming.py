"""
示例1: 使用RTP协议发送视频流
Example 1: Send Video Stream using RTP Protocol
"""
import sys
import os
import time

# 添加框架路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import (
    MediaPacket, MediaType, CodecType,
    TransportConfig, ProtocolType, TransportMode, RTPConfig
)
from core.protocol_factory import ProtocolFactory


def main():
    print("=" * 60)
    print("Example 1: RTP Video Streaming")
    print("=" * 60)
    
    # 1. 创建传输配置
    config = TransportConfig(
        protocol_type=ProtocolType.RTP,
        transport_mode=TransportMode.UDP,
        server_address="127.0.0.1",
        server_port=5004,
        local_port=5000,
        protocol_params={
            'rtp': {
                'payload_type': 96,
                'ssrc': 12345678,
                'clock_rate': 90000,
                'jitter_buffer_size': 100,
                'enable_nack': True,
                'enable_fec': False
            }
        }
    )
    
    print(f"\n1. 配置信息:")
    print(f"   协议: {config.protocol_type.value}")
    print(f"   服务器: {config.server_address}:{config.server_port}")
    print(f"   本地端口: {config.local_port}")
    
    # 2. 创建RTP适配器
    print(f"\n2. 创建RTP适配器...")
    rtp_adapter = ProtocolFactory.create(ProtocolType.RTP, config)
    
    if not rtp_adapter:
        print("   ✗ 创建适配器失败")
        return
    
    print(f"   ✓ 适配器创建成功: {rtp_adapter.get_protocol_name()}")
    print(f"   ✓ 连接状态: {'已连接' if rtp_adapter.is_connected() else '未连接'}")
    
    # 3. 注册接收回调
    def on_media_received(packet: MediaPacket):
        print(f"   接收到媒体包: 序列号={packet.sequence_number}, "
              f"时间戳={packet.timestamp}, 大小={packet.size}字节")
    
    rtp_adapter.on_media_data_received(on_media_received)
    
    # 4. 发送模拟视频帧
    print(f"\n3. 发送视频帧...")
    
    for i in range(10):
        # 创建模拟H.264视频帧
        is_key_frame = (i % 30 == 0)  # 每30帧一个关键帧
        payload = b'\x00\x00\x00\x01' + bytes([0x65 if is_key_frame else 0x41]) + \
                  bytes([i % 256 for _ in range(100)])  # 模拟NAL单元
        
        packet = MediaPacket(
            payload=payload,
            timestamp=i * 40000,  # 25fps: 40ms间隔
            media_type=MediaType.VIDEO,
            codec_type=CodecType.H264,
            is_key_frame=is_key_frame,
            sequence_number=i
        )
        
        success = rtp_adapter.send_media_data(packet)
        
        frame_type = "关键帧" if is_key_frame else "普通帧"
        status = "✓" if success else "✗"
        print(f"   {status} 帧 #{i:02d} ({frame_type}): {len(payload)}字节")
        
        time.sleep(0.04)  # 模拟25fps
    
    # 5. 获取传输统计
    print(f"\n4. 传输统计:")
    stats = rtp_adapter.get_transport_stats()
    print(f"   发送包数: {stats.packets_sent}")
    print(f"   发送字节: {stats.bytes_sent}")
    print(f"   接收包数: {stats.packets_received}")
    print(f"   丢包率: {stats.loss_rate:.2%}")
    print(f"   码率: {stats.bitrate:.2f} kbps")
    
    # 6. 关闭连接
    print(f"\n5. 关闭连接...")
    rtp_adapter.close()
    print(f"   ✓ 连接已关闭")
    
    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
