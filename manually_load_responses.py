#!/usr/bin/env python

import json
import hashlib
from app import get_question_answers, find_survey_place, submit_survey
from django.conf import settings

# The config.json file should be the same file that is used to configure the
# Textizen adapter for automatic importing.
with open('config.json') as configfile:
    config = json.load(configfile)

# The poll_info.json file is the result of downloading the poll from the
# Textizen API.
with open('poll_info.json') as textizen_poll_info_file:
    textizen_poll = json.load(textizen_poll_info_file)

# The surveys.json file is the result of downloading the places from the
# Shareabouts API with include_submissions and include_private enabled.
with open('surveys.json') as shareabouts_surveys_file:
    shareabouts_surveys = json.load(shareabouts_surveys_file)

# Pairs of medallion # (string), phone number (string)
seen_responses = set([
    # ('21', '+12679705555'),
    # ...
])

# Update the seen_responses set with data from the Shareabouts API.
for place_data in shareabouts_surveys['features']:
    try: medallion_number = str(place_data['properties']['medallion_number'])
    except KeyError:
        print('Skipping place {url}, which has no medallion_number.'.format(**place_data['properties']))
        continue

    for survey_data in place_data['properties']['submission_sets']['surveys']:
        source = survey_data.get('source', 'shareabouts')
        try:
            user_token = survey_data['user_token']
        except KeyError:
            print('Oddly, survey {url} has no user_token.'.format(**survey_data))
            continue

        if source.lower() == 'textizen' or user_token.lower().startswith('textizen'):
            phone_number = str(survey_data['private_participant_phone'])
            print('Adding ("{}", "{}") to the seen responses.'.format(medallion_number, phone_number))
            seen_responses.add((medallion_number, phone_number))

# Upload the new Textizen responses to Shareabouts.
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
