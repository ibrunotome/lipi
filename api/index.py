from flask import Flask
from bs4 import BeautifulSoup
import requests
import os

app = Flask(__name__)


def getFuturePublicTendersFromPciConcursos(terms, states):
    message = ''

    for term in terms:
        response = requests.get(f'https://www.pciconcursos.com.br/pesquisa/?q={term}')
        soup = BeautifulSoup(response.text, 'html.parser')
        future_public_tenders = soup.find_all('div', class_=['fa', 'na'])

        if not len(future_public_tenders):
            continue

        for line in future_public_tenders:
            title = line.find('a').get_text()
            state = line.find('div', class_='cc').get_text()
            link = line.find('a').get('href')
            slots = str(line.find('div', class_='cd')).replace('<br>', ' ').replace('</br>', '').replace('<br/>', '\n').replace('<span>', '').replace('</span>', '').replace('<div class="cd">', '').replace('</div>', '')
            date = str(line.find('div', class_='ce').find('span')).replace(
                '<br>', ' ').replace('</br>', '').replace('<span>', '').replace('</span>', '')

            if 'Militar' in title:
                continue

            if state in states:
                message += f'''
{state} {date} - {title}
{slots}
{link}

-----
'''

    return message


def sendTelegramMessage(message):
    botToken = os.environ['BOT_TOKEN']
    url = f'https://api.telegram.org/bot{botToken}/sendMessage'
    form_data = {
        'chat_id': os.environ['CHAT_ID'],
        'text': message
    }

    server = requests.post(url, data=form_data)
    return server.text


@app.route('/')
def home():
    return 'Bot Telegram para concursos públicos futuros de PC/PRF/PF e Guarda Municipal'


@app.route('/concursos')
def concursos():
    terms = ['policia', 'guarda municipal']
    states = ['SP', 'SC', 'MS', 'PR']
    message = getFuturePublicTendersFromPciConcursos(terms, states)

    if message:
        sendTelegramMessage(message)
        return message

    return 'Sem concursos para os estados escolhidos'
