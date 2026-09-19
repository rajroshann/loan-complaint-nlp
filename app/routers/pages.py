from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(include_in_schema=False)  # keeps these out of the /docs Swagger list - they're pages, not API endpoints
templates = Jinja2Templates(directory="app/templates")


@router.get("/login-page")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

@router.get("/predict-page")
def predict_page(request: Request):
    return templates.TemplateResponse(request, "predict.html", {})

@router.get("/history-page")
def history_page(request: Request):
    return templates.TemplateResponse(request, "history.html", {})

@router.get("/home-page")
def home_page(request: Request):
    return templates.TemplateResponse(request, "home.html", {})

@router.get("/signup-page")
def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html", {})