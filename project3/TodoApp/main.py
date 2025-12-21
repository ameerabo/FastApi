from fastapi import HTTPException, Path
from typing import Annotated

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends
from starlette import status

import models
from models import Todos
from database import engine, SessionLocal  # ← תיקון

app = FastAPI()



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool





@app.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency):
    return db.query(Todos).all()


@app.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404, detail = 'Todo not found.')


@app.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, todo_request: TodoRequest):
    todo_model = Todos(**todo_request.dict())

    db.add(todo_model)
    db.commit()


@app.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    # 1. חיפוש המשימה בבסיס הנתונים לפי ה-ID
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()

    # 2. אם המשימה לא קיימת - החזרת שגיאה 404
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found.')

    # 3. עדכון השדות של האובייקט שמצאנו בנתונים החדשים מהמשתמש
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    # 4. שמירת השינויים
    db.add(todo_model)
    db.commit()


# --- תמונה 4: מחיקה (DELETE) ---
@app.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    # 1. חיפוש המשימה כדי לוודא שהיא קיימת לפני המחיקה
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()

    # 2. אם לא נמצאה - החזרת שגיאה 404
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found.')

    # 3. ביצוע המחיקה בפועל מהטבלה
    db.query(Todos).filter(Todos.id == todo_id).delete()

    # 4. שמירת השינויים במסד הנתונים
    db.commit()