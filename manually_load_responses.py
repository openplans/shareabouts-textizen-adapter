#!/usr/bin/env python

import json
import hashlib
from app import get_question_answers, find_survey_place, submit_survey
from django.conf import settings

with open('config.json') as configfile:
    config = json.load(configfile)

with open('poll_info.json') as poll_info_file:
    textizen_poll = json.load(poll_info_file)

# Pairs of medallion # (string), phone number (string)
seen_responses = set([
    # ('21', '+12679705555'),
    # ...
])

count = 0
for textizen_session in textizen_poll['response_sequences']:
    textizen_responses = textizen_session['responses']
    phone_num = textizen_session['from']

    survey_data = {
        'source': 'textizen',
        'private_participant_phone': phone_num,
        'private_survey_phone': textizen_poll['phone'],
        'user_token': 'textizen:' + hashlib.md5((settings.SECRET_KEY + phone_num).encode()).hexdigest(),
        'created_datetime': textizen_session['last_response_created']
    }

    survey_data.update(get_question_answers(textizen_poll, textizen_responses, config))

    lookup_field = config['place_lookup']
    lookup_value = str(survey_data.get(lookup_field, ''))

    if (lookup_value, phone_num) in seen_responses:
        print('Skipping response for place %s from %s' % (lookup_value, phone_num))
        continue

    # Send the survey response to Shareabouts
    place = find_survey_place(survey_data, config)
    print('Saving a response for place %s from %s' % (lookup_value, phone_num))
    if place: submit_survey(place, survey_data, config)
    count += 1

print 'Saved %s responses' % count
