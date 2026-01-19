import os

from dotenv import load_dotenv

from gigachat import GigaChat


load_dotenv()

giga = GigaChat(
    credentials=os.getenv("GIGACHAT_AUTH_KEY", "NO SECRET KEY"),
    scope="GIGACHAT_API_PERS",
    model="GigaChat",
    ca_bundle_file="cerfs/russian_trusted_root_ca_pem.crt"
)

gigachat_token = giga.get_token()

print(gigachat_token)