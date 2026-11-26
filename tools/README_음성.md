# 음성 파일 만들기 (Microsoft Edge AI 음성)

## 준비 (한 번만)
- 클라우드 세션을 **Spain-Alvaro-Story 환경**으로 시작합니다. 이 환경은 `speech.platform.bing.com` 접속이 허용돼 있습니다.
- `pip install edge-tts`, ffmpeg가 필요합니다. 환경의 설정 스크립트가 있으면 자동으로 설치됩니다.

## 사용법
```
python3 tools/tts_episode.py --arc 96 1-5          # 96부작 1~5화
python3 tools/tts_episode.py 1178-1182             # 전체 화 번호로
python3 tools/tts_episode.py --arc 97 3 --role Nora,Ofelia   # 역할연습판에서 노라·오펠리아 대사를 비움
python3 tools/tts_episode.py --arc 98 1-38 --no-slow         # 느린판 생략
```
- 화마다 `음성/` 폴더에 3개 파일이 생깁니다: `_기본`, `_느린판`(0.8배속), `_역할연습_인물`(그 인물 대사 자리를 비움).
- 인물별 목소리는 `tools/voices.json`에서 바꿉니다. 목록에 없는 인물은 이름이 a로 끝나면 여성, 아니면 남성 목소리로 읽습니다.
- 한국어 상황 설명은 한국어 음성으로 읽고, 괄호 지문은 읽지 않습니다.

## 다른 대화창에서 쓸 프롬프트 예시
> Spain-Alvaro-Story 저장소의 `tools/README_음성.md`를 읽고, `tools/tts_episode.py`로 97부작 1~5화 음성 파일을 만들어. 역할연습판은 오펠리아로. 다 되면 `claude/amazing-davinci-bqdi00` 브랜치에 커밋·푸시하고 파일을 보내 줘.
