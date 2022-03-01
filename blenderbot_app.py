from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, Conversation, ConversationalPipeline
from flask import Flask
from flask import request
from pymessenger.bot import Bot

tokenizer = AutoTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
model = AutoModelForSeq2SeqLM.from_pretrained("facebook/blenderbot-400M-distill")
nlp = ConversationalPipeline(model=model, tokenizer=tokenizer)

app = Flask(__name__)
ACCESS_TOKEN = '*******'
VERIFY_TOKEN = 'TOKEN'
bot = Bot(ACCESS_TOKEN)

conversation = Conversation()

@app.route("/webhook", methods=['GET', 'POST'])
def receive_message():
    print('ICI', request)
    if request.method == 'GET':
        """Before allowing people to message your bot, Facebook has implemented a verify token
        that confirms all requests that your bot receives came from Facebook.""" 
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    #if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
        # get whatever message a user sent the bot
       output = request.get_json()
       for event in output['entry']:
          messaging = event['messaging']
          for message in messaging:
            if message.get('message'):
                #Facebook Messenger ID for user so we know where to send response back to
                recipient_id = message['sender']['id']
                text = message['message'].get('text')
                if text == 'exit':
                    reset()
                    send_message(recipient_id, 'See you later ;)')
                elif text:
                    response_sent_text = get_message(text)
                    resp_text = response_sent_text[-1]['text']
                    send_message(recipient_id, resp_text)
                #if user sends us a GIF, photo,video, or any other non-text item
                if message['message'].get('attachments'):
                    response_sent_nontext = get_message(text)
                    send_message(recipient_id, response_sent_nontext)
    return "Message Processed"

def get_message(text):
    return add_input(text)

#uses PyMessenger to send response to user
def send_message(recipient_id, response):
    #sends user the text message provided via input response parameter
    bot.send_text_message(recipient_id, response)
    return "success"

def add_input(text_message):
    # text = request.json['text']
    text = text_message
    conversation.add_user_input(text)
    result = nlp([conversation], do_sample=False , max_length=1000)
    messages = []
    for is_user, text in result.iter_texts():
        messages.append({
            'is_user': is_user,
            'text': text
        })
    # return {
    #     'uuid': result.uuid,
    #     'messages': messages
    # }
    return messages

def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error
    print(token_sent, VERIFY_TOKEN) 
    if token_sent == VERIFY_TOKEN:
        print("Token is ok !")
        #return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
        print(request.args.get("hub.challenge"))
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


# @app.route('/reset', methods = ['GET', 'POST'])
def reset():
    global conversation
    conversation = Conversation()
    return 'ok' 

# @app.route('/init_persona', methods = ['GET', 'POST'])
def init(text_message):
    #  text = request.json['text']
    text = text_message
    conversation.add_user_input('Hello')
    conversation.append_response(text)
    # Put the user's messages as "old message".
    conversation.mark_processed()
    return 'ok' 

if __name__ == "__main__":
    app.run()