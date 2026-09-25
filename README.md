# Text-to-Image Generation Application Using Cloudflare Workers AI

## Preparation for Running the App
1. Create the holy `Python Virtual Environment` using the command below.

```bash
python -m venv venv
```

or 

```bash
python3 -m venv venv
```

2. Activate the virtual environment.

```bash
source venv/bin/activate
```

or

```powershell
.\venv\Scripts\Activate.ps1
```

3. Install the required Python packages using `requirements.txt` file.

```bash
pip install -r requirements.txt
```

## Deployment
1. In `Domains > Hosting & DNS > Apache & nginx > nginx settings`, disable the Proxy mode.

2. In Additional nginx directives, enter the following:

```text
passenger_enabled on;
passenger_app_type wsgi;
passenger_startup_file wsgi.py;
passenger_app_root /var/www/vhosts/example.com/httpdocs;
passenger_python /var/www/vhosts/example.com/httpdocs/venv/bin/python;
```

2. Here is the content of `wsgi.py` file for ngix and Phusion Passenger:

```python
import sys
import os

# Set the project root directory
project_home = os.path.dirname(__file__)
sys.path.insert(0, project_home)

# Set Python interpreter to your venv
INTERP = os.path.join(project_home, "venv", "bin", "python3")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Import the app factory and create the application instance
from app import create_app

application = create_app()
```

3. Create the .env file and insert the following keys:

```text
CF_ACCOUNT_ID=
CF_API_TOKEN=
APP_USERNAME=
APP_PASSWORD=
SECRET_KEY=
FLASK_ENV=development
```

Here is how to create SECRET_KEY using command line. First activate the virtual environment and run the following command:
`python -c "import secrets; print(secrets.token_hex(32))"`