import ssl
import base64
import certifi
import socket
import logging
import argparse
import contextlib
import requests
import sys
from io import StringIO
from datetime import datetime
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from apscheduler.schedulers.blocking import BlockingScheduler   #pip3 install apscheduler
from tzlocal import get_localzone                               #pip3 install tzlocal
from Log4Me import Log4Me
from ConsoleTitle import ConsoleTitle
from KeyManager import KeyManager

# Constants
SCHEDULE_INTERVAL = 5
FORCE_TO_UPDATE = 0
CONTEXT = ssl.create_default_context(cafile=certifi.where())

# Configuration
API_ENDPOINT = ''
DNS_RESOLVER1 = ''
DNS_RESOLVER2 = ''
DYNDNS_USERNAME = ''
DYNDNS_UPDATER_KEY = ''
HOSTNAME = ''
ip_details = []


key_manager = KeyManager()


def init_config(file):
    global API_ENDPOINT, DNS_RESOLVER1, DNS_RESOLVER2, HOSTNAME, SCHEDULE_INTERVAL
    global DYNDNS_USERNAME, DYNDNS_UPDATER_KEY

    config_file = file

    logging.info(f'[init_config] Reading configuration from file - \'{config_file}\'')

    try:
        with open(config_file, 'r') as file:
            config_content = file.read()
    except Exception as e:
        logging.error(f'[init_config] Read config file error: {e}')
        exit(1)

    lines = config_content.split('\n')
    for line in lines:
        if line.startswith('%') or not line.strip():
            continue

        try:
            key, value = map(str.strip, line.split('=', 1))
            if key == 'API_ENDPOINT':
                API_ENDPOINT = value.strip('"')
            elif key == 'DNS_RESOLVER1':
                DNS_RESOLVER1 = value.strip('"')
            elif key == 'DNS_RESOLVER2':
                DNS_RESOLVER2 = value.strip('"')
            elif key == 'HOSTNAME':
                HOSTNAME = value.strip('"')
            elif key == 'DYNDNS_USERNAME':
                DYNDNS_USERNAME = value.strip('"')
            elif key == 'DYNDNS_UPDATER_KEY':
                DYNDNS_UPDATER_KEY = value.strip('"')
            elif key == 'SCHEDULE_INTERVAL':
                interval = value.strip('"')
                SCHEDULE_INTERVAL = int(interval) if interval.isnumeric() else SCHEDULE_INTERVAL
        except ValueError:
            print(f"[init_config] Error processing line: {line}")

    # Print the variables with colored text
    variable = (f'[init_config] Variable: '
                f'API_ENDPOINT = {API_ENDPOINT} | '
                f'DNS_RESOLVER1 = {DNS_RESOLVER1} | '
                f'DNS_RESOLVER2 = {DNS_RESOLVER2} | '
                f'HOSTNAME = {HOSTNAME} | '
                f'SCHEDULE_INTERVAL = {SCHEDULE_INTERVAL} | '
                f'dyndns_username = {DYNDNS_USERNAME} | '
                f'dyndns_updater_key = {DYNDNS_UPDATER_KEY}')

    logging.debug(variable)


def get_current_ip(dns_resolver):
    try:
        response = requests.get(dns_resolver)
        if response.status_code == 200:
            data = response.json()
            public_ip = data['ip']
            logging.info(f'[get_current_ip] Public IP address is: {public_ip} (source: {dns_resolver})')
            return public_ip
        else:
            logging.error(f'[get_current_ip] Failed to retrieve IP address. Status code: {response.status_code}')
            return None
    except requests.RequestException as e:
        logging.error(f'[get_current_ip] An error occurred: {e}')
        return None


def get_dyn_dns_ip():
    global HOSTNAME
    logging.info(f'[get_dyn_dns_ip] HOSTNAME: {HOSTNAME}')

    try:
        dyn_dns_ip = socket.gethostbyname(HOSTNAME)
        logging.info(f'[get_dyn_dns_ip] HOSTNAME_IP: {dyn_dns_ip}')
        return dyn_dns_ip
    except socket.gaierror:
        return None  # Return None if hostname resolution fails


def get_key_store(key_name):
    global key_manager

    if key_manager.exists(key_name):
        api_token = key_manager.get(key_name)
    else:
        key_manager.add(key_name)
        api_token = key_manager.get(key_name)

    return api_token


def set_key_store():
    global key_manager

    msg = f'[set_key_store] Set the key store:'
    print(f'{msg}')

    username =  key_manager.update(DYNDNS_USERNAME) if key_manager.exists(DYNDNS_USERNAME) else key_manager.add(DYNDNS_USERNAME)
    update_key =  key_manager.update(DYNDNS_UPDATER_KEY) if key_manager.exists(DYNDNS_UPDATER_KEY) else key_manager.add(DYNDNS_UPDATER_KEY)

    if not username == '' and not update_key == '':
        print('[set_key_store] Key Store is ready.')
    else:
        print('[set_key_store] Something wrong with Key Store.')


