import re
from datetime import datetime, date, time as dt_time
import unicodedata


# -------------------- xlsx 辅助函数 --------------------

# openpyxl 默认字体名列表：这些属于 Excel 在不同语言环境下的默认字体，
# 不携带有意义的样式信息，在输出时可以省略。
_XLSX_DEFAULT_FONT_NAMES = {"Calibri", "等线"}


def _get_xlsx_theme_fonts(file_path: str) -> dict:
    """从 xlsx 的 theme1.xml 中提取主题字体名称。

    Excel 主题定义了 majorFont（标题）和 minorFont（正文），
    每种下可有 latin（西文）和按 script 区分的东亚字体（如 Hans → 宋体）。

    Returns:
        {"major": {"latin": "Cambria", "Hans": "宋体", ...},
         "minor": {"latin": "Calibri", "Hans": "宋体", ...}}
        解析失败时返回空 dict。
    """

    import zipfile
    import xml.etree.ElementTree as ET

    result = {}
    try:
        with zipfile.ZipFile(file_path, "r") as z:
            if "xl/theme/theme1.xml" not in z.namelist():
                return result
            theme_xml = z.read("xl/theme/theme1.xml")
    except Exception:
        return result

    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    root = ET.fromstring(theme_xml)

    for role, tag in [("major", "majorFont"), ("minor", "minorFont")]:
        for font_scheme in root.iter(f"{{{ns['a']}}}{tag}"):
            fonts = {}
            latin = font_scheme.find("a:latin", ns)
            if latin is not None and latin.get("typeface"):
                fonts["latin"] = latin.get("typeface")
            ea = font_scheme.find("a:ea", ns)
            if ea is not None and ea.get("typeface"):
                fonts["ea"] = ea.get("typeface")
            for font_elem in font_scheme.findall("a:font", ns):
                script = font_elem.get("script")
                typeface = font_elem.get("typeface")
                if script and typeface:
                    fonts[script] = typeface
            result[role] = fonts

    return result


def _get_xlsx_theme_colors(file_path: str) -> list:
    """从 xlsx 的 theme1.xml 中提取主题配色方案的 RGB 值。

    Excel 主题色在 <a:clrScheme> 中按固定顺序排列：
        index 0  = dk1   (深色1，通常黑色)
        index 1  = lt1   (浅色1，通常白色)
        index 2  = dk2   (深色2)
        index 3  = lt2   (浅色2)
        index 4  = accent1
        index 5  = accent2
        index 6  = accent3
        index 7  = accent4
        index 8  = accent5
        index 9  = accent6
        index 10 = hlink
        index 11 = folHlink

    注意：openpyxl 中 theme 索引 0 对应 lt1、1 对应 dk1（与 XML 顺序
    前两个互换），其余 2-11 按上述 index 2-11 顺序对应。

    Returns:
        长度为 12 的列表，每个元素为 6 位 RGB hex 字符串（如 "4472C4"），
        解析失败时返回空列表。
    """
    import zipfile
    import xml.etree.ElementTree as ET

    try:
        with zipfile.ZipFile(file_path, "r") as z:
            if "xl/theme/theme1.xml" not in z.namelist():
                return []
            theme_xml = z.read("xl/theme/theme1.xml")
    except Exception:
        return []

    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    root = ET.fromstring(theme_xml)

    clr_scheme = root.find(".//a:clrScheme", ns)
    if clr_scheme is None:
        return []

    # XML 中的固定子元素顺序
    tag_order = ["dk1", "lt1", "dk2", "lt2",
                 "accent1", "accent2", "accent3", "accent4",
                 "accent5", "accent6", "hlink", "folHlink"]

    xml_colors = []  # 按 XML 顺序解析
    for tag in tag_order:
        elem = clr_scheme.find(f"a:{tag}", ns)
        if elem is None:
            xml_colors.append(None)
            continue
        # 可能是 <a:srgbClr val="..."/> 或 <a:sysClr ... lastClr="..."/>
        srgb = elem.find("a:srgbClr", ns)
        if srgb is not None:
            xml_colors.append(srgb.get("val", "").upper())
            continue
        sys_clr = elem.find("a:sysClr", ns)
        if sys_clr is not None:
            xml_colors.append(sys_clr.get("lastClr", "").upper())
            continue
        xml_colors.append(None)

    # openpyxl 的 theme 索引映射：theme 0 = lt1, theme 1 = dk1，其余不变
    # xml_colors 顺序: [dk1, lt1, dk2, lt2, accent1, ...]
    # 需要输出:        [lt1, dk1, dk2, lt2, accent1, ...]
    if len(xml_colors) >= 2:
        xml_colors[0], xml_colors[1] = xml_colors[1], xml_colors[0]

    return xml_colors


