
# AI Shopping Recommendation System

An intelligent e-commerce recommendation system that personalizes product suggestions using machine learning. The system combines a **React frontend**, **Django backend API**, and a **PostgreSQL database** to deliver smart, user-centric shopping experiences.

---

## 🚀 Features

*  Personalized product recommendations
*  AI/ML-based recommendation engine
*  User interaction tracking
*  Product browsing and search functionality
* ⚡Fast REST API built with Django

---

## 🏗️ Tech Stack

**Frontend**
* React.js
* Axios
* Tailwind CSS 

**Backend**

* Django
* Django REST Framework

**Database**

* PostgreSQL

**Machine Learning**

* Python (Pandas, NumPy, Scikit-learn)

---
## 📁 Project Structure

```
shopping-recommender-system/
│
├── frontend/          # React application
├── backend/           # Django REST API
├── ml_model/          # Recommendation engine (ML logic)
├── db/                # Database configs / migrations
└── README.md
```

---
## ⚙️ Installation & Setup
### 1. Clone the repository

```bash
git clone <your-repo-url>
cd shopping-recommender-system
```
---

## 🖥️ Backend Setup (Django)

### 2. Create virtual environment
```bash
python -m venv venv
```
### 3. Activate environment

```bash
venv\Scripts\activate
```


### 4. Install dependencies
```bash
pip install -r requirements.txt
```
---
### 5. Configure database (PostgreSQL)
Update `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```
### 6. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```
---
### 7. Start backend server
```bash
python manage.py runserver
```
Backend runs at:
```
http://127.0.0.1:8000/
```

## Frontend Setup (React)
### 8. Navigate to frontend

```bash
cd frontend
```

### 9. Install dependencies

```bash
npm install
```

### 10. Start development server
```bash
npm run dev
```

Frontend runs at:
```
http://localhost:3000/
```

##  Future Improvements

* Real-time learning recommendations
* Collaborative filtering enhancement
* Advanced analytics dashboard
* Deployment to cloud (AWS / Render / Heroku)
* Mobile app integration