def update_dyndns(ip_address):
    global DYNDNS_USERNAME, DYNDNS_UPDATER_KEY

    username = get_key_store(DYNDNS_USERNAME)
    updater_key = get_key_store(DYNDNS_UPDATER_KEY)

    url = f"{API_ENDPOINT}?hostname={HOSTNAME}&myip={ip_address}"
    logging.info(f'[update_dyndns] URL: {url}')

    # Create the Authorization header with basic authentication
    credentials = f"{username}:{updater_key}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }
    try:
        request = Request(url, headers=headers)  # Create a Request object with headers
        response = urlopen(request, context=CONTEXT)
        response_text = response.read().decode('utf-8')
        logging.info(f'[update_dyndns] Update Status: {response_text}]')
        return response_text
    except (URLError, HTTPError) as e:
        logging.error(f'[update_dyndns] Error: {e}')
        return str(e)


def get_ip_information():
    ip_a = get_current_ip(DNS_RESOLVER1) # Get the current public IP address
    ip_b = get_current_ip(DNS_RESOLVER2) # Get the current public IP address
    dyn_ip  = get_dyn_dns_ip() # Get the IP address associated with DynDNS hostname
    ip_info = {
        'DNS_RESOLVER1': ip_a,
        'DNS_RESOLVER2': ip_b,
        'DynDNS_IP': dyn_ip
    }
    return ip_info


def process_dyndns_update(force_update:bool = False):
    global ip_details

    current_ip_a = ip_details['DNS_RESOLVER1']
    current_ip_b = ip_details['DNS_RESOLVER2']
    dyn_dns_ip  = ip_details['DynDNS_IP']
    timestamp = datetime.now().strftime('%Y-%d-%m %H:%M:%S')
    msg_debug = f'[process_dyndns_update] {timestamp} DynDNS: {dyn_dns_ip}, DNS_RESOLVER1: {current_ip_a}, DNS_RESOLVER2 {current_ip_b}'
    logging.debug(msg_debug)

    if dyn_dns_ip is None:
        print(f"Failed to resolve IP address for hostname: {HOSTNAME}")
        return
    else:
        if current_ip_a is None or current_ip_b is None or current_ip_a != current_ip_b:
            msg_error = f'[process_dyndns_update] Error: Public IP result problem. DNS_RESOLVER1 ({DNS_RESOLVER1}), DNS_RESOLVER2 ({DNS_RESOLVER2})'
            logging.error(msg_error)
            print(msg_error)
        elif current_ip_a != dyn_dns_ip or force_update:
            logging.debug(f'[process_dyndns_update] current_ip: {current_ip_a}, dyn_dns_ip: {dyn_dns_ip}, force_update: {force_update}')

            # Update DynDNS with the current IP address
            update_response = update_dyndns(current_ip_a)
            print(f'[process_dyndns_update] {timestamp} {update_response}')
        else:
            msg = f'[process_dyndns_update] {timestamp} IP addresses match. No update needed. IP: {current_ip_a}'
            logging.info(msg)
            print(msg)


if __name__ == '__main__':
    ConsoleTitle.show_title('DynDNS_Updater', False, 50)

    parse = argparse.ArgumentParser()
    parse.add_argument('--run-now', action="store_true", )
    parse.add_argument('--interval', type=str, required=False, default=SCHEDULE_INTERVAL, )
    parse.add_argument('--force', action="store_true", )
    parse.add_argument('--status', action="store_true", )
    parse.add_argument('--setup', action="store_true", )
    parse.add_argument('--debug', action="store_true", )
    args = parse.parse_args()

    if args.debug:
        Log4Me.init_logging(log_level=logging.DEBUG, log_to_file=False)
    else:
        Log4Me.init_logging(log_to_file=False)

    init_config('main.config')

    input_interval = str(args.interval)

    if input_interval.isnumeric():
        schedule_interval = int(input_interval)

    logging.debug(f'{args}')

    if args.setup:
        set_key_store()
    else:
        ip_details = get_ip_information()

    if args.run_now:
        if args.force:
            process_dyndns_update(force_update=True)
        else:
            process_dyndns_update()

    if args.status:
        current_time = datetime.now().strftime('%Y-%d-%m %H:%M:%S')
        check_only_result = f"[check_only] {current_time} DynDNS: {ip_details['DynDNS_IP']}, "  \
                            f"DNS_RESOLVER1: {ip_details['DNS_RESOLVER1']} ({urlparse(DNS_RESOLVER1).netloc}), " \
                            f"DNS_RESOLVER2 {ip_details['DNS_RESOLVER2']} ({urlparse(DNS_RESOLVER2).netloc})"
        logging.debug(check_only_result)
        print(check_only_result)

    if len(sys.argv) == 1:
        scheduler = BlockingScheduler(timezone=get_localzone())
        scheduler.add_job(process_dyndns_update, 'interval', minutes=SCHEDULE_INTERVAL)

        # Capture the print_jobs() output into a string
        with contextlib.redirect_stdout(StringIO()) as buffer:
            scheduler.print_jobs()
        scheduler_msg = buffer.getvalue().rstrip('\n')
        logging.info(scheduler_msg)
        print(scheduler_msg)

        # Start the scheduler to run the job at specific time
        try:
            scheduler.start()
        except KeyboardInterrupt:
            print("Ctrl-C pressed. Stopping the scheduler...")
            scheduler.shutdown()