def _apply_tint(rgb_hex: str, tint: float) -> str:
    """对 6 位 RGB hex 应用 Excel 的 tint 色调偏移。

    tint > 0: 向白色混合（变亮）
    tint < 0: 向黑色混合（变暗）

    Args:
        rgb_hex: 6 位 RGB hex，如 "4472C4"
        tint: -1.0 到 1.0 之间的浮点数

    Returns:
        应用 tint 后的 6 位 RGB hex。
    """
    r = int(rgb_hex[0:2], 16)
    g = int(rgb_hex[2:4], 16)
    b = int(rgb_hex[4:6], 16)

    def _adjust(val, t):
        if t < 0:
            return int(val * (1.0 + t) + 0.5)
        else:
            return int(val * (1.0 - t) + 255 * t + 0.5)

    r = max(0, min(255, _adjust(r, tint)))
    g = max(0, min(255, _adjust(g, tint)))
    b = max(0, min(255, _adjust(b, tint)))

    return f"{r:02X}{g:02X}{b:02X}"


def _resolve_font_name(font, default_font_name: str,
                       theme_fonts: dict):
    """解析单元格的实际字体名称，处理 openpyxl 中 font.name 为 None 的情况。

    解析优先级：
      1. font.name 已显式设置 → 直接使用
      2. font.name 为 None，但 font.scheme 指向 "major"/"minor"
         → 从 theme_fonts 中查找对应的中文字体（Hans）或拉丁字体
      3. font.name 为 None，font.scheme 也为 None
         → 使用 default_font_name（工作簿默认字体），然后尝试
           通过其 scheme 解析主题中文字体

    Args:
        font: openpyxl Font 对象
        default_font_name: 工作簿 styles.xml 中 Font #0 的名称（如 "Calibri"）
        theme_fonts: _get_xlsx_theme_fonts 返回的主题字体字典

    Returns:
        解析出的字体名称，若为默认值（Calibri/等线）则返回 None。
    """
    if font.name:
        # 显式设置了字体名
        resolved = font.name
    elif font.scheme and font.scheme in theme_fonts:
        # font.name 为 None，但 scheme 指向 major/minor
        # 优先取中文字体（Hans），其次取 latin
        t = theme_fonts[font.scheme]
        resolved = t.get("Hans") or t.get("latin")
    else:
        # font.name 和 scheme 都为 None → 使用工作簿默认字体
        # 默认字体自身可能也是 scheme=minor 的主题字体，
        # 需要进一步解析其在中文环境下的真实名称
        resolved = default_font_name
        if resolved and resolved in _XLSX_DEFAULT_FONT_NAMES and theme_fonts:
            # 默认字体名看起来是 Calibri/等线，检查主题中的中文字体
            # Excel 默认字体一般对应 minor
            minor = theme_fonts.get("minor", {})
            hans = minor.get("Hans")
            if hans and hans not in _XLSX_DEFAULT_FONT_NAMES:
                resolved = hans

    if not resolved or resolved in _XLSX_DEFAULT_FONT_NAMES:
        return None
    return resolved


_SENTINEL = object()  # 用于区分"未提供 cached_value"与"cached_value 为 None"


