from fastapi import FastAPI, Request
from app.database import Base, async_engine as engine
from app.routers import categories, orders, products, users, cart
from app.routers import reviews
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import time
from loguru import logger


# Создаём таблицы
#Base.metadata.create_all(bind=engine)


# Создаём приложение FastAPI
app = FastAPI(
    title="FastAPI Интернет-магазин",
    version="0.1.0",
)

from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


@app.middleware("http")
async def log_middleware(request: Request, call_next):
    log_id = str(uuid4())
    with logger.contextualize(log_id=log_id):
        try:
            response = await call_next(request)
            if response.status_code in [401, 402, 403, 404]:
                logger.warning(f"Request to {request.url.path} failed")
            else:
                logger.info('Successfully accessed ' + request.url.path)
        except Exception as ex:
            logger.error(f"Request to {request.url.path} failed: {ex}")
            response = JSONResponse(content={"success": False}, status_code=500)
        return response

# Подключаем маршруты категорий и товаров
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(users.router)   
app.include_router(reviews.router)
app.include_router(cart.router)
app.include_router(orders.router)

# Корневой эндпоинт для проверки
@app.get("/")
async def root():
    """
    Корневой маршрут, подтверждающий, что API работает.
    """
    return {"message": "Добро пожаловать в API интернет-магазина!"}

app.mount("/media", StaticFiles(directory="media"), name="media")

# Add the session middleware first
app.add_middleware(SessionMiddleware, secret_key="my_secret_key")

# Write the route here
@app.get("/create_session")
async def session_set(request: Request):
    request.session["my_session"] = "1234"
    return "ok"

@app.get("/read_session")
async def session_info(request: Request):
    my_var = request.session.get("my_session")
    return my_var

@app.get("/delete_session")
async def session_delete(request: Request):
    my_var = request.session.pop("my_session")
    return my_var

class TimingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        start_time = time.time()
        await self.app(scope, receive, send)
        duration = time.time() - start_time
        print(f"Request duration: {duration:.10f} seconds")


app.add_middleware(TimingMiddleware)

logger.add("info.log", format="Log: [{extra[log_id]}:{time} - {level} - {message}]", level="INFO", enqueue=True)
