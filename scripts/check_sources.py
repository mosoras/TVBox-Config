#!/usr/bin/env python3
# MOSORA TVBox source checker - runs on GitHub Actions, no local Python needed.
import json, os, time, urllib.request, urllib.error, concurrent.futures
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'tvbox.json'
OUT = ROOT / 'site' / 'health.json'
TIMEOUT = 12
UA = 'Mozilla/5.0 (compatible; MOSORA-TVBox-Checker/1.0)'


def check(site):
    name = str(site.get('name') or site.get('key') or '未命名')
    key = str(site.get('key') or '')
    api = str(site.get('api') or '')
    stype = site.get('type')
    base = {'name': name, 'key': key, 'type': stype, 'api': api}
    # TVBox csp_* APIs are JavaScript/JAR classes, not ordinary HTTP endpoints.
    if str(stype) == '3' or not api.startswith(('http://', 'https://')):
        return {**base, 'status': '需TVBox实测', 'detail': '依赖 TVBox Spider/JAR 或客户端专用接口，不能用普通网页请求判断'}
    if str(stype) != '1':
        return {**base, 'status': '需TVBox实测', 'detail': '此类型不适合用通用 HTTP API 检测'}
    req = urllib.request.Request(api, headers={'User-Agent': UA, 'Accept': 'application/json, application/xml, text/xml, */*'})
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            code = r.status
            ctype = r.headers.get('Content-Type', '')
            body = r.read(512 * 1024)
        elapsed = round((time.time() - started) * 1000)
        if not body:
            return {**base, 'status': '访问异常', 'detail': f'HTTP {code}，响应为空', 'http': code, 'ms': elapsed}
        sample = body[:12000].decode('utf-8', 'ignore').lower()
        if any(s in sample for s in ('captcha', 'verify you are human', 'cloudflare', '安全验证', '访问过于频繁', '请求被拦截')):
            status, detail = '疑似拦截', f'HTTP {code}，返回验证码或安全拦截页面'
        elif '<html' in sample and 'json' not in ctype.lower():
            status, detail = '返回内容待确认', f'HTTP {code}，返回网页而非明显的 API 数据'
        else:
            try:
                obj = json.loads(body.decode('utf-8-sig', 'ignore'))
                if isinstance(obj, dict):
                    # MacCMS APIs commonly return code/list/class; empty list still means endpoint answered.
                    status, detail = '接口响应正常', f'HTTP {code}，JSON 响应成功'
                else:
                    status, detail = '返回内容待确认', f'HTTP {code}，JSON 格式不是常见对象结构'
            except Exception:
                if any(x in sample for x in ('<rss', '<list', '<?xml', '<class')):
                    status, detail = '接口响应正常', f'HTTP {code}，XML 响应成功'
                else:
                    status, detail = '返回内容待确认', f'HTTP {code}，有响应但无法识别为常见 JSON/XML'
        return {**base, 'status': status, 'detail': detail, 'http': code, 'ms': elapsed}
    except urllib.error.HTTPError as e:
        return {**base, 'status': '访问异常', 'detail': f'HTTP {e.code}', 'http': e.code}
    except Exception as e:
        return {**base, 'status': '访问异常', 'detail': f'{type(e).__name__}: {str(e)[:180]}'}


def main():
    if not CONFIG.exists():
        raise SystemExit('找不到仓库根目录的 tvbox.json。请确认配置文件名为 tvbox.json。')
    data = json.loads(CONFIG.read_text(encoding='utf-8-sig'))
    sites = data.get('sites', [])
    if not isinstance(sites, list):
        raise SystemExit('tvbox.json 中 sites 不是数组')
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check, [s if isinstance(s, dict) else {} for s in sites]))
    order = ['接口响应正常', '访问异常', '疑似拦截', '返回内容待确认', '需TVBox实测']
    counts = {k: sum(1 for x in results if x['status'] == k) for k in order}
    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total': len(results), 'counts': counts, 'results': results,
        'note': '仅检测 HTTP 接口的可访问性与响应格式；接口响应正常不代表视频可播放。csp/Spider 类站点需在 TVBox 内实测。'
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print('检测汇总：', counts)
    print('结果写入：', OUT)

if __name__ == '__main__':
    main()
