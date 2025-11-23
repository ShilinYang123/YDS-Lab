# 数字员工项目 - 后端API服务
# FastAPI + SQLAlchemy + Redis + MinIO

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import redis
import minio
import os
import uuid
import json
from typing import Optional, List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/digital_employee")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis配置
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# MinIO配置
minio_client = minio.Minio(
    os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    secure=False
)

# 创建MinIO存储桶
try:
    if not minio_client.bucket_exists("digital-employee"):
        minio_client.make_bucket("digital-employee")
except Exception as e:
    print(f"MinIO存储桶创建失败: {e}")

# 数据模型
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    task_type = Column(String, nullable=False)  # text_to_speech, lip_sync, full_pipeline
    
    # 输入参数
    input_text = Column(Text)
    reference_video_path = Column(String)
    reference_audio_path = Column(String)
    
    # 输出结果
    output_video_path = Column(String)
    output_audio_path = Column(String)
    
    # 质量评估
    lse_c_score = Column(String)
    lse_d_score = Column(String)
    mos_score = Column(String)
    
    # 时间和统计
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    processing_time = Column(Integer)  # 秒
    
    # 错误信息
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # 用户和权限
    user_id = Column(String)
    is_public = Column(Boolean, default=False)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# Pydantic模型
class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    task_type: str
    input_text: Optional[str] = None
    reference_video_path: Optional[str] = None
    reference_audio_path: Optional[str] = None
    is_public: bool = False

class TaskResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    task_type: str
    input_text: Optional[str]
    reference_video_path: Optional[str]
    reference_audio_path: Optional[str]
    output_video_path: Optional[str]
    output_audio_path: Optional[str]
    lse_c_score: Optional[str]
    lse_d_score: Optional[str]
    mos_score: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_time: Optional[int]
    error_message: Optional[str]
    retry_count: int
    user_id: Optional[str]
    is_public: bool

# FastAPI应用
app = FastAPI(
    title="数字员工API",
    description="基于LatentSync的数字员工生成系统",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 依赖注入
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    return redis_client

# API路由
@app.get("/")
def read_root():
    return {"message": "数字员工API服务运行正常", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        # 检查Redis连接
        redis_client.ping()
        
        # 检查MinIO连接
        minio_client.list_buckets()
        
        return {"status": "healthy", "timestamp": datetime.utcnow()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"服务异常: {str(e)}")

@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """创建任务"""
    try:
        # 创建任务
        db_task = Task(**task.dict())
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        # 将任务加入Redis队列
        task_data = {
            "task_id": db_task.id,
            "task_type": db_task.task_type,
            "input_text": db_task.input_text,
            "reference_video_path": db_task.reference_video_path,
            "reference_audio_path": db_task.reference_audio_path
        }
        redis_client.lpush("task_queue", json.dumps(task_data))
        
        return db_task
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")

@app.get("/api/tasks", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取任务列表"""
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    tasks = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()
    return tasks

@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """获取任务详情"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """取消任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status not in ["pending", "processing"]:
        raise HTTPException(status_code=400, detail="任务无法取消")
    
    task.status = "cancelled"
    task.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "任务已取消"}

@app.post("/api/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """上传参考视频"""
    try:
        # 检查文件类型
        if not file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="请上传视频文件")
        
        # 生成文件名
        file_extension = file.filename.split(".")[-1]
        file_name = f"videos/{uuid.uuid4()}.{file_extension}"
        
        # 上传到MinIO
        file_content = file.file.read()
        minio_client.put_object(
            "digital-employee",
            file_name,
            io.BytesIO(file_content),
            length=len(file_content),
            content_type=file.content_type
        )
        
        return {
            "filename": file.filename,
            "path": file_name,
            "size": len(file_content),
            "url": f"/uploads/{file_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.post("/api/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    """上传参考音频"""
    try:
        # 检查文件类型
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="请上传音频文件")
        
        # 生成文件名
        file_extension = file.filename.split(".")[-1]
        file_name = f"audios/{uuid.uuid4()}.{file_extension}"
        
        # 上传到MinIO
        file_content = file.file.read()
        minio_client.put_object(
            "digital-employee",
            file_name,
            io.BytesIO(file_content),
            length=len(file_content),
            content_type=file.content_type
        )
        
        return {
            "filename": file.filename,
            "path": file_name,
            "size": len(file_content),
            "url": f"/uploads/{file_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

# 队列监控API
@app.get("/api/queue/status")
async def get_queue_status(redis_client = Depends(get_redis)):
    """获取队列状态"""
    try:
        queue_length = redis_client.llen("task_queue")
        processing_tasks = redis_client.scard("processing_tasks")
        
        return {
            "queue_length": queue_length,
            "processing_tasks": processing_tasks,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取队列状态失败: {str(e)}")

# 统计API
@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """获取统计信息"""
    try:
        total_tasks = db.query(Task).count()
        pending_tasks = db.query(Task).filter(Task.status == "pending").count()
        processing_tasks = db.query(Task).filter(Task.status == "processing").count()
        completed_tasks = db.query(Task).filter(Task.status == "completed").count()
        failed_tasks = db.query(Task).filter(Task.status == "failed").count()
        
        return {
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "processing_tasks": processing_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": round(completed_tasks / max(total_tasks, 1) * 100, 2),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)