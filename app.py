import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, leave_room, emit
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['GEOAPIFY_API_KEY'] = os.getenv('GEOAPIFY_API_KEY')  # Load Geoapify API key
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Initialize SocketIO
socketio = SocketIO(app, manage_session=False)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

# Ride Model
class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(150), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    people = db.Column(db.Integer, nullable=False)
    stop = db.Column(db.String(150), nullable=True)
    stop_place_id = db.Column(db.String(100), nullable=True)

# Booking Model
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_model = db.Column(db.String(100), nullable=False)
    seat_capacity = db.Column(db.Integer, nullable=False)
    license_number = db.Column(db.String(50), nullable=False)
    departure_time = db.Column(db.String(50), nullable=False)
    people = db.Column(db.Integer, nullable=False)
    stop = db.Column(db.String(150), nullable=True)
    stop_place_id = db.Column(db.String(100), nullable=True)

# Participant Model
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(150), nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)
    people_joined = db.Column(db.Integer, nullable=False)
    stop = db.Column(db.String(150), nullable=True)
    stop_place_id = db.Column(db.String(100), nullable=True)

# Message Model for Chat
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(150), nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# Helper Functions
def parse_time(time_str):
    try:
        dt = datetime.strptime(time_str, '%Y-%m-%dT%H:%M')
        pdt_tz = timezone(timedelta(hours=-7))
        return dt.replace(tzinfo=pdt_tz).astimezone(timezone.utc)
    except ValueError as e:
        print(f"Error parsing time '{time_str}': {e}")
        return datetime(1900, 1, 1, tzinfo=timezone.utc)

def get_user_rides():
    if "user" not in session:
        return [], []
    user_participations = Participant.query.filter_by(user=session['user']).all()
    my_shared_rides = [Ride.query.get(p.ride_id) for p in user_participations if p.ride_id]
    my_booked_rides = [Booking.query.get(p.booking_id) for p in user_participations if p.booking_id]
    return my_shared_rides, my_booked_rides

# Custom Jinja2 Filters
@app.template_filter('todatetime')
def to_datetime_filter(value):
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M').replace(tzinfo=timezone.utc)
    except:
        return datetime.now(timezone.utc)

@app.template_filter('strftime')
def strftime_filter(dt, format_string):
    if not isinstance(dt, datetime):
        return dt
    return dt.strftime(format_string)

# SocketIO Events
@socketio.on('join')
def on_join(data):
    user = session.get('user')
    if not user:
        return
    room = data['room']
    ride_id = data.get('ride_id')
    booking_id = data.get('booking_id')
    
    # Validate participant
    participant = None
    if ride_id:
        participant = Participant.query.filter_by(user=user, ride_id=ride_id).first()
    elif booking_id:
        participant = Participant.query.filter_by(user=user, booking_id=booking_id).first()
    
    if not participant:
        emit('error', {'msg': 'You are not a participant in this ride.'})
        return
    
    join_room(room)
    emit('message', {'msg': f"{user} has joined the chat."}, room=room)

@socketio.on('leave')
def on_leave(data):
    user = session.get('user')
    if not user:
        return
    room = data['room']
    leave_room(room)
    emit('message', {'msg': f"{user} has left the chat."}, room=room)

@socketio.on('send_message')
def handle_message(data):
    user = session.get('user')
    if not user:
        return
    room = data['room']
    content = data['message']
    ride_id = data.get('ride_id')
    booking_id = data.get('booking_id')

    participant = None
    if ride_id:
        participant = Participant.query.filter_by(user=user, ride_id=ride_id).first()
    elif booking_id:
        participant = Participant.query.filter_by(user=user, booking_id=booking_id).first()
    
    if not participant:
        emit('error', {'msg': 'You are not a participant in this ride.'})
        return

    if not content:
        return

    message = Message(
        user=user,
        ride_id=ride_id if ride_id else None,
        booking_id=booking_id if booking_id else None,
        content=content
    )
    db.session.add(message)
    db.session.commit()

    emit('message', {
        'user': user,
        'content': content,
        'timestamp': message.timestamp.strftime('%b %d, %Y %I:%M %p'),
        'room': room
    }, room=room)


