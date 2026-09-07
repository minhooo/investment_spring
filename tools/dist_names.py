"""dist 산출물의 웹 파일명 규칙.

Vercel 정적 호스팅은 경로에 한글이 들어간 파일을 배포해도 404로 응답한다.
그래서 dist에 쓰는 파일명은 ASCII 조각(종목코드·영문 접미사)만 남긴다.
빌더 내부의 키·메타 파일명은 지금처럼 한글을 그대로 쓴다.
"""
import hashlib
import re

ASCII_PART = re.compile(r"^[A-Za-z0-9.\-]+$")


def is_web_safe(name):
    """배포 경로로 그대로 쓸 수 있는 이름인지 확인한다."""
    return bool(name) and all(ASCII_PART.match(part) for part in str(name).split("_") if part)


def dist_stem(key):
    """빌더 키에서 ASCII 조각만 남긴 dist 파일 이름(확장자 제외)을 만든다."""
    parts = [part for part in str(key).split("_") if part and ASCII_PART.match(part)]
    if not parts:
        return "page-" + hashlib.sha1(str(key).encode("utf-8")).hexdigest()[:10]
    return "_".join(parts)


def dist_page(key):
    """`dist_stem`에 .html을 붙인다. 이미 .html로 끝나면 중복해서 붙이지 않는다."""
    stem = dist_stem(key)
    return stem if stem.endswith(".html") else stem + ".html"
