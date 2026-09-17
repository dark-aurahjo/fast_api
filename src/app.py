from uuid import uuid4

from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

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
def get_tasks():
    return tasks

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    task = Task(id=str(uuid4()), title=payload.title, completed=False)
    tasks.append(task)
    return task

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)