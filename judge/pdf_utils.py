import os
import time
import shutil
import subprocess
import tempfile
import threading

# LibreOffice 不支持多进程/多线程并发调用，需要加锁串行执行
_libreoffice_lock = threading.Lock()


def _check_pdf_valid(file_path: str) -> int:
    """校验 PDF 文件是否可正常读取，并返回页数。

    Raises:
        ValueError: PDF 损坏、页数为 0 或超过 MAX_PAGE_LIMIT 时抛出。
    """

    from pypdf import PdfReader

    try:
        reader = PdfReader(file_path)
        page_count = len(reader.pages)
    except Exception as e:
        raise ValueError(f"PDF 损坏或无法读取: {os.path.basename(file_path)}, 错误: {e}")

    if page_count == 0:
        raise ValueError(f"PDF 页数为 0: {os.path.basename(file_path)}")
    if page_count > MAX_PAGE_LIMIT:
        raise ValueError(
            f"文件 {os.path.basename(file_path)} 共 {page_count} 页，超过 {MAX_PAGE_LIMIT} 页上限"
        )

    print(f"  📄 PDF 校验通过: {os.path.basename(file_path)} = {page_count} 页")
    return page_count


def _find_libreoffice() -> str:
    """查找系统中的 LibreOffice 可执行文件路径。

    按优先级依次查找：
        1. PATH 中的 libreoffice
        2. PATH 中的 soffice
        3. macOS 默认安装路径 /Applications/LibreOffice.app/Contents/MacOS/soffice
        4. Linux 常见路径（/usr/bin, /usr/local/bin, /snap/bin, /usr/lib, /opt 等）

    Returns:
        LibreOffice 可执行文件的绝对路径。

    Raises:
        FileNotFoundError: 未找到 LibreOffice 时抛出，包含安装提示。
    """

    # PATH 中查找
    for name in ("libreoffice", "soffice"):
        path = shutil.which(name)
        if path:
            return path

    # macOS 默认安装位置
    mac_path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if os.path.isfile(mac_path):
        return mac_path

    # Linux 常见位置
    for linux_path in (
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
        "/usr/local/bin/soffice",
        "/usr/local/bin/libreoffice",
        "/snap/bin/libreoffice",                        # Ubuntu snap 安装
        "/usr/lib/libreoffice/program/soffice",         # apt 安装的实际位置
        "/opt/libreoffice/program/soffice",             # 官方 .deb/.rpm 安装
        "/opt/libreoffice24.8/program/soffice",         # 带版本号的官方安装
    ):
        if os.path.isfile(linux_path):
            return linux_path

    raise FileNotFoundError(
        "未找到 LibreOffice。doc/docx/pptx → PDF 无损转换依赖 LibreOffice。\n"
        "安装方式：\n"
        "  macOS:   brew install --cask libreoffice\n"
        "  Ubuntu:  sudo apt install libreoffice\n"
        "  CentOS:  sudo yum install libreoffice\n"
        "排查提示：\n"
        f"  当前 PATH: {os.environ.get('PATH', '(未设置)')}\n"
        "  可尝试运行: find / -name soffice -type f 2>/dev/null"
    )


