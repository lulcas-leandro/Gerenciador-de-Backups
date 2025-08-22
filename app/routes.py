from flask import Blueprint, render_template, redirect, url_for, flash,request
from app import gerenciador_docker, agendador

routes_bp = Blueprint('principal', __name__)

@routes_bp.route('/')
def painel():
    lista_de_containers = gerenciador_docker.listar_containers_ativos()
    lista_de_backups = gerenciador_docker.listar_backups()
    lista_de_agendamentos = agendador.listar_agendamentos()
    return render_template(
        'index.html',
        containers = lista_de_containers,
        backups = lista_de_backups,
        agendamentos=lista_de_agendamentos)

@routes_bp.route('/backup/<container_id>')
def backup(container_id):
    resultado = gerenciador_docker.fazer_backup_container(container_id)
    flash(resultado['message'], 'success' if resultado['success'] else 'danger')
    return redirect(url_for('principal.painel'))

@routes_bp.route('/restaurar', methods = ['POST'])
def restaurar():
    nome_arquivo = request.form.get('nome_arquivo')
    container_id_destino = request.form.get('container_id_destino')
    resultado = gerenciador_docker.restaurar_backup(nome_arquivo, container_id_destino)
    flash(resultado['message'], 'success' if resultado['success'] else 'danger')
    return redirect(url_for('principal.painel'))

@routes_bp.route('/excluir/<nome_arquivo>')
def excluir(nome_arquivo):
    resultado = gerenciador_docker.excluir_backup(nome_arquivo)
    flash(resultado['message'], 'success' if resultado['success'] else 'danger')
    return redirect(url_for('principal.painel'))

@routes_bp.route('/agendar', methods=['POST'])
def agendar():
    container_info = request.form['container_id'].split('|')
    container_id = container_info[0]
    container_name = container_info[1]
    
    backup_time = request.form['backup_time']
    hora, minuto = map(int, backup_time.split(':'))

    try:
        agendador.agendar_backup(container_id, container_name, hora, minuto)
        flash(f"Backup para '{container_name}' agendado para as {hora:02d}:{minuto:02d}.", 'success')
    except Exception as e:
        flash(f"Erro ao criar agendamento: {e}", 'danger')

    return redirect(url_for('principal.painel'))

routes_bp.route('/agendamento/excluir/<job_id>')
def excluir_agendamento(job_id):
    if agendador.remover_agendamento(job_id):
        flash("Agendamento removido com sucesso.", 'success')
    else:
        flash("Erro ao remover agendamento.", 'danger')
    return redirect(url_for('principal.painel'))    