🚗 Shareway – A Flask-Based Ride Sharing Web App
Shareway is a campus-centric ride-sharing platform built using Flask, designed to connect students and working professionals for daily commutes and intercity rides. The app allows users to create and join rides, communicate in real-time using chat, and manage bookings seamlessly.

🌟 Features
🔐 User Authentication – Secure login and session management.

🗺️ Ride Creation & Search – Users can offer rides or find available ones.

👥 Participant Management – Join rides and see who else is participating.

💬 Real-Time Chat – Integrated Socket.IO chat for live conversation in ride rooms.

📅 Date & Time Validations – No past bookings or overlapping rides.

📍 Location Autocomplete – Powered by Geopify API for smoother UX.

🛠️ Tech Stack
Backend: Flask, Flask-SocketIO, SQLite

Frontend: HTML, CSS, JavaScript, Bootstrap

APIs Used: Geopify API (for location suggestions)

Database: SQLite (via SQLAlchemy ORM)

👨‍💻 Team Members

Name	ID	Role
Peeyush Bhandari	E23CSEU1835	Backend Developer
Manthan Sharma	E23CSEU1831	Backend Developer
Piyush Negi	E23CSEU1840	Database Designer
Ekarth Kumar Shukla	E23CSEU1851	Frontend Developer
Project Mentor: Garima Jaiswal, Assistant Professor

🚀 How to Run Locally
Clone the repository

bash
Copy
Edit
git clone https://github.com/yourusername/shareway.git
cd shareway
Create and activate virtual environment

bash
Copy
Edit
python -m venv venv
source venv/bin/activate   # On Windows use `venv\Scripts\activate`
Install dependencies

bash
Copy
Edit
pip install -r requirements.txt
Run the application

bash
Copy
Edit
python app.py
Access the app Visit http://localhost:5000 in your browser.
📄 License
MIT License – feel free to use, modify, and share!