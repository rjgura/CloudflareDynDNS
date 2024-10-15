#!/usr/bin/env python

import asyncio
import configparser
import logging
import sys
import time

from cloudflare import AsyncCloudflare
from logging.handlers import RotatingFileHandler
from pif import get_public_ip

start_time = time.time()

#
# Constants
#
SCRIPT_VERSION = 'v1.1.0'
CONFIG_PATH = r'LocalConfig/Settings.ini'
LOG_FILENAME = r'LocalConfig/CloudflareDynDNS.log'
'''
LOG_FILENAME = 'CloudflareDynDNS.log' for Windows 
LOG_FILENAME = '/var/log/CloudflareDynDNS.log' for Linux
'''
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
FORMATTER = logging.Formatter('[%(asctime)s][%(levelname)s]: %(message)s', DATE_FORMAT)

#
# Setup Logging
#
logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)

sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
sh.setFormatter(FORMATTER)
logger.addHandler(sh)

fh = RotatingFileHandler(LOG_FILENAME,
                         mode='a',
                         maxBytes=5*1024*1024,
                         backupCount=2,
                         encoding=None,
                         delay=False
                         )

fh.setLevel(logging.DEBUG)
fh.setFormatter(FORMATTER)
logger.addHandler(fh)

# Check if running on a linux system, but not from terminal
# This fix stops output going to an unattached terminal if being run by cron
if sys.platform[0:5] == 'linux' and not sys.stdout.isatty():
    logger.debug(f'Script running in Linux with no Terminal Connected, removing stream handler')
    logger.removeHandler(sh)

#
# Import Settings from Config File .ini
#
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

logger.debug(f'Loading config file: {CONFIG_PATH}')
try:
    last_recorded_ip = config['IP_ADDRESSES']['Last_Recorded_IP']
    DOMAINS_LIST = config.items('DOMAINS_LIST')
    RECORD_TYPE = config['RECORD_TYPE']['Record_Type']
    RECORD_NAME = config['RECORD_TYPE']['Record_Name']
    CLOUDFLARE_API_TOKEN = config['CREDENTIALS']['Cloudflare_API_Token']

 # TODO: Catch error when missing a section
 # TODO: Catch error when missing an entry

except KeyError:
    logger.error('Error loading config file: check that file exists and settings inside are correct')
    quit()

try:
    logger.debug('Getting External IP')
    external_ip = get_public_ip()
    logger.info(f'Got external IP: {external_ip}')

except Exception as e:
    logger.error(f'Error getting External IP: {e.__str__()}')
    sys.exit()

domain_update_error = False

if external_ip != last_recorded_ip:
    logger.debug(f'Creating new AsyncCloudflare API client')
    client = AsyncCloudflare(api_token=CLOUDFLARE_API_TOKEN)
    # TODO: Catch error if no network
    # TODO: Catch rate limit error

    async def update_a_record(domain, new_ip):
        try:
            # Get zone ID for domain from Cloudflare
            logger.debug(f'Getting Cloudflare zone records for {domain}')
            zones = [zone async for zone in client.zones.list(name=domain)]
            if not zones:
                logger.debug(f'Cloudflare zone not found for {domain}')
                return
            zone_id = zones[0].id
            logger.debug(f'Zone ID found for {domain}: {zone_id}')

            logger.debug(f'Getting DNS \'A\' record list for domain: {RECORD_NAME}.{domain} and zone ID: {zone_id}')
            records = [record async for record in client.dns.records.list(zone_id=zone_id,
                                                                          type="A",
                                                                          name=f"{RECORD_NAME}.{domain}"
                                                                          )]
            if not records:
                logger.info(f'No DNS \'A\' records found for domain: {RECORD_NAME}.{domain} and zone ID: {zone_id}')
                return

            for record in records:
                record_id = record.id

                logger.debug(f'Updating IP Address for domain: {RECORD_NAME}.{domain} and DNS \'A\' record ID: {record_id}')
                await client.dns.records.update(
                    zone_id=zone_id,
                    name=RECORD_NAME,
                    dns_record_id=record_id,
                    type="A",
                    content=new_ip
                )
                logger.info(f'DNS \'A\' record updated for domain: {RECORD_NAME}.{domain} to {external_ip}')

        except Exception as e:
            logger.error(f'Error updating DNS \'A\' record for domain: {RECORD_NAME}.{domain} and DNS \'A\' record ID: {record_id}')
            logger.error(f'Error: {e}')
            global domain_update_error
            domain_update_error = True

        # except Exception as e:
        #     logger.error(f'Error Trying to Update DNS Record: {e.__str__()}')
        #     sys.exit()

    # Collect all the tasks based on the number of domains in .ini
    async def main():
        logger.debug(f'Creating list of async tasks')
        for DOMAIN in DOMAINS_LIST:
            logger.debug(f'Adding async task to update domain: {RECORD_NAME}.{DOMAIN[1]} with IP Address: {external_ip}')
        tasks = [
            update_a_record(DOMAIN[1], external_ip)
            for DOMAIN in DOMAINS_LIST
        ]

        logger.debug(f'Running async tasks and awaiting their completion')
        await asyncio.gather(*tasks)

    # Run main event loop
    logger.debug(f'Starting asyncio run of main()')
    asyncio.run(main())

else:
    logger.info(f'DNS record is already: {external_ip}. No update needed')

#
# Debug code to check for asyncio tasks that haven't completed
#
# pending_tasks = asyncio.all_tasks()
# for task in pending_tasks:
#     logger.debug(f'Pending Task: {task.get_name()}')
#     task.cancel()
#     logger.debug(f'Pending Task Killed: {task.get_name()}')

# Update Config File .ini with new external IP address
if external_ip != last_recorded_ip and domain_update_error == False:
    if 'IP_ADDRESSES' not in config:
        config.add_section('IP_ADDRESSES')
        logger.info(f'Adding IP_ADDRESSES section to config file')
    config['IP_ADDRESSES']['Last_Recorded_IP'] = external_ip

    with open(CONFIG_PATH, 'w', encoding='utf-8') as configfile:
        # noinspection PyTypeChecker
        config.write(configfile)
    logger.info(f'Updated config file with new IP: {external_ip} - {CONFIG_PATH}')

logger.info("Script completed in %.2f seconds", (time.time() - start_time))