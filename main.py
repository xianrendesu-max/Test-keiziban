import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# =========================
# 外部BBS API設定
# =========================

BBS_EXTERNAL_API_BASE_URL = "https://bbs-server.vercel.app/"
MAX_API_WAIT_TIME = (3.0, 8.0)


def get_random_user_agent():
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }


# =========================
# 外部BBS APIアクセス
# =========================

async def fetch_bbs_posts():
    """外部BBSから投稿一覧を取得"""

    target_url = f"{BBS_EXTERNAL_API_BASE_URL}/posts"

    def sync_fetch():
        res = requests.get(
            target_url,
            headers=get_random_user_agent(),
            timeout=MAX_API_WAIT_TIME
        )
        res.raise_for_status()
        return res.json()

    return await run_in_threadpool(sync_fetch)


async def post_new_message(client_ip: str, name: str, body: str):
    """外部BBSへ新規投稿"""

    target_url = f"{BBS_EXTERNAL_API_BASE_URL}/post"

    def sync_post():
        headers = {
            **get_random_user_agent(),
            "X-Original-Client-IP": client_ip
        }
        res = requests.post(
            target_url,
            json={
                "name": name,
                "body": body
            },
            headers=headers,
            timeout=MAX_API_WAIT_TIME
        )
        res.raise_for_status()
        return res.json()

    return await run_in_threadpool(sync_post)


# =========================
# APIルート（完全互換）
# =========================

@app.get("/api/bbs/posts")
async def get_bbs_posts_route():
    """投稿一覧取得API（保存なし）"""
    try:
        return await fetch_bbs_posts()

    except requests.exceptions.HTTPError as e:
        return Response(
            content=e.response.text,
            media_type="application/json",
            status_code=e.response.status_code
        )

    except requests.exceptions.RequestException as e:
        return Response(
            content=f'{{"detail": "BBS API connection error or timeout: {str(e)}"}}',
            media_type="application/json",
            status_code=503
        )

    except Exception as e:
        return Response(
            content=f'{{"detail": "Unexpected error: {str(e)}"}}',
            media_type="application/json",
            status_code=500
        )


@app.post("/api/bbs/post")
async def post_new_message_route(request: Request):
    """新規投稿API（保存なし）"""
    try:
        # クライアントIP（外部BBS互換）
        client_ip = (
            request.headers.get("X-Original-Client-IP")
            or request.headers.get("X-Forwarded-For")
            or request.client.host
            or "unknown"
        ).split(",")[0].strip()

        data = await request.json()
        name = data.get("name", "")
        body = data.get("body", "")

        if not body:
            return Response(
                content='{"detail": "Body is required"}',
                media_type="application/json",
                status_code=400
            )

        return await post_new_message(client_ip, name, body)

    except requests.exceptions.HTTPError as e:
        return Response(
            content=e.response.text,
            media_type="application/json",
            status_code=e.response.status_code
        )

    except requests.exceptions.RequestException as e:
        return Response(
            content=f'{{"detail": "BBS API connection error or timeout: {str(e)}"}}',
            media_type="application/json",
            status_code=503
        )

    except Exception as e:
        return Response(
            content=f'{{"detail": "Unexpected error: {str(e)}"}}',
            media_type="application/json",
            status_code=500
        )


# =========================
# HTML
# =========================

@app.get("/bbs", response_class=HTMLResponse)
async def bbs(request: Request):
    """掲示板ページ"""
    return templates.TemplateResponse(
        "bbs.html",
        {"request": request}
    )
