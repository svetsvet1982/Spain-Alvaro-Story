"""알바로 이야기 화별 음성 생성 (Microsoft Edge AI 음성).

사용법:
  python3 tools/tts_episode.py 1178            # 전체 화 번호 하나
  python3 tools/tts_episode.py 1178-1182       # 범위
  python3 tools/tts_episode.py --arc 96 1-5    # 96부작 1~5화
옵션:
  --role 이름     역할연습판에서 비울 인물 (기본: Álvaro, 여러 명은 쉼표로)
  --no-slow       느린판(0.8배속) 생략
  --out 폴더      출력 폴더 (기본: 음성)
필요: pip install edge-tts, ffmpeg, 네트워크에서 speech.platform.bing.com 허용.
"""
import argparse, asyncio, json, os, re, subprocess, sys, tempfile
import certifi
if os.path.exists('/root/.ccr/ca-bundle.crt'):
    certifi.where = lambda: '/root/.ccr/ca-bundle.crt'   # 클라우드 세션의 프록시 인증서
import edge_tts, docx, openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROXY = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
SPK = re.compile(r'^([^:()]{1,40}?)(?: \([^)]*\))?:\s+(.*)$')

ap = argparse.ArgumentParser()
ap.add_argument('eps'); ap.add_argument('--arc', type=int)
ap.add_argument('--role', default='Álvaro'); ap.add_argument('--no-slow', action='store_true')
ap.add_argument('--out', default=os.path.join(ROOT, '음성'))
a = ap.parse_args()

wb = openpyxl.load_workbook(os.path.join(ROOT, '알바로_부작_화_목록.xlsx'))
rows = [r for r in wb['화 목록'].iter_rows(min_row=2, values_only=True) if r[0]]
pos = {r[0]: r[4] for r in rows}; arcof = {r[0]: r[1] for r in rows}
titles = {r[0]: r[2] for r in wb['부작 목록'].iter_rows(min_row=2, values_only=True) if isinstance(r[0], int)}
lo, _, hi = a.eps.partition('-'); lo = int(lo); hi = int(hi or lo)
if a.arc:
    first = min(e for e in pos if arcof[e] == a.arc)
    eps = [first + i - 1 for i in range(lo, hi + 1)]
else:
    eps = list(range(lo, hi + 1))
L = [p.text for p in docx.Document(os.path.join(ROOT, '알바로_대화문_심문확장.docx')).paragraphs]
V = json.load(open(os.path.join(ROOT, 'tools', 'voices.json'), encoding='utf-8'))
roles = set(x.strip() for x in a.role.split(',') if x.strip())

def voice(who):
    if who in V: return V[who]
    return ['es-ES-XimenaNeural', '+0Hz', '+0%'] if who.rstrip().endswith('a') else ['es-AR-TomasNeural', '+0Hz', '+0%']

def run(*cmd): subprocess.run(cmd, check=True)
def dur(f): return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout)
def silence(sec, f): run('ffmpeg', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono', '-t', f'{sec:.2f}', '-c:a', 'libmp3lame', '-b:a', '48k', f); return f

async def tts(text, v, f):
    await edge_tts.Communicate(text, v[0], pitch=v[1], rate=v[2], proxy=PROXY).save(f)

os.makedirs(a.out, exist_ok=True)
for e in eps:
    seg = [t.strip() for t in L[pos[e]:pos.get(e + 1, len(L))] if t.strip()]
    items = [('_ko', seg[0])]
    for l in seg[1:]:
        m = SPK.match(l)
        if m:
            t = re.sub(r'\([^)]*\)', '', m.group(2)).strip()
            if t: items.append((m.group(1).strip(), t))
    k = e - min(x for x in pos if arcof[x] == arcof[e]) + 1
    base = os.path.join(a.out, f'{arcof[e]:02d}부작_{k:02d}화_{e}화')
    tmp = tempfile.mkdtemp()
    fs = []
    for i, (who, t) in enumerate(items):
        f = f'{tmp}/{i:03d}.mp3'; asyncio.run(tts(t, voice(who), f)); fs.append(f)
    s05 = silence(0.5, f'{tmp}/s05.mp3'); s12 = silence(1.2, f'{tmp}/s12.mp3')
    def build(name, blank):
        lst = f'{tmp}/{name}.txt'; lines = []
        for i, ((who, _), f) in enumerate(zip(items, fs)):
            lines.append(f"file '{silence(dur(f) + 1.0, f'{tmp}/b{i}.mp3') if who in blank else f}'")
            lines.append(f"file '{s12 if i == 0 else s05}'")
        open(lst, 'w').write('\n'.join(lines))
        o = f'{base}_{name}.mp3'
        run('ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-ar', '24000', '-ac', '1', '-b:a', '64k', o)
        return o
    o = build('기본', set())
    if roles: build('역할연습_' + '_'.join(sorted(roles)), roles)
    if not a.no_slow:
        run('ffmpeg', '-loglevel', 'error', '-y', '-i', o, '-filter:a', 'atempo=0.8', '-b:a', '64k', f'{base}_느린판.mp3')
    used = sorted({w for w, _ in items if w != '_ko'})
    print(f'{e}화 ({titles.get(arcof[e], "")} {k}화): {dur(o)/60:.1f}분 · 인물: ' + ', '.join(f'{w}={voice(w)[0]}' for w in used))
