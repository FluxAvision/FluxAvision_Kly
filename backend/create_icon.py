"""
FluxaVision 客流统计系统 - 图标生成脚本

生成 Windows .ico 格式的应用图标（用于exe和安装程序）
"""
import os

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("需要安装 Pillow: pip install Pillow")


def create_icon(output_path: str):
    """创建 FluxaVision 应用图标"""
    if not HAS_PIL:
        # 创建一个简单的占位图标
        print(f"[Icon] PIL不可用，跳过图标生成: {output_path}")
        return

    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    images = []

    for size in sizes:
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 背景圆角矩形
        margin = max(1, size[0] // 16)
        draw.rounded_rectangle(
            [margin, margin, size[0] - margin, size[1] - margin],
            radius=size[0] // 5,
            fill=(0, 217, 255, 255),
        )

        # 深色 "F" 字母
        f_margin = size[0] // 4
        f_width = size[0] // 8
        f_height = size[1] - f_margin * 2
        bar_height = f_height // 4

        draw.rounded_rectangle(
            [f_margin, f_margin, f_margin + f_width, size[1] - f_margin],
            radius=f_width // 3,
            fill=(10, 25, 47, 255),
        )

        bar_x = f_margin + f_width + size[0] // 16
        bar_w = size[0] - bar_x - f_margin
        draw.rounded_rectangle(
            [bar_x, f_margin, bar_x + bar_w, f_margin + bar_height],
            radius=bar_height // 3,
            fill=(10, 25, 47, 255),
        )
        draw.rounded_rectangle(
            [bar_x, f_margin + bar_height + bar_height // 4, bar_x + bar_w, f_margin + bar_height * 2 + bar_height // 4],
            radius=bar_height // 3,
            fill=(10, 25, 47, 255),
        )

        # 保存为 ICO 格式需要多个尺寸
        images.append(img)

    # 保存为 ICO
    if len(images) > 0:
        images[0].save(output_path, format='ICO', sizes=[(s[0], s[1]) for s in sizes], append_images=images[1:])
        print(f"[Icon] 图标已保存: {output_path}")
    else:
        print(f"[Icon] 图标生成失败")


if __name__ == "__main__":
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    os.makedirs(assets_dir, exist_ok=True)
    create_icon(os.path.join(assets_dir, "icon.ico"))
