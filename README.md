shareabotus-textizen-adaptor
============================

Integrate a Textizen poll with a Shareabouts dataset

To load in responses manually:

1. Download a CSV snapshot of the Shareabouts API survey responses
2. Pick out the `medallion_number` and `private_participant_phone` fields
3. Copy them into the *manually_load_...* Python file
4. Make a list of tuples out of them in the `seen_responses` set.
5. Get a poll from the Textizen API

        curl -X POST "https://textizen.com/api/users/sign_in?email=<email>&password=<password>"
        curl "https://textizen.com/api/polls/440?auth_token=<auth_token>" > poll_info.json

6. Run the *manually_load_...* script