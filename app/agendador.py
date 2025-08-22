import json
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
import atexit
from . import gerenciador_docker

PASTA_AGENDAMENTOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agendamentos')
CAMINHO_AGENDAMENTOS = os.path.join(PASTA_AGENDAMENTOS, 'agendamentos.json')

scheduler = BackgroundScheduler(daemon=True)

def carregar_agendamentos():
    if not os.path.exists(CAMINHO_AGENDAMENTOS):
        return

    with open(CAMINHO_AGENDAMENTOS, 'r') as f:
        try:
            agendamentos = json.load(f)
            for job_info in agendamentos:
                agendar_backup(
                    container_id=job_info['container_id'],
                    container_name=job_info['container_name'],
                    hora=job_info['hora'],
                    minuto=job_info['minuto'],
                    salvar=False 
                )
        except (json.JSONDecodeError, TypeError):
            pass

def salvar_agendamentos():
    os.makedirs(PASTA_AGENDAMENTOS, exist_ok=True)

    agendamentos = []
    for job in scheduler.get_jobs():
        container_id = job.args[0]
        
        hora = None
        minuto = None

        for field in job.trigger.fields:
            if field.name == 'hour':
                hora = str(field)
            elif field.name == 'minute':
                minuto = str(field)

        container_name = job.name.replace('Backup diário para ', '')

        if hora is not None and minuto is not None:
            agendamentos.append({
                'job_id': job.id,
                'container_id': container_id,
                'container_name': container_name,
                'hora': int(hora),
                'minuto': int(minuto)
            })

    with open(CAMINHO_AGENDAMENTOS, 'w') as f:
        json.dump(agendamentos, f, indent=4)

def agendar_backup(container_id, container_name, hora, minuto, salvar=True):
    job_id = f"backup_{container_id}"
    scheduler.add_job(
        func=gerenciador_docker.fazer_backup_container,
        trigger='cron',
        hour=hora,
        minute=minuto,
        id=job_id,
        name=f"Backup diário para {container_name}",
        args=[container_id],
        replace_existing=True
    )
    if salvar:
        salvar_agendamentos()

def remover_agendamento(job_id):
    try:
        scheduler.remove_job(job_id)
        salvar_agendamentos()
        return True
    except JobLookupError:
        return False

def listar_agendamentos():
    jobs_info = []
    for job in scheduler.get_jobs():
        jobs_info.append({
            'id': job.id,
            'nome': job.name,
            'proxima_execucao': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jobs_info

def iniciar_agendador():
    if not scheduler.running:
        carregar_agendamentos()
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())
