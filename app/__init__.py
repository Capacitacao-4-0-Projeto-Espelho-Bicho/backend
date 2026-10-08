import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # ⚠️ MUDANÇA CRUCIAL AQUI: Adicionado "+psycopg2" para usar o driver correto
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://softskills_user:softskills_pass@db:5432/softskills_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializa o banco de dados com a aplicação
    db.init_app(app)
    
    # Rota raiz para testar se a API está no ar
    @app.route('/')
    def home():
        return jsonify({
            'status': 'online', 
            'message': 'API do Sistema de Recomendação - Soft Skills',
            'version': '1.0.0'
        })

    # Rota de Health Check (usada pelo frontend e testes)
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'healthy'})

    # Rota para listar competências (prova de que o banco está conectado)
    @app.route('/api/competencias')
    def listar_competencias():
        from sqlalchemy import text
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT id, nome FROM competencia ORDER BY id"))
                competencias = [{"id": row[0], "nome": row[1]} for row in result]
                return jsonify({'competencias': competencias})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return app