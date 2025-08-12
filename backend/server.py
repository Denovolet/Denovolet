from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

# Configurações
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'clinica_odontologica')
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')

# Configuração do banco
client = None
db = None

async def get_database():
    global client, db
    if client is None:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
    return db

app = FastAPI(title="Sistema de Agendamento - Clínica Odontológica")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class ServicoOdontologico(BaseModel):
    id: str
    nome: str
    duracao_minutos: int
    preco: Optional[float] = None
    descricao: Optional[str] = None

class CriarServicoOdontologico(BaseModel):
    nome: str
    duracao_minutos: int
    preco: Optional[float] = None
    descricao: Optional[str] = None

class Paciente(BaseModel):
    nome: str
    telefone: str
    email: Optional[EmailStr] = None
    observacoes: Optional[str] = None

class Agendamento(BaseModel):
    id: str
    paciente: Paciente
    servico_id: str
    servico_nome: str
    data_hora: datetime
    duracao_minutos: int
    status: str = "agendado"  # agendado, concluido, cancelado
    observacoes: Optional[str] = None
    criado_em: datetime

class CriarAgendamento(BaseModel):
    paciente: Paciente
    servico_id: str
    data_hora: datetime
    observacoes: Optional[str] = None

class HorarioFuncionamento(BaseModel):
    dia_semana: int  # 0=segunda, 6=domingo
    abertura: str  # formato HH:MM
    fechamento: str  # formato HH:MM
    ativo: bool = True

# Serviços padrão
servicos_padrao = [
    {"id": str(uuid.uuid4()), "nome": "Consulta de Avaliação", "duracao_minutos": 30, "preco": 150.0, "descricao": "Consulta inicial para avaliação"},
    {"id": str(uuid.uuid4()), "nome": "Limpeza Dental", "duracao_minutos": 45, "preco": 200.0, "descricao": "Profilaxia e limpeza completa"},
    {"id": str(uuid.uuid4()), "nome": "Obturação Simples", "duracao_minutos": 60, "preco": 300.0, "descricao": "Restauração de cárie simples"},
    {"id": str(uuid.uuid4()), "nome": "Tratamento de Canal", "duracao_minutos": 90, "preco": 800.0, "descricao": "Endodontia completa"},
    {"id": str(uuid.uuid4()), "nome": "Extração Dental", "duracao_minutos": 45, "preco": 250.0, "descricao": "Remoção de dente"},
]

@app.on_event("startup")
async def startup_event():
    db = await get_database()
    
    # Criar serviços padrão se não existirem
    servicos_existentes = await db.servicos.count_documents({})
    if servicos_existentes == 0:
        await db.servicos.insert_many(servicos_padrao)
    
    # Criar horários padrão se não existirem
    horarios_existentes = await db.horarios.count_documents({})
    if horarios_existentes == 0:
        horarios_padrao = [
            {"dia_semana": 0, "abertura": "08:00", "fechamento": "18:00", "ativo": True},
            {"dia_semana": 1, "abertura": "08:00", "fechamento": "18:00", "ativo": True},
            {"dia_semana": 2, "abertura": "08:00", "fechamento": "18:00", "ativo": True},
            {"dia_semana": 3, "abertura": "08:00", "fechamento": "18:00", "ativo": True},
            {"dia_semana": 4, "abertura": "08:00", "fechamento": "17:00", "ativo": True},
            {"dia_semana": 5, "abertura": "08:00", "fechamento": "12:00", "ativo": True},
            {"dia_semana": 6, "abertura": "00:00", "fechamento": "00:00", "ativo": False},
        ]
        await db.horarios.insert_many(horarios_padrao)

# ENDPOINTS DE SERVIÇOS
@app.get("/api/servicos", response_model=List[ServicoOdontologico])
async def listar_servicos():
    db = await get_database()
    servicos = []
    async for servico in db.servicos.find():
        servicos.append(ServicoOdontologico(**servico))
    return servicos