# Routes
@app.route('/')
def home():
    my_shared_rides, my_booked_rides = get_user_rides()
    return render_template('index.html', my_shared_rides=my_shared_rides, my_booked_rides=my_booked_rides)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for('register'))

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user'] = user.username
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


ride_messages = {}     
booking_messages = {}  

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()

    room = data.get('room')  # e.g. "ride-5" or "booking-3"
    content = data.get('content', '').strip()

    if not content or not room or 'user' not in session:
        return jsonify({'success': False, 'error': 'Missing required data'}), 400

    user = session['user']
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    message = {
        'user': user,
        'content': content,
        'timestamp': timestamp
    }

    # Store the message
    if room.startswith('ride-'):
        ride_id = int(room.split('-')[1])
        ride_messages.setdefault(ride_id, []).append(message)
    elif room.startswith('booking-'):
        booking_id = int(room.split('-')[1])
        booking_messages.setdefault(booking_id, []).append(message)
    else:
        return jsonify({'success': False, 'error': 'Invalid room'}), 400

    return jsonify({'success': True, 'message': message})



@app.route('/share')
def share_ride_page():
    if "user" not in session:
        flash("Please login to share a ride.", "warning")
        return redirect(url_for('login'))
    my_shared_rides, my_booked_rides = get_user_rides()
    return render_template('share.html', my_shared_rides=my_shared_rides, my_booked_rides=my_booked_rides)

@app.route('/share_ride', methods=['POST'])
def share_ride():
    if "user" not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('login'))

    name = request.form.get('name')
    destination = request.form.get('destination')
    time = request.form.get('time')
    people = request.form.get('people')
    stop = request.form.get('stop')
    stop_place_id = request.form.get('stop_place_id')

    if not stop:
        flash("Please provide a stop location.", "danger")
        return redirect(url_for('share_ride_page'))
    if not all([name, destination, time, people]):
        flash("All fields are required.", "danger")
        return redirect(url_for('share_ride_page'))

    try:
        people = int(people)
        if people < 1 or people > 7:
            flash("Number of people must be between 1 and 7.", "danger")
            return redirect(url_for('share_ride_page'))
    except ValueError:
        flash("Number of people must be a valid number.", "danger")
        return redirect(url_for('share_ride_page'))

    try:
        ride_time = parse_time(time)
        now = datetime.now(timezone.utc)
        if ride_time < now:
            flash("Cannot share a ride in the past.", "danger")
            return redirect(url_for('share_ride_page'))
    except ValueError:
        flash("Invalid time format.", "danger")
        return redirect(url_for('share_ride_page'))

    ride = Ride(
        name=name,
        destination=destination,
        time=time,
        people=people,
        stop=stop,
        stop_place_id=stop_place_id or None
    )
    db.session.add(ride)
    db.session.flush()
    p = Participant(
        user=session['user'],
        ride_id=ride.id,
        people_joined=people,
        stop=stop,
        stop_place_id=stop_place_id or None
    )
    db.session.add(p)
    db.session.commit()
    flash("Ride shared successfully!", "success")
    return redirect(url_for('all_rides'))

@app.route('/book')
def book_ride_page():
    if "user" not in session:
        flash("Please login to book a ride.", "warning")
        return redirect(url_for('login'))
    my_shared_rides, my_booked_rides = get_user_rides()
    return render_template('book.html', my_shared_rides=my_shared_rides, my_booked_rides=my_booked_rides)

