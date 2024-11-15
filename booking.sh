git pull origin
rm -rf .venv
uv python pin 3.12.7
asdf local python 3.12.7
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
