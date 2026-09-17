import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

from sqlalchemy import func

from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

# configurações do banco
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'chave-secreta-desenvolvimento-metpage'
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metpage.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# configuração do SQLAlchemy
db = SQLAlchemy(app)

# configuração do Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Faça login para acessar esta página."


#==================================
# MODELS
#==================================
class Usuario(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    senha = db.Column(db.String(255), nullable=False)

    perfil = db.Column(
        db.String(20),
        nullable=False,
        default='usuario'
    )


class Inscricao(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), nullable=False)

    endereco = db.Column(db.String(200))

    telefone = db.Column(db.String(20))

    pais = db.Column(db.String(50))

    estado = db.Column(db.String(50))

    cidade = db.Column(db.String(100))

    notificacoes = db.Column(db.Boolean, default=False)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('usuario.id'),
        nullable=True
    )

    data_inscricao = db.Column(db.DateTime, server_default=func.now())


# user_loader
@login_manager.user_loader
def carregar_usuario(user_id):
    return db.session.get(Usuario, int(user_id))


#==================================
# PAGINA INICIAL
#==================================
@app.route('/')
def raiz():
    return redirect(url_for('login'))


@app.route('/inicio')
@login_required
def pagina_inicio():
    return render_template('inicio.html')


#==================================
# LOOKS
#==================================
@app.route('/looks')
@login_required
def looks():
    return render_template('looks.html')


#==================================
# INSCRICAO
#==================================
@app.route('/inscricao', methods=['GET', 'POST'])
@login_required
def inscricao():

    if request.method == 'POST':

        nome = request.form.get('nome')
        email = request.form.get('email')
        endereco = request.form.get('endereco')
        telefone = request.form.get('telefone')
        pais = request.form.get('pais')
        estado = request.form.get('estado')
        cidade = request.form.get('cidade')
        notificacoes = True if request.form.get('notificacoes') else False

        if not nome or not email:
            flash("Preencha ao menos o nome e o email para se inscrever.")
            return redirect(url_for('inscricao'))

        nova_inscricao = Inscricao(
            nome=nome,
            email=email,
            endereco=endereco,
            telefone=telefone,
            pais=pais,
            estado=estado,
            cidade=cidade,
            notificacoes=notificacoes,
            usuario_id=current_user.id
        )

        db.session.add(nova_inscricao)

        db.session.commit()

        flash("Inscrição realizada com sucesso!")

        return redirect(url_for('inscricao'))

    return render_template('inscricao.html')


#==================================
# CADASTRO
#==================================
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():

    if request.method == 'POST':

        nome = request.form['nome']

        email = request.form['email']

        senha = request.form['senha']

        usuario_existente = Usuario.query.filter_by(
            email=email
        ).first()

        if usuario_existente:

            flash("Este e-mail já está cadastrado.")

            return redirect(url_for('cadastro'))

        senha_hash = generate_password_hash(senha)

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=senha_hash,
            perfil='usuario'
        )

        db.session.add(novo_usuario)

        db.session.commit()

        flash("Cadastro realizado com sucesso!")

        return redirect(url_for('login'))

    return render_template('cadastro.html')


#==================================
# LOGIN
#==================================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']

        senha = request.form['senha']

        usuario = Usuario.query.filter_by(
            email=email
        ).first()

        if usuario and check_password_hash(
            usuario.senha,
            senha
        ):

            login_user(usuario)

            return redirect(url_for('pagina_inicio'))

        flash("E-mail ou senha incorretos.")

    return render_template('login.html')


#==================================
# LOGOUT
#==================================
@app.route('/logout')
@login_required
def logout():

    logout_user()

    flash("Você saiu da sua conta.")

    return redirect(url_for('login'))


#==================================
# IMAGENS
#==================================
@app.route('/img/<path:nome_arquivo>')
def imagens(nome_arquivo):
    diretorio_img = os.path.join(app.root_path, 'img')
    return send_from_directory(diretorio_img, nome_arquivo)


#=========================================
#CRIAÇÃO DO BANCO
#=========================================
with app.app_context():
    db.create_all()

    #cria administrador padrão
    admin = Usuario.query.filter_by(email="admin@email.com").first()

    if not admin:
        admin = Usuario(
            nome='Administrador',
            email='admin@email.com',
            senha=generate_password_hash('123456'),
            perfil='admin'
        )
        db.session.add(admin)
        db.session.commit()


#=======================================
# EXECUÇÃO
#=======================================
if __name__ == "__main__":
    app.run(debug=True)