@app.post("/api/servicos", response_model=ServicoOdontologico)
async def criar_servico(servico: CriarServicoOdontologico):
    db = await get_database()
    novo_servico = {
        "id": str(uuid.uuid4()),
        **servico.dict()
    }
    await db.servicos.insert_one(novo_servico)
    return ServicoOdontologico(**novo_servico)

@app.get("/api/servicos/{servico_id}", response_model=ServicoOdontologico)
async def obter_servico(servico_id: str):
    db = await get_database()
    servico = await db.servicos.find_one({"id": servico_id})
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return ServicoOdontologico(**servico)

@app.put("/api/servicos/{servico_id}", response_model=ServicoOdontologico)
async def atualizar_servico(servico_id: str, servico: CriarServicoOdontologico):
    db = await get_database()
    servico_existente = await db.servicos.find_one({"id": servico_id})
    if not servico_existente:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    await db.servicos.update_one(
        {"id": servico_id},
        {"$set": servico.dict()}
    )
    
    servico_atualizado = await db.servicos.find_one({"id": servico_id})
    return ServicoOdontologico(**servico_atualizado)

@app.delete("/api/servicos/{servico_id}")
async def excluir_servico(servico_id: str):
    db = await get_database()
    resultado = await db.servicos.delete_one({"id": servico_id})
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return {"message": "Serviço excluído com sucesso"}

# ENDPOINTS DE AGENDAMENTOS
@app.get("/api/agendamentos", response_model=List[Agendamento])
async def listar_agendamentos(data: Optional[str] = None):
    db = await get_database()
    query = {}
    
    if data:
        try:
            data_obj = datetime.fromisoformat(data.replace('Z', '+00:00'))
            inicio_dia = data_obj.replace(hour=0, minute=0, second=0, microsecond=0)
            fim_dia = inicio_dia + timedelta(days=1)
            query = {
                "data_hora": {
                    "$gte": inicio_dia,
                    "$lt": fim_dia
                }
            }
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data inválido")
    
    agendamentos = []
    async for agendamento in db.agendamentos.find(query).sort("data_hora", 1):
        agendamentos.append(Agendamento(**agendamento))
    return agendamentos

@app.post("/api/agendamentos", response_model=Agendamento)
async def criar_agendamento(agendamento: CriarAgendamento):
    db = await get_database()
    
    # Verificar se o serviço existe
    servico = await db.servicos.find_one({"id": agendamento.servico_id})
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    # Verificar conflitos de horário
    inicio = agendamento.data_hora
    fim = inicio + timedelta(minutes=servico["duracao_minutos"])
    
    conflito = await db.agendamentos.find_one({
        "$and": [
            {"status": {"$ne": "cancelado"}},
            {
                "$or": [
                    {
                        "$and": [
                            {"data_hora": {"$lte": inicio}},
                            {"data_hora": {"$gte": inicio}}
                        ]
                    },
                    {
                        "$and": [
                            {"data_hora": {"$lt": fim}},
                            {"data_hora": {"$gte": inicio}}
                        ]
                    }
                ]
            }
        ]
    })
    
    if conflito:
        raise HTTPException(status_code=400, detail="Já existe um agendamento neste horário")
    
    novo_agendamento = {
        "id": str(uuid.uuid4()),
        "paciente": agendamento.paciente.dict(),
        "servico_id": agendamento.servico_id,
        "servico_nome": servico["nome"],
        "data_hora": agendamento.data_hora,
        "duracao_minutos": servico["duracao_minutos"],
        "status": "agendado",
        "observacoes": agendamento.observacoes,
        "criado_em": datetime.now()
    }
    
    await db.agendamentos.insert_one(novo_agendamento)
    return Agendamento(**novo_agendamento)

@app.get("/api/agendamentos/{agendamento_id}", response_model=Agendamento)
async def obter_agendamento(agendamento_id: str):
    db = await get_database()
    agendamento = await db.agendamentos.find_one({"id": agendamento_id})
    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    return Agendamento(**agendamento)

