# -*- coding: utf-8 -*-
"""
유틸리티 함수 모음
파일명 정규화, 경로 생성 등 공통 기능을 제공합니다.
"""

import os
import re


def sanitize_filename(name: str) -> str:
    """
    파일 또는 폴더 이름에 사용할 수 없는 특수문자를 제거하거나 치환합니다.
    Windows에서 사용 불가능한 문자: \\ / : * ? " < > |
    """
    # 윈도우에서 금지된 문자를 언더스코어로 치환
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    # 앞뒤 공백 및 점 제거 (Windows 제약)
    name = name.strip(' .')
    # 연속된 공백을 하나로
    name = re.sub(r'\s+', ' ', name)
    # 빈 문자열이면 기본값 반환
    if not name:
        return 'unnamed'
    return name


def make_episode_folder(base_path: str, webtoon_title: str, episode_no: int, episode_title: str) -> str:
    """
    에피소드 이미지를 저장할 폴더 경로를 생성합니다.
    구조: base_path / 웹툰제목 / 001화_에피소드제목
    중복 시 자동으로 뒤에 번호를 붙입니다.
    """
    # 웹툰 제목 폴더
    webtoon_folder = os.path.join(base_path, sanitize_filename(webtoon_title))
    # 에피소드 폴더명: 001화_제목 형식
    ep_folder_name = f"{episode_no:03d}화_{sanitize_filename(episode_title)}"
    ep_folder = os.path.join(webtoon_folder, ep_folder_name)

    # 폴더가 없으면 생성
    os.makedirs(ep_folder, exist_ok=True)
    return ep_folder


def make_webtoon_folder(base_path: str, webtoon_title: str) -> str:
    """
    웹툰 최상위 폴더 경로를 반환하고 생성합니다.
    """
    folder = os.path.join(base_path, sanitize_filename(webtoon_title))
    os.makedirs(folder, exist_ok=True)
    return folder


def format_file_size(size_bytes: int) -> str:
    """
    바이트 단위 파일 크기를 사람이 읽기 쉬운 형태로 변환합니다.
    예) 1048576 → '1.0 MB'
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"
