from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

DB_USER = os.environ.get("MYSQL_USER")
DB_PASSWORD = os.environ.get("MYSQL_PASSWORD")
DB_HOST = os.environ.get("MYSQL_HOST", "localhost")
DB_PORT = os.environ.get("MYSQL_PORT", "3306")
DB_NAME = os.environ.get("MYSQL_DB_NAME", "sinarc_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="SINARC API")

@app.get("/empresas/{cnpj_basico}")
async def get_empresa(cnpj_basico: str):
    db = SessionLocal()
    try:
        query = text("SELECT * FROM empresa WHERE cnpj_basico = :cnpj")
        result = db.execute(query, {"cnpj": cnpj_basico}).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        return dict(result._mapping)
    finally:
        db.close()

@app.get("/socios/{cnpj_basico}")
async def get_socios(cnpj_basico: str):
    db = SessionLocal()
    try:
        query = text("SELECT * FROM socios WHERE cnpj_basico = :cnpj")
        results = db.execute(query, {"cnpj": cnpj_basico}).fetchall()
        return [dict(row._mapping) for row in results]
    finally:
        db.close()

@app.get("/busca")
async def buscar_empresa(nome: str):
    db = SessionLocal()
    try:
        query = text("SELECT * FROM empresa WHERE razao_social LIKE :nome LIMIT 10")
        results = db.execute(query, {"nome": f"%{nome}%"}).fetchall()
        return [dict(row._mapping) for row in results]
    finally:
        db.close()
