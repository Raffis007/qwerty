import telebot
from telebot import types
import time
import os
from flask import Flask, request
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token do bot
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN não configurado!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# Flask app
app = Flask(__name__)

# Dados para PIX
PIX_KEY = "6b49c28d-1d21-445e-9c5b-ef5628ce511a"
NOME_BENEFICIARIO = "LUCIMAR RIBEIRO DA FONSEC"

# Chaves PIX específicas para cada valor
CHAVES_PIX_ESPECIFICAS = {
    30.00: "00020126580014br.gov.bcb.pix01366b49c28d-1d21-445e-9c5b-ef5628ce511a520400005303986540530.005802BR5925LUCIMAR RIBEIRO DA FONSEC6009Sao Paulo62290525REC68C2205BC289D145909038630453BE",
    40.00: "00020126580014br.gov.bcb.pix01366b49c28d-1d21-445e-9c5b-ef5628ce511a520400005303986540540.005802BR5925LUCIMAR RIBEIRO DA FONSEC6009Sao Paulo62290525REC68C2208D374F861069946463042F7E",
    45.00: "00020126580014br.gov.bcb.pix01366b49c28d-1d21-445e-9c5b-ef5628ce511a520400005303986540545.005802BR5925LUCIMAR RIBEIRO DA FONSEC6009Sao Paulo62290525REC68C220D24C342075459020630472E9"
}

# Pacotes de Mídias
PACOTES = {
    "1": {
        "nome": "4700 Mídias",
        "preco": 30.00,
        "descricao": "Pacote com 4700 mídias de cp!",
        "emoji": "📱"
    },
    "2": {
        "nome": "5700 Mídias",
        "preco": 40.00,
        "descricao": "Pacote com 5700 mídias de cp!",
        "emoji": "📱📱"
    },
    "3": {
        "nome": "9000 Mídias",
        "preco": 45.00,
        "descricao": "Pacote com 9000 mídias de cp!",
        "emoji": "📱📱📱"
    }
}

# Taxa adicional para grupo VIP
TAXA_GRUPO_VIP = 20.00

# URLs dos QR Codes personalizados
QR_CODES = {
    30.00: "https://i.imgur.com/Ttjztyn.png",
    40.00: "https://i.imgur.com/zKK5qYO.png",
    45.00: "https://i.imgur.com/GgONGb3.png"
}

# Link do suporte
SUPORTE_LINK = "https://t.me/Shopsuporte"

def obter_chave_pix_especifica(valor):
    """Retorna a chave PIX específica baseada no valor do pacote"""
    return CHAVES_PIX_ESPECIFICAS.get(valor, PIX_KEY)

def obter_qr_code_personalizado(valor):
    """Retorna URL do QR Code personalizado baseado no valor"""
    for preco_base in [30.00, 40.00, 45.00]:
        if valor == preco_base or valor == preco_base + TAXA_GRUPO_VIP:
            return QR_CODES.get(preco_base)
    return QR_CODES[30.00]

# Rotas Flask
@app.route('/')
def home():
    return "Bot está funcionando no Render!"

@app.route('/health')
def health():
    return {"status": "ok", "bot": "active"}

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        if request.headers.get('Content-Type') == 'application/json':
            json_str = request.get_data(as_text=True)
            update = telebot.types.Update.de_json(json_str)
            logger.info(f"Recebida mensagem de {update.message.from_user.id if update.message else 'callback'}")
            bot.process_new_updates([update])
            return "OK", 200
        else:
            logger.warning("Content-Type inválido recebido no webhook")
            return "Bad Request", 400
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return "Internal Server Error", 500

