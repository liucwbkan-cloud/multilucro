import logging
import sqlite3
import random
import requests
import os
import uuid
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuração de Logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do Banco de Dados no Disco Persistente do Render (/data) ou local
DB_DIR = "/data"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR, exist_ok=True)
    DB_PATH = "multilucro.db"
else:
    DB_PATH = os.path.join(DB_DIR, "multilucro.db")

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('mp_access_token', 'APP_USR-8795274098799200-110122-881e19882551e6846a65ae9be5029814-442748191')")
    cursor.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('nome_fantasia', 'Multi Lucro Investimentos')")
    cursor.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('preco_numero_sorte', '0.10')")
    cursor.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('planos_investimento', '7 dias (1%), 30 dias (3%), 90 dias (5%), 180 dias (8%), 365 dias (20%)')")

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
        CREATE TABLE IF NOT EXISTS lottery_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ganhador_id INTEGER,
            ganhador_nome TEXT,
            numero_sorteado INTEGER,
            premio REAL,
            acumulado TEXT DEFAULT 'Não',
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM config WHERE chave = ?", (chave,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else ""

def set_config(chave, valor):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO config (chave, valor) VALUES (?, ?)", (chave, valor))
    conn.commit()
    conn.close()

class WebAppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        # 1. Rota Raiz Pública: Fachada da Intermediadora Unipay Intermediações
        if path == '/' or path == '/index':
            html = """
            <html>
            <head><title>Unipay Intermediações - Soluções B2B & B2C</title></head>
            <body style="font-family: Arial; padding: 40px; background: #0b0f19; color: #f8fafc; text-align: center;">
                <div style="max-width: 800px; margin: auto; background: #1e293b; padding: 50px; border-radius: 16px; box-shadow: 0 4px 30px rgba(0,0,0,0.8);">
                    <h1 style="color: #38bdf8; font-size: 36px; margin-bottom: 10px;">⚡ Unipay Intermediações</h1>
                    <p style="color: #34d399; font-size: 18px; font-weight: bold; margin-top:0;">Soluções Avançadas em Pagamentos B2B & B2C e Consultorias Financeiras</p>
                    <p style="color: #94a3b8; font-size: 15px; line-height: 1.6; margin-top: 20px;">
                        Facilitamos transações financeiras de alta performance, automação de recebimentos via Pix e consultoria especializada para estruturação de ecossistemas de pagamentos corporativos.
                    </p>
                    <hr style="border: 0; border-top: 1px solid #334155; margin: 30px 0;">
                    
                    <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px; margin-bottom: 40px;">
                        <div style="background: #0f172a; padding: 20px; border-radius: 8px; width: 45%;">
                            <h3 style="color: #38bdf8;">🔄 Intermediação B2B</h3>
                            <p style="color: #94a3b8; font-size: 14px;">Gestão de fluxo de caixa, split de pagamentos e liquidez para empresas.</p>
                        </div>
                        <div style="background: #0f172a; padding: 20px; border-radius: 8px; width: 45%;">
                            <h3 style="color: #38bdf8;">💳 Operações B2C</h3>
                            <p style="color: #94a3b8; font-size: 14px;">Checkout transparente, emissão instantânea de Pix e alta conversão de vendas.</p>
                        </div>
                    </div>

                    <p style="color: #64748b; font-size: 13px;">© 2026 Unipay Intermediações Ltda. Todos os direitos reservados.</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

        # 2. Rota Oculta de Acesso ao Sistema (Login / Cadastro)
        elif path == '/app' or path == '/login':
            html = """
            <html>
            <head><title>Acesso Restrito - Plataforma</title></head>
            <body style="font-family: Arial; padding: 40px; background: #0f172a; color: #f8fafc; text-align: center;">
                <div style="max-width: 500px; margin: auto; background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.6);">
                    <h2 style="color: #38bdf8;">🔐 Acesso ao Sistema</h2>
                    <p style="color: #94a3b8; font-size: 14px; margin-bottom: 25px;">Informe suas credenciais ou ID para acessar seu painel.</p>
                    
                    <form method="GET" action="/dashboard" style="margin-bottom: 30px;">
                        <input type="number" name="user_id" placeholder="Digite seu ID de Usuário" required style="width:100%; padding:12px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px; margin-bottom: 12px;"><br>
                        <input type="submit" value="Entrar no Dashboard" style="background: #22c55e; color: white; padding: 12px; font-weight: bold; border: none; border-radius:6px; cursor: pointer; width:100%;">
                    </form>

                    <hr style="border: 0; border-top: 1px solid #334155; margin: 20px 0;">
                    <p style="color: #94a3b8; font-size: 14px;">Não tem uma conta?</p>
                    <a href="/cadastro" style="background: #38bdf8; color: #0f172a; padding: 10px 20px; font-weight: bold; border-radius: 6px; text-decoration: none; display: inline-block;">Criar Nova Conta</a>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

        elif path == '/cadastro':
            html = """
            <html>
            <head><title>Cadastro de Cliente</title></head>
            <body style="font-family: Arial; padding: 40px; background: #0f172a; color: #f8fafc; text-align: center;">
                <div style="max-width: 500px; margin: auto; background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.6);">
                    <h2 style="color: #38bdf8;">📝 Cadastro de Nova Conta</h2>
                    <form method="POST" action="/cadastrar">
                        <input type="text" name="nome" placeholder="Nome Completo" required style="width:100%; padding:10px; margin-bottom:10px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px;"><br>
                        <input type="text" name="cpf" placeholder="CPF" required style="width:100%; padding:10px; margin-bottom:10px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px;"><br>
                        <input type="text" name="pix" placeholder="Chave Pix para Resgates" required style="width:100%; padding:10px; margin-bottom:10px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px;"><br>
                        <input type="text" name="telefone" placeholder="Telefone" required style="width:100%; padding:10px; margin-bottom:10px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px;"><br>
                        <input type="email" name="email" placeholder="E-mail" required style="width:100%; padding:10px; margin-bottom:20px; background:#0f172a; border:1px solid #475569; color:white; border-radius:6px;"><br>
                        <input type="submit" value="Finalizar Cadastro" style="width:100%; background: #38bdf8; color: #0f172a; padding: 12px; font-weight: bold; border: none; border-radius:6px; cursor: pointer;">
                    </form>
                    <br><a href="/app" style="color: #94a3b8; font-size: 14px;">Já possui conta? Faça login</a>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

        # 3. Painel Administrativo Oculto (/admin)
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
                planos = get_config('planos_investimento')
                fantasia = get_config('nome_fantasia')

                conn = sqlite3.connect(DB_PATH, check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(saldo_investido), SUM(arrecadado_sorteios) FROM caixa WHERE id = 1")
                caixa = cursor.fetchone()
                cursor.execute("SELECT id, ganhador_id, ganhador_nome, numero_sorteado, premio, acumulado, data FROM lottery_history ORDER BY id DESC")
                historico = cursor.fetchall()
                conn.close()

                html = f"""
                <html>
                <head><title>Painel Administrativo - {fantasia}</title></head>
                <body style="font-family: Arial; padding: 30px; background: #0f172a; color: #f8fafc;">
                    <div style="max-width: 800px; margin: auto; background: #1e293b; padding: 30px; border-radius: 12px;">
                        <h2>⚙️ Painel Administrativo e Gestão de Sorteios</h2>
                        <form method="POST" action="/admin_save">
                            <label><b>Mercado Pago Access Token:</b></label><br>
                            <input type="text" name="mp_access_token" value="{mp_token}" style="width: 100%; padding: 8px; margin-bottom: 10px; background:#0f172a; color:#fff; border:1px solid #475569; border-radius:6px;"><br>
                            
                            <label><b>Nome Fantasia Interno:</b></label><br>
                            <input type="text" name="nome_fantasia" value="{fantasia}" style="width: 100%; padding: 8px; margin-bottom: 10px; background:#0f172a; color:#fff; border:1px solid #475569; border-radius:6px;"><br>

                            <label><b>Preço do Número da Sorte (R$):</b></label><br>
                            <input type="text" name="preco_numero_sorte" value="{preco_sorte}" style="width: 100%; padding: 8px; margin-bottom: 10px; background:#0f172a; color:#fff; border:1px solid #475569; border-radius:6px;"><br>

                            <label><b>Gestão de Planos de Investimento:</b></label><br>
                            <input type="text" name="planos_investimento" value="{planos}" style="width: 100%; padding: 8px; margin-bottom: 20px; background:#0f172a; color:#fff; border:1px solid #475569; border-radius:6px;"><br>
                            
                            <input type="submit" value="Salvar Configurações" style="background: #22c55e; color: white; padding: 12px; border: none; border-radius:6px; cursor: pointer; width:100%; font-weight:bold;">
                        </form>

                        <hr style="border: 0; border-top: 1px solid #334155; margin: 30px 0;">
                        <h3>📊 Caixa Atual</h3>
                        <p>Total Investido: R$ {caixa[0] or 0.0:.2f}</p>
                        <p>Total Arrecadado para Sorteio: R$ {caixa[1] or 0.0:.2f}</p>
                        
                        <form method="POST" action="/realizar_sorteio" style="margin-bottom: 15px;">
                            <input type="submit" value="Executar Sorteio Semanal" style="background: #eab308; color: #0f172a; font-weight:bold; padding: 12px; width:100%; border:none; border-radius:6px; cursor:pointer;">
                        </form>

                        <form method="POST" action="/resetar_banco" onsubmit="return confirm('Tem certeza absoluta que deseja apagar todos os dados e resetar o banco?');">
                            <input type="submit" value="⚠️ Resetar Banco de Dados (Zerar Sistema)" style="background: #ef4444; color: white; font-weight:bold; padding: 12px; width:100%; border:none; border-radius:6px; cursor:pointer;">
                        </form>

                        <h3 style="margin-top: 30px;">🏆 Histórico Geral de Sorteios</h3>
                        <div style="background:#0f172a; padding:15px; border-radius:8px; max-height:300px; overflow-y:auto;">
                """
                for h in historico:
                    ganhador_txt = f"Ganhador: {h[2]} (ID: {h[1]}) - Número: {h[3]}" if h[1] else "Acumulado (Nenhum ganhador)"
                    html += f"<p style='border-bottom:1px solid #334155; padding-bottom:8px;'>Sorteio #{h[0]} | {ganhador_txt} | Prêmio: R$ {h[4]:.2f} | Acumulado: {h[5]} | Data: {h[6]}</p>"
                
                html += f"""
                        </div>
                        <br><a href="/" style="color: #38bdf8;">Voltar à Página Principal</a>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(html.encode("utf-8"))
            else:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Usuario ou senha incorretos.")

        # 4. Dashboard do Usuário
        elif path == '/dashboard':
            user_id = query.get('user_id', ['1'])[0]
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM users WHERE user_id = ?", (user_id,))
            u = cursor.fetchone()
            if not u:
                self.wfile.write(b"Usuario nao encontrado. <a href='/app'>Voltar ao Login</a>")
                conn.close()
                return

            nome_usuario = u[0]
            cursor.execute("SELECT id, valor, prazo_dias, lucro_pct, status FROM investments WHERE user_id = ?", (user_id,))
            invs = cursor.fetchall()
            
            cursor.execute("SELECT numero FROM lottery_tickets WHERE user_id = ? AND status = 'ativo'", (user_id,))
            bilhetes = cursor.fetchall()

            cursor.execute("SELECT arrecadado_sorteios, saldo_investido FROM caixa WHERE id = 1")
            caixa_dados = cursor.fetchone()
            arrecadado_atual = caixa_dados[0] or 0.0
            investido_atual = caixa_dados[1] or 0.0
            estimativa_premio = (arrecadado_atual * 0.40) + (investido_atual * 0.08)

            cursor.execute("SELECT id, ganhador_id, numero_sorteado, premio, acumulado, data FROM lottery_history ORDER BY id DESC LIMIT 5")
            historico_sorteios = cursor.fetchall()
            conn.close()

            preco_sorte = float(get_config('preco_numero_sorte'))
            fantasia = get_config('nome_fantasia')

            html = f"""
            <html>
            <head><title>Dashboard - {fantasia}</title></head>
            <body style="font-family: Arial; padding: 20px; background: #0f172a; color: #f8fafc;">
                <div style="max-width: 750px; margin: auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h2>👤 Olá, {nome_usuario}</h2>
                        <a href="/app" style="background:#ef4444; color:#fff; padding:6px 12px; border-radius:6px; text-decoration:none; font-size:14px;">Sair</a>
                    </div>
                    <hr style="border: 0; border-top: 1px solid #334155; margin: 20px 0;">

                    <!-- Bloco de Investimentos -->
                    <div style="background:#0f172a; padding:20px; border-radius:8px; margin-bottom:20px;">
                        <h3>💰 Gestão de Investimentos</h3>
                        <form method="POST" action="/investir">
                            <input type="hidden" name="user_id" value="{user_id}">
                            <input type="number" step="0.01" name="valor" placeholder="Valor do Investimento (R$)" required style="width:100%; padding:10px; margin-bottom:10px; background:#1e293b; border:1px solid #475569; color:white; border-radius:6px;"><br>
                            <select name="prazo" style="width:100%; padding:10px; margin-bottom:10px; background:#1e293b; border:1px solid #475569; color:white; border-radius:6px;">
                                <option value="7_1">1 Semana (1% de Lucro)</option>
                                <option value="30_3">1 Mês (3% de Lucro)</option>
                                <option value="90_5">3 Meses (5% de Lucro)</option>
                                <option value="180_8">6 Meses (8% de Lucro)</option>
                                <option value="365_20">1 Ano (20% de Lucro)</option>
                            </select><br>
                            <input type="submit" value="Investir Agora (Gerar Pix)" style="background: #22c55e; color: white; padding: 12px; width:100%; border:none; border-radius:6px; cursor:pointer; font-weight:bold;">
                        </form>
                        <h4 style="margin-top:20px;">Seus Investimentos Ativos:</h4>
                        <ul style="line-height: 1.6; padding-left:20px;">
            """
            for i in invs:
                html += f"<li>ID #{i[0]} | R$ {i[1]:.2f} | Prazo: {i[2]}d | Lucro: {i[3]}% | Status: <b>{i[4]}</b></li>"
            
            html += f"""
                        </ul>
                    </div>

                    <!-- Bloco de Números da Sorte -->
                    <div style="background:#0f172a; padding:20px; border-radius:8px; margin-bottom:20px;">
                        <h3>🎟️ Números da Sorte (R$ {preco_sorte:.2f} cada)</h3>
                        <p style="color:#38bdf8; font-weight:bold;">Estimativa de Premiação para o Próximo Sorteio: R$ {estimativa_premio:.2f}</p>
                        <form method="POST" action="/comprar_sorte">
                            <input type="hidden" name="user_id" value="{user_id}">
                            <input type="number" name="qtd" placeholder="Quantidade de números" required style="width:100%; padding:10px; margin-bottom:10px; background:#1e293b; border:1px solid #475569; color:white; border-radius:6px;"><br>
                            <input type="submit" value="Comprar Números (Gerar Pix)" style="background: #eab308; color: #0f172a; font-weight:bold; padding: 12px; width:100%; border:none; border-radius:6px; cursor:pointer;">
                        </form>
                        <h4 style="margin-top:20px;">Seus Números Ativos para o Sorteio:</h4>
                        <div style="background:#1e293b; padding:10px; border-radius:6px; word-break:break-all;">
                            {', '.join([str(b[0]) for b in bilhetes]) if bilhetes else 'Nenhum número adquirido para o sorteio atual.'}
                        </div>
                    </div>

                    <!-- Bloco de Histórico de Sorteios -->
                    <div style="background:#0f172a; padding:20px; border-radius:8px;">
                        <h3>🏆 Histórico Recente de Sorteios</h3>
                        <div style="max-height:200px; overflow-y:auto;">
            """
            for h in historico_sorteios:
                status_ganho = f"Ganhador ID: {h[1]} (Num: {h[2]})" if h[1] else "Acumulado"
                html += f"<p style='border-bottom:1px solid #334155; padding-bottom:5px; font-size:14px;'>Sorteio #{h[0]} | {status_ganho} | Prêmio: R$ {h[3]:.2f} | Acumulado: {h[4]} | Data: {h[5]}</p>"

            html += f"""
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

        elif path == '/check_status':
            payment_id = query.get('payment_id', [''])[0]
            mp_token = get_config('mp_access_token')
            status = "pendente"
            if payment_id and not payment_id.startswith('simulado'):
                headers = {"Authorization": f"Bearer {mp_token}"}
                res = requests.get(f"https://api.mercadopago.com/v1/payments/{payment_id}", headers=headers)
                if res.status_code == 200:
                    status = res.json().get("status", "pendente")
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(f'{{"status": "{status}"}}'.encode("utf-8"))

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

            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
            if 'planos_investimento' in params:
                set_config('planos_investimento', params['planos_investimento'][0])

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<body style='font-family:Arial; background:#0f172a; color:#fff; text-align:center; padding:50px;'><h3>Configuracoes salvas!</h3><a href='/admin' style='color:#38bdf8;'>Voltar</a></body>")

        elif path == '/resetar_banco':
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS config")
            cursor.execute("DROP TABLE IF EXISTS users")
            cursor.execute("DROP TABLE IF EXISTS investments")
            cursor.execute("DROP TABLE IF EXISTS lottery_tickets")
            cursor.execute("DROP TABLE IF EXISTS lottery_history")
            cursor.execute("DROP TABLE IF EXISTS caixa")
            conn.commit()
            conn.close()
            init_db()

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<body style='font-family:Arial; background:#0f172a; color:#fff; text-align:center; padding:50px;'><h3>Banco de dados resetado com sucesso!</h3><a href='/admin' style='color:#38bdf8;'>Voltar ao Admin</a></body>")

        elif path == '/realizar_sorteio':
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT saldo_investido, arrecadado_sorteios FROM caixa WHERE id = 1")
            caixa = cursor.fetchone()
            montante_investido = caixa[0] or 0.0
            montante_sorteios = caixa[1] or 0.0

            premio = (montante_sorteios * 0.40) + (montante_investido * 0.08)

            cursor.execute("SELECT ticket_id, user_id, numero FROM lottery_tickets WHERE status = 'ativo'")
            bilhetes = cursor.fetchall()

            ganhador_id = None
            ganhador_nome = None
            numero_sorteado = 0
            acumulado = "Não"

            if bilhetes and random.random() < 0.05:
                sorteado = random.choice(bilhetes)
                ganhador_id = sorteado[1]
                numero_sorteado = sorteado[2]
                cursor.execute("SELECT nome FROM users WHERE user_id = ?", (ganhador_id,))
                g_nome = cursor.fetchone()
                ganhador_nome = g_nome[0] if g_nome else "Investidor"
            else:
                acumulado = "Sim"

            cursor.execute("INSERT INTO lottery_history (ganhador_id, ganhador_nome, numero_sorteado, premio, acumulado) VALUES (?, ?, ?, ?, ?)", 
                           (ganhador_id, ganhador_nome, numero_sorteado, premio, acumulado))
            
            cursor.execute("UPDATE lottery_tickets SET status = 'encerrado'")
            cursor.execute("UPDATE caixa SET arrecadado_sorteios = 0.0 WHERE id = 1")
            conn.commit()
            conn.close()

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            msg = f"Sorteio realizado! {'Ganhador: ' + str(ganhador_nome) if ganhador_id else 'Prêmio Acumulado!'} | Prêmio: R$ {premio:.2f}"
            self.wfile.write(b"<body style='font-family:Arial; background:#0f172a; color:#fff; text-align:center; padding:50px;'><h3>" + msg.encode("utf-8") + b"</h3><a href='/admin' style='color:#38bdf8;'>Voltar</a></body>")

        elif path == '/investir':
            user_id = params.get('user_id', ['1'])[0]
            valor = float(params.get('valor', ['0'])[0])
            prazo_raw = params.get('prazo', ['7_1'])[0]
            prazo, lucro = map(float, prazo_raw.split('_'))

            mp_token = get_config('mp_access_token')
            fantasia = get_config('nome_fantasia')
            
            headers = {
                "Authorization": f"Bearer {mp_token}",
                "Content-Type": "application/json",
                "X-Idempotency-Key": str(uuid.uuid4())
            }
            payload = {
                "transaction_amount": valor,
                "description": f"Investimento {fantasia} - Prazo {prazo} dias",
                "payment_method_id": "pix",
                "payer": {"email": "cliente@multilucro.com"}
            }
            
            response = requests.post("https://api.mercadopago.com/v1/payments", json=payload, headers=headers)
            qr_code = ""
            qr_base64 = ""
            payment_id = ""
            erro_msg = ""
            if response.status_code == 201:
                data = response.json()
                payment_id = str(data.get("id"))
                t_data = data.get("point_of_interaction", {}).get("transaction_data", {})
                qr_code = t_data.get("qr_code", "")
                qr_base64 = t_data.get("qr_code_base64", "")
            else:
                erro_msg = response.text

            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO investments (user_id, valor, prazo_dias, lucro_pct, payment_id, status) VALUES (?, ?, ?, ?, ?, 'pendente')", (user_id, valor, prazo, lucro, payment_id))
            cursor.execute("UPDATE caixa SET saldo_investido = saldo_investido + ? WHERE id = 1", (valor,))
            conn.commit()
            conn.close()

            html = f"""
            <body style="font-family:Arial; background:#0f172a; color:#fff; padding:30px; text-align:center;">
                <h2>🧾 Efetue o Pagamento via Pix</h2>
                <p>Valor: R$ {valor:.2f}</p>
                {"<img src='data:image/png;base64," + qr_base64 + "' style='width:200px; height:200px; background:#fff; padding:10px; border-radius:8px;'/>" if qr_base64 else ""}
                <p><b>PIX Copia e Cola (Toque para copiar):</b></p>
                <textarea id="pixCode" readonly onclick="copyPix()" style="width:80%; height:80px; background:#1e293b; color:#fff; padding:10px; border-radius:6px; border:1px solid #475569; cursor:pointer;" title="Clique para copiar">{qr_code or 'Erro: ' + erro_msg}</textarea>
                <p id="copyAlert" style="color:#22c55e; font-size:14px; height:20px;"></p>
                
                <p style="color:#38bdf8; font-weight:bold; margin-top:10px;">Validade do Pix: <span id="timer">15:00</span></p>
                <p id="status" style="color:#eab308; font-weight:bold; margin-top:10px;">Aguardando confirmação do pagamento...</p>
                
                <script>
                    function copyPix() {{
                        const copyText = document.getElementById("pixCode");
                        copyText.select();
                        copyText.setSelectionRange(0, 99999);
                        navigator.clipboard.writeText(copyText.value);
                        document.getElementById("copyAlert").innerText = "✔ Pix copiado para a área de transferência!";
                        setTimeout(() => {{ document.getElementById("copyAlert").innerText = ""; }}, 3000);
                    }}

                    let time = 15 * 60;
                    const timerInterval = setInterval(() => {{
                        let minutes = Math.floor(time / 60);
                        let seconds = time % 60;
                        document.getElementById("timer").innerText = minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
                        if (time <= 0) {{
                            clearInterval(timerInterval);
                            document.getElementById("timer").innerText = "Expirado";
                        }}
                        time--;
                    }}, 1000);

                    const paymentId = "{payment_id}";
                    const userId = "{user_id}";
                    
                    function checkPayment() {{
                        if (!paymentId) return;
                        fetch('/check_status?payment_id=' + paymentId)
                            .then(response => response.json())
                            .then(data => {{
                                if (data.status === 'approved') {{
                                    document.getElementById('status').innerHTML = "Pagamento Aprovado com Sucesso! Redirecionando...";
                                    document.getElementById('status').style.color = "#22c55e";
                                    setTimeout(() => {{
                                        window.location.href = '/dashboard?user_id=' + userId;
                                    }}, 2000);
                                }}
                            }});
                    }}
                    setInterval(checkPayment, 3000);
                </script>
                <br><br><a href="/dashboard?user_id={user_id}" style="color:#38bdf8;">Voltar ao Dashboard</a>
            </body>
            """
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        elif path == '/comprar_sorte':
            user_id = params.get('user_id', ['1'])[0]
            qtd = int(params.get('qtd', ['1'])[0])
            preco_sorte = float(get_config('preco_numero_sorte'))
            total = qtd * preco_sorte

            mp_token = get_config('mp_access_token')
            fantasia = get_config('nome_fantasia')
            
            headers = {
                "Authorization": f"Bearer {mp_token}",
                "Content-Type": "application/json",
                "X-Idempotency-Key": str(uuid.uuid4())
            }
            payload = {
                "transaction_amount": total,
                "description": f"Compra de {qtd} Números da Sorte - {fantasia}",
                "payment_method_id": "pix",
                "payer": {"email": "cliente@multilucro.com"}
            }
            response = requests.post("https://api.mercadopago.com/v1/payments", json=payload, headers=headers)
            qr_code = ""
            qr_base64 = ""
            payment_id = ""
            erro_msg = ""
            if response.status_code == 201:
                data = response.json()
                payment_id = str(data.get("id"))
                t_data = data.get("point_of_interaction", {}).get("transaction_data", {})
                qr_code = t_data.get("qr_code", "")
                qr_base64 = t_data.get("qr_code_base64", "")
            else:
                erro_msg = response.text

            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.cursor()
            for _ in range(qtd):
                num = random.randint(10000, 99999)
                cursor.execute("INSERT INTO lottery_tickets (user_id, numero, status) VALUES (?, ?, 'ativo')", (user_id, num))
            cursor.execute("UPDATE caixa SET arrecadado_sorteios = arrecadado_sorteios + ? WHERE id = 1", (total,))
            conn.commit()
            conn.close()

            html = f"""
            <body style="font-family:Arial; background:#0f172a; color:#fff; padding:30px; text-align:center;">
                <h2>🎟️ Pagamento dos Números da Sorte</h2>
                <p>Total: R$ {total:.2f}</p>
                {"<img src='data:image/png;base64," + qr_base64 + "' style='width:200px; height:200px; background:#fff; padding:10px; border-radius:8px;'/>" if qr_base64 else ""}
                <p><b>PIX Copia e Cola (Toque para copiar):</b></p>
                <textarea id="pixCode" readonly onclick="copyPix()" style="width:80%; height:80px; background:#1e293b; color:#fff; padding:10px; border-radius:6px; border:1px solid #475569; cursor:pointer;" title="Clique para copiar">{qr_code or 'Erro: ' + erro_msg}</textarea>
                <p id="copyAlert" style="color:#22c55e; font-size:14px; height:20px;"></p>
                
                <p style="color:#38bdf8; font-weight:bold; margin-top:10px;">Validade do Pix: <span id="timer">15:00</span></p>
                <p id="status" style="color:#eab308; font-weight:bold; margin-top:10px;">Aguardando confirmação do pagamento...</p>
                
                <script>
                    function copyPix() {{
                        const copyText = document.getElementById("pixCode");
                        copyText.select();
                        copyText.setSelectionRange(0, 99999);
                        navigator.clipboard.writeText(copyText.value);
                        document.getElementById("copyAlert").innerText = "✔ Pix copiado para a área de transferência!";
                        setTimeout(() => {{ document.getElementById("copyAlert").innerText = ""; }}, 3000);
                    }}

                    let time = 15 * 60;
                    const timerInterval = setInterval(() => {{
                        let minutes = Math.floor(time / 60);
                        let seconds = time % 60;
                        document.getElementById("timer").innerText = minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
                        if (time <= 0) {{
                            clearInterval(timerInterval);
                            document.getElementById("timer").innerText = "Expirado";
                        }}
                        time--;
                    }}, 1000);

                    const paymentId = "{payment_id}";
                    const userId = "{user_id}";
                    
                    function checkPayment() {{
                        if (!paymentId) return;
                        fetch('/check_status?payment_id=' + paymentId)
                            .then(response => response.json())
                            .then(data => {{
                                if (data.status === 'approved') {{
                                    document.getElementById('status').innerHTML = "Pagamento Aprovado com Sucesso! Redirecionando...";
                                    document.getElementById('status').style.color = "#22c55e";
                                    setTimeout(() => {{
                                        window.location.href = '/dashboard?user_id=' + userId;
                                    }}, 2000);
                                }}
                            }});
                    }}
                    setInterval(checkPayment, 3000);
                </script>
                <br><br><a href="/dashboard?user_id={user_id}" style="color:#38bdf8;">Voltar ao Dashboard</a>
            </body>
            """
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), WebAppHandler)
    logger.info(f"Servidor Web rodando na porta {port}")
    server.serve_forever()

if __name__ == '__main__':
    run_web_server()
