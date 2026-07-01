"""Bootstrap/Icons 정적 파일을 로컬 static 폴더에 다운로드합니다.
배포 전 또는 buildCommand에 추가하여 실행하세요.
"""
import urllib.request
import os

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "fonts"), exist_ok=True)

FILES = [
    (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css",
        "css/bootstrap.min.css",
    ),
    (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js",
        "js/bootstrap.bundle.min.js",
    ),
    (
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
        "css/bootstrap-icons.min.css",
    ),
    (
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff2",
        "fonts/bootstrap-icons.woff2",
    ),
    (
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff",
        "fonts/bootstrap-icons.woff",
    ),
]

for url, rel_path in FILES:
    dest = os.path.join(STATIC_DIR, rel_path)
    if os.path.exists(dest):
        print(f"이미 존재: {rel_path}")
        continue
    print(f"다운로드 중: {rel_path}")
    urllib.request.urlretrieve(url, dest)
    print(f"완료: {rel_path}")

# bootstrap-icons.min.css의 폰트 경로를 로컬 경로로 수정
css_path = os.path.join(STATIC_DIR, "css/bootstrap-icons.min.css")
with open(css_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("../fonts/", "/static/fonts/")

with open(css_path, "w", encoding="utf-8") as f:
    f.write(content)

print("\n정적 파일 다운로드 완료!")
