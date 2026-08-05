from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
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

# 3. Agora adicione a rota raiz para servir o index.html
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
    
    # Se o app mandou a data_hora, usamos ela. Senão, pegamos a hora UTC do servidor de Ohio e convertemos para o horário do Brasil (UTC-4)
    if data_hora:
        hora_final = data_hora
    else:
        # Fuso horário do Brasil (Ex: Mato Grosso do Sul / Brasília é UTC-4 ou UTC-3, ajustando para o horário local real)
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