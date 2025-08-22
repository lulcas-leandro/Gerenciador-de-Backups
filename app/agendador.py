from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
import atexit
from . import gerenciador_docker

scheduler = BackgroundScheduler(daemon=True)

def agendar_backup(container_id, container_name, hora, minuto):
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

def remover_agendamento(job_id):
    try: scheduler.remove_job(job_id)
    except JobLookupError: pass

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
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())