from flask import Flask
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil import parser
import requests
import os

app = Flask(__name__)

month_mapping = {
    'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr', 'maio': 'May', 'mai': 'May', 'jun': 'Jun',
    'jul': 'Jul', 'ago': 'Aug', 'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec',
}

terms = [
    'policia', 
    'guarda', 
    'agente',
    'vigia',
]

blacklist = [
    'Administrativo',
    'Agente de Combate',
    'Agente de Serviços Gerais',
    'Ambiental',
    'Construção',
    'Contador',
    'Consumidor',
    'Defesa Civil',
    'Diretoria',
    'Endemias',
    'Engenheiro',
    'Ensino',
    'Escolar',
    'Ornamentação',
    'Professor',
    'Saúde',
    'Servente'
]

states = ['SP', 'SC', 'PR', 'RS']

def alreadyAdded(a, b):
    try:
        return a.index(b) != -1
    except:
        return False


def getFutureEventsFromPciConcursos():
    message = ''
    links = []

    for term in terms:
        response = requests.get(f'https://www.pciconcursos.com.br/pesquisa/?q={term}&sa=Pesquisar&tipopesquisa=1')
        soup = BeautifulSoup(response.text, 'html.parser')
        future_events = soup.find_all('div', class_=['fa', 'na'])

        if not len(future_events):
            continue

        for line in future_events:
            title = line.find('a').get_text()
            state = line.find('div', class_='cc').get_text()
            link = line.find('a').get('href')
            slots = str(line.find('div', class_='cd')).replace('<br>', ' ').replace('</br>', '').replace('<br/>', '\n').replace('<span>', '').replace('</span>', '').replace('<div class="cd">', '').replace('</div>', '')
            date = str(line.find('div', class_='ce').find('span')).replace(
                '<br>', ' ').replace('</br>', '').replace('<span>', '').replace('</span>', '')

            if alreadyAdded(links, link):
                continue

            if any(substring in title for substring in blacklist):
                continue

            if any(substring in slots for substring in blacklist):
                continue

            links.append(link)

            if state in states:
                message += f'''
{state} {date} - {title}
{slots}
{link}

-----
'''

    return message


def getFutureEventsFromEnergiaConcursos():
    message = ''

    links = []
    for term in terms:
        response = requests.get(f'https://www.energiaconcursos.com.br/?s={term}')
        soup = BeautifulSoup(response.text, 'html.parser')
        future_events = [article for article in soup.find_all('article', class_='has-post-thumbnail') if 'size_1x1' not in article.get('class', [])]

        if not len(future_events):
            continue

        for line in future_events:
            id = line.get('data-id')
            title = line.find('a').get_text()
            link = line.find('a').get('href')
            date = line.find('time').get_text()

            if alreadyAdded(links, link):
                continue

            if is_older_than_24h(date):
                continue

            links.append(link)

            message += f'''
{date} - {title}
{link}

-----
'''

    return message


def convert_portuguese_date(text):
    for pt_month, en_month in month_mapping.items():
        if pt_month in text:
            text = text.replace(pt_month, en_month)
    return text


def is_older_than_24h(text):
    try:
        # Check if the format contains "Ontem"
        if "Ontem" in text:
            # Get the current date and subtract one day to get "Ontem"
            time_str = text.split("às")[-1].strip() if "às" in text else ""
            date = datetime.now() - timedelta(days=1)
            if time_str:
                date = date.replace(hour=int(time_str.split(":")[0]), minute=int(time_str.split(":")[1]))
        elif "às" in text:
            # Split the date and time part when "às" is present
            date_part, time_part = text.split("às")
            date_part = convert_portuguese_date(date_part.strip())  # Convert Portuguese date to English month
            time_part = time_part.strip()  # Time part, e.g., "16:15"
            
            # Combine the date and time
            date_time_str = f"{date_part} {time_part}"
            date = parser.parse(date_time_str)  # Parse the combined datetime string
        else:
            # No time part (e.g., "20 fev 2024")
            text = convert_portuguese_date(text)
            date = parser.parse(text)

        # Check if it's older than 24 hours
        return datetime.now() - date > timedelta(days=1)

    except Exception as e:
        print(f"Error: {e}")
        return False


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


@app.route('/concursos/pci')
def concursosPci():
    message = ''
    message += getFutureEventsFromPciConcursos()

    if message:
        sendTelegramMessage(message)

    return message

@app.route('/concursos/energia')
def concursosEnergia():
    message = ''
    message += getFutureEventsFromEnergiaConcursos()

    if message:
        sendTelegramMessage(message)

    return message

if __name__ == "__main__":
    app.run(debug=True)