"""build_prompt — assemble the judge user prompt + image/pdf channel manifests.

Files are split into text / ori_path(image) / trans_path/pdf / trans_path/compress
channels: text inline, image via image channel, pdf via pdf channel. A
"文件格式说明" trailer (xlsx multi-Sheet order, svg is XML, doc/docx/pptx
already converted to PDF) is appended.

Returns the 4-tuple (system_prompt, prompt, image_urls, pdf_urls).
"""

from .system_prompt import (
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_W_CODE_EXEC,
    OUTPUT_FORMAT_INSTRUCTION,
)


def build_prompt(instruction, model_response, file2content, file2type, rubrics_list,
                 use_code_exec=False):
    """
    构建打分 prompt，包含以下部分：
    1. instruction（任务描述）
    2. model_response（模型的回答）
    3. 文件内容（file2content）和文件类型（file2type）
    4. 打分细则（rubrics_list）

    file2type 取值：
        - "text": 纯文本内容（含 SVG），直接嵌入 prompt
        - "ori_path": 图片/PDF 原始文件 URL（此处为 base64 data URI），
          通过 image_urls/pdf_urls 传入
        - "trans_path/compress": 原始文件过大（>5MB），压缩后的 URL
        - "trans_path/pdf": doc/docx/pptx 转换后的 PDF URL，通过 pdf_urls 传入

    Returns:
        (system_prompt, prompt, image_urls, pdf_urls)
    """
    sections = []
    image_urls = []
    pdf_urls = []

    # ===================== 1. Task Instruction =====================
    sections.append("## Task Instruction")
    sections.append("[BEGIN: Task Instruction]")
    instruction_text = instruction.strip()
    if instruction_text:
        sections.append(instruction_text)
    else:
        sections.append("（此部分无内容）")
    sections.append("[END: Task Instruction]")

    # ===================== 2. Model Response =====================
    sections.append("\n## Model Response")
    sections.append("[BEGIN: Model Response]")
    response_text = model_response.strip()
    if response_text:
        sections.append(response_text)
    else:
        sections.append("（此部分无内容，被测模型未产生文字回复）")
    sections.append("[END: Model Response]")

    # ===================== 3. File Contents =====================
    sections.append("\n## File Contents")
    sections.append("[BEGIN: File Contents]")

    text_files = []
    # 每个 entry 为 (file_path, actual_path, source_desc)
    image_file_entries = []
    pdf_file_entries = []

    # ori_path 类型中，以下扩展名视为 PDF 文件，其余视为图片文件
    ORI_PATH_PDF_EXTENSIONS = (".pdf",)

    for file_path, content in file2content.items():
        ftype = file2type.get(file_path, "text")

        if ftype == "text":
            text_files.append((file_path, content))
        elif ftype == "ori_path":
            if file_path.lower().endswith(ORI_PATH_PDF_EXTENSIONS):
                pdf_urls.append(content)
                pdf_file_entries.append((file_path, content, None))
            else:
                image_urls.append(content)
                image_file_entries.append((file_path, content, None))
        elif ftype == "trans_path/compress":
            compress_desc = "原始文件过大，已压缩上传，内容质量可能有所下降"
            if file_path.lower().endswith(ORI_PATH_PDF_EXTENSIONS):
                pdf_urls.append(content)
                pdf_file_entries.append((file_path, content, compress_desc))
            else:
                image_urls.append(content)
                image_file_entries.append((file_path, content, compress_desc))
        elif ftype == "trans_path/pdf":
            pdf_urls.append(content)
            pdf_file_entries.append((file_path, content, "原始 doc/docx/pptx 文件，已转换为 PDF"))

    has_any_file = text_files or image_file_entries or pdf_file_entries

    # 先输出文本文件内容
    for file_path, content in text_files:
        sections.append(f'<file>{file_path}</file>')
        sections.append(f'<content>\n{content}\n</content>\n')

    # 再标注图片文件（实际内容通过 API 图片参数传入）
    if image_file_entries:
        sections.append("以下文件为图片文件，其内容已随消息一同传入，请参考对应图片进行判断：\n")
        for file_path, actual_path, source_desc in image_file_entries:
            sections.append(f'<file>{file_path}</file>')
            if source_desc:
                sections.append(f'（{source_desc}，已通过图片通道传入，对应路径: {actual_path}）\n')
            else:
                sections.append(f'（图片文件，已通过图片通道传入，对应路径: {actual_path}）\n')

    # 标注 PDF 文件（实际内容通过 API 文件参数传入）
    if pdf_file_entries:
        sections.append("以下文件为 PDF 文件，其内容已随消息一同传入，请参考对应 PDF 进行判断：\n")
        for file_path, actual_path, source_desc in pdf_file_entries:
            sections.append(f'<file>{file_path}</file>')
            if source_desc:
                sections.append(f'（{source_desc}，已通过文件通道传入，对应路径: {actual_path}）\n')
            else:
                sections.append(f'（PDF 文件，已通过文件通道传入，对应路径: {actual_path}）\n')

    if not has_any_file:
        sections.append("（此部分无内容，被测模型未生成任何文件）")

    # ---- 文件格式补充说明 ----
    format_notes = []
    has_xlsx = any(fp.lower().endswith(".xlsx") for fp in file2content)
    has_svg = any(fp.lower().endswith(".svg") for fp in file2content)
    has_office_pdf = any(
        fp.lower().endswith((".doc", ".docx", ".pptx")) for fp in file2content
    )
    if has_xlsx:
        format_notes.append(
            "- xlsx 文件：如包含多个子表（Sheet），上方文本内容中各子表按原文件中的先后顺序从上到下依次排列。"
        )
    if has_svg:
        format_notes.append(
            "- svg 文件：以 XML 纯文本形式嵌入，请直接阅读其源码内容进行判断。"
        )
    if has_office_pdf:
        format_notes.append(
            "- doc/docx/pptx 文件：原始文件已转换为 PDF 格式传入。"
            "注意：由于格式转换可能存在部分排版变化（如换行位置偏移、局部间距变化等）或字体变化，"
            "打分时请忽略此类局部排版或字体差异，重点关注内容本身是否满足要求。"
        )
    if format_notes:
        sections.append("\n**文件格式说明：**")
        sections.append("\n".join(format_notes))

    sections.append("[END: File Contents]")

    # ===================== 4. Rubrics =====================
    sections.append("\n## Rubrics")
    sections.append("[BEGIN: Rubrics]")
    sections.append("以下是评分细则，请逐条判断模型输出是否满足要求：\n")

    for rubric in rubrics_list:
        rid = rubric.get("id", "?")
        content = rubric.get("content", "")
        sections.append(f'**[Rubric {rid}]**')
        sections.append(f'{content}\n')

    sections.append("[END: Rubrics]")

    # ===================== 5. Output Format =====================
    sections.append(f"\n{OUTPUT_FORMAT_INSTRUCTION}")

    prompt = "\n".join(sections)

    if use_code_exec:
        system_prompt = SYSTEM_PROMPT_W_CODE_EXEC
    else:
        system_prompt = SYSTEM_PROMPT

    return system_prompt, prompt, image_urls, pdf_urls
