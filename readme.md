🚗 ShareWay – Campus-Centric Ride-Sharing Web App
 
ShareWay is a Flask-based ride-sharing platform designed to connect students and working professionals for daily commutes and intercity travel, with a focus on campus communities. Whether you're heading to class, work, or a weekend getaway, ShareWay makes ride-sharing seamless, cost-effective, and eco-friendly. Users can create or join rides, communicate in real-time via chat, and manage bookings with an intuitive interface.
Developed as a collaborative project by a team of four, ShareWay leverages modern web technologies to deliver a robust and user-friendly experience. This README provides a detailed guide to understanding, setting up, and contributing to the project.

🌟 Features
ShareWay offers a rich set of features to streamline ride-sharing:

🔐 Secure User Authentication  

Register with a unique username and password.
Secure login with hashed passwords using Werkzeug.
Session management to keep users logged in during their session.


🗺️ Ride Creation & Search  

Create shared rides with details like destination, time, number of people, and stops.
Search for available rides or bookings, filtered to show only future rides.
Support for both shared rides (up to 7 people) and booked rides (vehicle-specific).


👥 Participant Management  

Join or leave rides/bookings, with validation to prevent overbooking.
View participants and their chosen stops for each ride or booking.
Automatic removal of rides/bookings when all participants leave.


💬 Real-Time Chat  

Integrated Flask-SocketIO for live chat within ride or booking rooms.
Only participants can join chat rooms, ensuring privacy.
Messages are stored in the database for persistence and displayed with timestamps.


📅 Date & Time Validations  

Prevents scheduling rides or bookings in the past.
Disables leaving rides/bookings within 1 hour of departure.
Separates current and past rides/bookings in the user’s booking history.


📍 Location Autocomplete  

Powered by the Geoapify API for seamless stop location input.
Stores Geoapify place IDs for precise location tracking.


🔔 Flash Notifications  

User-friendly alerts for actions like successful ride creation, errors, or login issues.
Categorized as success, danger, warning, or info for clear feedback.


🧹 Clear Rides Option  

Admin-like functionality to reset all rides, bookings, and messages (requires login).




🛠️ Tech Stack
ShareWay is built with a modern, lightweight tech stack optimized for performance and ease of development:



Component
Technology
Description



Backend
Flask, Flask-SocketIO
Python web framework for routing, API handling, and real-time communication.


Frontend
HTML, CSS, JavaScript, Bootstrap
Responsive UI with dynamic rendering and styling.


Database
SQLite, SQLAlchemy ORM
Lightweight relational database with ORM for easy data management.


APIs
Geoapify API
Location autocomplete for user-friendly stop selection.


Environment
Python 3.8+, Virtualenv
Isolated Python environment for dependency management.


Version Control
Git, GitHub
Source code management and collaboration.



📊 Database Schema
ShareWay uses SQLite with SQLAlchemy ORM to manage data. The database includes five main models:

User  

id: Integer, primary key
username: String(150), unique, required
password_hash: String(256), required (hashed with Werkzeug)


Ride  

id: Integer, primary key
name: String(100), required
destination: String(150), required
time: String(50), required (format: YYYY-MM-DDTHH:MM)
people: Integer, required (max 7)
stop: String(150), optional
stop_place_id: String(100), optional (Geoapify place ID)


Booking  

id: Integer, primary key
vehicle_model: String(100), required
seat_capacity: Integer, required
license_number: String(50), required
departure_time: String(50), required (format: YYYY-MM-DDTHH:MM)
people: Integer, required
stop: String(150), optional
stop_place_id: String(100), optional


Participant  

id: Integer, primary key
user: String(150), required
ride_id: Integer, foreign key to Ride, optional
booking_id: Integer, foreign key to Booking, optional
people_joined: Integer, required
stop: String(150), optional
stop_place_id: String(100), optional


Message  

id: Integer, primary key
user: String(150), required
ride_id: Integer, foreign key to Ride, optional
booking_id: Integer, foreign key to Booking, optional
content: Text, required
timestamp: DateTime, default to current UTC time




👨‍💻 Team Members
ShareWay was developed by a dedicated team of four students under expert guidance:



Name
ID
Role



Peeyush Bhandari
E23CSEU1835
Backend Developer


Manthan Sharma
E23CSEU1831
Backend Developer


Piyush Negi
E23CSEU1840
Database Designer


