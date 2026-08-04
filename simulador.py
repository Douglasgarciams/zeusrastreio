import requests
import time
import random
from datetime import datetime

URL = "http://127.0.0.1:8000/location"

# Lista de veículos da frota com posições iniciais ligeiramente diferentes em São Paulo
frota = [
    {"device_id": "ZEUS-VEICULO-01", "lat": -23.55052, "lon": -46.63330},
    {"device_id": "ZEUS-VEICULO-02", "lat": -23.56152, "lon": -46.65530},
    {"device_id": "ZEUS-VEICULO-03", "lat": -23.53552, "lon": -46.62030},
]

print("Iniciando simulação de frota (Múltiplos Veículos)...")
print("Pressione CTRL+C para parar.\n")

while True:
    for veiculo in frota:
        # Simula movimento aleatório
        veiculo["lat"] += random.uniform(-0.0008, 0.0008)
        veiculo["lon"] += random.uniform(-0.0008, 0.0008)
        
        payload = {
            "device_id": veiculo["device_id"],
            "latitude": round(veiculo["lat"], 6),
            "longitude": round(veiculo["lon"], 6),
            "accuracy": 4.5,
            "speed": round(random.uniform(10.0, 60.0), 1),
            "battery": random.randint(50, 100),
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        try:
            response = requests.post(URL, json=payload)
            if response.status_code == 201:
                print(f"[{veiculo['device_id']}] Enviado -> Lat: {payload['latitude']}, Lon: {payload['longitude']}")
        except Exception as e:
            print(f"[{veiculo['device_id']}] Erro de conexão: {e}")
            
    print("-" * 40)
    time.sleep(5)