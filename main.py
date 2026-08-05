import os
import shutil
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
import databases
import sqlalchemy

# Configuração do Banco de Dados SQLite (ou outro compatível)
DATABASE_URL = "sqlite:///./gps_tracker.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Tabela unificada para Posições e Multimídia
posicoes = sqlalchemy.Table(
    "posicoes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("imei", sqlalchemy.String),
    sqlalchemy.Column("lat", sqlalchemy.Float),
    sqlalchemy.Column("lon", sqlalchemy.Float),
    sqlalchemy.Column("speed", sqlalchemy.Float),
    sqlalchemy.Column("data_hora", sqlalchemy.String),
    sqlalchemy.Column("tipo", sqlalchemy.String), # 'gps', 'foto' ou 'audio'
    sqlalchemy.Column("arquivo_url", sqlalchemy.String, nullable=True),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
metadata.create_all(engine)

app = FastAPI(title="Zeus Rastreio API")

# Pasta para salvar arquivos recebidos fisicamente
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Expõe a pasta de uploads publicamente para o painel web conseguir exibir
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Rota original de Posições GPS
@app.get("/api/posicoes")
async def salvar_posicao(imei: str, lat: float, lon: float, speed: float, data_hora: str):
    query = posicoes.insert().values(
        imei=imei, lat=lat, lon=lon, speed=speed, data_hora=data_hora, tipo="gps", arquivo_url=None
    )
    last_id = await database.execute(query)
    return {"status": "sucesso", "id": last_id}

# Nova Rota para Upload de Mídia (Fotos e Áudios)
@app.post("/api/multimidia")
async def receber_multimidia(
    imei: str = Form(...),
    tipo: str = Form(...), # 'foto' ou 'audio'
    data_hora: str = Form(...),
    file: UploadFile = File(...)
):
    # Salva o arquivo na pasta do servidor
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Gera a URL pública para acesso no painel web
    arquivo_url = f"/uploads/{file.filename}"

    # Salva o registro no banco de dados
    query = posicoes.insert().values(
        imei=imei,
        lat=0.0, # Caso queira associar à última coordenada depois
        lon=0.0,
        speed=0.0,
        data_hora=data_hora,
        tipo=tipo,
        arquivo_url=arquivo_url
    )
    last_id = await database.execute(query)
    return {"status": "sucesso", "tipo": tipo, "url": arquivo_url, "id": last_id}

# Rota para o Painel Web listar todas as ocorrências e mídias
@app.get("/api/historico")
async def listar_historico(imei: str):
    query = posicoes.select().where(posicoes.c.imei == imei).order_by(posicoes.c.id.desc())
    results = await database.fetch_all(query)
    return [dict(row) for row in results]