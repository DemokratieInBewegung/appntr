#!/usr/bin/env bash

# run this from within running docker container (e.g. after having done "docker-compose exec web /bin/bash")

EMAIL=$1
if [ -z "$EMAIL" ]; then
    echo "USAGE: $0 <destination mailadress>"
    echo "       invoke this command from within a running environment, for example from"
    echo "       within a docker container (e.g. after having entered the container via"
    echo "       'docker-compose exec web /bin/bash')."
    exit 1
fi

python manage.py shell -c "from django.conf import settings; from django.core.mail import EmailMessage; EmailMessage('Testmail', 'Nur eine Testmail. Bitte ignorieren', settings.DEFAULT_FROM_EMAIL, ['$EMAIL'], reply_to=(settings.REPLY_TO_EMAIL,));"
