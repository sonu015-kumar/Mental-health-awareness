from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["bdi_result"]
collection = db["users"]

# BDI quiz questions and options
bdi_questions = [
    {"question": "1. Sadness", "options": ["I do not feel sad.", "I feel sad much of the time.", "I am sad all the time.", "I am so sad I can't stand it."]},
    {"question": "2. Pessimism", "options": ["I am not discouraged about my future.", "I feel more discouraged than I used to.", "I do not expect things to work out for me.", "My future is hopeless."]},
    {"question": "3. Past Failure", "options": ["I do not feel like a failure.", "I have failed more than I should have.", "As I look back, I see a lot of failures.", "I feel I am a complete failure."]},
    {"question": "4. Loss of Pleasure", "options": ["I get as much pleasure as I ever did from things.", "I do not get as much pleasure as I used to.", "I get very little pleasure from the things I used to enjoy.", "I cannot get any pleasure from anything."]},
    {"question": "5. Guilty Feelings", "options": ["I do not feel particularly guilty.", "I feel guilty a good part of the time.", "I feel guilty all of the time.", "I feel guilty most of the time."]},
    {"question": "6. Punishment Feelings", "options": ["I do not feel I am being punished.", "I feel I may be punished.", "I expect to be punished.", "I feel I am being punished."]},
    {"question": "7. Self-Dislike", "options": ["I feel good about myself.", "I do not like myself.", "I hate myself.", "I feel I am a worthless person."]},
    {"question": "8. Self-Criticalness", "options": ["I do not criticize or blame myself more than usual.", "I am more critical of myself than I used to be.", "I criticize myself for all of my faults.", "I blame myself for everything bad that happens."]},
    {"question": "9. Suicidal Thoughts or Wishes", "options": ["I do not have any thoughts of killing myself.", "I have thoughts of killing myself, but I would not carry them out.", "I would like to kill myself.", "I would kill myself if I had the chance."]},
    {"question": "10. Crying", "options": ["I do not cry anymore than I used to.", "I cry more than I used to.", "I cry all the time now.", "I used to be able to cry, but now I can't."]},
    {"question": "11. Agitation", "options": ["I am no more restless or agitated than usual.", "I feel more restless or agitated than usual.", "I am so restless or agitated that I can't sit still.", "I am so restless or agitated that I move around a lot."]},
    {"question": "12. Loss of Interest", "options": ["I am not more irritable than usual.", "I am more irritable than usual.", "I am irritated all the time.", "I am angry at everything."]},
    {"question": "13. Indecisiveness", "options": ["I am not more indecisive than usual.", "I have more difficulty making decisions than usual.", "I can't make decisions at all.", "I feel completely incapable of making decisions."]},
    {"question": "14. Worthlessness", "options": ["I do not feel that I am worthless.", "I feel more worthless than I used to.", "I feel worthless.", "I feel as though I am totally worthless."]},
    {"question": "15. Loss of Energy", "options": ["I have as much energy as I ever did.", "I have less energy than I used to.", "I have very little energy.", "I have no energy at all."]},
    {"question": "16. Changes in Sleeping Pattern", "options": ["I sleep as well as I used to.", "I sleep more than usual.", "I sleep less than usual.", "I wake up much earlier than I used to and cannot get back to sleep."]},
    {"question": "17. Irritability", "options": ["I am not more irritable than usual.", "I am more irritable than usual.", "I am very irritable.", "I am so irritable that I am angry all the time."]},
    {"question": "18. Changes in Appetite", "options": ["I have not experienced any change in my appetite.", "I eat more than I used to.", "I eat less than I used to.", "I have no appetite at all."]},
    {"question": "19. Concentration Difficulty", "options": ["I have no trouble concentrating.", "I have trouble concentrating more than usual.", "I have to force myself to concentrate.", "I cannot concentrate at all."]},
    {"question": "20. Tiredness or Fatigue", "options": ["I am not more tired than usual.", "I am more tired than usual.", "I am too tired to do anything.", "I am so tired that I cannot get out of bed."]},
    {"question": "21. Loss of Interest in Sex", "options": ["I have not noticed any loss of interest in sex.", "I have less interest in sex than I used to.", "I have lost almost all interest in sex.", "I have no interest in sex."]}
]

response_mapping = {
    option: score for score, options in enumerate(zip(*[q['options'] for q in bdi_questions])) for option in options
}

def analyze_risk(responses):
    total_score = sum(response_mapping.get(r, 0) for r in responses)
    if total_score <= 13:
        risk = "Minimal Depression"
    elif total_score <= 19:
        risk = "Mild Depression"
    elif total_score <= 28:
        risk = "Moderate Depression"
    else:
        risk = "Severe Depression"
    return {"score": total_score, "risk_level": risk}

