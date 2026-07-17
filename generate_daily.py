import os
import json
import requests
from datetime import datetime, timedelta, timezone

# 한국 시간(KST) 구하기
kst = timezone(timedelta(hours=9))
today = datetime.now(kst)
date_str = today.strftime('%Y-%m-%d')
display_date = today.strftime('%Y년 %m월 %d일')

# API 키 가져오기 (GitHub Secrets에서 주입)
API_KEY = os.environ.get('UPSTAGE_API_KEY')
if not API_KEY:
    raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")

def generate_content():
    url = 'https://api.upstage.ai/v1/solar/chat/completions'
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    prompt = """
    다음 조건에 맞춰 일상 생활영어 대화문 3가지를 만들어주세요:
    1. 상황: 부모와 초등학생 자녀가 겪는 일상 상황 3가지 
       (※ 매우 중요: 단순한 기상이나 등교 인사 대신 식사 편식, 친구와의 다툼, 심부름, 주말 나들이 계획, 날씨에 따른 옷차림, 감정 표현 등 매번 겹치지 않는 구체적이고 새로운 상황을 설정해 주세요.)
    2. 대화: 상황당 자주 쓰이는 2~3턴의 대화 (영어 및 한국어)
    3. 추가 학습: 각 상황의 핵심 포인트(Key Point) 1개와 유사 표현(Similar Expressions) 2개
    
    반드시 아래 JSON 형식으로만 응답하세요:
    {
      "situations": [
        {
          "title": "상황 제목",
          "dialogue": [
            { "speaker": "Parent 또는 Child", "en": "영어 문장", "ko": "한국어 해석" }
          ],
          "keyPoint": "핵심 표현",
          "similarExpressions": ["유사 표현 1", "유사 표현 2"]
        }
      ]
    }
    """
    
      prompt = """
    ... (긴 프롬프트)
    """

    payload = {        # ← 4칸 들여쓰기로 수정
        "model": "solar-pro",
        "messages": [
            {"role": "system", "content": "당신은 친절한 초등영어 선생님입니다. 매번 창의적이고 중복되지 않는 새로운 대화문을 작성합니다. JSON 포맷으로만 응답하세요."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "response_format": {"type": "json_object"}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return json.loads(response.json()['choices'][0]['message']['content'])

def create_daily_html(data):
    # 폴더가 없으면 생성
    os.makedirs('daily', exist_ok=True)
    
    cards_html = ""
    titles = []
    
    for idx, sit in enumerate(data['situations']):
        titles.append(sit['title'])
        dialogue_html = "".join([
            f"""
            <div class="mb-3 {'text-left' if d['speaker'].lower() == 'parent' else 'text-right'}">
              <span class="inline-block px-2 py-1 rounded text-xs font-bold mb-1 {'bg-indigo-100 text-indigo-800' if d['speaker'].lower() == 'parent' else 'bg-green-100 text-green-800'}">
                {'👨‍👩‍👦 부모' if d['speaker'] == 'Parent' else '👧 아이'}
              </span>
              <p class="text-lg font-semibold text-gray-800">{d['en']}</p>
              <p class="text-sm text-gray-500">{d['ko']}</p>
            </div>
            """ for d in sit['dialogue']
        ])
        
        similar_html = "".join([f'<li class="text-sm text-gray-700">💡 {exp}</li>' for exp in sit['similarExpressions']])
        
        cards_html += f"""
        <div class="bg-white rounded-xl shadow-md p-6 border-t-4 border-blue-400 mb-6">
          <h2 class="text-xl font-bold text-gray-800 mb-4 border-b pb-2">상황 {idx+1}. {sit['title']}</h2>
          <div class="bg-gray-50 rounded-lg p-4 mb-4">{dialogue_html}</div>
          <div>
            <h3 class="font-bold text-gray-800 text-sm mb-1">🎯 핵심 포인트</h3>
            <p class="text-sm text-gray-700 bg-yellow-50 p-3 rounded mb-3">{sit['keyPoint']}</p>
            <h3 class="font-bold text-gray-800 text-sm mb-1">🔄 유사 표현</h3>
            <ul class="space-y-1 bg-blue-50 p-3 rounded">{similar_html}</ul>
          </div>
        </div>
        """
        
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{display_date} 생활영어</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="p-4 md:p-8 max-w-3xl mx-auto bg-gray-100">
  <a href="../index.html" class="inline-block mb-6 text-blue-500 hover:underline font-semibold">← 목록으로 돌아가기</a>
  <h1 class="text-2xl font-bold text-gray-800 mb-6">📅 {display_date} 오늘의 회화</h1>
  {cards_html}
</body>
</html>"""

    # 오늘 날짜로 html 파일 저장
    file_path = f"daily/{date_str}.html"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return titles

def update_index_html(titles):
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
        
    # 새로운 링크 카드 생성 (최신순으로 상단에 추가하기 위해 Placeholder 바로 밑에 추가)
    summary = ", ".join(titles)
    new_card = f"""
      <!-- DAILY_CARDS_PLACEHOLDER -->
      <a href="daily/{date_str}.html" class="block bg-white p-6 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-1 transition duration-200 border border-gray-100">
        <h2 class="text-xl font-bold text-blue-600 mb-2">{display_date}</h2>
        <p class="text-gray-600 text-sm line-clamp-2">{summary}</p>
      </a>"""
      
    updated_content = content.replace("<!-- DAILY_CARDS_PLACEHOLDER -->", new_card)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(updated_content)

if __name__ == "__main__":
    print(f"{date_str} 작업 시작...")
    data = generate_content()
    titles = create_daily_html(data)
    update_index_html(titles)
    print("완료되었습니다!")
