"""
    This labda created for serving SeamenExchange Lex bot
    """

import json
import datetime
import time
import os
import dateutil.parser
import logging
import requests
import re


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

"""
    Helper functions from Rent Car example
    """
def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
    }
}


def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
    }
}


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
    }
    }

return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
    }
}

"""
    This function assembles a question Regex pattern
    """
def q_pattern(*tokens):
    reply = r''
    for t in tokens:
        if t == r'{slot}':
            reply+=r'([\w\s]+)\s*'
        else:
            reply+=r'(?:\b'+t+r'\b)\s*'
    return reply.lower()


"""
    List of recognised question patterns
    """
question_patterns = [
                     q_pattern('What', 'is', 'the','{slot}', 'meaning'),
                     q_pattern('What','is','{slot}'),
                     q_pattern('What','are','{slot}'),
                     q_pattern('Who', 'is', 'the','{slot}', 'meaning'),
                     q_pattern('Who','is','{slot}'),
                     q_pattern('Who','are','{slot}'),
                     q_pattern('Tell','me','about','{slot}'),
                     q_pattern('Tell','about','{slot}'),
                     q_pattern('I', 'want', 'to', 'know', 'about','{slot}','meaning'),
                     q_pattern('I', 'want', 'to', 'know', 'about','{slot}'),
                     q_pattern('I', 'want', '{slot}', 'description'),
                     q_pattern('I', 'want', '{slot}', 'meaning'),
                     q_pattern('I', 'need', '{slot}', 'description'),
                     q_pattern('Describe','me','{slot}'),
                     q_pattern('Describe','{slot}'),
                     q_pattern('What', 'does', '{slot}', 'mean'),
                     q_pattern('{slot}','description'),
                     q_pattern('Explain','me','{slot}','meaning'),
                     q_pattern('Explain','me','{slot}'),
                     q_pattern('Explain','{slot}'),
                     q_pattern('{slot}','meaning'),
                     ]

"""
    Returns parsed slot from raw user input
    """
def get_slot(request):
    import re
    
    for pattern in question_patterns:
        m = re.match(pattern,request.lower().strip())
        if m:
            return m.group(1)
            break;
    return ""

"""
    Main answering function
    """
def answer_question(intent_request):
    slots = intent_request['currentIntent']['slots']
    confirmation_status = intent_request['currentIntent']['confirmationStatus']
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    if slots.has_key('term'):
        #if we there is a Slot parsed by Lex let's use it
        term = slots['term']
        if term is None:
            #Slot could be None and we should try to parse it from raw input
            term = get_slot(intent_request['inputTranscript'])
    else:
        #There is definitely no Slot parsed by Lex and we should try to parse it from raw input
        term = get_slot(intent_request['inputTranscript'])
    
    terms = []
    if not term is None and len(term) > 0:
        #We got term - a parsed Slot and request a Knowledge base to match it
        r = requests.get("https://www.seamenexchange.com/terms/search?q="+term)
        terms = json.loads(r.content.replace('\n',' '))

    reply = "I don't know"
    if len(terms) > 0:
        #Knowledge base tagged suggested terms with their similarity to requested term. We need most relevant.
        terms = sorted(terms, key=lambda t:t['similar'], reverse=True)
        if(float(terms[0]["similar"]) < 1):
            #No exact match. Bot gives user some suggestions
            reply = "I can tell you about: "
            for t in terms[:3]:
                reply += t['title'] + ", "
            if reply.endswith(", "):
                reply = reply[:-2]
        else:
            #Exact match found. Let's prettify it to be a more human-like answer.
            body = terms[0]['body'][0].lower() + terms[0]['body'][1:]
            if body.startswith("is "):
                verb = " "
            elif body.startswith("the ") or body.startswith("a ") or body.startswith("an "):
                verb = " is "
            elif body.startswith("this "):
                verb = " "
                body = body[4:]
            else:
                verb = " : "
            reply = terms[0]['title']  +  verb  + body

    return close(
                 session_attributes,
                 'Fulfilled',
                 {
                 'contentType': 'PlainText',
                 'content': reply
                 }
                 )

"""
    Dispatcher from Rent Car example
    """
def dispatch(intent_request):
    
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    
    intent_name = intent_request['currentIntent']['name']
    #There is only one handler for all intents
    return answer_question(intent_request)

# --- Main handler --- from Rent Car example

def lambda_handler(event, context):
    """
        Route the incoming request based on intent.
        The JSON body of the request is provided in the event slot.
        """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    
    return dispatch(event)