def _format_excel_value(value, number_format: str) -> str:
    """根据 Excel number_format 格式化数值，使输出与单元格显示一致。

    仅对 int / float 类型生效。对于无法识别的格式会 fallback 到默认表示。

    支持的常见格式：
        #,##0  /  #,##0.00        — 千分位分隔
        0%  /  0.00%              — 百分比
        0.00  /  0.0              — 固定小数位
        ¥#,##0  /  $#,##0.00     — 带货币符号
        0.00E+00                  — 科学计数法
    """
    if not isinstance(value, (int, float)):
        return str(value)

    if not number_format or number_format == "General":
        # General 格式：去掉尾零
        return f"{value:g}"

    # ---------- 预处理格式字符串 ----------
    # Excel 格式可能包含多段（正数;负数;零;文本），取正数段
    fmt = number_format.split(";")[0]

    # 去掉颜色标记，如 [Red]、[Color1] 等
    fmt = re.sub(r'\[[A-Za-z]+\d*\]', '', fmt)

    # 去掉条件标记，如 [>100]、[<=0] 等
    fmt = re.sub(r'\[[<>=!]+[^]]*\]', '', fmt)

    fmt = fmt.strip()
    if not fmt:
        return f"{value:g}"

    # ---------- 百分比 ----------
    if '%' in fmt:
        pct_value = value * 100
        # 计算小数位数：% 前面的 0 的小数部分
        dec_match = re.search(r'\.([0#]+)\s*%', fmt)
        decimals = len(dec_match.group(1)) if dec_match else 0
        formatted = f"{pct_value:,.{decimals}f}" if '#' in fmt and ',' in fmt else f"{pct_value:.{decimals}f}"
        # 如果格式里没有千分位逗号，去掉逗号
        if ',' not in fmt.replace('%', ''):
            formatted = formatted.replace(',', '')
        return formatted + '%'

    # ---------- 科学计数法 ----------
    if 'E+' in fmt.upper() or 'E-' in fmt.upper():
        dec_match = re.search(r'\.([0#]+)[Ee]', fmt)
        decimals = len(dec_match.group(1)) if dec_match else 2
        return f"{value:.{decimals}E}"

    # ---------- 提取前缀（货币符号等）和后缀 ----------
    # 前缀：格式开头的非 #0., 字符（如 ¥, $, "USD " 等）
    # Excel 格式中用引号包裹或直接放置的字面量
    prefix = ""
    suffix = ""
    # 提取被引号包裹的字面量
    quoted_parts = re.findall(r'"([^"]*)"', fmt)
    fmt_clean = re.sub(r'"[^"]*"', '', fmt)

    # 提取前缀：格式开头的非格式字符
    prefix_match = re.match(r'^([^#0.,\s]*)', fmt_clean)
    if prefix_match:
        prefix = prefix_match.group(1)

    # 提取后缀：格式末尾的非格式字符
    suffix_match = re.search(r'([^#0.,\s]*)$', fmt_clean)
    if suffix_match:
        suffix = suffix_match.group(1)

    # 如果有引号内容且前缀/后缀为空，尝试使用引号内容
    if quoted_parts and not prefix:
        prefix = quoted_parts[0]
    if len(quoted_parts) > 1 and not suffix:
        suffix = quoted_parts[-1]

    # ---------- 千分位与小数位 ----------
    has_comma = ',' in fmt_clean
    dec_match = re.search(r'\.([0#]+)', fmt_clean)
    if dec_match:
        decimals = len(dec_match.group(1))
    else:
        # 格式中没有小数点 → 0 位小数
        decimals = 0 if re.search(r'[0#]', fmt_clean) else None

    if decimals is not None:
        if has_comma:
            formatted = f"{value:,.{decimals}f}"
        else:
            formatted = f"{value:.{decimals}f}"
        return prefix + formatted + suffix

    # ---------- fallback ----------
    return f"{value:g}"


def _xlsx_cell_to_text(cell, theme_fonts: dict = None,
                       default_font_name: str = None,
                       theme_colors: list = None,
                       cached_value=_SENTINEL) -> str:
    """将一个 openpyxl Cell 转为 '内容 {样式}' 形式的字符串。

    样式仅在非默认值时才输出：
        格式   — number_format 非 'General' 时
        字体   — 解析后的字体名非默认 'Calibri'/'等线' 时
        字号   — font.size 非 11.0 时
        加粗   — font.bold 为 True 时
        颜色   — 字体颜色非默认黑色时
        底色   — 单元格有背景填充时

    Args:
        cached_value: 来自 data_only=True 工作簿的缓存值，用于替换公式。
            传入 _SENTINEL（默认）表示未提供。
    """

    # ---- 值 ----
    value = cell.value
    nf = cell.number_format

    # 公式单元格：使用 data_only 工作簿中的缓存值
    if isinstance(value, str) and value.startswith("=") and cached_value is not _SENTINEL:
        if cached_value is not None:
            value = cached_value
        # cached_value 为 None 表示 Excel 未缓存计算结果，保留公式文本

    if value is None:
        value_str = ""
    elif isinstance(value, datetime):
        value_str = value.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(value, date):
        value_str = value.strftime("%Y-%m-%d")
    elif isinstance(value, dt_time):
        value_str = value.strftime("%H:%M:%S")
    elif isinstance(value, (int, float)):
        # 根据 number_format 格式化数值，保持与 Excel 显示一致
        value_str = _format_excel_value(value, nf)
    else:
        value_str = str(value)

    # ---- 样式收集 ----
    styles = []

    # 数据格式（nf 已在上方提取）
    if nf and nf != "General":
        styles.append(f"格式:{nf}")

    # 字体
    font = cell.font
    if font:
        resolved_name = _resolve_font_name(
            font, default_font_name or "", theme_fonts or {})
        if resolved_name:
            styles.append(f"字体:{resolved_name}")
        if font.size is not None and font.size != 11.0:
            styles.append(f"字号:{font.size}")
        if font.bold:
            styles.append("加粗")
        color_str = _extract_color(font.color, theme_colors=theme_colors,
                                   filter_default="000000")
        if color_str:
            styles.append(f"颜色:{color_str}")
    
    # 单元格底色
    fill = cell.fill
    if fill and fill.patternType and fill.patternType != "none":
        fill_str = _extract_color(fill.fgColor, theme_colors=theme_colors,
                                  filter_default="FFFFFF")
        if fill_str:
            styles.append(f"底色:{fill_str}")

    # ---- 组装 ----
    if not styles:
        return value_str
    style_tag = " {" + ", ".join(styles) + "}"
    if not value_str:
        return style_tag.strip()
    return value_str + style_tag