def generate_motivation_message(risk_level):
    return {
        "Minimal Depression": "You're doing great! Keep up the positive mindset!",
        "Mild Depression": "It's okay to feel this way. Take care of yourself and reach out for support.",
        "Moderate Depression": "You are not alone. Consider talking to someone who can help you through this.",
        "Severe Depression": "Please seek professional help. You're not alone, and support is available."
    }.get(risk_level, "Stay strong and don't hesitate to seek help.")

@app.route('/')
def home():
    return render_template('index.html', questions=bdi_questions)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        name = request.form.get("name")
        age = request.form.get("age")
        sex = request.form.get("sex")
        phone = request.form.get("phone")
        responses = [request.form.get(f"responses{i}") for i in range(21)]


        result = analyze_risk(responses)
        motivation = generate_motivation_message(result["risk_level"])

        user_id = collection.insert_one({
            "name": name,
            "age": age,
            "sex": sex,
            "phone": phone,
            "responses": responses,
            "score": result["score"],
            "risk_level": result["risk_level"],
            "motivation_message": motivation,
            "date": datetime.now()
        }).inserted_id

        return redirect(url_for('results', user_id=str(user_id)))

    return render_template('index.html', questions=bdi_questions)

@app.route('/results/<user_id>')
def results(user_id):
    user_data = collection.find_one({"_id": ObjectId(user_id)})
    if not user_data or 'responses' not in user_data:
        return "Invalid data", 400

    return render_template('index.html', page="results", analysis={
        "score": user_data["score"],
        "risk_level": user_data["risk_level"]
    }, motivation_message=user_data["motivation_message"])
  

# Chat support Q&A
chat_questions = [
        ("Have you been experiencing a persistently low mood for most of the day, almost every day, for at least two weeks?", "You're stronger than you feel right now. This is a season, not forever. Take small steps, reach out, and keep going. You are not alone."),
        ("Have you been feeling hopeless or helpless?", "It's okay to feel this way. Remember, even the darkest clouds can’t hide the sun forever. You are not alone in this, and brighter days are ahead."),
        ("Have you lost interest or pleasure in activities that you previously found enjoyable?", "If you're feeling this way, it's okay. Your spark isn't gone—it's just dimmed for now. Start small, be kind to yourself, and remember: even the darkest nights end with sunrise. You will find joy again."),
        ("Do you feel a significant decrease in energy or increased fatigue, making daily activities harder to complete?", "It’s okay to feel drained—your mind and body are asking for care. Rest when you need to, take small steps, and remember: even slow progress is still progress. You are stronger than you think."),
        ("Have you experienced a significant loss of confidence or self-esteem?", "If you're feeling excessive guilt or blaming yourself unfairly, please remember: You are human, and you deserve kindness—even from yourself. Mistakes don’t define you, and you don’t have to carry burdens alone. Be gentle with yourself, and if these feelings persist, reaching out for support can help lighten the load. You are worthy of peace and healing."),
        ("Have you had recurrent thoughts of death, suicide, or engaged in any suicidal behavior?","I'm really sorry you're feeling this way. You are not alone, and your life matters. Please reach out to someone you trust—a friend, family member, or professional. There is help available, and you deserve support. You don’t have to face this alone.If you're in immediate danger or need urgent help, please reach out to a crisis helpline or seek professional assistance. There is hope, and you are worth fighting for."),
        ("Do you find it difficult to think, concentrate, or make decisions?","If you're struggling to think, concentrate, or make decisions, be kind to yourself. Your mind is overwhelmed, not broken. Take small steps, prioritize rest, and give yourself grace. Clarity will come—you're stronger than this moment."),
        ("Have you noticed changes in your movement, such as restlessness or slowed activity?","If you've noticed restlessness or slowed movement, your body might be responding to stress or exhaustion. Listen to it, be patient with yourself, and take small steps toward balance. You’re not alone, and things can get better."),
        ("Are you experiencing any sleep disturbances, such as trouble falling asleep, staying asleep, or sleeping too much?","If you're struggling with sleep, your mind and body might be asking for extra care. Try to create a calming routine, be gentle with yourself, and remember—this won’t last forever. Rest will come, and you are not alone."),
        ("Have you had noticeable changes in appetite, such as eating significantly more or less than usual, leading to weight change?","If your appetite has changed, it’s okay—your body responds to stress in different ways. Be gentle with yourself, nourish your body when you can, and seek support if needed. You deserve care, and things can get better."),
        (" you experienced a persistently depressed mood for most of the day, nearly every day, for at least two weeks?","If you're asking this for yourself, and the answer is yes, please know that you're not alone. You deserve support, and help is available. Talking to a trusted friend, family member, or professional can make a difference. You are valued, and things can get better."),
    ]

# Chatbot-like route
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    selected_question = None
    answer = None
    if request.method == 'POST':
        question_index = int(request.form['question_index'])
        if 0 <= question_index < len(chat_questions):
            selected_question, answer = chat_questions[question_index]
    return render_template('chat.html', questions=chat_questions, selected_question=selected_question, answer=answer)

if __name__ == '__main__':
    app.run(debug=True)
