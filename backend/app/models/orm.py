from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Text, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    github_id = Column(Integer, unique=True, nullable=False)
    login = Column(String, nullable=False)
    name = Column(String)
    email = Column(String)
    avatar_url = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    job_id = Column(String, primary_key=True)
    repo_url = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"))
    status = Column(String, nullable=False)
    progress = Column(Integer, nullable=False)
    stage = Column(String, nullable=False)
    error = Column(Text)
    result_json = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

class AnalysisChunk(Base):
    __tablename__ = "analysis_chunks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, ForeignKey("analysis_jobs.job_id"), nullable=False)
    file_path = Column(String, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    start_line = Column(Integer)
    end_line = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
