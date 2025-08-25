import docker
import io
import tarfile
import time
import os
from datetime import datetime
from config import PASTA_BACKUPS, IMAGENS_DE_BANCO_DE_DADOS

cliente = docker.from_env()

def listar_containers_ativos():
    try:
        containers_ativos = cliente.containers.list()
        lista_filtrada = []
        for container in containers_ativos:
            imagem_tag = container.image.tags[0] if container.image.tags else ''
            if any(db_img in imagem_tag for db_img in IMAGENS_DE_BANCO_DE_DADOS):
                lista_filtrada.append({
                    'id': container.short_id,
                    'nome': container.name,
                    'imagem': imagem_tag
                })
        return lista_filtrada
    except docker.errors.DockerException:
        return []

def fazer_backup_container(container_id):
    try:
        container = cliente.containers.get(container_id)
    except docker.errors.NotFound:
        return {'success': False, 'message': 'Contêiner não encontrado.'}

    env_vars = {var.split('=')[0]: var.split('=', 1)[1] for var in container.attrs['Config']['Env']}
    imagem_nome = container.image.tags[0]
    comando_backup, extensao_arquivo = None, 'sql'

    if 'postgres' in imagem_nome:
        db_user = env_vars.get('POSTGRES_USER', 'postgres')
        db_name = env_vars.get('POSTGRES_DB', 'postgres')
        comando_backup = f'pg_dump -U {db_user} -d {db_name}'
        extensao_arquivo = 'dump'
    elif 'mysql' in imagem_nome or 'mariadb' in imagem_nome:
        db_name = env_vars.get('MYSQL_DATABASE')
        db_user = env_vars.get('MYSQL_USER')
        db_pass = env_vars.get('MYSQL_PASSWORD') or env_vars.get('MYSQL_ROOT_PASSWORD')
        if not all([db_name, db_user, db_pass]): return {'success': False, 'message': 'Variáveis de ambiente do MySQL não encontradas.'}
        comando_backup = f'mysqldump -u {db_user} -p{db_pass} {db_name}'

    if not comando_backup: return {'success': False, 'message': 'Tipo de banco de dados não suportado.'}

    os.makedirs(PASTA_BACKUPS, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome_arquivo = f'{container.name}_{timestamp}.{extensao_arquivo}'
    caminho_completo = os.path.join(PASTA_BACKUPS, nome_arquivo)

    try:
        _, stream = container.exec_run(comando_backup, stream=True)
        with open(caminho_completo, 'wb') as f:
            for chunk in stream:
                f.write(chunk)
        return {'success': True, 'message': f'Backup criado: {nome_arquivo}'}
    except Exception as e:
        return {'success': False, 'message': f'Erro no backup: {e}'}

def restaurar_backup(nome_arquivo, container_id_destino):
    caminho_backup = os.path.join(PASTA_BACKUPS, nome_arquivo)
    if not os.path.exists(caminho_backup):
        return {'success': False, 'message': 'Arquivo de backup não encontrado.'}

    try:
        container = cliente.containers.get(container_id_destino)
    except docker.errors.NotFound:
        return {'success': False, 'message': f'Contêiner de destino não encontrado.'}

    nome_arquivo_no_container = os.path.basename(caminho_backup)
    caminho_no_container = f"/tmp/{nome_arquivo_no_container}"

    try:
        with open(caminho_backup, 'rb') as f:
            dados_backup = f.read()

        pw_tarstream = io.BytesIO()
        with tarfile.open(fileobj=pw_tarstream, mode='w') as tar:
            tarinfo = tarfile.TarInfo(name=nome_arquivo_no_container)
            tarinfo.size = len(dados_backup)
            tar.addfile(tarinfo, io.BytesIO(dados_backup))
        
        pw_tarstream.seek(0)
        container.put_archive(path='/tmp', data=pw_tarstream)
    except Exception as e:
        return {'success': False, 'message': f'Falha ao copiar o backup para o contêiner: {e}'}

    env_vars = {var.split('=')[0]: var.split('=', 1)[1] for var in container.attrs['Config']['Env']}
    imagem_nome = container.image.tags[0]
    comando_restauracao = None

    if 'postgres' in imagem_nome:
        db_user = env_vars.get('POSTGRES_USER', 'postgres')
        db_name = env_vars.get('POSTGRES_DB', 'postgres')
        comando_pre = f'psql -U {db_user} -d {db_name} -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"'
        container.exec_run(comando_pre)
        comando_restauracao = f'psql -U {db_user} -d {db_name} < {caminho_no_container}'
    elif 'mysql' in imagem_nome or 'mariadb' in imagem_nome:
        db_name = env_vars.get('MYSQL_DATABASE')
        db_user = env_vars.get('MYSQL_USER')
        db_pass = env_vars.get('MYSQL_PASSWORD') or env_vars.get('MYSQL_ROOT_PASSWORD')
        if not all([db_name, db_user, db_pass]):
            return {'success': False, 'message': 'Variáveis de ambiente do MySQL não encontradas.'}
        comando_restauracao = f'mysql -u {db_user} -p{db_pass} {db_name} < {caminho_no_container}'

    if not comando_restauracao:
        return {'success': False, 'message': 'Banco de dados não suportado para restauração.'}

    try:
        exit_code, (stdout, stderr) = container.exec_run(cmd=f'sh -c "{comando_restauracao}"', demux=True)
        if exit_code == 0:
            message = f'Backup {nome_arquivo} restaurado para {container.name}.'
            success = True
        else:
            error_details = stderr.decode('utf-8', errors='ignore').strip() if stderr else "Nenhuma saída de erro."
            message = f'Erro ao restaurar (código {exit_code}). Detalhes: {error_details}'
            success = False
        
        return {'success': success, 'message': message}
    except Exception as e:
        return {'success': False, 'message': f'Exceção na restauração: {e}'}
    finally:
        container.exec_run(f'rm {caminho_no_container}')

def listar_backups():
    if not os.path.exists(PASTA_BACKUPS): return []
    backups_info = []
    for filename in os.listdir(PASTA_BACKUPS):
        caminho_completo = os.path.join(PASTA_BACKUPS, filename)
        if os.path.isfile(caminho_completo):
            stats = os.stat(caminho_completo)
            backups_info.append({
                'nome_arquivo': filename,
                'tamanho_kb': round(stats.st_size / 1024, 2),
                'data': datetime.fromtimestamp(stats.st_mtime).strftime('%d/%m/%Y %H:%M:%S')
            })
    backups_info.sort(key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y %H:%M:%S'), reverse=True)
    return backups_info

def excluir_backup(nome_arquivo):
    caminho_completo = os.path.join(PASTA_BACKUPS, nome_arquivo)
    if os.path.exists(caminho_completo):
        os.remove(caminho_completo)
        return {'success': True, 'message': f'Backup {nome_arquivo} excluído.'}
    return {'success': False, 'message': 'Arquivo não encontrado.'}
    
