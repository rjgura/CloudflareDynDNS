# CloudflareDynDNS

This script is modified from [GoDaddyDNS](https://github.com/rjgura/GoDaddyDynDNS) to keep Cloudflare's DNS records updated with your current external IP address.  This creates a Dynamic DNS solution for domain names that use Cloudflare as their authoritative nameservers.

## Getting Started

This script assumes that you already have a Cloudflare account and your domain(s) are added and active. 

### Prerequisites

   1. Cloudflare account
   2. Domain name added and active on Cloudflare
   3. Cloudflare API Token via Cloudflare Dashboard
   4. Python 3.12.6 64 bit
   5. [cloudflare-python](https://github.com/cloudflare/cloudflare-python)
   6. pif 0.8.2 module for Python


### Installing

1. Download and install [Python](https://www.python.org/downloads/)
2. Install cloudflare-python module for Python
3. Install the pif module for Python (pip install pif)
4. Copy CloudflareDynDNS.py to the system you will run from (only one system per network is needed)
5. Copy and modify the CloudflareDynDNS.ini
6. Edit CloudflareDynDNS.py to point to your CloudflareDynDNS.ini and select a location for the log file
7. Schedule a recurring job to run CloudflareDynDNS.py

## Built With

* [Python](https://www.python.org/) - Python is a programming language that lets you work quickly and integrate systems more effectively.

* [PyCharm](https://www.jetbrains.com/pycharm/) - The Python IDE for Professional Developers

* [cloudflareDynDNS](https://github.com/cloudflare/cloudflare-python) - Python library useful for updating DNS settings through the GoDaddy v1 API

* [pif](https://github.com/barseghyanartur/pif) - Public IP address checker 
