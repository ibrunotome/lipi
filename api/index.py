from flask import Flask
from bs4 import BeautifulSoup
import requests
import os

app = Flask(__name__)

def getFuturePublicTenders(term, states):
    response = requests.get(f'https://www.pciconcursos.com.br/pesquisa/?q={term}')
    soup = BeautifulSoup(response.text, 'html.parser')
    future_public_tenders = soup.find_all('div', class_='fa')

    if not len(future_public_tenders):
        return ''

    message = ''
    for line in future_public_tenders:
        title = line.find('a').get_text()
        state = line.find('div', class_='cc').get_text()
        link = line.find('a').get('href')
        slots = str(line.find('div', class_='cd')).replace('<br>', ' ').replace('</br>', '').replace('<br/>', '\n').replace('<span>', '').replace('</span>', '').replace('<div class="cd">', '').replace('</div>', '')
        date = str(line.find('div', class_='ce').find('span')).replace('<br>', ' ').replace('</br>', '').replace('<span>', '').replace('</span>', '')

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
    term = 'policia'
    states = ['SP', 'SC', 'MS', 'PR', 'MG']
    message = getFuturePublicTenders(term, states)
    
    if message:
        sendTelegramMessage(message)

    return message
