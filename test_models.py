# Criei para testarmos os modelos do banco de dados (EXECUTAR SEMPRE APÓS MEXER EM ALGUM ARQUIVO DA MODELS/)
from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    print("Verificando modelos...")

    for table_name in db.metadata.tables:
        print(f"OK: {table_name}")

    print("\nTotal de tabelas reconhecidas:", len(db.metadata.tables))

    # Força a validação dos relacionamentos
    db.configure_mappers()

    print("\nTodos os modelos foram carregados corretamente!")