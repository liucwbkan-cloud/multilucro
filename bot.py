import logging
import sqlite3
import random
import requests
import os
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuração de Logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização do Banco de Dados SQLite Unificado
def init_db():
    conn = sqlite3.connect('multilucro.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('mp_access_token', 'APP_USR-8795274098799200-110122-881e19882551e6846a65ae9be5029814-442748191')")
    cursor.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('nome_fantasia', 'Multi Lucro Investimentos')")
    cursor.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('preco_numero_sorte', '10.0')")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cpf TEXT,
            pix TEXT,
            telefone TEXT,
            email TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            valor REAL,
            prazo_dias INTEGER,
            lucro_pct REAL,
            payment_id TEXT,
            status TEXT DEFAULT 'pendente'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lottery_tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            numero INTEGER,
            status TEXT DEFAULT 'ativo'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS caixa (
            id INTEGER PRIMARY KEY,
            saldo_investido REAL,
            arrecadado_sorteios REAL
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO caixa (id, saldo_investido, arrecadado_sorteios) VALUES (1, 0.0, 0.0)")
    
    conn.commit()
    conn.close()

init_db()

def get_config(chave):
    conn = sqlite3.connect('multilucro.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM config WHERE chave = ?", (chave,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else ""

def set_config(chave, valor):
    conn = sqlite3.connect('multilucro.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO config (chave, valor) VALUES (?, ?)", (chave, valor))
    conn.commit()
    conn.close()

# Servidor Web Completo (Landing Page, Dashboard, Sorteios e Painel Admin /admin)
class WebAppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        fantasia = get_config('nome_fantasia')

        # 1. Landing Page Pública (Home)
        if path == '/' or path == '/index':
            html = f"""
            <html>
            <head><title>{fantasia} - Página Inicial</title></head>
            <body style="font-family: Arial; padding: 40px; background: #0f172a; color: #f8fafc; text-align: center;">
                <div style="max-width: 600px; margin: auto; background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.6);">
                    <h1 style="color: #38bdf8;">💎 {fantasia}</h1>
                    <p style="color: #94a3b8; font-size: 16px;">Invista seus valores com segurança e rentabilidade garantida. Participe também dos nossos sorteios semanais!</p>
                    <hr style="border: 0; border-top: 1px solid #334155; margin: 30px 0;">
                    
                    <h3>Já possui cadastro? Faça seu Login</h3>
                    <form method="GET" action="/dashboard" style="margin-bottom: 25px;">
                        <input type="number" name="user_id" placeholder="Digite seu ID de Usuário" required style="width:80%; padding:10px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px; margin-bottom: 10px;"><br>
                        <input type="submit" value="Entrar no Dashboard" style="background: #22c55e; color: white; padding: 10px 20px; font-weight: bold; border: none; border-radius:6px; cursor: pointer;">
                    </form>

                    <h3>Novo por aqui? Cadastre-se</h3>
                    <form method="POST" action="/cadastrar">
                        <input type="text" name="nome" placeholder="Nome Completo" required style="width:100%; padding:10px; margin-bottom:10px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px;"><br>
                        <input type="text" name="cpf" placeholder="CPF" required style="width:100%; padding:10px; margin-bottom:10px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px;"><br>
                        <input type="text" name="pix" placeholder="Chave Pix para Resgates" required style="width:100%; padding:10px; margin-bottom:10px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px;"><br>
                        <input type="text" name="telefone" placeholder="Telefone (com DDD)" required style="width:100%; padding:10px; margin-bottom:10px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px;"><br>
                        <input type="email" name="email" placeholder="E-mail" required style="width:100%; padding:10px; margin-bottom:20px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px;"><br>
                        <input type="submit" value="Criar Conta e Acessar" style="width:100%; background: #38bdf8; color: #0f172a; padding: 12px; font-weight: bold; border: none; border-radius:6px; cursor: pointer;">
                    </form>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

        # 2. Painel Administrativo (/admin)
        elif path == '/admin':
            auth_header = self.headers.get('Authorization')
            if auth_header is None or not auth_header.startswith('Basic '):
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="Painel Administrativo"')
                self.end_headers()
                self.wfile.write(b"Autenticacao necessaria.")
                return

            import base64
            auth_decoded = base64.b64decode(auth_header.split()[1]).decode('utf-8')
            user, pwd = auth_decoded.split(':', 1)

            if user == 'admult' and pwd == '010407':
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()

                mp_token = get_config('mp_access_token')
                preco_sorte = get_config('preco_numero_sorte')

                html = f"""
                <html>
                <head><title>Painel Administrativo - {fantasia}</title></head>
                <body style="font-family: Arial; padding: 30px; background: #0f172a; color: #f8fafc;">
                    <div style="max-width: 600px; margin: auto; background: #1e293b; padding: 30px; border-radius: 12px;">
                        <h2>⚙️ Painel de Configurações Gerais</h2>
                        <form method="POST" action="/admin_save">
                            <label><b>Mercado Pago Access Token:</b></label><br>
                            <input type="text" name="mp_access_token" value="{mp_token}" style="width: 100%; padding: 8px; margin-bottom: 15px; background:#0f172a; color:#fff; border:1px solid #475569;"><br>
                            
                            <label><b>Nome Fantasia:</b></label><br>
                            <input type="text" name="nome_fantasia" value="{fantasia}" style="width: 100%; padding: 8px; margin-bottom: 15px; background:#0f172a; color:#fff; border:1px solid #475569;"><br>

                            <label><b>Preço do Número da Sorte (R$):</b></label><br>
                            <input type="text" name="preco_numero_sorte" value="{preco_sorte}" style="width: 100%; padding: 8px; margin-bottom: 25px; background:#0f172a; color:#fff; border:1px solid #475569;"><br>
                            
                            <input type="submit" value="Salvar Configurações" style="background: #22c55e; color: white; padding: 12px 20px; border: none; border-radius:6px; cursor: pointer; width:100%;">
                        </form>
                        <br><a href="/" style="color: #38bdf8;">Voltar à Página Inicial</a>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(html.encode("utf-8"))
            else:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Usuario ou senha incorretos.")

        # 3. Dashboard do Usuário
        elif path == '/dashboard':
            user_id = query.get('user_id', ['1'])[0]
            conn = sqlite3.connect('multilucro.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM users WHERE user_id = ?", (user_id,))
            u = cursor.fetchone()
            if not u:
                self.wfile.write(b"Usuario nao encontrado. <a href='/'>Voltar</a>")
                conn.close()
                return

            nome_usuario = u[0]
            cursor.execute("SELECT id, valor, prazo_dias, lucro_pct, status FROM investments WHERE user_id = ?", (user_id,))
            invs = cursor.fetchall()
            
            cursor.execute("SELECT numero FROM lottery_tickets WHERE user_id = ? AND status = 'ativo'", (user_id,))
            bilhetes = cursor.fetchall()
            conn.close()

            preco_sorte = float(get_config('preco_numero_sorte'))

            html = f"""
            <html>
            <head><title>Dashboard - {fantasia}</title></head>
            <body style="font-family: Arial; padding: 30px; background: #0f172a; color: #f8fafc;">
                <div style="max-width: 700px; margin: auto; background: #1e293b; padding: 30px; border-radius: 12px;">
                    <h2>👤 Painel de Controle - Olá, {nome_usuario} (ID: {user_id})</h2>
                    <a href="/" style="color: #ef4444; text-decoration: none;">Sair / Trocar Conta</a>
                    <hr style="border: 0; border-top: 1px solid #334155; margin: 20px 0;">

                    <h3>💰 Realizar Novo Investimento</h3>
                    <form method="POST" action="/investir">
                        <input type="hidden" name="user_id" value="{user_id}">
                        <input type="number" step="0.01" name="valor" placeholder="Valor do Investimento (R$)" required style="width:100%; padding:10px; margin-bottom:10px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px;"><br>
                        <select name="prazo" style="width:100%; padding:10px; margin-bottom:10px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px;">
                            <option value="7_1">1 Semana (1% de Lucro)</option>
                            <option value="30_3">1 Mês (3% de Lucro)</option>
                            <option value="90_5">3 Meses (5% de Lucro)</option>
                            <option value="180_8">6 Meses (8% de Lucro)</option>
                            <option value="365_20">1 Ano (20% de Lucro)</option>
                        </select><br>
                        <input type="submit" value="Gerar Pix para Investir" style="background: #22c55e; color: white; padding: 12px; width:100%; border:none; border-radius:6px; cursor:pointer; font-weight:bold;">
                    </form>

                    <h3 style="margin-top: 30px;">🎟️ Números da Sorte (R$ {preco_sorte:.2f} cada)</h3>
                    <form method="POST" action="/comprar_sorte">
                        <input type="hidden" name="user_id" value="{user_id}">
                        <input type="number" name="qtd" placeholder="Quantidade de números desejados" required style="width:100%; padding:10px; margin-bottom:10px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px;"><br>
                        <input type="submit" value="Comprar Números (Gerar Pix)" style="background: #eab308; color: #0f172a; font-weight:bold; padding: 12px; width:100%; border:none; border-radius:6px; cursor:pointer;">
                    </form>

                    <h3 style="margin-top: 30px;">📊 Seus Investimentos Ativos</h3>
                    <ul style="line-height: 1.8;">
            """
            for i in invs:
                html += f"<li>ID #{i[0]} | R$ {i[1]:.2f} | Prazo: {i[2]}d | Lucro: {i[3]}% | Status: <b>{i[4]}</b></li>"
            
            html += f"""
                    </ul>

                    <h3 style="margin-top: 30px;">🎟️ Seus Números da Sorte Ativos</h3>
                    <p style="background: #0f172a; padding: 10px; border-radius: 6px;">{', '.join([str(b[0]) for b in bilhetes]) if bilhetes else 'Nenhum número adquirido para este sorteio.'}</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = urllib.parse.parse_qs(post_data)

        if path == '/cadastrar':
            nome = params.get('nome', [''])[0]
            cpf = params.get('cpf', [''])[0]
            pix = params.get('pix', [''])[0]
            telefone = params.get('telefone', [''])[0]
            email = params.get('email', [''])[0]

            conn = sqlite3.connect('multilucro.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (nome, cpf, pix, telefone, email) VALUES (?, ?, ?, ?, ?)", (nome, cpf, pix, telefone, email))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()

            self.send_response(303)
            self.send_header('Location', f'/dashboard?user_id={user_id}')
            self.end_headers()

        elif path == '/admin_save':
            if 'mp_access_token' in params:
                set_config('mp_access_token', params['mp_access_token'][0])
            if 'nome_fantasia' in params:
                set_config('nome_fantasia', params['nome_fantasia'][0])
            if 'preco_numero_sorte' in params:
                set_config('preco_numero_sorte', params['preco_numero_sorte'][0])

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<body style='font-family:Arial; background:#0f172a; color:#fff; text-align:center; padding:50px;'><h3>Configuracoes salvas com sucesso!</h3><a href='/admin' style='color:#38bdf8;'>Voltar ao Painel Admin</a></body>")

        elif path == '/investir':
            user_id = params.get('user_id', ['1'])[0]
            valor = float(params.get('valor', ['0'])[0])
            prazo_raw = params.get('prazo', ['7_1'])[0]
            prazo, lucro = map(float, prazo_raw.split('_'))

            mp_token = get_config('mp_access_token')
            fantasia = get_config('nome_fantasia')
            headers = {"Authorization": f"Bearer {mp_token}", "Content-Type": "application/json"}
            payload = {
                "transaction_amount": valor,
                "description": f"Investimento {fantasia} - Prazo {prazo} dias",
                "payment_method_id": "pix",
                "payer": {"email": "cliente@multilucro.com"}
            }
            
            response = requests.post("https://api.mercadopago.com/v1/payments", json=payload, headers=headers)
            qr_code = ""
            erro_msg = ""
            if response.status_code == 201:
                data = response.json()
                qr_code = data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")
            else:
                erro_msg = response.text

            conn = sqlite3.connect('multilucro.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO investments (user_id, valor, prazo_dias, lucro_pct, status) VALUES (?, ?, ?, ?, 'pendente')", (user_id, valor, prazo, lucro))
            conn.commit()
            conn.close()

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"""
            <body style="font-family:Arial; background:#0f172a; color:#fff; padding:30px; text-align:center;">
                <h2>🧾 Fatura Pix Gerada</h2>
                <p>Valor: R$ {valor:.2f}</p>
                <p><b>PIX Copia e Cola:</b></p>
                <textarea style="width:100%; height:120px; background:#1e293b; color:#fff; padding:10px;">{qr_code or 'Erro retornado pelo Mercado Pago: ' + erro_msg}</textarea><br><br>
                <a href="/dashboard?user_id={user_id}" style="color:#38bdf8;">Voltar ao Dashboard</a>
            </body>
            """.encode("utf-8"))

        elif path == '/comprar_sorte':
            user_id = params.get('user_id', ['1'])[0]
            qtd = int(params.get('qtd', ['1'])[0])
            preco_sorte = float(get_config('preco_numero_sorte'))
            total = qtd * preco_sorte

            mp_token = get_config('mp_access_token')
            fantasia = get_config('nome_fantasia')
            headers = {"Authorization": f"Bearer {mp_token}", "Content-Type": "application/json"}
            payload = {
                "transaction_amount": total,
                "description": f"Compra de {qtd} Números da Sorte - {fantasia}",
                "payment_method_id": "pix",
                "payer": {"email": "cliente@multilucro.com"}
            }
            response = requests.post("https://api.mercadopago.com/v1/payments", json=payload, headers=headers)
            qr_code = ""
            erro_msg = ""
            if response.status_code == 201:
                data = response.json()
                qr_code = data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")
            else:
                erro_msg = response.text

            conn = sqlite3.connect('multilucro.db', check_same_thread=False)
            cursor = conn.cursor()
            for _ in range(qtd):
                num = random.randint(10000, 99999)
                cursor.execute("INSERT INTO lottery_tickets (user_id, numero, status) VALUES (?, ?, 'ativo')", (user_id, num))
            cursor.execute("UPDATE caixa SET arrecadado_sorteios = arrecadado_sorteios + ? WHERE id = 1", (total,))
            conn.commit()
            conn.close()

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"""
            <body style="font-family:Arial; background:#0f172a; color:#fff; padding:30px; text-align:center;">
                <h2>🎟️ {qtd} Números da Sorte Adquiridos!</h2>
                <p>Total a Pagar via Pix: R$ {total:.2f}</p>
                <p><b>PIX Copia e Cola:</b></p>
                <textarea style="width:100%; height:120px; background:#1e293b; color:#fff; padding:10px;">{qr_code or 'Erro retornado pelo Mercado Pago: ' + erro_msg}</textarea><br><br>
                <a href="/dashboard?user_id={user_id}" style="color:#38bdf8;">Voltar ao Dashboard</a>
            </body>
            """.encode("utf-8"))

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), WebAppHandler)
    logger.info(f"Servidor Web rodando na porta {port}")
    server.serve_forever()

if __name__ == '__main__':
    run_web_server()
