"""
MinerU 本地转换服务

将 PDF/DOCX/PPTX/XLSX/图片 转为 Markdown，保留图片到本地。
前端通过 HTTP 调用此服务。

启动:
    python mineru_service.py [--port 8899]

依赖:
    pip install flask requests python-dotenv
"""

import argparse
import io
import json
import os
import shutil
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

# ── MinerU API 配置 ──────────────────────────────────────
BASE_URL = "https://mineru.net"

_dotenv_path = Path.home() / ".claude" / "skills" / "mineru" / ".env"
load_dotenv(_dotenv_path)

MINERU_TOKEN = os.environ.get("MINERU_TOKEN", "")
if not MINERU_TOKEN:
    print("\033[31m错误: 未找到 MINERU_TOKEN\033[0m")
    print("请确保 ~/.claude/skills/mineru/.env 中包含 MINERU_TOKEN")
    sys.exit(1)

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {MINERU_TOKEN}",
}

OUTPUT_DIR = Path(__file__).parent / "mineru_output"
IMAGES_DIR = OUTPUT_DIR / "images"

app = Flask(__name__)

# 限制上传大小 50MB
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024


# ── MinerU API 封装 ──────────────────────────────────────

def _api_data(fmt: str = "md") -> dict:
    return {
        "model_version": "vlm",
        "enable_formula": True,
        "enable_table": True,
        "language": "ch",
    }


def upload_file(file_path: str, fmt: str = "md") -> tuple[str, str]:
    """上传文件到 MinerU，返回 (batch_id, data_id)"""
    path = Path(file_path)
    data_id = path.stem
    data = _api_data(fmt)
    data["files"] = [{"name": path.name, "data_id": data_id}]

    resp = requests.post(f"{BASE_URL}/api/v4/file-urls/batch", headers=HEADERS, json=data)
    result = resp.json()
    if result.get("code") != 0:
        raise RuntimeError(f"获取上传链接失败: {result.get('msg', '')}")

    batch_id = result["data"]["batch_id"]
    upload_url = result["data"]["file_urls"][0]

    with open(path, "rb") as f:
        put_resp = requests.put(upload_url, data=f)
    if put_resp.status_code not in (200, 201):
        raise RuntimeError(f"上传失败: HTTP {put_resp.status_code}")

    return batch_id, data_id


def poll_batch(batch_id: str, data_id: str, on_progress=None) -> dict:
    """轮询批量任务直到完成"""
    while True:
        resp = requests.get(
            f"{BASE_URL}/api/v4/extract-results/batch/{batch_id}", headers=HEADERS
        )
        result = resp.json()
        if result.get("code") != 0:
            raise RuntimeError(f"查询失败: {result.get('msg')}")

        items = result["data"].get("extract_result", [])
        for item in items:
            if item.get("data_id") == data_id:
                state = item.get("state", "")
                if state == "done":
                    return item
                elif state == "failed":
                    raise RuntimeError(f"解析失败: {item.get('err_msg', '')}")
                elif state in ("pending", "running", "converting", "waiting-file"):
                    progress = item.get("extract_progress", {})
                    p = None
                    if progress:
                        p = f"{progress.get('extracted_pages', '?')}/{progress.get('total_pages', '?')}"
                    if on_progress:
                        on_progress(state, p)
                break
        time.sleep(3)


def download_and_extract(zip_url: str, output_dir: Path, stem: str) -> tuple[str, list[str]]:
    """下载 zip，提取 MD 内容和图片路径，返回 (md_content, image_filenames)"""
    resp = requests.get(zip_url)
    resp.raise_for_status()

    tmp = output_dir / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    md_content = ""
    image_files: list[str] = []

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        zf.extractall(tmp)
        names = zf.namelist()

    # 找 MD 文件
    for name in names:
        if name.endswith(".md"):
            md_path = tmp / name
            if md_path.is_file():
                md_content = md_path.read_text(encoding="utf-8")

    # 提取图片到公共目录
    img_src = tmp / "images"
    if img_src.is_dir():
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        for img_file in sorted(img_src.iterdir()):
            if img_file.is_file():
                dst = images_dir / f"{stem}-{img_file.name}"
                shutil.move(str(img_file), str(dst))
                image_files.append(dst.name)

    # 整理：把 md 文件移到 output 根目录
    for name in names:
        if name.endswith(".md"):
            src = tmp / name
            if src.is_file():
                dst = output_dir / f"{stem}.md"
                shutil.copy2(str(src), str(dst))
                break

    shutil.rmtree(tmp, ignore_errors=True)
    return md_content, sorted(image_files)


def convert_with_mineru(file_path: str, on_progress=None) -> dict:
    """完整转换流程，返回结果 dict"""
    stem = Path(file_path).stem

    # 1. 上传
    batch_id, data_id = upload_file(file_path)

    # 2. 轮询
    result = poll_batch(batch_id, data_id, on_progress)

    # 3. 下载
    zip_url = result.get("full_zip_url")
    if not zip_url:
        raise RuntimeError("未获取到下载链接")

    md_content, image_files = download_and_extract(zip_url, OUTPUT_DIR, stem)

    return {
        "title": stem,
        "content": md_content,
        "name": Path(file_path).name,
        "images": image_files,
    }


# ── Flask 路由 ──────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "mineru": True})


@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return jsonify({"error": "未提供文件"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "文件名为空"}), 400

    # 保存到临时文件
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp)
        tmp_path = tmp.name

    progress_log = []

    def on_progress(state, pages):
        progress_log.append({"state": state, "pages": pages})

    try:
        result = convert_with_mineru(tmp_path, on_progress)
        result["progress"] = progress_log
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.unlink(tmp_path)


@app.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)


@app.route("/files/<filename>")
def serve_file(filename):
    """提供下载转换后的 MD 文件"""
    return send_from_directory(OUTPUT_DIR, filename)


# ── 入口 ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MinerU 本地转换服务")
    parser.add_argument("--port", type=int, default=8899, help="监听端口 (默认: 8899)")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址 (默认: 127.0.0.1)")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\033[36mMinerU 转换服务启动 → http://{args.host}:{args.port}\033[0m")
    print(f"\033[32m输出目录: {OUTPUT_DIR}\033[0m")
    print(f"\033[33m按 Ctrl+C 停止\033[0m")

    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