@app.route('/book_ride', methods=['POST'])
def book_ride():
    if "user" not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('login'))

    vehicle_model = request.form.get('vehicle_model')
    seat_capacity = request.form.get('seat_capacity')
    license_number = request.form.get('license_number')
    departure_time = request.form.get('departure_time')
    people = request.form.get('people')
    stop = request.form.get('stop')
    stop_place_id = request.form.get('stop_place_id')

    if not stop:
        flash("Please provide a stop location.", "danger")
        return redirect(url_for('book_ride_page'))
    if not all([vehicle_model, seat_capacity, license_number, departure_time, people]):
        flash("All fields are required.", "danger")
        return redirect(url_for('book_ride_page'))

    try:
        seat_capacity = int(seat_capacity)
        people = int(people)
        if seat_capacity < 1 or people < 1 or people > seat_capacity:
            flash("Invalid seat capacity or number of people.", "danger")
            return redirect(url_for('book_ride_page'))
    except ValueError:
        flash("Seat capacity and people must be valid numbers.", "danger")
        return redirect(url_for('book_ride_page'))

    try:
        booking_time = parse_time(departure_time)
        now = datetime.now(timezone.utc)
        if booking_time < now:
            flash("Cannot book a ride in the past.", "danger")
            return redirect(url_for('book_ride_page'))
    except ValueError:
        flash("Invalid time format.", "danger")
        return redirect(url_for('book_ride_page'))

    booking = Booking(
        vehicle_model=vehicle_model,
        seat_capacity=seat_capacity,
        license_number=license_number,
        departure_time=departure_time,
        people=people,
        stop=stop,
        stop_place_id=stop_place_id or None
    )
    db.session.add(booking)
    db.session.flush()
    p = Participant(
        user=session['user'],
        booking_id=booking.id,
        people_joined=people,
        stop=stop,
        stop_place_id=stop_place_id or None
    )
    db.session.add(p)
    db.session.commit()
    flash("Ride booked successfully!", "success")
    return redirect(url_for('all_rides'))

@app.route('/rides')
def all_rides():
    if "user" not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('login'))

    now = datetime.now(timezone.utc)

    rides = []
    for ride in Ride.query.all():
        ride_time = parse_time(ride.time)
        if ride_time > now:
            rides.append(ride)

    bookings = []
    for booking in Booking.query.all():
        booking_time = parse_time(booking.departure_time)
        if booking_time > now:
            bookings.append(booking)

    my_shared_rides, my_booked_rides = get_user_rides()

    participants = {}
    ride_stops = {}
    booking_stops = {}
    ride_join_disabled = {}
    booking_join_disabled = {}
    ride_leave_disabled = {}
    booking_leave_disabled = {}
    ride_messages = {}
    booking_messages = {}

    user_participations = Participant.query.filter_by(user=session['user']).all()
    for p in user_participations:
        if p.ride_id:
            participants[(session['user'], 'ride', p.ride_id)] = p
        elif p.booking_id:
            participants[(session['user'], 'booking', p.booking_id)] = p

    all_participants = Participant.query.all()

    for ride in rides:
        ride_stops[ride.id] = [ride.stop] if ride.stop else []
        ride_join_disabled[ride.id] = ride.people >= 7
        ride_time = parse_time(ride.time)
        ride_leave_disabled[ride.id] = ride_time < now + timedelta(hours=1)
        ride_messages[ride.id] = [{
            'user': msg.user,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%b %d, %Y %I:%M %p')
        } for msg in Message.query.filter_by(ride_id=ride.id).order_by(Message.timestamp.asc()).all()]
        for p in all_participants:
            if p.ride_id == ride.id and p.stop:
                ride_stops[ride.id].append(p.stop)

    for booking in bookings:
        booking_stops[booking.id] = [booking.stop] if booking.stop else []
        booking_join_disabled[booking.id] = booking.people >= booking.seat_capacity
        booking_time = parse_time(booking.departure_time)
        booking_leave_disabled[booking.id] = booking_time < now + timedelta(hours=1)
        booking_messages[booking.id] = [{
            'user': msg.user,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%b %d, %Y %I:%M %p')
        } for msg in Message.query.filter_by(booking_id=booking.id).order_by(Message.timestamp.asc()).all()]
        for p in all_participants:
            if p.booking_id == booking.id and p.stop:
                booking_stops[booking.id].append(p.stop)

    return render_template('rides.html',
        rides=rides,
        bookings=bookings,
        participants=participants,
        my_shared_rides=my_shared_rides,
        my_booked_rides=my_booked_rides,
        ride_stops=ride_stops,
        booking_stops=booking_stops,
        ride_join_disabled=ride_join_disabled,
        booking_join_disabled=booking_join_disabled,
        ride_leave_disabled=ride_leave_disabled,
        booking_leave_disabled=booking_leave_disabled,
        ride_messages=ride_messages,
        booking_messages=booking_messages,
        datetime=datetime,
        timedelta=timedelta,
        timezone=timezone
    )

