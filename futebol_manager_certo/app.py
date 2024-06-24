from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# Configuração do aplicativo Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///football_manager_certo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'sua_chave_secreta_aqui'

# Configuração do SQLAlchemy
db = SQLAlchemy(app)

# Definição dos modelos

# Definição do modelo Jogador
class Jogador(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    posicao = db.Column(db.String(50), nullable=False)
    total_gols = db.Column(db.Integer, default=0)

    def __str__(self):
        return self.nome  # Retorna o nome do jogador ao converter para string

class Jogo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    time1 = db.Column(db.String(100), nullable=False)
    time2 = db.Column(db.String(100), nullable=False)
    vencedor = db.Column(db.String(100), nullable=False)

class Gol(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jogador_id = db.Column(db.Integer, db.ForeignKey('jogador.id'), nullable=False)
    jogador = db.relationship('Jogador', backref=db.backref('gols', lazy=True))
    jogo_id = db.Column(db.Integer, db.ForeignKey('jogo.id'), nullable=True)  # Permite valor nulo
    quantidade = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Date, nullable=False, default=datetime.utcnow)  # Adicionando campo de data

# Criação das tabelas no banco de dados, se elas ainda não existirem
with app.app_context():
    db.create_all()

# Rota para adicionar jogador
@app.route('/adicionar_jogador', methods=['GET', 'POST'])
def adicionar_jogador():
    if request.method == 'POST':
        nome = request.form['nome']
        posicao = request.form['posicao']
        
        print(f"Tentando adicionar jogador: Nome = {nome}, Posição = {posicao}")
        
        jogador_existente = Jogador.query.filter_by(nome=nome).first()
        if jogador_existente:
            flash(f'O jogador {nome} já está cadastrado.')
            return redirect(url_for('adicionar_jogador'))
        
        novo_jogador = Jogador(nome=nome, posicao=posicao)
        
        try:
            db.session.add(novo_jogador)
            db.session.commit()
            flash('Jogador adicionado com sucesso!')
            print(f"Jogador adicionado: ID = {novo_jogador.id}, Nome = {novo_jogador.nome}, Posição = {novo_jogador.posicao}")
            return redirect(url_for('index'))
        except IntegrityError as e:
            db.session.rollback()
            flash('Erro ao adicionar jogador. Nome duplicado ou violação de restrição de chave. Por favor, tente novamente.')
            print(f"Erro de Integridade: {str(e)}")
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar jogador: {str(e)}. Por favor, tente novamente.')
            print(f"Erro ao adicionar jogador: {str(e)}")
    
    return render_template('adicionar_jogador.html')

@app.route('/adicionar_gol', methods=['POST', 'GET'])
def adicionar_gol():
    jogadores = Jogador.query.all()
    jogos = Jogo.query.all()

    if request.method == 'POST':
        jogador_id = request.form['jogador']
        quantidade = int(request.form['quantidade'])

        novo_gol = Gol(jogador_id=jogador_id, quantidade=quantidade)

        try:
            db.session.add(novo_gol)
            db.session.commit()

            jogador = Jogador.query.get(jogador_id)
            jogador.total_gols += quantidade
            db.session.commit()

            flash('Gol registrado com sucesso!')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar gol: {str(e)}. Por favor, tente novamente.')
            print(str(e))

        return redirect(url_for('index'))

    return render_template('adicionar_gol.html', jogadores=jogadores, jogos=jogos)

@app.route('/top_goleadores', methods=['GET', 'POST'])
def top_goleadores():
    from sqlalchemy import extract

    if request.method == 'POST':
        mes = int(request.form['mes'])
        ano = int(request.form['ano'])
        data_inicial = datetime(ano, mes, 1)
        if mes == 12:
            data_final = datetime(ano + 1, 1, 1)
        else:
            data_final = datetime(ano, mes + 1, 1)
        
        top_jogadores = (db.session.query(Jogador, db.func.sum(Gol.quantidade).label('total_gols'))
                         .join(Gol)
                         .filter(Gol.data >= data_inicial, Gol.data < data_final)
                         .group_by(Jogador.id)
                         .order_by(db.desc('total_gols'))
                         .limit(10)
                         .all())
        
        ano_atual = datetime.now().year  # Obtém o ano atual
        return render_template('top_goleadores.html', jogadores=top_jogadores, mes=mes, ano=ano, ano_atual=ano_atual)

    # Se for um GET, apenas renderiza a página sem dados filtrados
    return render_template('top_goleadores.html')


@app.route('/top_goleadores_anual', methods=['GET', 'POST'])
def top_goleadores_anual():
    if request.method == 'POST':
        ano = int(request.form['ano'])
        data_inicial = datetime(ano, 1, 1)
        data_final = datetime(ano + 1, 1, 1)

        top_jogadores = (db.session.query(Jogador, db.func.sum(Gol.quantidade).label('total_gols'))
                         .join(Gol)
                         .filter(Gol.data >= data_inicial, Gol.data < data_final)
                         .group_by(Jogador.id)
                         .order_by(db.desc('total_gols'))
                         .limit(10)
                         .all())

        ano_atual = datetime.now().year  # Obtém o ano atual
        return render_template('top_goleadores_anual.html', jogadores=top_jogadores, ano=ano, ano_atual=ano_atual)

    # Se for um GET, apenas renderiza a página sem dados filtrados
    return render_template('top_goleadores_anual.html')


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
