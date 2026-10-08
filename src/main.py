from uuid import uuid4

from fastapi import FastAPI, status, HTTPException, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    """Базовый класс для всех моделей таблиц БД"""
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))

class TaskORM(Base):
    """Модель для таблицы задачи в Базе Данных"""
    __tablename__ = "tasks"

    title: Mapped[str]
    completed: Mapped[bool] = mapped_column(default=False)

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

def get_db():
    """Функция для создания сессий с БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

book = ""

categories = [
    {
        "id": str(uuid4()),
        "name": "Учеба"
    },
    {
        "id": str(uuid4()),
        "name": "Работа"
    }
]

class Task(BaseModel):
    id: str
    title: str
    completed: bool

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str

class Book(BaseModel):
    book: str

class Category(BaseModel):
    id: str
    name: str

class CategoryCreate(BaseModel):
    name: str

class CategoryUpdate(BaseModel):
    name: str | None = None

tasks: list[Task] = []

@app.get("/tasks", response_model=list[Task])
def get_tasks(db: Session = Depends(get_db)) -> list[Task]:
    tasks = db.scalars(select(TaskORM)).all()
    return [task_to_model(task) for task in tasks]

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> Task:
    """Создать новую задачу"""
    task = TaskORM(title=payload.title, completed=False)

    db.add(task)
    db.commit()
    return task_to_model(task)

@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db)) -> Task:
    task = db.get(TaskORM, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")

    task.title = payload.title if payload.title is not None else task.title
    task.completed = payload.completed if payload.completed is not None else task.completed
    db.commit()
    return task_to_model(task)

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, db: Session = Depends(get_db)) -> None:
    """Удалить задачу"""
    task = db.get(TaskORM, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")

    db.delete(task)
    db.commit()

@app.post("/book", response_model=Book)
def create_book(data:Book):
    global book
    book = data.book
    return {"message":"Книга добавлена"}

@app.get("/book")
def get_book():
    if book:
        return {"message": f"Любимая книга: {book}"}
    else:
        return {"message": "Книга не найдена"}

@app.post("/categories", response_model=Category)
def create_category(category_create:CategoryCreate):
    global categories
    new_category = Category(id = uuid4(), name = category_create.name)
    categories.append(new_category)
    return new_category

@app.get("/categories", response_model=list[Category])
def get_categories():
    return categories

@app.patch("/categories/{category_id}", response_model=Category)
def update_category(category_id:str, category_update:CategoryUpdate):
    for category in categories:
        if category['id'] == category_id:
            category['name'] = category_update.name
            return category
    raise HTTPException(status_code=404, detail="Категория не найдена")

@app.delete("/categories/{category_id}", response_model=dict)
def delete_category(category_id:str):
    for index, category in enumerate(categories):
        if category['id'] == category_id:
            del categories[index]
            return {"message":"Категория удалена"}
    raise HTTPException(status_code=404, detail="Категория не найдена")

def task_to_model(task: TaskORM) -> Task:
    """Конвертация объекта ORM в Pydantic"""
    return Task(id=task.id, title=task.title, completed=task.completed)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)