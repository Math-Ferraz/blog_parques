from flask import Flask, render_template, request, redirect, url_for, flash, session
import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from datetime import datetime

# ==========================================================
# 0. CONFIGURAÇÃO INICIAL
# ==========================================================

load_dotenv()

app = Flask(__name__)
# A secret key é usada pelo Flask e pelo Flask-Admin e é NECESSÁRIA para o uso de 'session'
app.secret_key = "uma_chave_secreta_forte_aqui"  # Mantenha-a secreta e longa!

# CONFIGURAÇÃO DO BANCO DE DADOS (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Definições de ADMIN para a autenticação simples (MUDE ISSO EM PRODUÇÃO!)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'projeto_parque2025' 

# ==========================================================
# 1. MODELO DO BANCO DE DADOS
# ==========================================================
class Noticia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    # Trocamos 'metadata' (palavra reservada) para 'metadata_info'
    metadata_info = db.Column(db.String(100), nullable=False) 
    imagem = db.Column(db.String(50), nullable=False) # Ex: 'parque1.jpg'
    conteudo_principal = db.Column(db.Text, nullable=False) # Permite HTML para formatação
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow) # Adiciona data

    def __repr__(self):
        return f"Noticia('{self.titulo}', '{self.metadata_info}')"

with app.app_context():
    db.create_all()


# ==========================================================
# 2. ROTAS DO SITE (FRONT-END)
# ==========================================================

@app.route('/')
def index():
    # Obtém todas as notícias do banco de dados (as mais recentes primeiro)
    noticias = Noticia.query.order_by(Noticia.data_criacao.desc()).all()
    return render_template('index.html', noticias=noticias)

@app.route('/atividades')
def atividades():
    return render_template('atividades.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/noticia/<int:noticia_id>')
def exibir_noticia(noticia_id):
    noticia = Noticia.query.get_or_404(noticia_id)
    return render_template('noticia_detalhe.html', noticia=noticia)

@app.route('/participe', methods=['GET', 'POST'])
def participe():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        mensagem = request.form['mensagem']

        destinatario = os.getenv("EMAIL_DESTINO")
        remetente = os.getenv("EMAIL_ORIGEM")
        senha = os.getenv("EMAIL_SENHA")

        conteudo = f"Nova sugestão de {nome} ({email}):\n\n{mensagem}"
        msg = MIMEText(conteudo, "plain", "utf-8")
        msg["Subject"] = f"Sugestão de {nome}"
        msg["From"] = remetente
        msg["To"] = destinatario

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as conexao:
                conexao.starttls()
                conexao.login(remetente, senha)
                conexao.send_message(msg)
            # Flash com categoria de sucesso
            flash("Sugestão enviada com sucesso! Obrigado pela contribuição.","sucesso")
        except Exception as e:
            # Flash com categoria de erro
            flash("Erro ao enviar a sugestão. Tente novamente.", "erro")
            print(e)

        return redirect(url_for('participe'))

    return render_template('participe.html')

# ==========================================================
# 3. ROTAS DE AUTENTICAÇÃO
# ==========================================================

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Login realizado com sucesso!', 'sucesso')
            return redirect(url_for('admin.index')) # Redireciona para o painel do Admin
        else:
            flash('Credenciais inválidas.', 'erro')
    
    # Renderiza o formulário de login (você deve criar este arquivo HTML)
    return render_template('admin_login.html')

@app.route('/admin_logout')
def admin_logout():
    session.pop('logged_in', None)
    flash('Você saiu da sua conta.', 'sucesso')
    return redirect(url_for('index')) # Redireciona para a página inicial


# ==========================================================
# 4. CONFIGURAÇÃO DO FLASK-ADMIN (PROTEGIDO)
# ==========================================================

# Classe base que verifica se o usuário está logado
class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        # Retorna True apenas se 'logged_in' estiver na session
        return session.get('logged_in')

    def _handle_view(self, name, **kwargs):
        # Se não estiver acessível, redireciona para a rota de login
        if not self.is_accessible():
            return redirect(url_for('admin_login'))
        # Senão, permite o acesso normal
        return super()._handle_view(name, **kwargs)

# Classe customizada para a view principal do Admin (necessária para proteger o /admin)
class CustomAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return session.get('logged_in')

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('admin_login'))
        return super()._handle_view(name, **kwargs)

# Classe de Notícia herda da view autenticada
class NoticiaAdminView(AuthenticatedModelView):
    # 1. Colunas que aparecerão na lista de notícias
    column_list = ('id', 'titulo', 'metadata_info', 'imagem', 'data_criacao')
    
    # 2. Colunas que aparecerão no formulário de criação/edição
    form_columns = ('titulo', 'metadata_info', 'imagem', 'conteudo_principal')
    
    # 3. Colunas que podem ser ordenadas
    column_sortable_list = ('id', 'titulo', 'data_criacao')
    
    # 4. Rótulos das colunas (para exibição amigável)
    column_labels = dict(
        titulo='Título da Notícia', 
        metadata_info='Tags/Metadata', 
        imagem='Nome do Arquivo da Imagem (Ex: parque1.jpg)', 
        conteudo_principal='Conteúdo (Permite HTML)', 
        data_criacao='Data de Criação'
    )

# Cria a instância do Admin, agora com a view principal protegida
admin = Admin(app, name='Parque Vivos Admin', index_view=CustomAdminIndexView(name='Home', url='/admin'))

# ADICIONA A VIEW PROTEGIDA
admin.add_view(NoticiaAdminView(Noticia, db.session, name='Notícias (Cards)'))


# ==========================================================
# 5. EXECUÇÃO
# ==========================================================
# Gunicorn cuidará da execução em produção
#if __name__ == '__main__':
#    app.run(debug=True)