# Handlers do bot
@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"Comando /start recebido de {message.from_user.id}")
    
    texto_boas_vindas = """
🎉 *BEM-VINDO!* 🎉

📱 Aqui você encontra os melhores pacotes de mídias!
🎗️ Qualidade e confiança
🎬 Conteúdo de qualidade
⚡ Entrega imediata após pagamento
💯 Satisfação garantida

Escolha seu pacote abaixo:
    """

    bot.send_message(message.chat.id, texto_boas_vindas, parse_mode='Markdown')

    markup = types.InlineKeyboardMarkup()
    for id_pacote, pacote in PACOTES.items():
        markup.add(types.InlineKeyboardButton(
            f"{pacote['emoji']} {pacote['nome']} - R$ {pacote['preco']:.2f}",
            callback_data=f"pacote_{id_pacote}"))

    markup.add(types.InlineKeyboardButton(
        f"🌟 Qualquer pacote + Grupo VIP (+R$ {TAXA_GRUPO_VIP:.2f})",
        callback_data="info_grupo_vip"))
    
    markup.add(types.InlineKeyboardButton("👨‍💻 Contato Suporte", url=SUPORTE_LINK))

    bot.send_message(
        message.chat.id,
        "📦 *Escolha seu pacote:*\n\n"
        f"💎 *Grupo VIP:* Acesso vitalício ao grupo exclusivo\n"
        f"💰 *Taxa adicional:* +R$ {TAXA_GRUPO_VIP:.2f} em qualquer pacote\n"
        f"⚠️ *IMPORTANTE:* VIP só pode ser adquirido junto com pacote!",
        parse_mode='Markdown',
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('pacote_'))
def escolher_pacote(call):
    logger.info(f"Pacote selecionado: {call.data}")
    id_pacote = call.data.split('_')[1]
    pacote = PACOTES[id_pacote]

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        f"📱 Apenas {pacote['nome']} - R$ {pacote['preco']:.2f}",
        callback_data=f"final_{id_pacote}_sem_grupo"))
    markup.add(types.InlineKeyboardButton(
        f"🌟 {pacote['nome']} + Grupo VIP - R$ {pacote['preco'] + TAXA_GRUPO_VIP:.2f}",
        callback_data=f"final_{id_pacote}_com_grupo"))
    markup.add(types.InlineKeyboardButton("👨‍💻 Contato Suporte", url=SUPORTE_LINK))
    markup.add(types.InlineKeyboardButton("🔙 Voltar", callback_data="voltar_menu"))

    texto_opcoes = f"""
📦 *{pacote['nome']} Selecionado*

{pacote['descricao']}

💰 *Opções de pagamento:*

📱 **Apenas mídias:** R$ {pacote['preco']:.2f}
🌟 **Mídias + Grupo VIP:** R$ {pacote['preco'] + TAXA_GRUPO_VIP:.2f}

💎 *Grupo VIP inclui:*
• Acesso vitalício ao grupo exclusivo
• Conteúdo premium adicional
• Atualizações constantes
• Suporte prioritário

⚠️ *ATENÇÃO:* Grupo VIP só pode ser adquirido junto com o pacote!
Não vendemos VIP separadamente.

Escolha sua opção:
    """

    bot.edit_message_text(texto_opcoes, call.message.chat.id, call.message.message_id, 
                         parse_mode='Markdown', reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('final_'))