Ekarth Kumar Shukla
E23CSEU1851
Frontend Developer


Project Mentor: Garima Jaiswal, Assistant Professor

🚀 Getting Started
Follow these steps to run ShareWay locally on your machine.
Prerequisites

Python 3.8+: Install from python.org.
Git: Install from git-scm.com.
Geoapify API Key: Sign up at Geoapify to get an API key.
VS Code (optional): For development and debugging.

Installation

Clone the Repository  
git clone https://github.com/yourusername/shareway.git
cd shareway


Create and Activate a Virtual Environment  
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install DependenciesEnsure requirements.txt includes dependencies like flask, flask-socketio, flask-sqlalchemy, python-dotenv, werkzeug. Then run:
pip install -r requirements.txt

Example requirements.txt:
flask==2.3.3
flask-socketio==5.3.6
flask-sqlalchemy==3.0.5
python-dotenv==1.0.0
werkzeug==3.0.1


Set Up Environment VariablesCreate a .env file in the project root:
GEOAPIFY_API_KEY=your_geoapify_api_key_here


Run the Application  
python app.py


Access the AppOpen your browser and navigate to:
http://localhost:5000




🖥️ Usage Guide

Register/Login  

Navigate to /register to create an account.
Use /login to access your account.


Share a Ride  

Go to /share, fill in ride details (name, destination, time, people, stop).
Submit to create a ride (max 7 people).


Book a Ride  

Visit /book, enter vehicle details (model, seat capacity, license, time, people, stop).
Submit to create a booking.


View Rides  

Access /rides to see all available rides and bookings.
Join a ride/booking by selecting it and specifying your stop and number of people.


Chat in Real-Time  

Join a ride/booking’s chat room to communicate with participants.
Messages are saved and displayed with timestamps.


Manage Bookings  

Check /my_bookings to view current and past rides/bookings.
Leave a ride/booking if it’s more than 1 hour away.


Clear Data (Admin)  

Use /clear_rides to reset all rides, bookings, and messages (requires login).




🧪 Testing
To test ShareWay:

Unit Tests (Future Work):  

Add tests for routes (e.g., /login, /share_ride) using pytest or unittest.
Test SocketIO events with mock clients.


Manual Testing:

Register multiple users and create/join rides.
Verify chat functionality by joining ride rooms.
Test edge cases (e.g., past ride creation, overbooking).


Browser Compatibility:

Tested on Chrome, Firefox, and Edge with Bootstrap’s responsive design.




🤝 Contributing
We welcome contributions to ShareWay! To contribute:

Fork the RepositoryClick the "Fork" button on GitHub and clone your fork:
git clone https://github.com/yourusername/shareway.git


Create a Branch  
git checkout -b feature/your-feature-name


Make Changes  

Follow PEP 8 for Python code.
Update documentation (e.g., README, comments) for new features.
Add tests if applicable.


Commit and Push  
git add .
git commit -m "Add your-feature-name"
git push origin feature/your-feature-name


Create a Pull Request  

Go to the original repository on GitHub.
Submit a PR with a clear description of changes.


Code Review  

Respond to feedback from maintainers.
Ensure tests pass and code aligns with project standards.




🐛 Known Issues

Redundant Message Storage: The /send_message route stores messages in dictionaries (ride_messages, booking_messages) alongside the Message model. Consider removing dictionaries for consistency.
SocketIO Initialization: Two SocketIO initializations exist; consolidate into one.
Time Zone: parse_time assumes PDT (UTC-7). Make timezone configurable for global use.
Error Handling: Limited handling for database or Geoapify API failures. Add try-catch blocks.

Report issues or suggest improvements via GitHub Issues.

📄 License
This project is licensed under the MIT License. You are free to use, modify, and distribute ShareWay, provided you include the license and copyright notice.

🙏 Acknowledgments

Geoapify: For providing the location autocomplete API.
Flask & SocketIO Communities: For robust frameworks and documentation.
Bootstrap: For responsive and modern UI components.
Mentor: Garima Jaiswal, for guiding the team through development.
Team: Peeyush, Manthan, Piyush, and Ekarth for their dedication.


📬 Contact
For questions, feedback, or collaboration:

GitHub: yourusername/shareway
Email: [your-team-email@example.com]
Mentor: Garima Jaiswal (garima.jaiswal@university.edu)

Join us in making commuting smarter and greener with ShareWay! 🚗