@app.route('/join_ride/<int:ride_id>', methods=['POST'])
def join_ride(ride_id):
    if "user" not in session:
        flash("You must be logged in.", "warning")
        return redirect(url_for('login'))

    ride = Ride.query.get_or_404(ride_id)
    additional_people = request.form.get('additional_people')
    stop = request.form.get('stop', '').strip()
    stop_place_id = request.form.get('stop_place_id')

    try:
        additional_people = int(additional_people)
        if additional_people < 1:
            flash("Number of people must be at least 1.", "danger")
            return redirect(url_for('all_rides'))
    except ValueError:
        flash("Invalid number of people.", "danger")
        return redirect(url_for('all_rides'))

    if not stop:
        flash("Please provide a stop location.", "danger")
        return redirect(url_for('all_rides'))

    if ride.people + additional_people > 7:
        flash("This shared ride cannot exceed 7 people.", "danger")
        return redirect(url_for('all_rides'))

    ride.people += additional_people
    p = Participant(
        user=session['user'],
        ride_id=ride_id,
        people_joined=additional_people,
        stop=stop,
        stop_place_id=stop_place_id or None
    )
    db.session.add(p)
    db.session.commit()
    flash("Successfully joined shared ride!", "success")
    return redirect(url_for('all_rides'))

@app.route('/join_booking/<int:booking_id>', methods=['POST'])
def join_booking(booking_id):
    if "user" not in session:
        flash("You must be logged in.", "warning")
        return redirect(url_for('login'))

    booking = Booking.query.get_or_404(booking_id)
    additional_people = request.form.get('additional_people')
    stop = request.form.get('stop', '').strip()
    stop_place_id = request.form.get('stop_place_id')

    try:
        additional_people = int(additional_people)
        if additional_people < 1:
            flash("Number of people must be at least 1.", "danger")
            return redirect(url_for('all_rides'))
    except ValueError:
        flash("Invalid number of people.", "danger")
        return redirect(url_for('all_rides'))

    if not stop:
        flash("Please provide a stop location.", "danger")
        return redirect(url_for('all_rides'))

    if booking.people + additional_people > booking.seat_capacity:
        flash("Not enough seats available in this booking.", "danger")
        return redirect(url_for('all_rides'))

    booking.people += additional_people
    p = Participant(
        user=session['user'],
        booking_id=booking_id,
        people_joined=additional_people,
        stop=stop,
        stop_place_id=stop_place_id or None
    )
    db.session.add(p)
    db.session.commit()
    flash("Successfully joined booked ride!", "success")
    return redirect(url_for('all_rides'))

@app.route('/leave_ride/<int:ride_id>', methods=['POST'])
def leave_ride(ride_id):
    if "user" not in session:
        flash("You must be logged in.", "warning")
        return redirect(url_for('login'))

    ride = Ride.query.get_or_404(ride_id)
    participation = Participant.query.filter_by(user=session['user'], ride_id=ride_id).first()

    if not participation:
        flash("You are not part of this ride.", "warning")
        return redirect(url_for('all_rides'))

    ride_time = parse_time(ride.time)
    now = datetime.now(timezone.utc)
    if ride_time < now + timedelta(hours=1):
        flash("Cannot leave ride within one hour of departure.", "danger")
        return redirect(url_for('all_rides'))

    ride.people -= participation.people_joined
    db.session.delete(participation)
    if ride.people <= 0:
        db.session.delete(ride)
    db.session.commit()
    flash("You have left the shared ride.", "info")
    return redirect(url_for('all_rides'))

@app.route('/leave_booking/<int:booking_id>', methods=['POST'])
def leave_booking(booking_id):
    if "user" not in session:
        flash("You must be logged in.", "warning")
        return redirect(url_for('login'))

    booking = Booking.query.get_or_404(booking_id)
    participation = Participant.query.filter_by(user=session['user'], booking_id=booking_id).first()

    if not participation:
        flash("You are not part of this booking.", "warning")
        return redirect(url_for('all_rides'))

    booking_time = parse_time(booking.departure_time)
    now = datetime.now(timezone.utc)
    if booking_time < now + timedelta(hours=1):
        flash("Cannot leave booking within one hour of departure.", "danger")
        return redirect(url_for('all_rides'))

    booking.people -= participation.people_joined
    if booking.people <= 0:
        db.session.delete(booking)
    db.session.commit()
    flash("You have left the booked ride.", "info")
    return redirect(url_for('all_rides'))

