import cv2
import numpy as np
import os


def imread_safe(path: str):
    """한글 등 유니코드 경로를 포함한 이미지 읽기 (Windows cv2.imread 한계 우회)"""
    try:
        buf = np.fromfile(path, dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


def imwrite_safe(path: str, img) -> bool:
    """유니코드 경로에 이미지 저장"""
    try:
        ext = os.path.splitext(path)[1].lower() or ".jpg"
        ok, buf = cv2.imencode(ext, img)
        if ok:
            buf.tofile(path)
        return ok
    except Exception:
        return False
