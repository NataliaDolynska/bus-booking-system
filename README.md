# A bus booking platform for groups 🚏 🚌
<em>WEB APP that allows both customers and administrators to perform booking processes in different roles</em>

## Overview
The **VGI Booking App** is a scalable and tested booking management system built on open-source technologies. It is designed to handle complex transportation tasks while ensuring compatibility with AI solutions.

### 🌐 [GTFS](https://www.vgi.de/GTFS-Daten_Download) Dataset 

This project uses timetable data from the VGI (Verkehrsverbund Großraum Ingolstadt) region, provided in the GTFS (General Transit Feed Specification) format.
The dataset includes:

**Lines:** Public transport routes in the VGI region.

**Departure Times:** Scheduled times for stops.

**Routes:** Detailed paths of lines.

**Stops:** Locations of stops within the VGI region.

For a detailed description of the GTFS format, refer to the General Transit Feed Specification Reference.
### Features
- User authentication and profile management
- Easy booking and cancellation system
- Notifications and reminders for upcoming bookings
- Admin dashboard for managing appointments
- Responsive UI for mobile and desktop

### 🔥 Tech Stack

**Frontend:** HTMX, Tailwind CSS

**Backend:** Python, Node.js, Django, GTFS Kit

**Database:** PostgreSQL, PostGIS
### Sign IN
![](https://github.com/NataliaDolynska/bus-booking-system/blob/master/img/sign_in.png)
### Usability
✅ **Tested & Running**: The solution is fully operational and reliable.

✅ **Open-Source**: Built using open-source technologies for flexibility and community support.

✅  **Scalability**: Designed to scale based on predefined parameters.

✅ **Advanced GIS Support**: Utilizes **PostGIS** to extend **PostgreSQL**, enabling advanced spatial and transportation functionalities.

✅ **AI Compatibility**: Supports AI integration with **PostgreSQL as a Vector Store**, making it ideal for intelligent data processing.

### 👩‍💻User role - booking selection 
![](https://github.com/NataliaDolynska/bus-booking-system/blob/master/img/booking.png)
![](https://github.com/NataliaDolynska/bus-booking-system/blob/master/img/booking_done.png)

### Admin role
![](https://github.com/NataliaDolynska/bus-booking-system/blob/master/img/admin.png)
![](https://github.com/NataliaDolynska/bus-booking-system/blob/master/img/admin1.png)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/vgi-booking-app.git 
   ```

2. Install Python Dependencies:
  ```bash  
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
 ```

3. Install Node.js Dependencies:
```
npm install
```
4. Database Setup
   
If you're not using Docker, set up PostgreSQL manually:

- Create a PostgreSQL database.

- Update .env with your database credentials.

- Run migrations:

```
python manage.py migrate
```

5. Start the Backend Server
```
python manage.py runserver
```

6. Start the Frontend 
```
npm run dev
```

### More Information 
For a detailed overview of the **VGI Booking App**, please refer to the [presentation](VGI_booking_presentation.pdf).  


### 📄 License

This project is licensed under the **Apache 2.0 License**. See the LICENSE file for details.
Please note: Public deployments of this game must visibly credit the original creator, **Natalia Dolynska**, on the main UI.
