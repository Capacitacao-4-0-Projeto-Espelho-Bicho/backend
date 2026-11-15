import click
from sqlalchemy import func
from app.extensions import db
from app.models import User

# Aqui vamos registrar os comandos CLI relacionados ao gerenciamento 
# do servidor e do banco de dados. Esses comandos podem ser executados no terminal para realizar 
# tarefas administrativas, como definir o perfil de um usuário existente.
# A ideia é fornecer uma interface de linha de comando para facilitar a 
# administração do sistema, permitindo que os administradores realizem ações 
# diretamente no banco de dados sem precisar acessar a interface web, nem mexer no banco (no caso 
# do registro de Admin).
def registrar_comandos(app):
    @app.cli.command('definir-perfil')
    @click.argument('email')
    @click.argument('papel', type=click.Choice(['usuario', 'gestor', 'admin']))
    def definir_perfil(email, papel):
        """Define o papel de uma conta existente pelo terminal do servidor."""
        usuario = db.session.scalar(db.select(User).where(func.lower(func.trim(User.email)) == email.strip().lower()))
        if usuario is None:
            raise click.ClickException('Usuário não encontrado.')
        usuario.papel = papel
        db.session.commit()
        click.echo(f'Perfil atualizado para {papel}.')
