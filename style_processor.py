import cv2
import numpy as np
from typing import Callable
from logger_config import get_logger

logger = get_logger("style_processor")


def _blend(original: np.ndarray, styled: np.ndarray, intensity: float) -> np.ndarray:
    intensity = max(0.0, min(1.0, float(intensity)))
    if intensity >= 1.0:
        return styled
    if intensity <= 0.0:
        return original
    return cv2.addWeighted(original, 1 - intensity, styled, intensity, 0)


def _resize_if_needed(img: np.ndarray, max_side: int = 1200) -> np.ndarray:
    h, w = img.shape[:2]
    if max(h, w) <= max_side:
        return img
    scale = max_side / max(h, w)
    new_h, new_w = int(h * scale), int(w * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def anime_style(img: np.ndarray, intensity: float = 1.0) -> np.ndarray:
    orig = img.copy()
    img = _resize_if_needed(img)

    color = cv2.bilateralFilter(img, 9, 300, 300)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 2
    )
    edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    hsv = cv2.cvtColor(color, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.25, 0, 255)
    hsv[..., 2] = np.clip(hsv[..., 2] * 1.1, 0, 255)
    color = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    Z = color.reshape((-1, 3)).astype(np.float32)
    K = 12
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, label, center = cv2.kmeans(Z, K, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    center = np.uint8(center)
    quantized = center[label.flatten()].reshape(color.shape)

    result = cv2.bitwise_and(quantized, edges)

    if result.shape != orig.shape:
        result = cv2.resize(result, (orig.shape[1], orig.shape[0]), interpolation=cv2.INTER_LINEAR)
    return _blend(orig, result, intensity)


def sketch_style(img: np.ndarray, intensity: float = 1.0) -> np.ndarray:
    orig = img.copy()
    img = _resize_if_needed(img)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    invert = cv2.bitwise_not(gray)
    blur = cv2.GaussianBlur(invert, (21, 21), 0)
    inv_blur = cv2.bitwise_not(blur)
    sketch = cv2.divide(gray, inv_blur, scale=256.0)

    sketch = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)

    noise = np.random.normal(0, 8, sketch.shape).astype(np.int16)
    sketch = np.clip(sketch.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    if sketch.shape != orig.shape:
        sketch = cv2.resize(sketch, (orig.shape[1], orig.shape[0]), interpolation=cv2.INTER_LINEAR)
    return _blend(orig, sketch, intensity)


def vintage_style(img: np.ndarray, intensity: float = 1.0) -> np.ndarray:
    orig = img.copy()
    img = _resize_if_needed(img).astype(np.float32)

    result = img.copy()
    result[..., 0] = np.clip(result[..., 0] * 0.75 + 35, 0, 255)
    result[..., 1] = np.clip(result[..., 1] * 0.88 + 20, 0, 255)
    result[..., 2] = np.clip(result[..., 2] * 1.05, 0, 255)

    h, w = result.shape[:2]
    kernel_size = min(h, w) // 2
    if kernel_size % 2 == 0:
        kernel_size += 1
    result = cv2.GaussianBlur(result, (kernel_size, kernel_size), 0)

    kernel_vignette = np.ones_like(result)
    for i in range(h):
        for j in range(w):
            dx = (j - w / 2) / (w / 2)
            dy = (i - h / 2) / (h / 2)
            d = np.sqrt(dx * dx + dy * dy)
            factor = 1.0 - 0.5 * min(1.0, d * 0.9)
            kernel_vignette[i, j] = factor

    result = (result * kernel_vignette).astype(np.float32)

    noise = np.random.normal(0, 6, result.shape).astype(np.float32)
    result = np.clip(result + noise, 0, 255).astype(np.uint8)

    if result.shape != orig.shape:
        result = cv2.resize(result, (orig.shape[1], orig.shape[0]), interpolation=cv2.INTER_LINEAR)
    return _blend(orig, result, intensity)


def cartoon_style(img: np.ndarray, intensity: float = 1.0) -> np.ndarray:
    orig = img.copy()
    img = _resize_if_needed(img)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 7)
    edges = cv2.Canny(blur, 80, 160)
    edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)
    edges = 255 - edges
    edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    color = cv2.bilateralFilter(img, 12, 250, 250)

    hsv = cv2.cvtColor(color, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.4, 0, 255)
    hsv[..., 2] = np.clip(hsv[..., 2] * 1.15, 0, 255)
    color = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    result = cv2.bitwise_and(color, edges)

    if result.shape != orig.shape:
        result = cv2.resize(result, (orig.shape[1], orig.shape[0]), interpolation=cv2.INTER_LINEAR)
    return _blend(orig, result, intensity)


