#!/usr/bin/env python

import os
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
CONFIG_PATH = r'LocalConfig/CloudflareDynDNS.ini'
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
sh.setLevel(logging.INFO)
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

if sys.platform[0:5] == 'linux' and not sys.stdout.isatty():
    logger.removeHandler(sh)

#
# Import CloudflareDynDNS.ini
#
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

try:
    LAST_RECORDED_IP = config.items('LAST_RECORDED_IP')
    DOMAINS = config.items('DOMAINS')
    RECORD_TYPE = config['RECORD']['Record_Type']
    RECORD_NAME = config['RECORD']['Record_Name']
    CLOUDFLARE_API_TOKEN = config['CREDENTIALS']['Cloudflare_API_Token']

except KeyError:
    logger.error('Error loading ini: check ini exists and settings are correct')
    quit()

try:
    logger.debug('Getting Public IP')
    publicIP = get_public_ip()
    logger.info('Got Public IP: ' + publicIP)

except Exception as e:
    logger.error('Error Getting Public IP: ' + e.__str__())
    sys.exit()

if publicIP != LAST_RECORDED_IP:
    client = AsyncCloudflare(api_token=CLOUDFLARE_API_TOKEN)
    for DOMAIN in DOMAINS:
        try:
            async def update_a_record(domain, new_ip):
                logger.debug('Getting Cloudflare Records for ' + DOMAIN[1])
                zones = await client.zones.list(name=domain)
                if not zones:
                    logger.debug(f'Zone not found for {domain}')
                    return
                zone_id = zones[0]['id']

                records = await client.dns.records.list(zone_id=zone_id, type="A", name=domain)
                if not records:
                    logger.debug(f'No A records found for {domain}')
                    return

                for record in records:
                    record_id = record['id']
                    await client.dns.records.update(
                        zone_id=zone_id,
                        record_id=record_id,
                        type="A",
                        content=new_ip,
                    )
                    logger.debug(f'Updated A record for {domain} to {new_ip}')
                    logger.info('DNS Record Updated for ' + DOMAIN[1] + ':' + record["data"] + ' to ' + publicIP)
        except Exception as e:
            logger.debug(f'Error updating A record for {domain}: {e}')
            except Exception as e:
            logger.error('Error Trying to Update DNS Record' + e.__str__())
            sys.exit()
            except Exception as e:
                logger.error('Error Getting GoDaddy Records: ' + e.__str__())
else:
    logger.info('DNS Record Update not Needed for ' + DOMAIN[1] + ':' + publicIP)


async def main():
    tasks = [
        update_a_record(domain_info['name'], domain_info['new_ip'])
        for domain_info in domains_to_update
    ]

    await asyncio.gather(*tasks)

asyncio.run(main())


                # TODO: Update CloudflareDynDNS.ini with new external IP address


                # TODO: Set CloudflareDynDNS.ini with error so will try to update Cloudflare again on next run
logger.info("Code Executed in %s Seconds", (time.time() - start_time))