from flask import Flask, request, render_template, url_for, redirect
from firebase_admin import credentials
from firebase_admin import db as dbFirebase
import firebase_admin
import os
import psycopg2
from flask import session
from flask import flash
from flask_sqlalchemy import SQLAlchemy
import datetime
import base64

app = Flask(__name__)
db = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://inrbkbfqwjvcnb:83df34940918d53940c4bd30b5a185d3d79726cd36230f4a402f4a8f8579e680@ec2-174-129-35-61.compute-1.amazonaws.com:5432/da8gvk43j45moa'#'postgres://postgres:postgres@localhost:5432/test'
app.secret_key = b'1234'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

from models import *

@app.route("/")
def inicio():
	if session.get('AUTH') != None:
		if session['AUTH'] == True:
			return index()
		else:
			session['AUTH'] = False
			return render_template('login.html', val = session['AUTH'])
	else:
		session['AUTH'] = False
		return render_template('login.html', val = session['AUTH'])

@app.route('/profesor/<int:id>')
def profesor(id):
	if session.get('AUTH') == True:
		profesor = Profesor.query.filter_by(idProfesor=id).first()
		date = Asesoria.query.filter_by(idProfesor=id).first().fecha
		fecha = datetime.date.today()
		return render_template('detalleProfesor.html', profesor=profesor, fecha=fecha)
	else:
		return inicio()

@app.route('/misCitas')
def citas():
	if session.get('AUTH') == True:
		alumnoid = session['id']
		citas = Cita.query.filter_by(idAlumno=alumnoid)
		return render_template('misCitas.html', citas=citas)
	else:
		return inicio()

@app.route('/detalleHistorial/<id>')
def detalleHistorial(id):
	if session.get('AUTH') == True:
		profesor = Profesor.query.filter_by(idProfesor=int(id)).first()
		fecha = datetime.date.today()
		return render_template('detalleHistorial.html', profesor=profesor, fecha=fecha)
	else:
		return inicio()
	

@app.route('/temasHistorial/<id>')
def temasHistorial(id):
	if session.get('AUTH') == True:
		asesoria = Asesoria.query.filter_by(idAsesoria=int(id)).first()
		return render_template('temasHistorial.html', asesoria=asesoria)
	else:
		return inicio()
	
@app.route('/historial')
def historial():
	if session.get('AUTH') == True:
		profesores = Profesor.query.all()
		return render_template('historial.html', profesores=profesores)
	else:
		return inicio()

@app.route('/login', methods=['POST'])
def login():
	pw = encode(request.form['uname'], request.form['psw'])
	alumno = Alumno.query.filter_by(usuarioAlumno=request.form['uname'], contrasena=pw).first()
	if alumno:
		session['AUTH'] = True
		session['id'] = alumno.idAlumno
		session['username'] = alumno.usuarioAlumno
		session['nombre'] = alumno.nombre
		return index()
	else:
		return render_template('login.html', val = True)

def do_the_login():
	connectToFirebase()
	nodo_raiz = dbFirebase.reference()
	lista_alumnos = nodo_raiz.child('Usuarios/Alumnos').get()
	lista_docentes = nodo_raiz.child('Usuarios/Profesores').get()
	Test.AUTH = False
	for alumno in lista_alumnos:
		usuario = str(alumno.get("user"))
		password = str(alumno.get("password"))
		postUsuario = request.form['uname'] + ""
		postPassword = request.form['psw'] + ""
		if (usuario == postUsuario and password == postPassword):
			Test.AUTH = True
			print(Test.AUTH)
			break
	if Test.AUTH == True:
		session['username'] = request.form['uname']
		redirect('/index')
	else:
		return render_template('login.html', val = True)

@app.route("/index")
def index():
	if session.get('AUTH') == True:
		profesores = Profesor.query.all()
		return render_template('index.html', profesores=profesores)
	else:
		return inicio()

@app.route("/reservarCita/<int:idAs>")
def reservarCita(idAs):
	if session.get('AUTH') == True:
		session['idAs'] = idAs
		asesoria = Asesoria.query.filter_by(idAsesoria=idAs).first()
		return render_template('reservarCita.html', asesoria=asesoria)
	else:
		return inicio()

@app.route("/generarReserva", methods=['POST'])
def generarReserva():
	if session.get('AUTH') == True:
		fecha = datetime.date.today()
		cita = Cita(idAlumno=session['id'], idAsesoria=session['idAs'], fecha=fecha, pregunta=request.form['consulta'])
		db.session.add(cita)
		db.session.commit()
		asesoria = Asesoria.query.filter_by(idAsesoria=session['idAs']).first()
		return render_template('reservarCita.html', asesoria=asesoria)
	else:
		return inicio()

@app.route("/cancelarReserva/<int:id>")
def cancelarReserva(id):
	cita = Cita.query.filter_by(idCita = id).first()
	db.session.delete(cita)
	db.session.commit()
	return redirect('/misCitas')

@app.route("/cerrarSesion")
def cerrarSesion():
	session['AUTH'] = False
	return inicio()

def connectToFirebase():
	SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
	json_URL = SITE_ROOT + '/static/json/login.json'
	if (not len(firebase_admin._apps)):
		cred = credentials.Certificate(json_URL)
		firebase_admin.initialize_app(cred, {'databaseURL' : 'https://crashsoft-e0a3e.firebaseio.com/'})

def encode(key, clear):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc).encode()).decode()

def init():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    #firebase_admin.initialize_app()

if __name__ == "__main__":
	init()
	#main()
