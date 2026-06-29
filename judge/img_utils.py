import os
import io
from PIL import Image


def _compress_image(file_path: str, max_size: int = 5 * 1024 * 1024) -> str:
    """将超过 max_size 的图片压缩到限制以内，返回（可能是压缩后的）文件路径。

    压缩策略：
    1. 先尝试降低 JPEG quality（从 85 开始，最低 20）；
    2. 若仍然超限，则逐步缩小分辨率（每次缩为 80%），同时继续降 quality。

    压缩后的文件保存到 .trans/ 目录下，原文件不会被修改。

    Args:
        file_path: 图片文件的绝对路径。
        max_size: 最大允许字节数，默认 5 MB。

    Returns:
        若原图未超限，返回原路径；否则返回压缩后文件的绝对路径。
    """
    if os.path.getsize(file_path) <= max_size:
        return file_path

    print(f"图片文件超过 {max_size / 1024 / 1024:.0f}MB，开始压缩: {file_path}")

    # 准备输出目录
    trans_dir = os.path.join(os.path.dirname(file_path), ".trans")
    os.makedirs(trans_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    out_path = os.path.join(trans_dir, f"{base_name}_compressed.jpg")

    # 缓存命中：若压缩文件已存在且不早于源文件，直接返回
    if os.path.isfile(out_path) and os.path.getmtime(out_path) >= os.path.getmtime(file_path):
        print(f"图片压缩缓存命中，跳过压缩: {out_path}")
        return out_path

    with Image.open(file_path) as img:
        img = img.convert("RGB")
        width, height = img.size

        # 第一阶段：只降 quality
        for quality in range(85, 19, -5):
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            if buf.tell() <= max_size:
                with open(out_path, "wb") as f:
                    f.write(buf.getvalue())
                print(f"图片压缩完成 (quality={quality}): {out_path}")
                return out_path

        # 第二阶段：缩小分辨率 + 降 quality
        scale = 0.8
        for _ in range(10):
            new_w = int(width * scale)
            new_h = int(height * scale)
            if new_w < 100 or new_h < 100:
                break
            resized = img.resize((new_w, new_h), Image.LANCZOS)
            for quality in range(70, 19, -5):
                buf = io.BytesIO()
                resized.save(buf, format="JPEG", quality=quality, optimize=True)
                if buf.tell() <= max_size:
                    with open(out_path, "wb") as f:
                        f.write(buf.getvalue())
                    print(
                        f"图片压缩完成 (scale={scale:.2f}, quality={quality}): {out_path}"
                    )
                    return out_path
            scale *= 0.8

    # 兜底：用最低参数强制保存
    with Image.open(file_path) as img:
        img = img.convert("RGB")
        new_w = int(img.width * scale)
        new_h = int(img.height * scale)
        resized = img.resize((max(new_w, 100), max(new_h, 100)), Image.LANCZOS)
        resized.save(out_path, format="JPEG", quality=20, optimize=True)
    print(f"警告: 图片压缩到最低质量仍可能超限: {out_path}")
    return out_path