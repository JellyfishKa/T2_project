import os
import pytest
from dotenv import load_dotenv
from gigachat import GigaChat

load_dotenv()


@pytest.fixture
def giga():
    return GigaChat(
        credentials=os.getenv("GIGACHAT_AUTH_KEY"),
        scope="GIGACHAT_API_PERS",
        model="GigaChat",
        ca_bundle_file="../cerfs/russian_trusted_root_ca_pem.crt",
    )


def test_gigachat_token_exists_inside_env():
    assert os.getenv("GIGACHAT_AUTH_KEY")


def test_gigachat_chat_started(giga):
    response = giga.chat(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Привет, напиши короткий приветственный текст!",
                }
            ]
        }
    )
    assert response
    assert response.choices
    assert response.choices[0].message.content

