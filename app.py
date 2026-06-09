import os
import io
import zipfile
import uuid
import time
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import (
    PORT, HOST, UPLOAD_DIR, OUTPUT_DIR,
    ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE, STYLES
)
from style_processor import process_image, STYLE_FUNCTIONS, check_style_availability
from stats_manager import record_processing, get_stats
from logger_config import get_logger

logger = get_logger("app")

app = FastAPI(title="图像风格转换服务", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logger.info("启动阶段：正在对 8 种风格进行可用性自检...")
    try:
        avail = check_style_availability(force=True)
        ok_count = sum(1 for v in avail.values() if v)
        logger.info(f"风格自检完成：{ok_count}/{len(avail)} 种风格可用 - {avail}")
    except Exception as e:
        logger.exception(f"风格自检失败: {e}")


def _validate_extension(filename: str) -> bool:
    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_EXTENSIONS


def _save_upload(file_bytes: bytes, filename: str) -> str:
    ext = os.path.splitext(filename)[1] or ".png"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(save_path, "wb") as f:
        f.write(file_bytes)
    return save_path


def _save_output(image_bytes: bytes, style_id: str) -> str:
    unique_name = f"{uuid.uuid4().hex}_{style_id}.png"
    save_path = os.path.join(OUTPUT_DIR, unique_name)
    with open(save_path, "wb") as f:
        f.write(image_bytes)
    return save_path


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.1f}ms")
    return response


@app.get("/api/styles")
async def get_styles():
    availability = check_style_availability(force=False)
    style_list = []
    for s in STYLES:
        style_list.append({
            **s,
            "available": availability.get(s["id"], False),
        })
    return JSONResponse(content={"styles": style_list})


@app.get("/api/stats")
async def api_get_stats():
    stats = get_stats()
    return JSONResponse(content={"stats": stats})


@app.post("/api/process")
async def process_single(
    file: UploadFile = File(...),
    style: str = Form(...),
    intensity: float = Form(0.8),
):
    availability = check_style_availability(force=False)
    if not availability.get(style, False):
        raise HTTPException(status_code=400, detail=f"风格当前不可用: {style}")

    if style not in STYLE_FUNCTIONS:
        raise HTTPException(status_code=400, detail=f"不支持的风格: {style}")

    if not _validate_extension(file.filename or ""):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式，支持: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"文件过大，最大支持 {MAX_UPLOAD_SIZE // 1024 // 1024}MB")

    try:
        _save_upload(file_bytes, file.filename or "image.png")
        result_bytes = process_image(file_bytes, style, intensity)
        output_path = _save_output(result_bytes, style)
        record_processing(style, 1)
        filename = Path(output_path).name
        return JSONResponse(content={
            "success": True,
            "filename": filename,
            "url": f"/outputs/{filename}",
            "style": style,
            "intensity": intensity,
        })
    except ValueError as e:
        logger.error(f"处理图片失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("处理图片时发生错误")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.post("/api/batch")
async def process_batch(
    files: List[UploadFile] = File(...),
    style: str = Form(...),
    intensity: float = Form(0.8),
):
    availability = check_style_availability(force=False)
    if not availability.get(style, False):
        raise HTTPException(status_code=400, detail=f"风格当前不可用: {style}")

    if style not in STYLE_FUNCTIONS:
        raise HTTPException(status_code=400, detail=f"不支持的风格: {style}")

    if len(files) > 20:
        raise HTTPException(status_code=400, detail="批量处理最多支持20张图片")

    results = []
    error_count = 0
    success_count = 0

    for file in files:
        try:
            if not _validate_extension(file.filename or ""):
                error_count += 1
                results.append({"name": file.filename, "error": "不支持的格式"})
                continue

            file_bytes = await file.read()
            if len(file_bytes) > MAX_UPLOAD_SIZE:
                error_count += 1
                results.append({"name": file.filename, "error": "文件过大"})
                continue

            _save_upload(file_bytes, file.filename or "image.png")
            result_bytes = process_image(file_bytes, style, intensity)
            output_path = _save_output(result_bytes, style)
            success_count += 1
            results.append({
                "name": file.filename,
                "filename": Path(output_path).name,
                "url": f"/outputs/{Path(output_path).name}",
            })
        except Exception as e:
            logger.error(f"批量处理 {file.filename} 失败: {e}")
            error_count += 1
            results.append({"name": file.filename, "error": str(e)})

    if success_count > 0:
        record_processing(style, success_count)

    has_success = success_count > 0
    return JSONResponse(content={
        "success": has_success,
        "total": len(files),
        "success_count": success_count,
        "error_count": error_count,
        "style": style,
        "intensity": intensity,
        "results": results,
    }, status_code=200 if has_success or error_count == 0 else 200)


@app.post("/api/batch/download")
async def download_batch(request: Request):
    body = await request.json()
    filenames = body.get("filenames", [])

    if not filenames:
        raise HTTPException(status_code=400, detail="请提供文件名列表")

    if len(filenames) > 50:
        raise HTTPException(status_code=400, detail="最多支持打包50个文件")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for fname in filenames:
            fpath = os.path.join(OUTPUT_DIR, os.path.basename(fname))
            if os.path.exists(fpath):
                zipf.write(fpath, arcname=os.path.basename(fname))

    zip_buffer.seek(0)
    ts = int(time.time())
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=styled_images_{ts}.zip"},
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "port": PORT}


app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

_static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir, html=True), name="static")


@app.get("/")
async def root():
    index_path = os.path.join(_static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "service": "图像风格转换服务",
        "port": PORT,
        "api_docs": "/docs",
        "styles_endpoint": "/api/styles",
    }


def run():
    import sys
    import subprocess
    logger.info(f"启动图像风格转换服务: http://{HOST}:{PORT}")
    logger.info("首次启动需要加载 OpenCV/FastAPI 等依赖库，约需 20-40 秒，请耐心等待...")
    try:
        import uvicorn
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            log_level="info",
        )
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.warning(f"直接运行失败: {e}，尝试使用子进程启动 uvicorn...")
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app:app",
            "--host", HOST,
            "--port", str(PORT),
            "--log-level", "info",
        ], cwd=os.path.dirname(os.path.abspath(__file__)))


if __name__ == "__main__":
    run()