@app.put("/api/agendamentos/{agendamento_id}/status")
async def atualizar_status_agendamento(agendamento_id: str, status: str):
    db = await get_database()
    if status not in ["agendado", "concluido", "cancelado"]:
        raise HTTPException(status_code=400, detail="Status inválido")
    
    resultado = await db.agendamentos.update_one(
        {"id": agendamento_id},
        {"$set": {"status": status}}
    )
    
    if resultado.modified_count == 0:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    
    return {"message": "Status atualizado com sucesso"}

@app.delete("/api/agendamentos/{agendamento_id}")
async def excluir_agendamento(agendamento_id: str):
    db = await get_database()
    resultado = await db.agendamentos.delete_one({"id": agendamento_id})
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    return {"message": "Agendamento excluído com sucesso"}

# ENDPOINTS DE HORÁRIOS
@app.get("/api/horarios", response_model=List[HorarioFuncionamento])
async def listar_horarios():
    db = await get_database()
    horarios = []
    async for horario in db.horarios.find().sort("dia_semana", 1):
        horarios.append(HorarioFuncionamento(**horario))
    return horarios

@app.put("/api/horarios/{dia_semana}")
async def atualizar_horario(dia_semana: int, horario: HorarioFuncionamento):
    db = await get_database()
    if dia_semana < 0 or dia_semana > 6:
        raise HTTPException(status_code=400, detail="Dia da semana inválido (0-6)")
    
    resultado = await db.horarios.update_one(
        {"dia_semana": dia_semana},
        {"$set": horario.dict()}
    )
    
    if resultado.modified_count == 0:
        raise HTTPException(status_code=404, detail="Horário não encontrado")
    
    return {"message": "Horário atualizado com sucesso"}

# ENDPOINT PARA HORÁRIOS DISPONÍVEIS
@app.get("/api/horarios-disponiveis")
async def obter_horarios_disponiveis(data: str, servico_id: str):
    db = await get_database()
    
    try:
        data_obj = datetime.fromisoformat(data.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido")
    
    # Obter serviço para duração
    servico = await db.servicos.find_one({"id": servico_id})
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    # Obter horário de funcionamento do dia
    dia_semana = data_obj.weekday()
    horario_funcionamento = await db.horarios.find_one({"dia_semana": dia_semana})
    
    if not horario_funcionamento or not horario_funcionamento["ativo"]:
        return {"horarios_disponiveis": []}
    
    # Gerar slots de 30 em 30 minutos
    abertura = datetime.strptime(horario_funcionamento["abertura"], "%H:%M").time()
    fechamento = datetime.strptime(horario_funcionamento["fechamento"], "%H:%M").time()
    
    inicio_dia = data_obj.replace(hour=abertura.hour, minute=abertura.minute, second=0, microsecond=0)
    fim_dia = data_obj.replace(hour=fechamento.hour, minute=fechamento.minute, second=0, microsecond=0)
    
    # Obter agendamentos do dia
    agendamentos_dia = []
    async for agendamento in db.agendamentos.find({
        "data_hora": {
            "$gte": inicio_dia,
            "$lt": fim_dia + timedelta(days=1)
        },
        "status": {"$ne": "cancelado"}
    }):
        agendamentos_dia.append(agendamento)
    
    # Gerar horários disponíveis
    horarios_disponiveis = []
    current_time = inicio_dia
    
    while current_time + timedelta(minutes=servico["duracao_minutos"]) <= fim_dia:
        # Verificar se há conflito
        conflito = False
        for agendamento in agendamentos_dia:
            agendamento_inicio = agendamento["data_hora"]
            agendamento_fim = agendamento_inicio + timedelta(minutes=agendamento["duracao_minutos"])
            
            if (current_time < agendamento_fim and 
                current_time + timedelta(minutes=servico["duracao_minutos"]) > agendamento_inicio):
                conflito = True
                break
        
        if not conflito:
            horarios_disponiveis.append(current_time.strftime("%H:%M"))
        
        current_time += timedelta(minutes=30)
    
    return {"horarios_disponiveis": horarios_disponiveis}

@app.get("/api/status")
async def status():
    return {"status": "Sistema de Agendamento Odontológico funcionando!", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)