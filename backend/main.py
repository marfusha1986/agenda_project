from fastapi import FastAPI,HTTPException,Request
from pydantic import BaseModel
from typing import Optional
from backend.database import get_db_connection
from datetime import date
from PySide6.QtCore import QDate 


app = FastAPI(title="Agenda API",version="1.0")

#Pydantic Modelleri
class TaskCreate(BaseModel):
    title:str
    due_date:Optional[date] = None
    is_recurring:int=0
    category:Optional[str] = "Genel"

class TaskUpdate(BaseModel):
    due_time:Optional[str] = None

@app.get("/")
def read_root():
    return{"message":"Agenda API çalışıyor!"}

#1. Görev Ekleme Endpointi
@app.post("/tasks/")
def create_task(task:TaskCreate):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO tasks (title, due_date, is_recurring, status, postpone_count, category)
            VALUES (:1, :2, :3, 'pending', 0, :4)
            """,
            (task.title, task.due_date, task.is_recurring, task.category)
        )
        conn.commit()
        return {
            "status":"success",
            "message":"Görev başarıyla eklendi!"
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500,detail=str(e))

    finally:
        cursor.close()
        conn.close()

#2.Görev Listeleme Endpointi
@app.get("/tasks/")
def get_tasks():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Tarih dönüşümüyle uğraşmadan doğrudan kolonları çekiyoruz
        cursor.execute("SELECT id, title, due_date FROM tasks")
        rows = cursor.fetchall()
        
        tasks = []
        for row in rows:
            # Oracle'dan gelen tarih objesini güvenle string'e çevirelim
            raw_date = row[2]
            date_str = str(raw_date) if raw_date else "Tarihsiz"
            
            tasks.append({
                "id": row[0],
                "title": row[1],
                "due_date": date_str
            })
        return tasks
    except Exception as e:
        print("GET TASKS HATASI:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.patch("/tasks/{task_id}")
async def update_task(task_id: int, request: Request):
    body = await request.json()
    new_date = body.get("due_date") # "2026-09-23" gibi string geliyor
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Python tarafında string gelen tarihi Oracle'ın DATE tipine uygun formatlıyoruz
        cursor.execute(
            "UPDATE tasks SET due_date = TO_DATE(:due_date, 'YYYY-MM-DD') WHERE id = :id",
            {"due_date": new_date, "id": task_id}
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Görev bulunamadı")
        return {"message": "Görev başarıyla ertelendi"}
    except Exception as e:
        conn.rollback()
        print("UPDATE TASK HATASI:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

#3.Görev Erteleme  & Disiplin Kotrolu Endpointi
@app.post("/tasks/{task_id}/postpone")
def postpone_task(task_id:int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        #Önce görevin mevcut erteleme sayısını görelim
        cursor.execute("SELECT postpone_count, title FROM tasks WHERE id = :1", (task_id,))
        task = cursor.fetchone()

        if not task:
            raise HTTPException(status_code=404,detail="Görev bulunamadı")

        current_count = task[0]
        new_count = current_count + 1

        #Disiplin alarmı(3 ve ya daha fazla erteleme için)
        warning_message = None
        if new_count >= 3:
            warning_message = f"DİSİPLİN UYARISI: '{task_id} adlı görevi 3 kez ertelediniz.Programa sadık kalmalısın!"

        #Veri Tabanında Erteleme sayısını artıralım
        cursor.execute(
            """
            UPDATE tasks 
            SET postpone_count = :1,status = 'postpone'
            WHERE id = :2
            """,
            (new_count,task_id)
        )
        conn.commit()

        return{
            "status":"success",
            "postpone_count":new_count,
            "discipline_alarm": warning_message is not None,
            "message":warning_message or "Görev ertelendi"
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500,detail=str(e))
    finally:
        cursor.close()
        conn.close()

#4.Görev silme Endpointi
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        #Önce görevin var olup olmadığını kontrol et
        cursor.execute("SELECT id FROM tasks WHERE id = :1",(task_id,))
        task = cursor.fetchone()

        if not task:
            raise HTTPException(status_code=404,detail="Silinecek görev bulunamadı!")

        #Görevi veri tabanından silelim (İlişkili loglar ON DELETE CASCADE sayesinde
        #       otomatik silinecektir)
        cursor.execute("DELETE FROM tasks WHERE id=:1",(task_id,))
        conn.commit()

        return {"status":"success",
                "message":f"ID'si {task_id} olan görev başarıyla silindi."}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500,detail=str(e))
    finally:
        cursor.close()
        conn.close()