@app.route('/clear_rides')
def clear_rides():
    if "user" not in session:
        return "Unauthorized", 403
    
    Ride.query.delete()
    Booking.query.delete()
    Participant.query.delete()
    Message.query.delete()
    db.session.commit()
    
    flash("All rides, bookings, and messages cleared successfully!", "success")
    return redirect(url_for('all_rides'))

@app.route('/my_bookings')
def my_bookings():
    if "user" not in session:
        flash("Please log in to view your bookings.", "warning")
        return redirect(url_for('login'))

    my_shared_rides, my_booked_rides = get_user_rides()
    if not (my_shared_rides or my_booked_rides):
        flash("You haven't joined any rides yet.", "info")
        return redirect(url_for('all_rides'))

    now = datetime.now(timezone.utc)
    two_hours_ago = now - timedelta(hours=2)

    current_shared = [ride for ride in my_shared_rides if ride and parse_time(ride.time) > two_hours_ago]
    previous_shared = [ride for ride in my_shared_rides if ride and parse_time(ride.time) <= two_hours_ago]
    valid_booked_rides = [booking for booking in my_booked_rides if booking and hasattr(booking, 'departure_time')]
    current_booked = [booking for booking in valid_booked_rides if parse_time(booking.departure_time) > two_hours_ago]
    previous_booked = [booking for booking in valid_booked_rides if parse_time(booking.departure_time) <= two_hours_ago]

    participants = {}
    ride_stops = {}
    booking_stops = {}
    ride_leave_disabled = {}
    booking_leave_disabled = {}
    ride_messages = {}
    booking_messages = {}
    all_participants = Participant.query.all()

    for p in all_participants:
        if p.ride_id:
            participants[(p.user, 'ride', p.ride_id)] = p
            if p.stop:
                ride_stops.setdefault(p.ride_id, []).append(p.stop)
        elif p.booking_id:
            participants[(p.user, 'booking', p.booking_id)] = p
            if p.stop:
                booking_stops.setdefault(p.booking_id, []).append(p.stop)

    for ride in my_shared_rides:
        if ride:
            if ride.stop and ride.id not in ride_stops:
                ride_stops[ride.id] = [ride.stop]
            elif ride.stop:
                ride_stops[ride.id].insert(0, ride.stop)
            ride_time = parse_time(ride.time)
            ride_leave_disabled[ride.id] = ride_time < now + timedelta(hours=1)
            ride_messages[ride.id] = [{
                'user': msg.user,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime('%b %d, %Y %I:%M %p')
            } for msg in Message.query.filter_by(ride_id=ride.id).order_by(Message.timestamp.asc()).all()]

    for booking in valid_booked_rides:
        if booking.stop and booking.id not in booking_stops:
            booking_stops[booking.id] = [booking.stop]
        elif booking.stop:
            booking_stops[booking.id].insert(0, booking.stop)
        booking_time = parse_time(booking.departure_time)
        booking_leave_disabled[booking.id] = booking_time < now + timedelta(hours=1)
        booking_messages[booking.id] = [{
            'user': msg.user,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%b %d, %Y %I:%M %p')
        } for msg in Message.query.filter_by(booking_id=booking.id).order_by(Message.timestamp.asc()).all()]

    return render_template('my_bookings.html',
        current_shared=current_shared,
        previous_shared=previous_shared,
        current_booked=current_booked,
        previous_booked=previous_booked,
        participants=participants,
        ride_stops=ride_stops,
        booking_stops=booking_stops,
        ride_leave_disabled=ride_leave_disabled,
        booking_leave_disabled=booking_leave_disabled,
        ride_messages=ride_messages,
        booking_messages=booking_messages,
        datetime=datetime,
        timedelta=timedelta,
        timezone=timezone
    )

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)