# -*- coding: utf-8 -*-
import os
import re

# HTML 템플릿 - 메인 에피소드 목록 리스트
INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{webtoon_name} - 에피소드 목록</title>
    <style>
        body {{
            background-color: #1e1e2e;
            color: #e0e0e0;
            font-family: '맑은 고딕', 'Malgun Gothic', sans-serif;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        h1 {{
            color: #03c75a;
            text-align: center;
            border-bottom: 2px solid #3a3a5a;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .episode-list {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .episode-item {{
            background-color: #2a2a3e;
            padding: 15px 20px;
            border-radius: 8px;
            text-decoration: none;
            color: #e0e0e0;
            font-size: 1.1em;
            transition: background-color 0.2s, transform 0.1s;
            border-left: 5px solid #03c75a;
        }}
        .episode-item:hover {{
            background-color: #383852;
            transform: translateX(5px);
        }}
        .episode-number {{
            color: #03c75a;
            font-weight: bold;
            display: inline-block;
            width: 60px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 {webtoon_name}</h1>
        <div class="episode-list">
            {episode_links}
        </div>
    </div>
</body>
</html>
"""

# HTML 템플릿 - 개별 에피소드 뷰어
VIEWER_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{episode_name} - {webtoon_name}</title>
    <style>
        body {{
            background-color: #121212;
            color: #e0e0e0;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            font-family: '맑은 고딕', 'Malgun Gothic', sans-serif;
        }}
        .nav-bar {{
            position: sticky;
            top: 0;
            width: 100%;
            background-color: rgba(30, 30, 46, 0.95);
            display: flex;
            justify-content: center;
            padding: 15px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
            z-index: 1000;
            backdrop-filter: blur(5px);
        }}
        .nav-container {{
            width: 100%;
            max-width: 800px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 15px;
            box-sizing: border-box;
        }}
        .top-nav-stack {{
            display: flex;
            flex-direction: column;
            width: 100%;
            gap: 12px;
        }}
        .nav-top-actions {{
            display: flex;
            justify-content: center;
            gap: 10px;
            width: 100%;
        }}
        .nav-main {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
        }}
        .nav-btn {{
            color: #fff;
            text-decoration: none;
            background-color: #03c75a;
            padding: 8px 16px;
            border-radius: 4px;
            font-family: inherit;
            font-weight: bold;
            font-size: 0.95em;
            transition: background-color 0.2s;
            white-space: nowrap;
        }}
        .nav-btn:hover {{
            background-color: #02a84a;
        }}
        .nav-btn.disabled {{
            background-color: #444;
            color: #888;
            pointer-events: none;
        }}
        .nav-select {{
            padding: 8px 12px;
            border-radius: 4px;
            background-color: #2a2a3e;
            color: #fff;
            border: 1px solid #444;
            font-family: inherit;
            font-size: 0.95em;
            cursor: pointer;
            outline: none;
        }}
        .nav-select:hover {{
            border-color: #03c75a;
        }}
        .nav-select option {{
            background-color: #1e1e2e;
            color: #fff;
        }}
        .title-text {{
            color: #e0e0e0;
            font-family: inherit;
            font-size: 1.1em;
            font-weight: bold;
            text-align: center;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            flex-grow: 1;
            margin: 0 15px;
        }}
        .viewer-container {{
            max-width: 800px;
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-top: 10px;
        }}
        .viewer-container img {{
            width: 100%;
            height: auto;
            display: block; /* 이미지 사이의 여백 제거 */
        }}
        .author-box {{
            width: 100%;
            max-width: 760px;
            margin: 30px 20px 20px 20px;
            background-color: #232334;
            border: 1px solid #3a3a5a;
            border-left: 4px solid #03c75a;
            border-radius: 8px;
            padding: 16px 20px;
            box-sizing: border-box;
        }}
        .author-box-header {{
            color: #03c75a;
            font-weight: bold;
            font-size: 1.0em;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .author-box-content {{
            color: #d0d0d0;
            font-size: 0.95em;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .comments-section {{
            width: 100%;
            max-width: 760px;
            margin: 20px auto 40px auto;
            padding: 0 20px;
            box-sizing: border-box;
        }}
        .comments-header {{
            color: #03c75a;
            font-weight: bold;
            font-size: 1.1em;
            border-bottom: 2px solid #3a3a5a;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        .comment-card {{
            background-color: #232334;
            border: 1px solid #333348;
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 10px;
        }}
        .comment-meta {{
            display: flex;
            justify-content: space-between;
            font-size: 0.85em;
            color: #8888aa;
            margin-bottom: 6px;
        }}
        .comment-user {{
            font-weight: bold;
            color: #c0c0d8;
        }}
        .comment-text {{
            color: #e0e0e0;
            font-size: 0.95em;
            line-height: 1.5;
            word-break: break-word;
            margin-bottom: 8px;
        }}
        .comment-stats {{
            font-size: 0.85em;
            color: #03c75a;
            display: flex;
            gap: 15px;
        }}
        .bottom-nav {{
            margin-top: 20px;
            margin-bottom: 60px;
        }}
    </style>
</head>
<body>
    <div class="nav-bar">
        <div class="nav-container">
            <div class="top-nav-stack">
                <div class="nav-top-actions">
                    <a href="../{index_filename}" class="nav-btn" style="background-color: #3a3a5a;">목록으로</a>
                    <select class="nav-select" onchange="if(this.value) window.location.href=this.value;">
                        <option value="" disabled>회차 이동...</option>
                        {episode_options}
                    </select>
                </div>
                <div class="nav-main">
                    {prev_btn}
                    <div class="title-text">{episode_name}</div>
                    {next_btn}
                </div>
            </div>
        </div>
    </div>
    
    <div class="viewer-container">
        {audio_player}
        {image_tags}
        {author_box}
        {comments_box}
    </div>

    <div class="nav-bar bottom-nav" style="position: relative; box-shadow: none; background-color: transparent;">
        <div class="nav-container" style="justify-content: center; gap: 15px;">
            {prev_btn}
            <a href="../{index_filename}" class="nav-btn" style="background-color: #3a3a5a;">목록으로</a>
            {next_btn}
        </div>
    </div>
    
    <script>
        let lastScrollTop = 0;
        const navBar = document.querySelector('.nav-bar');
        window.addEventListener('scroll', function() {{
            let scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            if (scrollTop > lastScrollTop && scrollTop > 50) {{
                navBar.style.transform = 'translateY(-100%)';
                navBar.style.transition = 'transform 0.3s ease-in-out';
            }} else {{
                navBar.style.transform = 'translateY(0)';
            }}
            lastScrollTop = scrollTop;
        }});
    </script>
</body>
</html>
"""

def generate_viewer(webtoon_folder: str):
    """
    다운로드된 웹툰 폴더를 스캔하여 오프라인 HTML 뷰어를 생성합니다.
    - webtoon_folder 내의 에피소드 폴더 목록 구성
    - webtoon_folder/[웹툰명] 모아보기.html 생성 (목록)
    - webtoon_folder/오프라인 뷰어/[에피소드명].html 생성 (뷰어)
    """
    import json
    from utils import sanitize_filename

    webtoon_name = os.path.basename(os.path.normpath(webtoon_folder))
    
    # 1. '오프라인 뷰어' 폴더 생성
    viewer_dir = os.path.join(webtoon_folder, "오프라인 뷰어")
    if not os.path.exists(viewer_dir):
        os.makedirs(viewer_dir, exist_ok=True)
    
    # 2. 에피소드 폴더 목록 스캔 및 정렬
    items = os.listdir(webtoon_folder)
    episodes = []
    
    for item in items:
        item_path = os.path.join(webtoon_folder, item)
        if os.path.isdir(item_path) and item != "오프라인 뷰어":
            # '숫자화_문자열' 패턴인지 검사
            match = re.match(r'^(\d+)화_', item)
            if match:
                ep_no = int(match.group(1))
                episodes.append({'dir': item, 'no': ep_no, 'path': item_path})
                
    if not episodes:
        return # 에피소드가 없으면 무시
        
    # 회차 번호 기준으로 오름차순 정렬 (Gap이 있어도 안전하게 정렬)
    episodes.sort(key=lambda e: e['no'])
    
    # 3. 메인 [웹툰명] 모아보기.html 생성 (목록)
    index_filename = f"{sanitize_filename(webtoon_name)} 모아보기.html"
    
    episode_links = []
    for ep in episodes:
        dir_name = str(ep['dir'])
        title_part = dir_name.split('_', 1)[1] if '_' in dir_name else dir_name
        viewer_html_name = f"{sanitize_filename(dir_name)}.html"
        link_html = f'''
        <a href="오프라인 뷰어/{viewer_html_name}" class="episode-item">
            <span class="episode-number">{ep['no']}화</span>
            <span class="episode-title">{title_part}</span>
        </a>'''
        episode_links.append(link_html)
        
    index_content = INDEX_TEMPLATE.format(
        webtoon_name=webtoon_name,
        episode_links="".join(reversed(episode_links)) # 최신화가 위에 오도록
    )
    
    index_path = os.path.join(webtoon_folder, index_filename)
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
        
    # 4. '오프라인 뷰어' 폴더 내에 각 에피소드용 HTML 생성
    for i, ep in enumerate(episodes):
        dir_name = str(ep['dir'])
        viewer_html_name = f"{sanitize_filename(dir_name)}.html"
        
        # 이전 화 / 다음 화 링크 (Gap이 있어도 실제 인접 회차로 정확히 연결)
        prev_link = f"./{sanitize_filename(episodes[i-1]['dir'])}.html" if i > 0 else "#"
        next_link = f"./{sanitize_filename(episodes[i+1]['dir'])}.html" if i < len(episodes) - 1 else "#"
        
        prev_btn = f'<a href="{prev_link}" class="nav-btn{" disabled" if i == 0 else ""}">◀ 이전 화</a>'
        next_btn = f'<a href="{next_link}" class="nav-btn{" disabled" if i == len(episodes)-1 else ""}">다음 화 ▶</a>'
        
        ep_dir = ep['path']
        
        # BGM 오디오 파일 수집
        audio_player = ""
        for file in os.listdir(ep_dir):
            if file.lower().endswith(('.mp3', '.m4a', '.wav', '.ogg')):
                audio_src = f"../{dir_name}/{file}"
                audio_player = f'''
        <div class="audio-container" style="width: 100%; max-width: 600px; margin: 15px 0 20px 0; text-align: center; background: #2a2a3e; padding: 12px 16px; border-radius: 8px; border: 1px solid #3a3a5a; box-sizing: border-box;">
            <div style="color: #03c75a; font-size: 0.9em; font-weight: bold; margin-bottom: 8px;">🎵 배경음악 (BGM)</div>
            <audio controls loop style="width: 100%; outline: none;">
                <source src="{audio_src}">
                브라우저가 오디오 재생을 지원하지 않습니다.
            </audio>
        </div>'''
                break

        # 이미지 파일 목록 수집
        img_files = []
        for file in os.listdir(ep_dir):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')) and not file.startswith('thumbnail'):
                img_files.append(file)
                
        # 파일명 기준 정렬
        img_files.sort()
        
        image_tags = []
        for img in img_files:
            image_tags.append(f'<img src="../{dir_name}/{img}" loading="lazy" alt="Image">')
            
        # 작가의 말 (info.json 또는 author_words.txt)
        author_box = ""
        info_json_path = os.path.join(ep_dir, "info.json")
        if os.path.exists(info_json_path):
            try:
                with open(info_json_path, "r", encoding="utf-8") as f:
                    ep_meta = json.load(f)
                    words = ep_meta.get("author_words", "").strip()
                    if words:
                        author_box = f'''
        <div class="author-box">
            <div class="author-box-header">✍ 작가의 말</div>
            <div class="author-box-content">{words}</div>
        </div>'''
            except Exception:
                pass

        # 베스트 댓글 (comments.json)
        comments_box = ""
        comments_json_path = os.path.join(ep_dir, "comments.json")
        if os.path.exists(comments_json_path):
            try:
                with open(comments_json_path, "r", encoding="utf-8") as f:
                    comments_data = json.load(f)
                    if isinstance(comments_data, list) and comments_data:
                        c_cards = []
                        for c in comments_data:
                            c_cards.append(f'''
            <div class="comment-card">
                <div class="comment-meta">
                    <span class="comment-user">{c.get('userName', '익명')}</span>
                    <span>{c.get('regTime', '')}</span>
                </div>
                <div class="comment-text">{c.get('contents', '')}</div>
                <div class="comment-stats">
                    <span>👍 {c.get('sympathyCount', 0)}</span>
                    <span>👎 {c.get('antipathyCount', 0)}</span>
                </div>
            </div>''')
                        comments_box = f'''
        <div class="comments-section">
            <div class="comments-header">💬 베스트 댓글 ({len(comments_data)})</div>
            {"".join(c_cards)}
        </div>'''
            except Exception:
                pass

        title_part = dir_name.split('_', 1)[1] if '_' in dir_name else dir_name
        episode_name = f"{ep['no']}화 {title_part}"
        
        # 에피소드 선택 옵션 생성 (동일 폴더 내 파일 참조)
        episode_options_list = []
        for option_ep in reversed(episodes):
            opt_dir = str(option_ep['dir'])
            opt_title_part = opt_dir.split('_', 1)[1] if '_' in opt_dir else opt_dir
            opt_name = f"{option_ep['no']}화 {opt_title_part}"
            opt_val = f"./{sanitize_filename(opt_dir)}.html"
            
            selected = " selected" if ep['path'] == option_ep['path'] else ""
            episode_options_list.append(f'<option value="{opt_val}"{selected}>{opt_name}</option>')
            
        episode_options = "\n                    ".join(episode_options_list)
        
        viewer_content = VIEWER_TEMPLATE.format(
            webtoon_name=webtoon_name,
            episode_name=episode_name,
            prev_btn=prev_btn,
            next_btn=next_btn,
            audio_player=audio_player,
            image_tags="\n        ".join(image_tags),
            author_box=author_box,
            comments_box=comments_box,
            index_filename=index_filename,
            episode_options=episode_options
        )
        
        viewer_path = os.path.join(viewer_dir, viewer_html_name)
        with open(viewer_path, 'w', encoding='utf-8') as f:
            f.write(viewer_content)

