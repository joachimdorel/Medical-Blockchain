import datetime
import json

import requests
from flask import render_template, redirect, request, flash, url_for
from app import app, db
from app.forms import LoginForm, RegistrationForm, MedicineForm, BatchForm
from flask_login import current_user, login_user, login_required, logout_user
from app.models import Actor, Medicine, Adress, Batch

from sqlalchemy.exc import IntegrityError

# The node with which our application interacts, there can be multiple
# such nodes as well.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000/"

transactions = []
errors =[]
batch_id = None

def fetch_transactions():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        chain_content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for transaction in block["transactions"]:
                transaction["index"] = block["index"]
                transaction["hash"] = block["previous_hash"]
                chain_content.append(transaction)

        global transactions
        transactions = sorted(chain_content, key=lambda k: k['timestamp'], reverse=True)

def fetch_transactions_without_double():
    """
    Function to fetch the chain from a blockchain node, parse the data,
    check that each transactions only appear once and store it locally.
    """
    get_chain_address = "{}chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        chain_content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for transaction in block["transactions"]:
                transaction["index"] = block["index"]
                transaction["hash"] = block["previous_hash"]
                chain_content.append(transaction)

        chain_content_cp = []
        for transaction in chain_content:
            transaction_confirmed_or_rejected = False
            for t in chain_content:
                if t["batch_id"] == transaction["batch_id"] and t["sender_id"] == transaction["sender_id"] and t["recipient_id"] == transaction["recipient_id"] and t["timestamp"] != transaction["timestamp"]:
                    transaction_confirmed_or_rejected = True
            if transaction_confirmed_or_rejected is False or transaction["status"] != "waiting" :
                chain_content_cp.append(transaction)

        global transactions
        transactions = sorted(chain_content_cp, key=lambda k: k['timestamp'], reverse=True)

