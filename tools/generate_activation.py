"""
FluxaVision 授权码生成工具 (授权平台使用)

使用方法:
  python generate_activation.py <硬件指纹> <路数> <天数> [私钥文件路径]

示例:
  python generate_activation.py A1B2C3D4E5F6A7B8 4 365
  python generate_activation.py A1B2C3D4E5F6A7B8 8 365 ../data/private_key.hex
  python generate_activation.py A1B2C3D4E5F6A7B8 16 3650 my_key.hex

参数说明:
  硬件指纹 - 客户从软件激活页面获取的32位硬件指纹
  路数     - 授权的RTSP视频通道数 (摄像头数量)
  天数     - 授权的有效天数
  私钥文件 - Ed25519私钥HEX文件路径 (默认: ../data/private_key.hex)

输出:
  激活码: FLUXA.{payload}.{signature}
  以及解析后的明文信息
"""
import sys
import os

# 确保能导入 backend 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from license_crypto import sign_activation_code, extract_code_info


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        print("\n错误: 参数不足")
        print("用法: python generate_activation.py <硬件指纹> <路数> <天数> [私钥文件]")
        sys.exit(1)

    fingerprint = sys.argv[1].strip().upper()
    channels = int(sys.argv[2])
    days = int(sys.argv[3])
    key_file = sys.argv[4] if len(sys.argv) > 4 else os.path.join(
        os.path.dirname(__file__), "..", "data", "private_key.hex"
    )

    # 参数校验
    if len(fingerprint) < 8:
        print(f"错误: 硬件指纹太短 ({len(fingerprint)} 位, 至少需要8位)")
        sys.exit(1)
    if channels < 1 or channels > 999:
        print(f"错误: 路数无效 ({channels}, 范围 1-999)")
        sys.exit(1)
    if days < 1 or days > 36500:
        print(f"错误: 天数无效 ({days}, 范围 1-36500)")
        sys.exit(1)

    # 读取私钥
    if not os.path.exists(key_file):
        print(f"错误: 私钥文件不存在: {key_file}")
        print("请确保私钥文件在正确位置")
        sys.exit(1)

    with open(key_file, "r") as f:
        private_key_hex = f.read().strip()

    if len(private_key_hex) != 64:
        print(f"错误: 私钥格式无效 (长度 {len(private_key_hex)}, 期望64个HEX字符 = 32字节)")
        sys.exit(1)

    # 生成激活码
    print("=" * 60)
    print("FluxaVision 授权码生成器")
    print("=" * 60)
    print(f"\n  硬件指纹: {fingerprint[:8]}{'*' * (len(fingerprint) - 8)}")
    print(f"  授权路数: {channels} 路")
    print(f"  授权天数: {days} 天")

    activation_code = sign_activation_code(fingerprint, channels, days, private_key_hex)

    print(f"\n{'─' * 60}")
    print(f"  激活码:")
    print(f"  {activation_code}")
    print(f"{'─' * 60}")

    # 解析确认
    info = extract_code_info(activation_code)
    print(f"\n  解析确认:")
    print(f"    绑定指纹: {info.get('fingerprint', '?')}")
    print(f"    授权路数: {info.get('channels', '?')} 路")
    print(f"    授权天数: {info.get('days', '?')} 天")
    print(f"    签发时间: {info.get('issuedDate', '?')}")
    print(f"\n  激活码长度: {len(activation_code)} 字符")
    print("=" * 60)


if __name__ == "__main__":
    main()