# Excel 标准索引色表（indexed 0-63），每个元素为 6 位 RGB hex
_XLSX_INDEXED_COLORS = [
    "000000", "FFFFFF", "FF0000", "00FF00", "0000FF", "FFFF00", "FF00FF", "00FFFF",  # 0-7
    "000000", "FFFFFF", "FF0000", "00FF00", "0000FF", "FFFF00", "FF00FF", "00FFFF",  # 8-15
    "800000", "008000", "000080", "808000", "800080", "008080", "C0C0C0", "808080",  # 16-23
    "9999FF", "993366", "FFFFCC", "CCFFFF", "660066", "FF8080", "0066CC", "CCCCFF",  # 24-31
    "000080", "FF00FF", "FFFF00", "00FFFF", "800080", "800000", "008080", "0000FF",  # 32-39
    "00CCFF", "CCFFFF", "CCFFCC", "FFFF99", "99CCFF", "FF99CC", "CC99FF", "FFCC99",  # 40-47
    "3366FF", "33CCCC", "99CC00", "FFCC00", "FF9900", "FF6600", "666699", "969696",  # 48-55
    "003366", "339966", "003300", "333300", "993300", "993366", "333399", "333333",  # 56-63
]


def _extract_color(color, theme_colors: list = None,
                   filter_default: str = "000000") -> str:
    """从 openpyxl Color 对象中提取可读的颜色表示。

    对于 theme / indexed 类型的颜色，会解析为实际的 #RRGGBB 值。

    Args:
        color: openpyxl Color 对象
        theme_colors: _get_xlsx_theme_colors 返回的主题色列表
        filter_default: 要过滤的默认颜色（6 位大写 hex），
            字体传 "000000"（过滤黑色），底色传 "FFFFFF"（过滤白色）。

    返回值示例：
        "#FF0000"       — 纯 RGB 红色
        "#4472C4"       — 由 theme 解析出的实际颜色
        "#C0C0C0"       — 由 indexed 解析出的实际颜色
        ""              — 默认/无颜色
    """
    if color is None:
        return ""

    if color.type == "rgb" and color.rgb:
        rgb = str(color.rgb)
        # openpyxl 存储 ARGB（8 位），前 2 位为 alpha
        if len(rgb) == 8:
            alpha = rgb[:2]
            rgb_hex = rgb[2:]
        else:
            alpha = "FF"
            rgb_hex = rgb

        # if rgb_hex == "92D050":
        #     pdb.set_trace()

        # 过滤默认颜色
        if rgb_hex.upper() == filter_default:
            return ""
        # if alpha == "00":
        #     return ""
        return f"#{rgb_hex}"

    if color.type == "theme":
        if color.theme is not None and theme_colors:
            idx = color.theme
            if idx < len(theme_colors) and theme_colors[idx]:
                rgb_hex = theme_colors[idx]
                # 应用 tint 偏移
                if color.tint and color.tint != 0:
                    rgb_hex = _apply_tint(rgb_hex, color.tint)
                # 过滤默认颜色
                if rgb_hex.upper() == filter_default:
                    return ""
                return f"#{rgb_hex}"
        # theme_colors 不可用时，回退到输出 theme 编号
        if color.theme is not None:
            return f"theme:{color.theme}"
        return ""

    if color.type == "indexed":
        if color.indexed is not None:
            # indexed 64 = 无色 (system foreground default)
            if color.indexed == 64:
                return ""
            if color.indexed < len(_XLSX_INDEXED_COLORS):
                rgb_hex = _XLSX_INDEXED_COLORS[color.indexed]
                # 过滤默认颜色
                if rgb_hex.upper() == filter_default:
                    return ""
                return f"#{rgb_hex}"
            return f"indexed:{color.indexed}"
        return ""

    return ""


# -------------------- 通用格式化辅助 --------------------

def _display_width(s: str) -> int:
    """计算字符串的终端显示宽度，全角字符算 2 格。"""

    width = 0
    for ch in s:
        eaw = unicodedata.east_asian_width(ch)
        width += 2 if eaw in ("F", "W") else 1
    return width


def _pad(text: str, target_width: int) -> str:
    """用空格将 text 填充到 target_width 个显示宽度。"""
    pad_needed = target_width - _display_width(text)
    return text + " " * max(pad_needed, 0)