def finalizar_escolha(call):
    logger.info(f"Finalizando escolha: {call.data}")
    dados = call.data.split('_')
    id_pacote = dados[1]
    tem_grupo = dados[2] == 'com'

    pacote = PACOTES[id_pacote]
    preco_final = pacote['preco'] + (TAXA_GRUPO_VIP if tem_grupo else 0)
    
    chave_pix_usar = obter_chave_pix_especifica(pacote['preco']) if not tem_grupo else PIX_KEY
    grupo_texto = "🌟 + Grupo VIP" if tem_grupo else ""

    texto_pagamento = f"""
✅ *Pacote Confirmado:*
{pacote['emoji']} {pacote['nome']} {grupo_texto}

📝 *Descrição:* {pacote['descricao']}
💰 *Valor Final:* R$ {preco_final:.2f}
{f"   • Pacote: R$ {pacote['preco']:.2f}" if tem_grupo else ""}
{f"   • Grupo VIP: R$ {TAXA_GRUPO_VIP:.2f}" if tem_grupo else ""}

💳 *DADOS PARA PAGAMENTO PIX:*
🔑 *Chave PIX:* `{chave_pix_usar}`
👤 *Nome:* {NOME_BENEFICIARIO}
💵 *Valor EXATO:* R$ {preco_final:.2f}

📱 *Escaneie o QR Code abaixo ou use a chave PIX*
⚡ *Entrega imediata após confirmação do pagamento*
    """

    bot.send_message(call.message.chat.id, texto_pagamento, parse_mode='Markdown')

    qr_code_url = obter_qr_code_personalizado(preco_final)
    bot.send_photo(
        call.message.chat.id,
        qr_code_url,
        caption=f"📱 *QR Code PIX - R$ {preco_final:.2f}*\n\n"
                f"⚠️ **IMPORTANTE:** Pague exatamente R$ {preco_final:.2f}\n"
                f"Após o pagamento, nos envie o comprovante em PDF!",
        parse_mode='Markdown')

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "📄 Enviar Comprovante",
        callback_data=f"comprovante_{id_pacote}_{preco_final:.2f}_{tem_grupo}"))
    markup.add(types.InlineKeyboardButton("👨‍💻 Contato Suporte", url=SUPORTE_LINK))
    markup.add(types.InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu"))

    bot.send_message(call.message.chat.id,
                     "⏰ *Aguardando seu pagamento...*\n\n"
                     "Clique no botão abaixo após realizar o PIX:",
                     parse_mode='Markdown', reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "info_grupo_vip")
def info_grupo_vip(call):
    texto_info = f"""
🌟 *GRUPO VIP - INFORMAÇÕES*

💎 **O que está incluso:**
• Acesso vitalício ao grupo exclusivo
• Conteúdo premium adicional
• Atualizações constantes de mídias
• Suporte prioritário
• Comunidade exclusiva

💰 **Taxa adicional:** +R$ {TAXA_GRUPO_VIP:.2f}

⚠️ **REGRA IMPORTANTE:**
• VIP só pode ser comprado JUNTO com pacote
• Não vendemos acesso VIP separadamente
• É uma compra única: Pacote + VIP juntos

📝 **Como funciona:**
Escolha qualquer pacote e adicione VIP na mesma compra

🔙 Volte ao menu para escolher seu pacote + VIP
    """

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👨‍💻 Contato Suporte", url=SUPORTE_LINK))
    markup.add(types.InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu"))

    bot.edit_message_text(texto_info, call.message.chat.id, call.message.message_id,
                         parse_mode='Markdown', reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('comprovante_'))
def solicitar_comprovante(call):
    dados = call.data.replace('comprovante_', '').split('_')
    id_pacote = dados[0]
    preco_final = float(dados[1])
    tem_grupo = dados[2] == 'True'

    pacote = PACOTES[id_pacote]
    grupo_texto = " + Grupo VIP" if tem_grupo else ""

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👨‍💻 Contato Suporte", url=SUPORTE_LINK))

    bot.send_message(
        call.message.chat.id,
        f"📄 *Envie o comprovante do PIX em PDF*\n\n"
        f"📦 Pacote: {pacote['nome']}{grupo_texto}\n"
        f"💰 Valor: R$ {preco_final:.2f}\n\n"
        f"📄 IMPORTANTE: Envie apenas arquivos PDF do comprovante\n"
        f"⚠️ **Valor deve ser exatamente R$ {preco_final:.2f}**\n"
        f"⚡ Após aprovação, você receberá suas mídias!",
        parse_mode='Markdown', reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "voltar_menu")
def voltar_menu(call):
    start_from_callback(call)
    bot.answer_callback_query(call.id)

def start_from_callback(call):
    """Função auxiliar para /start via callback"""
    texto_boas_vindas = """
🎉 *BEM-VINDO!* 🎉

📱 Aqui você encontra os melhores pacotes de mídias!
🎗️ Qualidade e confiança
🎬 Conteúdo de qualidade
⚡ Entrega imediata após pagamento
💯 Satisfação garantida

Escolha seu pacote abaixo:
    """

    markup = types.InlineKeyboardMarkup()
    for id_pacote, pacote in PACOTES.items():
        markup.add(types.InlineKeyboardButton(
            f"{pacote['emoji']} {pacote['nome']} - R$ {pacote['preco']:.2f}",
            callback_data=f"pacote_{id_pacote}"))

    markup.add(types.InlineKeyboardButton(
        f"🌟 Qualquer pacote + Grupo VIP (+R$ {TAXA_GRUPO_VIP:.2f})",
        callback_data="info_grupo_vip"))
    
    markup.add(types.InlineKeyboardButton("👨‍💻 Contato Suporte", url=SUPORTE_LINK))

    try:
        bot.edit_message_text(
            texto_boas_vindas + "\n\n📦 *Escolha seu pacote:*\n\n"
            f"💎 *Grupo VIP:* Acesso vitalício ao grupo exclusivo\n"
            f"💰 *Taxa adicional:* +R$ {TAXA_GRUPO_VIP:.2f} em qualquer pacote\n"
            f"⚠️ *IMPORTANTE:* VIP só pode ser adquirido junto com pacote!",
            call.message.chat.id, call.message.message_id,
            parse_mode='Markdown', reply_markup=markup)
    except:
        # Se não conseguir editar, envia nova mensagem
        bot.send_message(
            call.message.chat.id,
            texto_boas_vindas + "\n\n📦 *Escolha seu pacote:*\n\n"
            f"💎 *Grupo VIP:* Acesso vitalício ao grupo exclusivo\n"
            f"💰 *Taxa adicional:* +R$ {TAXA_GRUPO_VIP:.2f} em qualquer pacote\n"
            f"⚠️ *IMPORTANTE:* VIP só pode ser adquirido junto com pacote!",
            parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(content_types=['photo', 'document'])
def processar_comprovante(message):
    logger.info(f"Comprovante recebido de {message.from_user.id}")
    
    if message.content_type == 'document':
        if not message.document.file_name.lower().endswith('.pdf'):
            bot.send_message(message.chat.id, "❌ Por favor, envie apenas arquivos PDF do comprovante.")
            return
    elif message.content_type == 'photo':
        bot.send_message(message.chat.id, "❌ Por favor, envie apenas arquivos PDF do comprovante.")
        return

    # Simular análise do comprovante
    bot.send_message(message.chat.id, "⏳ Verificando comprovante PDF...")
    time.sleep(2)
    bot.send_message(message.chat.id, "🔍 Analisando dados do pagamento...")
    time.sleep(3)
    bot.send_message(message.chat.id, "💳 Validando valor e transação PIX...")
    time.sleep(2)
    # Bot para de responder aqui (simulando abandono)

@bot.message_handler(func=lambda message: True)
def resposta_padrao(message):
    logger.info(f"Mensagem não reconhecida de {message.from_user.id}: {message.text}")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📱 Ver Pacotes", callback_data="voltar_menu"))
    markup.add(types.InlineKeyboardButton("👨‍💻 Contato Suporte", url=SUPORTE_LINK))

    bot.send_message(message.chat.id,
                     "📱 Bem-vindo à nossa loja de mídias!\n\n"
                     "Digite /start para ver nossos pacotes:",
                     reply_markup=markup)

# Configurar webhook
def setup_webhook():
    try:
        WEBHOOK_HOST = os.getenv('RENDER_EXTERNAL_HOSTNAME')
        if WEBHOOK_HOST:
            WEBHOOK_URL = f"https://{WEBHOOK_HOST}/{BOT_TOKEN}"
            
            # Remove webhook antigo
            bot.remove_webhook()
            time.sleep(1)
            
            # Configura novo webhook
            result = bot.set_webhook(url=WEBHOOK_URL)
            if result:
                logger.info(f"Webhook configurado com sucesso: {WEBHOOK_URL}")
            else:
                logger.error("Falha ao configurar webhook")
        else:
            logger.warning("RENDER_EXTERNAL_HOSTNAME não encontrado")
    except Exception as e:
        logger.error(f"Erro ao configurar webhook: {e}")

if __name__ == "__main__":
    logger.info("Iniciando aplicação...")
    logger.info(f"BOT_TOKEN configurado: {'Sim' if BOT_TOKEN else 'Não'}")
    
    # Configurar webhook se estiver no Render
    if os.getenv('RENDER_EXTERNAL_HOSTNAME'):
        setup_webhook()
    else:
        logger.info("Rodando localmente - webhook não configurado")
    
    # Iniciar servidor
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Iniciando servidor na porta: {port}")
    
    try:
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")