def oil_paint_style(img: np.ndarray, intensity: float = 1.0) -> np.ndarray:
    orig = img.copy()
    img = _resize_if_needed(img)

    result = cv2.ximgproc.anisotropicDiffusion(img, 0.01, 0.05, 5) if hasattr(cv2, 'ximgproc') else cv2.bilateralFilter(img, 15, 150, 150)
    h, w = result.shape[:2]
    radius = 5
    intensities = 20
    output = np.zeros_like(result)

    for y in range(h):
        for x in range(w):
            y_min = max(0, y - radius)
            y_max = min(h, y + radius + 1)
            x_min = max(0, x - radius)
            x_max = min(w, x + radius + 1)
            region = result[y_min:y_max, x_min:x_max]

            gray_region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            gray_idx = (gray_region * intensities / 255).astype(np.uint8)

            max_count = 0
            best_i = 0
            for i in range(intensities + 1):
                count = np.sum(gray_idx == i)
                if count > max_count:
                    max_count = count
                    best_i = i

            mask = (gray_idx == best_i)
            masked = region[mask]
            if len(masked) > 0:
                output[y, x] = np.mean(masked, axis=0)

    if output.shape != orig.shape:
        output = cv2.resize(output, (orig.shape[1], orig.shape[0]), interpolation=cv2.INTER_LINEAR)
    return _blend(orig, output, intensity)


def watercolor_style(img: np.ndarray, intensity: float = 1.0) -> np.ndarray:
    orig = img.copy()
    img = _resize_if_needed(img)

    bilateral = cv2.bilateralFilter(img, 12, 150, 150)

    h, w = bilateral.shape[:2]
    alpha = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            alpha[y, x] = 0.7 + 0.3 * np.random.random()
    alpha3 = np.stack([alpha] * 3, axis=-1)

    blurred = cv2.GaussianBlur(bilateral, (0, 0), 3)
    result = (bilateral.astype(np.float32) * alpha3 + blurred.astype(np.float32) * (1 - alpha3))
    result = np.clip(result, 0, 255).astype(np.uint8)

    hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 0.75, 0, 255)
    hsv[..., 2] = np.clip(hsv[..., 2] * 1.1, 0, 255)
    result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    if result.shape != orig.shape:
        result = cv2.resize(result, (orig.shape[1], orig.shape[0]), interpolation=cv2.INTER_LINEAR)
    return _blend(orig, result, intensity)


def pixel_style(img: np.ndarray, intensity: float = 1.0) -> np.ndarray:
    orig = img.copy()
    h, w = orig.shape[:2]

    pixel_size = max(4, int(min(h, w) / 120))
    small_h = h // pixel_size
    small_w = w // pixel_size

    small = cv2.resize(orig, (small_w, small_h), interpolation=cv2.INTER_NEAREST)
    result = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

    hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.15, 0, 255)
    result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    return _blend(orig, result, intensity)


def cyberpunk_style(img: np.ndarray, intensity: float = 1.0) -> np.ndarray:
    orig = img.copy()
    img = _resize_if_needed(img).astype(np.float32)

    result = img.copy()
    result[..., 0] = np.clip(result[..., 0] * 1.4 - 20, 0, 255)
    result[..., 1] = np.clip(result[..., 1] * 0.75 + 10, 0, 255)
    result[..., 2] = np.clip(result[..., 2] * 0.9 + 40, 0, 255)

    h, w, _ = result.shape
    hsv = cv2.cvtColor(result.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    for i in range(h):
        row_factor = 1.0 + 0.0008 * abs(i - h / 2)
        hsv[i, :, 2] = np.clip(hsv[i, :, 2] * row_factor, 0, 255)
    result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

    noise = np.random.normal(0, 4, result.shape).astype(np.float32)
    result = np.clip(result + noise, 0, 255).astype(np.uint8)

    lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[..., 0] = np.clip(lab[..., 0] * 1.05, 0, 255)
    result = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)

    if result.shape != orig.shape:
        result = cv2.resize(result, (orig.shape[1], orig.shape[0]), interpolation=cv2.INTER_LINEAR)
    return _blend(orig, result, intensity)


STYLE_FUNCTIONS: dict[str, Callable] = {
    "anime": anime_style,
    "sketch": sketch_style,
    "vintage": vintage_style,
    "cartoon": cartoon_style,
    "oil_paint": oil_paint_style,
    "watercolor": watercolor_style,
    "pixel": pixel_style,
    "cyberpunk": cyberpunk_style,
}


def process_image(image_bytes: bytes, style_id: str, intensity: float = 0.8) -> bytes:
    if style_id not in STYLE_FUNCTIONS:
        raise ValueError(f"Unknown style: {style_id}")

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image data")

    logger.info(f"Processing image shape={img.shape}, style={style_id}, intensity={intensity}")

    func = STYLE_FUNCTIONS[style_id]
    result = func(img, intensity=intensity)

    _, encoded = cv2.imencode(".png", result, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return encoded.tobytes()
