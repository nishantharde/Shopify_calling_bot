# ngrok http --domain=kid-one-spaniel.ngrok-free.app 5000 

from flask import Flask, request, jsonify, url_for
from twilio.twiml.voice_response import VoiceResponse, Gather
import json
from parse_info import Parser
from data_extractor import Extractor

app = Flask(__name__)

with open('orders.json') as f:
    orders = json.load(f)

@app.route("/")
def hello():
    return "Hello User, you may send requests"

@app.route("/voice", methods=['POST'])
def voice():
    response = VoiceResponse()

    caller_number = request.form['From']
    print(f"Incoming call from: {caller_number}")

    gather = Gather(input='speech', action='/handle_speech', method='POST')
    gather.say("Thank you for calling XYZ Shopify, please tell me your order number.")
    response.append(gather)

    return str(response)

@app.route("/handle_speech", methods=['POST'])
def handle_speech():
    response = VoiceResponse()

    speech_result = request.form['SpeechResult']
    caller_number = request.form['From']

    result = Parser().parse("Thank you for calling XYZ Shopify, please tell me your order number.\n" + speech_result.strip())

    print(result)

    action_url = url_for('handle_dtmf', order_number=result, caller_number=caller_number)
    gather = Gather(input='dtmf', num_digits=1, action=action_url, method='POST')
    gather.say(f"Your order number is {result['spoken']}, if this order number is correct, then press 1 if not then press any other key to enter manually.")
    response.append(gather)

    return str(response)

@app.route("/handle_dtmf", methods=['POST'])
def handle_dtmf():
    response = VoiceResponse()
    digit = request.form['Digits']
    print(f"DTMF input was: {digit} {type(digit)}")

    order_number = request.args.get('order_number')
    caller_number = request.args.get('caller_number')

    if digit == '1':
        response.say('Please wait while we get your order status.')
        response.redirect(url_for('order_status', order_number=order_number['formatted'], caller_number=caller_number, _external=True))
    else:
        action_url = url_for('manual_response', caller_number=caller_number, _external=True)
        gather = Gather(input='dtmf', num_digits=20, action=action_url, method='POST')
        gather.say(f"Please enter your order number manually ending with the hashtag symbol.")
        response.append(gather)

    return str(response)

@app.route("/manual_response", methods=['POST', 'GET'])
def manual_response():
    response = VoiceResponse()
    order_number = {'formatted': request.args.get('Digits') if request.method == 'GET' else request.form['Digits'], 'spoken': None}
    caller_number = request.args.get('caller_number')

    print(order_number)

    response.say('Please wait while we get your order status.')
    response.redirect(url_for('order_status', order_number=order_number['formatted'], caller_number=caller_number, _external=True))

    return str(response)


@app.route("/order_status", methods=['GET'])
def order_status():
    response = VoiceResponse()

    order_number = request.args.get('order_number')
    print(order_number)
    caller_number = request.args.get('caller_number')

    extractor = Extractor(phone_number=caller_number, order_number=order_number)

    print(int(order_number), caller_number)

    order_status = extractor.extractData()

    if order_status:
        response.say(order_status)
    else:
        response.say("Sorry, I couldn't find your order. Please try again.")

    response.hangup()
    return str(response)


if __name__ == "__main__":
    app.run(debug=True)