import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

# =========================
# FastAPI
# =========================

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# =========================
# 外部BBS API設定（Vercel）
# =========================

BBS_EXTERNAL_API_BASE_URL = "https://bbs-server.vercel.app"
MAX_API_WAIT_TIME = (3.0, 8.0)


def get_user_agent():
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }


# =========================
# 外部BBS API 呼び出し
# =========================

async def fetch_bbs_posts():
    """投稿一覧取得"""

    url = f"{BBS_EXTERNAL_API_BASE_URL}/posts"

    def sync():
        res = requests.get(
            url,
            headers=get_user_agent(),
            timeout=MAX_API_WAIT_TIME
        )
        res.raise_for_status()
        return res.json()

    return await run_in_threadpool(sync)


async def post_new_message(username: str, password: str, body: str):
    """新規投稿"""

    url = f"{BBS_EXTERNAL_API_BASE_URL}/post"

    def sync():
        res = requests.post(
            url,
            headers=get_user_agent(),
            json={
                "username": username,
                "password": password,
                "body": body
            },
            timeout=MAX_API_WAIT_TIME
        )
        res.raise_for_status()
        return res.json()

    return await run_in_threadpool(sync)


async def login_user(username: str, password: str):
    """ログイン"""

    url = f"{BBS_EXTERNAL_API_BASE_URL}/login"

    def sync():
        res = requests.post(
            url,
            headers=get_user_agent(),
            json={
                "username": username,
                "password": password
            },
            timeout=MAX_API_WAIT_TIME
        )
        res.raise_for_status()
        return res.json()

    return await run_in_threadpool(sync)


async def register_user(username: str, password: str):
    """新規登録"""

    url = f"{BBS_EXTERNAL_API_BASE_URL}/register"

    def sync():
        res = requests.post(
            url,
            headers=get_user_agent(),
            json={
                "username": username,
                "password": password
            },
            timeout=MAX_API_WAIT_TIME
        )
        res.raise_for_status()
        return res.json()

    return await run_in_threadpool(sync)


# =========================
# API（UI用プロキシ）
# =========================

@app.get("/api/bbs/posts")
async def api_get_posts():
    try:
        return await fetch_bbs_posts()

    except requests.exceptions.HTTPError as e:
        return Response(
            content=e.response.text,
            media_type="application/json",
            status_code=e.response.status_code
        )

    except Exception as e:
        return Response(
            content=f'{{"detail":"{str(e)}"}}',
            media_type="application/json",
            status_code=500
        )


@app.post("/api/bbs/post")
async def api_post_message(req: Request):
    try:
        data = await req.json()

        username = data.get("username")
        password = data.get("password")
        body = data.get("body", "").strip()

        if not username or not password or not body:
            return Response(
                content='{"detail":"username, password, body required"}',
                media_type="application/json",
                status_code=400
            )

        return await post_new_message(username, password, body)

    except requests.exceptions.HTTPError as e:
        return Response(
            content=e.response.text,
            media_type="application/json",
            status_code=e.response.status_code
        )

    except Exception as e:
        return Response(
            content=f'{{"detail":"{str(e)}"}}',
            media_type="application/json",
            status_code=500
        )


@app.post("/api/auth/login")
async def api_login(req: Request):
    try:
        data = await req.json()
        return await login_user(
            data.get("username"),
            data.get("password")
        )

    except requests.exceptions.HTTPError as e:
        return Response(
            content=e.response.text,
            media_type="application/json",
            status_code=e.response.status_code
        )

    except Exception as e:
        return Response(
            content=f'{{"detail":"{str(e)}"}}',
            media_type="application/json",
            status_code=500
        )


@app.post("/api/auth/register")
async def api_register(req: Request):
    try:
        data = await req.json()
        return await register_user(
            data.get("username"),
            data.get("password")
        )

    except requests.exceptions.HTTPError as e:
        return Response(
            content=e.response.text,
            media_type="application/json",
            status_code=e.response.status_code
        )

    except Exception as e:
        return Response(
            content=f'{{"detail":"{str(e)}"}}',
            media_type="application/json",
            status_code=500
        )


# =========================
# HTML ルート
# =========================

@app.get("/bbs", response_class=HTMLResponse)
async def bbs_page(request: Request):
    return templates.TemplateResponse(
        "bbs.html",
        {"request": request}
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )
