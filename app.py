#!/usr/bin/env python

import ujson as json
import os
import requests
import sys

from django.conf import settings
from django.conf.urls import patterns
from django.http import HttpResponse
from django.core.management import execute_from_command_line

# Project configuration
settings.configure(
    DEBUG=(os.environ.get('DEBUG', 'True').lower() not in ('false', 'off')),
    SECRET_KEY=os.environ.get('SECRET_KEY', 'random_secret_key'),
    ACCESS_TOKEN=os.environ.get('ACCESS_TOKEN'),

    ROOT_URLCONF=sys.modules[__name__],
    ALLOWED_HOSTS=['*'],
)

# Textizen POST hook
def hook(request):
    # Only capture poll.copleted events
    if request.POST.get('event', None) != 'poll.completed':
        return HttpResponse('', status=204)

    # Load the textizen mapping config
    with open('config.json') as configfile:
        config = json.load(configfile)

    # Load the data from the request body
    # NOTE: We may end up with a KeyError, but Sentry will catch it.
    textizen_responses = json.loads(request.POST['responses'])

    survey_data = {}
    survey_data.update(get_general_info(textizen_responses))
    survey_data.update(get_question_answers(textizen_responses, config))

    # Send the survey response to Shareabouts
    place = find_survey_place(survey_data, config)
    submit_survey(place, survey_data, config)

    return HttpResponse('Powered by Django')

def get_general_info(responses):
    r = responses[0]
    return {
        'private_participant_phone': r['from'],
        'participant_id': r['participant_id'],
        'private_survey_phone': r['to']
    }

def get_question_answers(responses, config):
    data = {}
    for response in responses:
        question_id = response['question_id']
        option_id = response['matching_option_id']

        # NOTE: These may raise a KeyError, but Sentry will catch it.
        attr = config['question_attrs'][question_id]
        if option_id:
            value = config['option_values'][option_id]
        else:
            value = response['response']

        data[attr] = value
    return data

def find_survey_place(survey_data, config):
    lookup_field = config['place_lookup']
    lookup_value = survey_data[lookup_field]
    # TODO: Config below
    response = requests.get('https://data.shareabouts.org/api/v2/motu/datasets/bikeshare/places?%s=%s' % (lookup_field, lookup_value))
    places = response.json()

    # If we have more than one place, we should panic
    assert(len(places['features']) == 1)

    return places['features'][0]

def submit_survey(place, survey_data, config):
    retries = 5

    while retries > 0:
        # TODO: Config below
        response = requests.post(
            place['properties']['url'] + '/surveys',
            data=json.dumps(survey_data),
            headers={
                'Content-type': 'application/json',
                'Authorization': 'Bearer ' + settings.ACCESS_TOKEN
            })

        if response.status_code == 201:
            return
        retries -= 1

    # Setting these values for access in stack trace
    status_code = response.status_code
    response_body = response.content
    raise Exception('Too many retries while trying to post survey')

urlpatterns = patterns('',
    (r'^$', hook),
)

# Project management commands
if __name__ == "__main__":
    execute_from_command_line(sys.argv)