def _convert_to_pdf_via_libreoffice(file_path: str, use_pdf_cache: bool = True) -> str:
    """使用 LibreOffice headless 模式将文件无损转换为 PDF。

    转换后的 PDF 保存在源文件同级目录下的 ./.trans/ 子目录中，
    文件名保持原名、扩展名替换为 .pdf。

    Args:
        file_path: 待转换文件的路径（支持 .doc / .docx / .pptx 等
                   LibreOffice 可打开的任意格式）。
        use_pdf_cache: 是否使用 .trans/ 下已转换的 PDF 缓存。
                       True 则优先使用缓存，False 则删除旧缓存并重新转换。

    Returns:
        转换后 PDF 文件的绝对路径。

    Raises:
        FileNotFoundError: 未找到 LibreOffice 时抛出。
        RuntimeError: LibreOffice 转换失败时抛出，包含 stderr 信息。
    """

    soffice = _find_libreoffice()

    abs_file = os.path.abspath(file_path)
    trans_dir = os.path.join(os.path.dirname(abs_file), ".trans")
    os.makedirs(trans_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(abs_file))[0]
    expected_pdf = os.path.join(trans_dir, f"{base_name}.pdf")

    # 不使用缓存时，删除已有的 PDF 强制重新转换
    if not use_pdf_cache and os.path.isfile(expected_pdf):
        print(f"use_pdf_cache=False，删除旧缓存: {expected_pdf}")
        os.remove(expected_pdf)

    # 如果已经转换过且源文件未更新，直接返回缓存
    if os.path.isfile(expected_pdf):
        if os.path.getmtime(expected_pdf) >= os.path.getmtime(abs_file):
            print(f"  📋 PDF 缓存命中，跳过转换: {os.path.basename(abs_file)}")
            print(f"PDF 缓存命中，跳过转换: {expected_pdf}")
            _check_pdf_valid(expected_pdf)
            return expected_pdf

    # LibreOffice headless 转换
    # 当路径过长时（超过 200 字符），LibreOffice 可能静默失败，
    # 因此使用临时短路径目录进行转换，再将结果移回目标位置。
    use_tmp = len(abs_file) > 200 or len(trans_dir) > 200

    print(f"  🔄 正在转换为 PDF: {os.path.basename(abs_file)} ...")
    print(f"正在转换为 PDF: {abs_file}")
    t_start = time.time()

    if use_tmp:
        tmp_dir = tempfile.mkdtemp(prefix="lo_conv_")
        tmp_src = os.path.join(tmp_dir, os.path.basename(abs_file))
        shutil.copy2(abs_file, tmp_src)
        conv_src = tmp_src
        conv_outdir = tmp_dir
    else:
        tmp_dir = None
        conv_src = abs_file
        conv_outdir = trans_dir

    # 为每次调用分配独立的 UserInstallation，避免多进程并发时 profile 锁冲突
    profile_dir = tempfile.mkdtemp(prefix="lo_profile_")

    cmd = [
        soffice,
        "--headless",
        "--norestore",
        f"-env:UserInstallation=file://{profile_dir}",
        "--convert-to", "pdf",
        "--outdir", conv_outdir,
        conv_src,
    ]

    with _libreoffice_lock:
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,  # 2 分钟超时，防止大文件卡死
            )
        except subprocess.TimeoutExpired:
            elapsed = time.time() - t_start
            if tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            shutil.rmtree(profile_dir, ignore_errors=True)
            print(f"  ❌ LibreOffice 转换超时 (>{120}s): {os.path.basename(abs_file)} (已耗时 {elapsed:.1f}s)")
            raise TimeoutError(
                f"LibreOffice 转换超时: {abs_file} (超过 120 秒)"
            )
    elapsed = time.time() - t_start

    if result.returncode != 0:
        stderr_msg = result.stderr.decode("utf-8", errors="replace").strip()
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        shutil.rmtree(profile_dir, ignore_errors=True)
        print(f"  ❌ 转换失败: {os.path.basename(abs_file)} (耗时 {elapsed:.1f}s)")
        raise RuntimeError(
            f"LibreOffice 转换失败 (returncode={result.returncode}): {stderr_msg}\n"
            f"命令: {' '.join(cmd)}"
        )

    # 如果使用了临时目录，将 PDF 移回目标 .trans/ 目录
    if tmp_dir:
        tmp_pdf = os.path.join(tmp_dir, f"{base_name}.pdf")
        if os.path.isfile(tmp_pdf):
            shutil.move(tmp_pdf, expected_pdf)
        shutil.rmtree(tmp_dir, ignore_errors=True)
    shutil.rmtree(profile_dir, ignore_errors=True)

    # 确认输出文件存在
    if not os.path.isfile(expected_pdf):
        raise RuntimeError(
            f"LibreOffice 转换完成但未找到输出文件: {expected_pdf}\n"
            f"stdout: {result.stdout.decode('utf-8', errors='replace').strip()}"
        )

    print(f"  ✅ 转换完成: {os.path.basename(abs_file)} -> PDF (耗时 {elapsed:.1f}s)")
    print(f"转换完成: {expected_pdf}")

    # 校验转换后的 PDF 是否可正常读取、页数是否超限
    _check_pdf_valid(expected_pdf)

    return os.path.abspath(expected_pdf)


MAX_PAGE_LIMIT = 20  # doc/docx/pptx 转 PDF 前的页数上限


def _get_page_count_before_convert(file_path: str):
    """在转 PDF 之前，快速估算 doc/docx/pptx 的页数/slide 数。

    - .pptx: 统计 zip 内 ppt/slides/slideN.xml 的数量
    - .docx: 从 zip 内 docProps/app.xml 中读取 <Pages> 元素
    - .doc:  尝试用 olefile 读取 SummaryInformation 中的 page count

    Returns:
        int | None: 页数，无法获取时返回 None（不阻断后续流程）。
    """

    ext = os.path.splitext(file_path)[1].lower()

    import zipfile
    import xml.etree.ElementTree as ET
    import olefile

    try:
        if ext == ".pptx":
            with zipfile.ZipFile(file_path, "r") as z:
                slide_count = sum(
                    1 for name in z.namelist()
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml")
                )
            return slide_count if slide_count > 0 else None

        if ext == ".docx":
            with zipfile.ZipFile(file_path, "r") as z:
                if "docProps/app.xml" not in z.namelist():
                    return None
                app_xml = z.read("docProps/app.xml")
            root = ET.fromstring(app_xml)
            # 命名空间可能是 vt 或默认
            ns = {"ep": "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"}
            pages_elem = root.find("ep:Pages", ns)
            if pages_elem is not None and pages_elem.text:
                return int(pages_elem.text)
            return None

        if ext == ".doc":
            try:
                ole = olefile.OleFileIO(file_path)
                meta = ole.get_metadata()
                ole.close()
                if meta.num_pages and meta.num_pages > 0:
                    return meta.num_pages
            except Exception:
                pass
            return None

    except Exception as e:
        print(f"  ⚠️ 无法预估页数 ({os.path.basename(file_path)}): {e}")
        return None

    return None


def _check_page_limit(file_path: str):
    """检查 doc/docx/pptx 页数是否超过上限，超过则 raise ValueError。"""
    page_count = _get_page_count_before_convert(file_path)
    if page_count is not None:
        print(f"  📄 预估页数: {os.path.basename(file_path)} = {page_count} 页")
        if page_count > MAX_PAGE_LIMIT:
            raise ValueError(
                f"文件 {os.path.basename(file_path)} 共 {page_count} 页，超过 {MAX_PAGE_LIMIT} 页上限，跳过转换"
            )
    else:
        print(f"  📄 无法预估页数: {os.path.basename(file_path)}，继续转换")

