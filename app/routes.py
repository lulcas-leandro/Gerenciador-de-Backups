from flask import Blueprint, render_template, redirect, url_for, flash,request
from app import gerenciador_docker

routes_bp = Blueprint('principal', __name__)

@routes_bp.route('/')
def painel():
    lista_de_containers = gerenciador_docker.listar_containers_ativos()
    lista_de_backups = gerenciador_docker.listar_backups()
    return render_template(
        'index.html',
        containers = lista_de_containers,
        backups = lista_de_backups)
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