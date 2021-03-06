# -*- coding: utf-8 -*-
import psycopg2
import psycopg2.extras
conn = psycopg2.connect('dbname=usuario user=postgres password=flasknao host=127.0.0.1')
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
from flask import render_template, request, session
from app import app
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import PKCS1_v1_5
from Crypto import Random
from base64 import b64encode, b64decode



def geradorChaves(tamanho_chave):
	#2048
	random_generator = Random.new().read
	# criando as chaves. tamanho fixo.
	key = RSA.generate(tamanho_chave, random_generator)
	# chaves publica e privada
	private = key
	public = key.publickey()
	return public, private


def encrypt(mensagem, chave_publica):
	#RSA - implementação PKCS#1 OAEP
	cipher = PKCS1_OAEP.new(chave_publica)
	return cipher.encrypt(mensagem)

def decrypt(mensagem, chave_privada):
	#RSA - implementação PKCS#1 OAEP
	cipher = PKCS1_OAEP.new(chave_privada)
	return cipher.decrypt(mensagem)



@app.route('/')
def home():
	return render_template('home.html')
@app.route('/homecliente')
def homecliente():
	return render_template('homecliente.html')
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
	return render_template('homecadastro.html')

@app.route('/caixadeentrada', methods=['GET', 'POST'])
def caixadeentrada():
	conn = psycopg2.connect('dbname=usuario user=postgres password=flasknao host=127.0.0.1')
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	cur.execute("SELECT mensagem FROM Mensagem where destinatario='%s';"%str(session['name']))
	lista_mensagens = cur.fetchall()
	mensagem =(lista_mensagens[-1][-1])
	cur.close()
	cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	cur.execute("SELECT remetente FROM Mensagem where destinatario='%s';"%str(session['name']))
	lista_remetente = cur.fetchall()
	remetente =(lista_remetente[-1][-1])
	cur.close()
	priv = psycopg2.connect('dbname=private user=postgres password=flasknao host=127.0.0.1')
	e = priv.cursor(cursor_factory=psycopg2.extras.DictCursor)
	e.execute("SELECT chavprivat FROM Private where email='%s';" %str(session['name']))
	x = e.fetchall()
	e.close()
	keyprivate = (x[0][0])
	final = b64decode(keyprivate)
	chave_privada = RSA.importKey(final)
	descriptografada = decrypt(b64decode(mensagem), chave_privada)
	return render_template('caixaentrada.html', caixa=descriptografada.decode(), remetente=remetente)

@app.route('/escrever', methods=['GET', 'POST'])
def escrever():
	if (request.method == 'POST'):
		remetente = request.form['remetente']
		destinatario = request.form['destinatario']
		mensagemdestino = request.form['mensagem']
		publi = psycopg2.connect('dbname=publico user=postgres password=flasknao host=127.0.0.1')
		t = publi.cursor(cursor_factory=psycopg2.extras.DictCursor)
		t.execute("SELECT chavpublic FROM Public where email= '%s';"%(destinatario))
		x = t.fetchall()
		t.close()
		keypublic = (x[0][0])
		final = b64decode(keypublic)
		chave_publica = RSA.importKey(final)
		print (mensagemdestino)
		resultado = encrypt(mensagemdestino.encode(), chave_publica)
		conn = psycopg2.connect('dbname=usuario user=postgres password=flasknao host=127.0.0.1')
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute("INSERT INTO Mensagem (remetente,destinatario,mensagem) VALUES ('%s','%s','%s')"%(remetente,destinatario,b64encode(resultado).decode()))
		conn.commit()
		cur.close()
		return render_template('escrevercliente.html')
	return render_template('escrevercliente.html')
@app.route('/cliente', methods=['GET', 'POST'])
def cliente():
	if (request.method == 'POST'):
		chave_publica, chave_privada = geradorChaves(2048)
		nome = request.form['nome']
		senha = request.form['senha']
		email = request.form['email']
		cpf = request.form['cpf']
		x = chave_publica.exportKey('DER')
		chavefinalpublic = b64encode(x).decode()
		y = chave_privada.exportKey('DER')
		chavefinalprivat = b64encode(y).decode()
		conn = psycopg2.connect('dbname=usuario user=postgres password=flasknao host=127.0.0.1')
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute("INSERT INTO cliente (nome,senha,email,cpf) VALUES ('%s','%s','%s', %s)"%(nome,senha,email,cpf))
		conn.commit()
		cur.close()
		publi = psycopg2.connect('dbname=publico user=postgres password=flasknao host=127.0.0.1')
		t = publi.cursor(cursor_factory=psycopg2.extras.DictCursor)
		t.execute("INSERT INTO Public (nome,email,chavpublic) VALUES ('%s','%s','%s')"%(nome,email,chavefinalpublic))
		publi.commit()
		t.close()
		priv = psycopg2.connect('dbname=private user=postgres password=flasknao host=127.0.0.1')
		e = priv.cursor(cursor_factory=psycopg2.extras.DictCursor)
		e.execute("INSERT INTO Private (nome,email,chavprivat) VALUES ('%s','%s','%s')"%(nome,email,chavefinalprivat))
		priv.commit()
		e.close()
		return render_template('cliente.html')
	return render_template('cliente.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	
	if (request.method == 'POST'):
		email = request.form['email']
		senha = request.form['password']
		conn = psycopg2.connect('dbname=usuario user=postgres password=flasknao host=127.0.0.1')
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute("SELECT * FROM cliente;")
		x = cur.fetchall()
		for i in x:
			if (i['email'] == email) and (i['senha'] == senha):
				session['name'] = request.form['email']
				return render_template('homecliente.html')
	return render_template('login.html')

