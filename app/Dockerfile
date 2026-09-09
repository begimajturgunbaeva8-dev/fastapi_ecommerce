FROM python:3.12-alpine

# устанавливаем переменные окружения
ENV HOME=/home/fast \
    APP_HOME=/home/fast/app \
    PYTHONPATH="/home/fast" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# создаем домашнюю директорию для пользователя(/home/fast) и директорию для проекта(/home/fast/app)
# создаем группу fast
# создаем отдельного пользователя fast
RUN mkdir -p $APP_HOME \
    && addgroup -S fast \
    && adduser -S fast -G fast

# устанавливаем рабочую директорию
WORKDIR $HOME

# копирование проекта FastAPI в рабочую директорию
# Copy files with proper ownership directly
COPY --chown=fast:fast app app
COPY --chown=fast:fast media media
COPY --chown=fast:fast requirements.txt alembic.ini .env ./

# Upgrade pip and install requirements
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Switch to non-root user after setup
USER fast
