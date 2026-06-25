"""
将 logo.svg 的波形图案渲染为 Windows .ico 图标文件
"""
from PIL import Image, ImageDraw
import os

def create_icon(output_path=None):
    """根据 logo.svg 的波形样式生成多尺寸 .ico"""
    if output_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(os.path.dirname(script_dir), "assets", "logo.ico")
    sizes = [256, 128, 64, 48, 32, 16]

    # 渐变色：#8a2387 → #e94057 → #f27121
    gradient_colors = [
        (138, 35, 135),   # #8a2387
        (180, 40, 100),   # 中间色
        (233, 64, 87),    # #e94057
        (242, 113, 33),   # #f27121
    ]

    # 波形路径点（简化自 SVG path）
    wave_points = [
        (25, 135), (35, 135), (40, 65), (50, 65),
        (60, 65), (65, 135), (75, 135), (85, 135),
        (90, 80), (100, 80), (110, 80), (115, 135),
        (125, 135), (135, 135), (140, 65), (150, 65),
        (160, 65), (165, 135), (175, 135),
    ]

    images = []
    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 缩放坐标到目标尺寸
        scale = size / 200
        scaled = [(int(x * scale), int(y * scale)) for x, y in wave_points]

        # 绘制波形线条（带渐变色）
        line_width = max(2, int(14 * scale))
        for i in range(len(scaled) - 1):
            # 根据水平位置计算渐变色
            t = (scaled[i][0] + scaled[i+1][0]) / (2 * size)
            if t < 0.33:
                c = gradient_colors[0]
            elif t < 0.5:
                c = gradient_colors[1]
            elif t < 0.75:
                c = gradient_colors[2]
            else:
                c = gradient_colors[3]

            draw.line([scaled[i], scaled[i+1]], fill=c, width=line_width)

        images.append(img)

    # 保存为 .ico
    images[0].save(
        output_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"✅ 图标已生成: {output_path} ({os.path.getsize(output_path)} bytes)")


if __name__ == "__main__":
    create_icon()