def fetch_current_actor_transactions():
    get_chain_address = "{}chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        transactions_actor=[]
        data_transactions=[]
        chain = json.loads(response.content)
        for element in chain["chain"]:
            for transaction_elem in element["transactions"]:
                data_transactions.append(transaction_elem)

        current_transactions = sorted(data_transactions, key=lambda k: k['timestamp'], reverse=True)

        batch_with_owner = []

        for t in current_transactions:
            batch_have_owner = False
            for b in batch_with_owner:
                if b['batch_id'] == t['batch_id']:
                    batch_have_owner = True

            if not batch_have_owner:
                if t['status'] == "accepted" or t['status'] == "waiting":
                    if t['recipient_id'] == current_user.id:
                        transactions_actor.append(t)
                if t['status'] == "refused":
                    if t['sender_id'] == current_user.id:
                        transactions_actor.append(t)
                batch_with_owner.append(t)

        global transactions
        transactions = sorted(transactions_actor, key=lambda k: k['timestamp'], reverse=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        actor = Actor.query.filter_by(actor_name=form.actor_name.data).first()
        if actor is None or not actor.check_password(form.password.data):
            flash('Invalid actor name or password')
            return redirect(url_for('login'))

        login_user(actor, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        actor = Actor(actor_name=form.actor_name.data, email=form.email.data, phone=form.phone.data, manufacturer=form.manufacturer.data)
        actor.set_password(form.password.data)
        db.session.add(actor)
        db.session.flush() # to get the id of the actor just added

        adress = Adress(street=form.street.data, city=form.city.data, state=form.state.data, zip_code=form.zip_code.data, country=form.country.data, id=actor.id)
        db.session.add(adress)
        db.session.commit()
        flash('Congratulations, you are now registered!')

        login_user(actor, remember=True)

        return redirect(url_for('index'))
    return render_template('register.html', title='Register', form=form)

@app.route('/')
def index():
    fetch_transactions()
    return render_template('index.html',
                           title='Medical Blockchain',
                           transactions=transactions,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string,
                           errors=errors)

@app.route('/medicine')
def medicine():
    """
    List the data of a specific medicine
    """
    fetch_transactions()
    global transactions
    global med_id

    medicine_transaction = []
    owner = None

    flash("Does not work yet")
    for transaction in transactions:
        pass
        '''
        if transaction['batch_id'] == int(batch_id):
            if owner == None and transaction["status"] == "accepted":
                owner=transaction["recipient_id"]
            medicine_transaction.append(transaction)
        '''

    data = {}
    data["owner"] = owner
    return render_template('medicine.html',
                           title='Data of a particular medicine',
                           transactions=medicine_transaction,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string,
                           batch_id=batch_id,
                           data=data,
                           errors=errors)

@app.route('/actor/<actor_name>')
@login_required
def actor(actor_name):
    actor = Actor.query.filter_by(actor_name=actor_name).first_or_404()
    adress = Adress.query.filter_by(id=actor.id).first()
    return render_template('actor.html', title=actor.actor_name, actor=actor, adress=adress)


@app.route('/user_medicine')
@login_required
def user_medicine():
    """
    List all the medicine of a specific user (his stock)
    """
    fetch_transactions_without_double()

    medicines = Medicine.query.filter_by(manufacturer_id=current_user.id).all()

    #blockchain
    user_id = current_user.id
    transactions_user = []
    for transaction in transactions:
        medicine_send_forward = False
        if transaction["recipient_id"] == user_id and transaction["status"] == "accepted":
            for t in transactions:
                if t["sender_id"] == user_id and transaction["batch_id"] == t["batch_id"] and t["status"] == "accepted" and t["sender_id"] != t["recipient_id"]:
                    medicine_send_forward = True
            if medicine_send_forward is False:
                transactions_user.append(transaction)

    return render_template('user_medicine.html',
                           title='Data of an user stock',
                           transactions=transactions_user,
                           medicines=medicines,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string,
                           user_id=user_id,
                           errors=errors)

@app.route('/request_mine', methods=['GET'])
@login_required
def request_mine():
    mine_address = "{}mine".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(mine_address)

    return redirect(url_for('index'))

def mine_blockchain():
    mine_address = "{}mine".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(mine_address)

@app.route('/fetch_transactions_for_id', methods=['POST'])
@login_required
def fetch_transactions_for_id():
    """
    Endpoint to get all the transaction for a given ID
    """
    user_id = current_user.id

    return redirect(url_for('user_transactions'))

@app.route('/fetch_medicine_for_med_id', methods=['POST'])
def fetch_medicine_for_med_id():
    """
    Endpoint to get all the medicine for a given med_id
    """
    med = request.form["med_id"]
    global med_id
    med_id = med

    return redirect(url_for('medicine'))

@app.route('/fetch_medicine_for_user_id', methods=['POST'])
@login_required
def fetch_medicine_for_user_id():
    """
    Endpoint to get all the medicine for a given user_id
    """
    user_id = current_user.id

    return redirect(url_for('user_medicine'))

@app.route('/new_medicine', methods=['GET', 'POST'])
@login_required
def new_medicine():
    """
    Endpoint to add a new medicine to the blockchain
    """
    form = MedicineForm()

    if form.validate_on_submit():
        try:
            medicine = Medicine(medicine_name=form.medicine_name.data, GTIN=form.gtin.data, manufacturer_id=current_user.id)
            db.session.add(medicine)
            db.session.flush()
            db.session.commit()

            # Blockchain part
            post_object = {
                'med_id': medicine.medicine_id,
                'sender_id': current_user.id
            }
            flash('New medicine added!')
            new_medicine_address = "{}register_medicine".format(CONNECTED_NODE_ADDRESS)

            requests.post(new_medicine_address,
                          json=post_object,
                          headers={'Content-type': 'application/json'})
        except IntegrityError:
            flash('This medicine already exist.')
        return redirect(url_for('new_medicine'))
    return render_template('new_medicine.html', title='New Medicine', form=form)

@app.route('/new_batch', methods=['POST'])
@login_required
def new_batch():
    if request.method == 'POST':
        if request.form['exp_date']=='' or request.form['quantity']=='':
            flash('Missing data')
        else:
            batch=Batch(exp_date=request.form['exp_date'], medicine_id=request.form['medicine_id'], quantity=request.form['quantity'])
            db.session.add(batch)
            db.session.flush()
            db.session.commit()

            json_object = {
                'batch_id': int(batch.batch_id),
                'sender_id': int(current_user.id),
                'quantity': int(request.form['quantity'])
            }

            new_batch_adress="{}register_batch".format(CONNECTED_NODE_ADDRESS)
            requests.post(new_batch_adress,
                          json=json_object,
                          headers={'Content-type': 'application/json'})

            return redirect(url_for('user_medicine'))

    return redirect(url_for('user_medicine'))

@app.route('/send_batch', methods=['POST'])
@login_required
def send_batch():
    fetch_current_actor_transactions()
    if request.method == 'POST':
        if request.form['batch_id']=='' or request.form['recipient_id']=='':
            flash('Missing data')
        else:
            user_owner_batch = False

            for t in transactions:
                if int(request.form['batch_id']) == int(t['batch_id']):
                    user_owner_batch = True

            if user_owner_batch:
                json_object = {
                    'batch_id': int(request.form['batch_id']),
                    'sender_id': int(current_user.id),
                    'recipient_id': int(request.form['recipient_id']),
                    'quantity': int(Batch.query.filter_by(batch_id=request.form['batch_id']).first().quantity)
                }
                new_transaction_address = "{}new_transaction".format(CONNECTED_NODE_ADDRESS)
                response = requests.post(   new_transaction_address,
                                            json=json_object,
                                            headers={'Content-type': 'application/json'})

            else:
                flash('You are not the owner of the batch')
            return redirect(url_for('user_transactions'))


@app.route('/user_transactions')
@login_required
def user_transactions():
    fetch_current_actor_transactions()

    user_transactions = []
    for transaction in transactions:

        medicine = Medicine.query.filter_by(medicine_id=Batch.query.filter_by(batch_id=transaction['batch_id']).first().medicine_id).first()
        transaction.update( {'medicine_name': medicine.medicine_name, 'medicine_id': medicine.medicine_id} )

        user_transactions.append(transaction)

    return render_template('user_transactions.html',
                           title='List of yours transactions',
                           transactions=user_transactions,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string,
                           user_id=current_user.id,
                           errors=errors)

@app.route('/submit_accept_transaction', methods=['POST'])
@login_required
def submit_accept_transaction():
    """
    Endpoint to the confirmation of a transaction in the blockchain
    """
    if request.method == 'POST':
        json_object = {
            'batch_id': int(request.form['batch_id']),
            'sender_id': int(request.form['sender_id']),
            'recipient_id': int(current_user.id),
            'quantity': int(request.form['quantity']),
            'status': request.form['statusTransaction']
        }


        submit_accept_transaction = "{}response_transaction".format(CONNECTED_NODE_ADDRESS)

        requests.post(submit_accept_transaction,
                      json=json_object,
                      headers={'Content-type': 'application/json'})

        mine_blockchain()

        return redirect(url_for('user_transactions'))


def timestamp_to_string(epoch_time):
    """
    Convert the timestamp to a readable string
    """
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M:%S - %d/%m/%Y')
