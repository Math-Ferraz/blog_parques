import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

remetente = os.getenv("EMAIL_ORIGEM")
senha = os.getenv("EMAIL_SENHA")
destinatario = os.getenv("EMAIL_DESTINO")

conteudo = "Teste de envio automático pelo Flask usando senha de app Gmail."

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as conexao:
        conexao.starttls()
        conexao.login(remetente, senha)
        conexao.sendmail(remetente, destinatario, conteudo.encode('utf-8'))
    print("✅ E-mail enviado com sucesso!")
except Exception as e:
    print("❌ Erro ao enviar e-mail:", e)
