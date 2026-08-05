import os
import shutil
from fastapi import FastAPI, Depends, HTTPException, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import models
import schemas
from database import engine, SessionLocal
from typing import Optional
from datetime import datetime
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta, timezone

# 1. Crie o aplicativo PRIMEIRO
app = FastAPI(title="Rastreador GPS API", version="2.0")

# 2. Configure os middlewares e o banco logo em seguida
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

# Configuração da pasta de arquivos salvos (Uploads de mídia)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Torna a pasta de uploads acessível publicamente pela web
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 3. Rota raiz para servir o index.html
@app.get("/", response_class=HTMLResponse)
def ler_raiz():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/location", status_code=201)
def receive_location(data: schemas.LocationCreate, db: Session = Depends(get_db)):
    db_location = models.LocationModel(**data.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    
    return {
        "status": "sucesso", 
        "mensagem": "Localização salva com sucesso", 
        "id_registro": db_location.id
    }

@app.get("/locations/{device_id}")
def get_device_locations(
    device_id: str, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    query = db.query(models.LocationModel).filter(models.LocationModel.device_id == device_id)
    
    if start_date:
        query = query.filter(models.LocationModel.timestamp >= start_date)
    if end_date:
        query = query.filter(models.LocationModel.timestamp <= end_date)
        
    locations = query.all()
    if not locations:
        raise HTTPException(status_code=404, detail="Nenhum registro encontrado para este dispositivo")
    return locations

@app.get("/devices")
def get_active_devices(db: Session = Depends(get_db)):
    devices = db.query(models.LocationModel.device_id).distinct().all()
    return [d[0] for d in devices]

@app.get("/api/posicoes")
def gps_tracker_get(
    imei: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    speed: Optional[float] = 0.0,
    timestamp: Optional[str] = None,
    data_hora: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if not imei or not lat or not lon:
        return {"status": "ok", "message": "Servidor online"}
    
    if data_hora:
        hora_final = data_hora
    else:
        fuso_brasil = timezone(timedelta(hours=-4))
        hora_final = datetime.now(fuso_brasil).isoformat()
    
    db_location = models.LocationModel(
        device_id=imei,
        latitude=lat,
        longitude=lon,
        speed=speed,
        timestamp=hora_final
    )
    db.add(db_location)
    db.commit()
    
    return {"status": "success"}

# --- NOVA ROTA: RECEBER FOTOS E ÁUDIOS DO APP ---
@app.post("/api/multimidia", status_code=201)
def receber_multimidia(
    imei: str = Form(...),
    tipo: str = Form(...),  # Ex: 'foto' ou 'audio'
    data_hora: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Salva o arquivo fisicamente na pasta 'uploads' do servidor
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # URL pública que o painel web usará para exibir a foto ou tocar o áudio
    arquivo_url = f"/uploads/{file.filename}"

    if not data_hora:
        fuso_brasil = timezone(timedelta(hours=-4))
        data_hora = datetime.now(fuso_brasil).isoformat()

    # Opcional: Salvando a ocorrência da mídia no modelo de localização 
    # (ou você pode criar uma tabela separada no models.py caso prefira)
    db_location = models.LocationModel(
        device_id=imei,
        latitude=0.0,  # Sem coordenadas GPS diretas no momento da foto/áudio
        longitude=0.0,
        speed=0.0,
        timestamp=data_hora,
        # Se o seu models.py aceitar campos extras, você pode salvar a URL aqui
        # note: certifique-se de ajustar o models.py se quiser persistir a coluna 'arquivo_url'
    )
    
    db.add(db_location)
    db.commit()

    return {
        "status": "sucesso",
        "tipo": tipo,
        "url_arquivo": arquivo_url,
        "mensagem": f"{tipo.capitalize()} recebido e salvo com sucesso!"
    }