import docker
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
    if not os.path.exists(caminho_backup): return {'success': False, 'message': 'Arquivo de backup não encontrado.'}

    try:
        container = cliente.containers.get(container_id_destino)
    except docker.errors.NotFound: return {'success': False, 'message': f'Contêiner de destino não encontrado.'}

    env_vars = {var.split('=')[0]: var.split('=', 1)[1] for var in container.attrs['Config']['Env']}
    imagem_nome = container.image.tags[0]
    comando_restauracao = None

    if 'postgres' in imagem_nome:
        db_user = env_vars.get('POSTGRES_USER', 'postgres')
        db_name = env_vars.get('POSTGRES_DB', 'postgres')
        comando_pre = f'psql -U {db_user} -d {db_name} -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"'
        container.exec_run(comando_pre)
        comando_restauracao = ['psql', '-U', db_user, '-d', db_name]
    elif 'mysql' in imagem_nome or 'mariadb' in imagem_nome:
        db_name = env_vars.get('MYSQL_DATABASE')
        db_user = env_vars.get('MYSQL_USER')
        db_pass = env_vars.get('MYSQL_PASSWORD') or env_vars.get('MYSQL_ROOT_PASSWORD')
        if not all([db_name, db_user, db_pass]): return {'success': False, 'message': 'Variáveis de ambiente do MySQL não encontradas.'}
        comando_restauracao = ['mysql', f'--user={db_user}', f'--password={db_pass}', db_name]

    if not comando_restauracao: return {'success': False, 'message': 'Banco de dados não suportado para restauração.'}

    with open(caminho_backup, 'rb') as f:
        dados_backup = f.read()

    try:
        exec_id = cliente.api.exec_create(container.id, cmd=comando_restauracao, stdin=True)['Id']
        socket = cliente.api.exec_start(exec_id, socket=True)
        if hasattr(socket, '_sock'):
            socket._sock.sendall(dados_backup)
            socket._sock.close()
        else:
            socket.sendall(dados_backup)
            socket.close()
        
        # Aguarda a finalização da execução do comando de restauração
        while True:
            res = cliente.api.exec_inspect(exec_id)
            if not res.get('Running'):
                break
            time.sleep(0.2)

        # Verifica o código de saída após a conclusão
        if res.get('ExitCode') == 0:
            return {'success': True, 'message': f'Backup {nome_arquivo} restaurado para {container.name}.'}
        else:
            return {'success': False, 'message': f'Erro ao restaurar (código {res.get("ExitCode")}).'}
    except Exception as e:
        return {'success': False, 'message': f'Exceção na restauração: {e}'}

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
    
