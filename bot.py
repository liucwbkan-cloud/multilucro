import logging
import sqlite3
import random
import requests
import os
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.request import HTTPXRequest

# Configuração de Logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Banco de Dados SQLite para Configurações Dinâmicas e Sistema
def init_db():
    conn = sqlite3.connect('multilucro.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT
        )
    ''')
    
    # Configurações padrão iniciais
    cursor.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('token_telegram', '9224084908:AAEdezPAnFHcc8NPuwtsPG1VEMRxZ1PrDHA')")
    cursor.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('mp_access_token', 'TEST-0000000000000000-000000-00000000000000000000000000000000-0')")
    cursor.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('nome_fantasia', 'Multi Lucro Investimentos')")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
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
            data_investimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pendente'
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE investments ADD COLUMN payment_id TEXT")
    except sqlite3.OperationalError:
        pass
        
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lottery_tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            numero INTEGER
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

# Servidor HTTP com Painel de Configurações Web Protegido (User: admult / Senha: 010407)
class ConfigHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/config':
            auth_header = self.headers.get('Authorization')
            if auth_header is None or not auth_header.startswith('Basic '):
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="Painel de Configuracoes Multi Lucro"')
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

                t_telegram = get_config('token_telegram')
                mp_token = get_config('mp_access_token')
                fantasia = get_config('nome_fantasia')

                html = f"""
                <html>
                <head><title>Multi Lucro - Painel de Configurações</title></head>
                <body style="font-family: Arial; padding: 20px; background: #f4f4f9;">
                    <h2>⚙️ Painel Administrativo - Multi Lucro</h2>
                    <form method="POST" action="/save">
                        <label><b>Token do Bot Telegram:</b></label><br>
                        <input type="text" name="token_telegram" value="{t_telegram}" style="width: 100%; padding: 8px; margin-bottom: 10px;"><br>
                        
                        <label><b>Mercado Pago Access Token:</b></label><br>
                        <input type="text" name="mp_access_token" value="{mp_token}" style="width: 100%; padding: 8px; margin-bottom: 10px;"><br>
                        
                        <label><b>Nome Fantasia:</b></label><br>
                        <input type="text" name="nome_fantasia" value="{fantasia}" style="width: 100%; padding: 8px; margin-bottom: 20px;"><br>
                        
                        <input type="submit" value="Salvar Alteracoes" style="background: #28a745; color: white; padding: 10px 20px; border: none; cursor: pointer;">
                    </form>
                </body>
                </html>
                """
                self.wfile.write(html.encode("utf-8"))
            else:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Usuario ou senha incorretos.")
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Multi Lucro Bot online na nuvem com sucesso!")

    def do_POST(self):
        if self.path == '/save':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(post_data)

            if 'token_telegram' in params:
                set_config('token_telegram', params['token_telegram'][0])
            if 'mp_access_token' in params:
                set_config('mp_access_token', params['mp_access_token'][0])
            if 'nome_fantasia' in params:
                set_config('nome_fantasia', params['nome_fantasia'][0])

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h3>Configuracoes salvas com sucesso! Reinicie o servico no Render se alterou o Token do Bot.</h3><a href='/'>Voltar</a>")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), ConfigHandler)
    logger.info(f"Servidor Web rodando na porta {port}")
    server.serve_forever()

user_states = {}

async def post_init(application: Application):
    commands = [
        ("start", "Iniciar o bot e painel principal"),
        ("investir", "Fazer um novo investimento"),
        ("meus_investimentos", "Ver e resgatar investimentos"),
        ("sorte", "Comprar numeros da sorte"),
        ("cadastro", "Ver meus dados cadastrais")
    ]
    await application.bot.set_my_commands(commands)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('multilucro.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        user_states[user_id] = {'step': 'nome'}
        await update.message.reply_text(
            "🚀 **Bem-vindo à Multi Lucro Investimentos!**\n\n"
            "Para começar, precisamos realizar seu cadastro.\n"
            "Por favor, digite seu **Nome Completo**:"
        )
    else:
        await main_menu(update, context)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Meus Investimentos & Resgates", callback_data='ver_investimentos'),
         InlineKeyboardButton("💰 Investir Agora", callback_data='novo_investimento')],
        [InlineKeyboardButton("🎟️ Números da Sorte", callback_data='comprar_sorte'),
         InlineKeyboardButton("👤 Meu Cadastro", callback_data='ver_cadastro')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"💎 **Painel Principal - {get_config('nome_fantasia')}**\n\nEscolha uma opção abaixo:"
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id in user_states:
        step = user_states[user_id]['step']
        
        if step == 'nome':
            user_states[user_id]['nome'] = text
            user_states[user_id]['step'] = 'cpf'
            await update.message.reply_text("Ótimo! Agora digite seu **CPF**:")
        elif step == 'cpf':
            user_states[user_id]['cpf'] = text
            user_states[user_id]['step'] = 'pix'
            await update.message.reply_text("Perfeito. Digite sua **Chave Pix** para recebimento de resgates:")
        elif step == 'pix':
            user_states[user_id]['pix'] = text
            user_states[user_id]['step'] = 'telefone'
            await update.message.reply_text("Informe seu número de **Telefone** (com DDD):")
        elif step == 'telefone':
            user_states[user_id]['telefone'] = text
            user_states[user_id]['step'] = 'email'
            await update.message.reply_text("Para finalizar o cadastro, digite seu **E-mail**:")
        elif step == 'email':
            nome = user_states[user_id]['nome']
            cpf = user_states[user_id]['cpf']
            pix = user_states[user_id]['pix']
            telefone = user_states[user_id]['telefone']
            email = text

            conn = sqlite3.connect('multilucro.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO users (user_id, nome, cpf, pix, telefone, email) VALUES (?, ?, ?, ?, ?, ?)",
                           (user_id, nome, cpf, pix, telefone, email))
            conn.commit()
            conn.close()

            del user_states[user_id]
            await update.message.reply_text(f"✅ **Cadastro realizado com sucesso na {get_config('nome_fantasia')}!**")
            await main_menu(update, context)
            
        elif user_states[user_id].get('step') == 'valor_investimento':
            try:
                valor = float(text.replace(',', '.'))
                prazo = user_states[user_id]['prazo']
                lucro = user_states[user_id]['lucro']

                mp_token = get_config('mp_access_token')
                headers = {
                    "Authorization": f"Bearer {mp_token}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "transaction_amount": valor,
                    "description": f"Investimento {get_config('nome_fantasia')} - Prazo {prazo} dias",
                    "payment_method_id": "pix",
                    "payer": {
                        "email": "cliente@multilucro.com"
                    }
                }
                
                response = requests.post("https://api.mercadopago.com/v1/payments", json=payload, headers=headers)
                
                if response.status_code != 201:
                    del user_states[user_id]
                    await update.message.reply_text(
                        "❌ **Erro ao gerar a cobrança Pix!**\n\n"
                        "Não foi possível conectar à intermediadora de pagamentos (Verifique o Token no painel de configurações).\n"
                        "O investimento **não** foi registrado."
                    )
                    await main_menu(update, context)
                    return

                data = response.json()
                payment_id = str(data.get("id"))
                point_of_interaction = data.get("point_of_interaction", {})
                qr_data = point_of_interaction.get("transaction_data", {})
                qr_code_copia_cola = qr_data.get("qr_code")

                if not qr_code_copia_cola:
                    del user_states[user_id]
                    await update.message.reply_text(
                        "❌ **Erro na resposta do Pix!** O código Copia e Cola não foi retornado. Investimento cancelado."
                    )
                    await main_menu(update, context)
                    return

                conn = sqlite3.connect('multilucro.db', check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO investments (user_id, valor, prazo_dias, lucro_pct, payment_id, status) VALUES (?, ?, ?, ?, ?, 'pendente')",
                               (user_id, valor, prazo, lucro, payment_id))
                cursor.execute("UPDATE caixa SET saldo_investido = saldo_investido + ? WHERE id = 1", (valor,))
                conn.commit()
                conn.close()

                del user_states[user_id]
                
                await update.message.reply_text(
                    f"🧾 **Fatura Pix Gerada - {get_config('nome_fantasia')}**\n\n"
                    f"💰 Valor: R$ {valor:.2f}\n"
                    f"📈 Retorno previsto: {lucro}% em {prazo} dias\n\n"
                    f"📋 **PIX Copia e Cola:**\n`{qr_code_copia_cola}`\n\n"
                    f"⏳ *Realize o pagamento via Pix utilizando o código acima.*"
                )
                await main_menu(update, context)
            except ValueError:
                await update.message.reply_text("❌ Valor inválido. Digite apenas números (ex: 150.00):")
                
        elif user_states[user_id].get('step') == 'qtd_sorte':
            try:
                qtd = int(text)
                custo_unitario = 10.0
                total = qtd * custo_unitario

                conn = sqlite3.connect('multilucro.db', check_same_thread=False)
                cursor = conn.cursor()
                for _ in range(qtd):
                    num_sorte = random.randint(10000, 99999)
                    cursor.execute("INSERT INTO lottery_tickets (user_id, numero) VALUES (?, ?)", (user_id, num_sorte))
                
                cursor.execute("UPDATE caixa SET arrecadado_sorteios = arrecadado_sorteios + ? WHERE id = 1", (total,))
                conn.commit()
                conn.close()

                del user_states[user_id]
                await update.message.reply_text(
                    f"🎟️ **{qtd} Números da Sorte Adquiridos com Sucesso!**\n"
                    f"Total pago: R$ {total:.2f}\n\n"
                    f"Boa sorte! Os sorteios ocorrem semanalmente."
                )
                await main_menu(update, context)
            except ValueError:
                await update.message.reply_text("❌ Insira um número inteiro válido:")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'ver_cadastro':
        conn = sqlite3.connect('multilucro.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT nome, cpf, pix, telefone, email FROM users WHERE user_id = ?", (user_id,))
        u = cursor.fetchone()
        conn.close()

        if u:
            text = (f"👤 **Seus Dados - {get_config('nome_fantasia')}**\n\n"
                    f"Nome: {u[0]}\nCPF: {u[1]}\nPix: {u[2]}\nTelefone: {u[3]}\nE-mail: {u[4]}")
        else:
            text = "Cadastre-se primeiro usando /start"
        
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data='voltar_menu')]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'novo_investimento':
        keyboard = [
            [InlineKeyboardButton("1 Semana (1% de lucro)", callback_data='inv_7_1')],
            [InlineKeyboardButton("1 Mês (3% de lucro)", callback_data='inv_30_3')],
            [InlineKeyboardButton("3 Meses (5% de lucro)", callback_data='inv_90_5')],
            [InlineKeyboardButton("6 Meses (8% de lucro)", callback_data='inv_180_8')],
            [InlineKeyboardButton("1 Ano (20% de lucro)", callback_data='inv_365_20')],
            [InlineKeyboardButton("⬅️ Voltar", callback_data='voltar_menu')]
        ]
        await query.message.edit_text("📈 **Selecione o prazo do seu investimento:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('inv_'):
        _, dias, lucro = query.data.split('_')
        user_states[user_id] = {'step': 'valor_investimento', 'prazo': int(dias), 'lucro': float(lucro)}
        await query.message.reply_text("💵 Digite o valor que deseja **investir** (ex: 500.00):")

    elif query.data == 'ver_investimentos':
        conn = sqlite3.connect('multilucro.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT id, valor, prazo_dias, lucro_pct, status FROM investments WHERE user_id = ?", (user_id,))
        invs = cursor.fetchall()
        conn.close()

        if not invs:
            text = "📊 Você não possui investimentos registrados."
            keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data='voltar_menu')]]
        else:
            text = "📊 **Seus Investimentos & Opções de Resgate:**\n\n"
            keyboard = []
            for inv in invs:
                inv_id, valor, prazo, lucro, status = inv
                text += f"ID: #{inv_id} | R$ {valor:.2f} | Prazo: {prazo}d | Lucro: {lucro}% | Status: **{status}**\n"
                keyboard.append([InlineKeyboardButton(f"💸 Resgatar Investimento #{inv_id}", callback_data=f'resgatar_{inv_id}')])
            keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data='voltar_menu')])
            
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('resgatar_'):
        inv_id = int(query.data.split('_')[1])
        conn = sqlite3.connect('multilucro.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT valor, status FROM investments WHERE id = ? AND user_id = ?", (inv_id, user_id))
        inv = cursor.fetchone()
        
        if inv:
            valor_investido, status = inv
            taxa_antecipacao = valor_investido * 0.30
            valor_liquido = valor_investido - taxa_antecipacao
            
            cursor.execute("UPDATE investments SET status = 'resgatado' WHERE id = ?", (inv_id,))
            conn.commit()
            conn.close()

            await query.message.edit_text(
                f"💸 **Resgate Solicitado com Sucesso!**\n\n"
                f"Valor Investido: R$ {valor_investido:.2f}\n"
                f"Taxa de Antecipação (30%): -R$ {taxa_antecipacao:.2f}\n"
                f"**Valor Líquido a Receber via Pix:** R$ {valor_liquido:.2f}\n\n"
                f"O pagamento será enviado para sua chave Pix cadastrada em instantes.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data='voltar_menu')]])
            )
        else:
            conn.close()
            await query.answer("Investimento não encontrado.", show_alert=True)

    elif query.data == 'comprar_sorte':
        user_states[user_id] = {'step': 'qtd_sorte'}
        await query.message.reply_text("🎟️ Cada número da sorte custa **R$ 10,00**.\nQuantos números você deseja comprar?")

    elif query.data == 'voltar_menu':
        await main_menu(update, context)

def main():
    # Inicia o servidor HTTP web em background na porta fornecida pelo Render (ou 10000)
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()

    token = get_config('token_telegram')

    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )
    
    app = Application.builder().token(token).request(request).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("investir", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    app.add_error_handler(error_handler)

    print("🤖 Bot Multi Lucro rodando na nuvem com Painel de Configurações Web!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
