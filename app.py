from flask import Flask, redirect, session, request, render_template, url_for
import random
import uuid
import logging 
from datetime import timedelta

app = Flask(__name__)
app.config["SECRET_KEY"] = "test"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

logger = logging.getLogger('werkzeug') # grabs underlying WSGI logger
handler = logging.FileHandler('test.log') # creates handler for the log file
logger.addHandler(handler) # adds handler to the werkzeug WSGI logger

def generate_session():
    logging.info("New session requested. Generated session data")

    session_uuid = str(uuid.uuid4())
    random_number = random.randint(1, 100)
    
    logging.info("Session created, writing to disk.")
    with open("sessions.txt", "a") as file:
        file.write(f"{session_uuid},{random_number}\n")

    return session_uuid

def generate_number(session_uuid):
    logging.info("Existing session found, but no number is assigned. Generating number.")

    random_number = random.randint(1, 100)

    logging.info("Number created, writing to disk")
    with open("sessions.txt", "a") as file:
        file.write(f"{ session_uuid },{random_number}\n")

    return random_number

def get_number(session_uuid):
    random_number = 0
    logging.debug("Session query requested. Opening file.")
    try:
        with open("sessions.txt", "r") as file:
            sessions = file.readlines()
            logging.debug("Searching session file.")
            for session_line in sessions:
                if session_line.split(",")[0] == session_uuid:
                    random_number = int(session_line.split(",")[1])
                    break
    except FileNotFoundError:
        logging.error("Sessions file does not exist, creating file.")
        open("sessions.txt", "x").close()

    if random_number == 0:
        logging.warning("Session not found in file! { 'session_uuid': " + str(session_uuid) +  " }")
        return generate_number(session_uuid)

    return random_number

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/number-guesser/cpu/submit", methods=["GET", "POST"])
def cpu_submit_guess():
    if "session_uuid" in session:
        app.logger.info("User opened existing session: " + str(session["session_uuid"]))
        number = get_number(session["session_uuid"])
        if number == 0:
            redirect(url_for("cpu_generated_number_guesser"))
   
    if request.method == "POST":
        guessed_number = 0
        guessed_number_form_value = request.form.get("guessed_number")
        if guessed_number_form_value is not None:
            try:
                guessed_number = int(guessed_number_form_value)
            except ValueError:
                logging.error("Invalid Input Received for guessed_number.")
                guessed_number = 0
        else:
            return render_template("error.html")

        if guessed_number == number:
            session.pop("session_uuid", None)
            return redirect(url_for("cpu_generated_number_guesser", status="success"))
        elif guessed_number < number:
            return render_template("ng_cpu.html", cpu_response="Your guess is too low", win_status=False)
        elif guessed_number > number:
            return render_template("ng_cpu.html", cpu_response="Your guess is too high", win_status=False)
   

@app.route('/number-guesser/cpu', methods=["GET", "POST"])
def cpu_generated_number_guesser():
    win_status = request.args.get("status")
    if win_status == "success":
        return render_template("ng_cpu.html", cpu_response="Correct!", win_status=True)

    session.permanent = True
    if "session_uuid" in session:
        app.logger.info("User opened existing session: " + str(session["session_uuid"]))
        number = get_number(session["session_uuid"])
        if number == 0:
            number = generate_number(session["session_uuid"])
    else:
        app.logger.info("No session found, Generating session.")
        session_uuid = generate_session()
        session["session_uuid"] = session_uuid

    cpu_response = "Please guess a number and submit."
    return render_template("ng_cpu.html", cpu_response=cpu_response)

@app.route('/number-guesser/human')
def human_generated_number_guesser():
    return render_template('ng_human.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
