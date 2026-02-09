import os
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from passlib.context import CryptContext
from typing import Optional

# =====================
# 環境変数
# =====================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL / SUPABASE_KEY が未設定です")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================
# FastAPI 設定
# =====================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番では制限推奨
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =====================
# Models
# =====================
class RegisterData(BaseModel):
    username: str
    password: str

class LoginData(BaseModel):
    username: str
    password: str

class PostData(BaseModel):
    body: str
    username: Optional[str] = None  # フロントには不要
    password: Optional[str] = None  # フロントには不要

# =====================
# ユーザー登録
# =====================
@app.post("/api/auth/register")
async def register(data: RegisterData):
    if len(data.username) < 3 or len(data.password) < 4:
        raise HTTPException(status_code=400, detail="入力が短すぎます")

    hashed = pwd_context.hash(data.password)
    try:
        supabase.table("users").insert({
            "username": data.username,
            "password": hashed
        }).execute()
        return {"success": True}
    except Exception:
        raise HTTPException(status_code=409, detail="ユーザー名は既に使われています")

# =====================
# ログイン
# =====================
@app.post("/api/auth/login")
async def login(data: LoginData):
    res = supabase.table("users") \
        .select("id, password") \
        .eq("username", data.username) \
        .limit(1) \
        .execute()

    if not res.data:
        raise HTTPException(status_code=401, detail="ユーザーが存在しません")

    user = res.data[0]
    if not pwd_context.verify(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="パスワードが違います")

    return {"success": True, "user_id": user["id"], "username": data.username}

# =====================
# 投稿取得
# =====================
@app.get("/api/bbs/posts")
async def get_posts():
    try:
        res = supabase.table("posts") \
            .select("id, username, body, created_at") \
            .order("created_at", desc=True) \
            .execute()
        return {"posts": res.data}
    except Exception:
        raise HTTPException(status_code=500, detail="投稿取得に失敗しました")

# =====================
# 投稿作成
# =====================
@app.post("/api/bbs/post")
async def create_post(data: PostData, user_id: Optional[int] = None):
    if not data.body.strip():
        raise HTTPException(status_code=400, detail="本文が空です")

    # フロントはログインユーザーIDを送る
    if not user_id:
        raise HTTPException(status_code=401, detail="ログインしてください")

    try:
        now = datetime.now(timezone.utc).isoformat()
        supabase.table("posts").insert({
            "user_id": user_id,
            "username": data.username,
            "body": data.body.strip(),
            "created_at": now
        }).execute()
        return {"success": True}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="投稿に失敗しました")

# =====================
# HTMLページ
# =====================
@app.get("/bbs", response_class=HTMLResponse)
async def bbs_page(request: Request):
    return templates.TemplateResponse("bbs.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})
