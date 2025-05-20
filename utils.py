import re

def sanitize(text: str) -> str:
    """파일명에 사용할 수 없는 문자를 제거"""
    return re.sub(r'[\\/:"*?<>|]+', "_", text)
