from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time
from decimal import Decimal
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import plotly.express as px
import pandas as pd
import numpy as np
import pyodbc
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = 'skyguest'

# Замените на ваши реальные данные
server = 'ALINA-BOOK'
database = 'SkyGuest'
driver = 'ODBC Driver 17 for SQL Server'

# Строка подключения
conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes'
connection = pyodbc.connect(conn_str)
cursor = connection.cursor()

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    keyword = StringField('Ключевое слово', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Войти')


# Ваш код для формы и маршрута
class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    keyword = StringField('Ключевое слово', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')


class NewPasswordForm(FlaskForm):
    new_password = PasswordField('Новый пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите новый пароль', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Обновить пароль')


class EditProfileForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    new_password = PasswordField('Новый пароль')
    confirm_password = PasswordField('Подтвердите новый пароль')
    submit = SubmitField('Сохранить изменения')


class ChangeNameForm(FlaskForm):
    new_name = StringField('Новое имя', validators=[DataRequired()])
    submit = SubmitField('Сохранить')


class ChangeEmailForm(FlaskForm):
    new_email = StringField('Новый email', validators=[DataRequired(), Email()])
    submit = SubmitField('Сохранить')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Текущий пароль', validators=[DataRequired(), Length(min=6)])
    new_password = PasswordField('Новый пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите новый пароль', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Сохранить')


class ChangeKeywordForm(FlaskForm):
    current_keyword = StringField('Текущее ключевое слово', validators=[DataRequired()])
    new_keyword = StringField('Новое ключевое слово', validators=[DataRequired()])
    confirm_new_keyword = StringField('Подтвердите новое ключевое слово', validators=[DataRequired()])
    submit = SubmitField('Сохранить')


def hash_string(input_string):
    # Генерация хеша для строки с использованием generate_password_hash
    return generate_password_hash(input_string)


def hash_password(password):
    # Генерация хешированного пароля с использованием hash_string
    return hash_string(password)


@app.route('/')
def index():
    form = RegistrationForm()
    return render_template('index.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if request.method == 'POST' and form.validate_on_submit():
        # Получение данных из формы
        username = form.username.data
        email = form.email.data
        raw_password = form.password.data
        raw_keyword = form.keyword.data

        hashed_password = hash_password(raw_password)
        hashed_keyword = hash_password(raw_keyword)

        # Проверка уникальности email
        cursor.execute("SELECT * FROM Users WHERE email=?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Email уже зарегистрирован. Пожалуйста, выберите другой email.', 'danger')
            return redirect(url_for('register'))

        # Вставка нового пользователя в базу данных
        query = "INSERT INTO Users (username, email, password, keyword) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (username, email, hashed_password, hashed_keyword))
        connection.commit()

        # Получение ID только что зарегистрированного пользователя
        cursor.execute("SELECT id FROM Users WHERE email=?", (email,))
        user_id = cursor.fetchone().id

        # Устанавливаем user_id в сессии
        session['user_id'] = user_id

        flash('Регистрация прошла успешно!', 'success')

        # Перенаправление на страницу профиля пользователя
        return redirect(url_for('user_profile'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Проверка наличия пользователя в базе данных
        cursor.execute("SELECT * FROM Users WHERE username=?", (username,))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user.id
            # Проверка пароля с использованием check_password_hash
            if check_password_hash(user.password, form.password.data):
                if username == "Admin":
                    flash('Вход выполнен как администратор!', 'success')
                    # Перенаправление на страницу администратора
                    return redirect(url_for('admin_check'))
                else:
                    flash('Вход выполнен успешно!', 'success')
                    # Перенаправление на страницу профиля пользователя
                    return redirect(url_for('user_profile'))

        flash('Неверные имя пользователя или пароль. Пожалуйста, зарегистрируйтесь.', 'danger')
        # Перенаправление на страницу регистрации
        return redirect(url_for('register'))

    return render_template('login.html', form=form)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()

    if request.method == 'POST' and form.validate_on_submit():
        email = form.email.data
        keyword = form.keyword.data

        # Проверка наличия пользователя в базе данных
        cursor.execute("SELECT * FROM Users WHERE email=?", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user.keyword, form.keyword.data):
            session['user_id'] = user.id
            # Перенаправление на страницу ввода нового пароля
            return redirect(url_for('new_password'))

        else:
            # Перенаправление на страницу регистрации, так как пользователя нет
            flash('Пользователь с таким email и ключевым словом не найден. Зарегистрируйтесь.', 'danger')
            return redirect(url_for('register'))

    return render_template('forgot_password.html', form=form)


@app.route('/new_password', methods=['GET', 'POST'])
def new_password():
    # Проверяем, авторизован ли пользователь
    if 'user_id' not in session:
        flash('Пожалуйста, введите новый пароль.', 'danger')
        return redirect(url_for('login'))

    form = NewPasswordForm()

    if request.method == 'POST' and form.validate_on_submit():
        user_id = session['user_id']
        new_password = form.new_password.data
        confirm_password = form.confirm_password.data

        # Проверка совпадения нового и подтвержденного пароля
        if new_password != confirm_password:
            flash('Пароли не совпадают. Попробуйте еще раз.', 'danger')
            return redirect(url_for('new_password'))

        # Обновление пароля в базе данных
        hashed_password = hash_password(new_password)
        cursor.execute("UPDATE Users SET password=? WHERE id=?", (hashed_password, user_id))
        connection.commit()

        flash('Пароль успешно обновлен. Войдите с новым паролем.', 'success')
        return redirect(url_for('login'))

    return render_template('new_password.html', form=form)


@app.route('/user_profile')
def user_profile():
    # Проверяем, авторизован ли пользователь
    if 'user_id' not in session:
        flash('Пожалуйста, войдите, чтобы просмотреть свой профиль.', 'danger')
        return redirect(url_for('login'))

    # Получаем данные профиля пользователя из базы данных на основе user_id
    user_id = session['user_id']
    cursor.execute("SELECT * FROM Users WHERE id=?", (user_id,))
    user_profile_data = cursor.fetchone()

    if not user_profile_data:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('login'))

    return render_template('user_profile.html', user_profile_data=user_profile_data)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('index'))


@app.route('/my_profile', methods=['GET', 'POST'])
def my_profile():
    # Проверяем, авторизован ли пользователь
    if 'user_id' not in session:
        flash('Пожалуйста, войдите, чтобы просмотреть свой профиль.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor.execute("SELECT * FROM Users WHERE id=?", (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('login'))

    form = EditProfileForm()

    if request.method == 'POST' and form.validate_on_submit():
        # Обновление данных профиля в базе данных
        user_id = session['user_id']
        username = form.username.data
        email = form.email.data
        new_password = form.new_password.data
        confirm_password = form.confirm_password.data

        # Проверка совпадения нового и подтвержденного пароля
        if new_password and new_password != confirm_password:
            flash('Пароли не совпадают. Попробуйте еще раз.', 'danger')
            return redirect(url_for('my_profile'))

        # Обновление данных профиля
        cursor.execute("UPDATE Users SET username=?, email=? WHERE id=?", (username, email, user_id))

        # Обновление пароля, если указан новый пароль
        if new_password:
            hashed_password = hash_password(new_password)
            cursor.execute("UPDATE Users SET password=? WHERE id=?", (hashed_password, user_id))

        connection.commit()

        flash('Изменения сохранены успешно!', 'success')
        return redirect(url_for('my_profile'))

    # Заполняем форму текущими данными профиля
    form.username.data = user_data.username
    form.email.data = user_data.email

    return render_template('my_profile.html', form=form, user_profile_data=user_data)


@app.route('/change_name', methods=['POST'])
def change_name():
    form = ChangeNameForm()

    if request.method == 'POST' and form.validate_on_submit():
        new_name = form.new_name.data
        user_id = session['user_id']

        # Обновление имени в базе данных
        cursor.execute("UPDATE Users SET username=? WHERE id=?", (new_name, user_id))
        connection.commit()

        flash('Имя успешно изменено!', 'success')
        return redirect(url_for('my_profile'))

    flash('Ошибка при изменении имени. Пожалуйста, попробуйте еще раз.', 'danger')
    return redirect(url_for('my_profile'))


@app.route('/change_email', methods=['POST'])
def change_email():
    form = ChangeEmailForm()

    if request.method == 'POST' and form.validate_on_submit():
        new_email = form.new_email.data
        user_id = session['user_id']

        # Проверка уникальности email
        cursor.execute("SELECT id FROM Users WHERE email=?", (new_email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Указанный email уже используется. Пожалуйста, выберите другой.', 'danger')
            return redirect(url_for('my_profile'))

        # Обновление email в базе данных
        cursor.execute("UPDATE Users SET email=? WHERE id=?", (new_email, user_id))
        connection.commit()

        flash('Email успешно изменен!', 'success')
        return redirect(url_for('my_profile'))

    flash('Ошибка при изменении email. Пожалуйста, попробуйте еще раз.', 'danger')
    return redirect(url_for('my_profile'))


@app.route('/change_password', methods=['POST'])
def change_password():
    form = ChangePasswordForm()

    if request.method == 'POST' and form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data
        confirm_password = form.confirm_password.data
        user_id = session['user_id']

        # Получаем текущий хешированный пароль пользователя из базы данных
        cursor.execute("SELECT password FROM Users WHERE id=?", (user_id,))
        user = cursor.fetchone()

        if user and check_password_hash(user.password, current_password):
            # Проверяем, совпадают ли новый пароль и его подтверждение
            if new_password == confirm_password:
                # Обновляем пароль в базе данных
                hashed_password = hash_password(new_password)
                cursor.execute("UPDATE Users SET password=? WHERE id=?", (hashed_password, user_id))
                connection.commit()

                flash('Пароль успешно изменен!', 'success')
                return redirect(url_for('my_profile'))
            else:
                flash('Новый пароль и подтверждение пароля не совпадают. Пожалуйста, попробуйте еще раз.', 'danger')
        else:
            flash('Текущий пароль введен неверно. Пожалуйста, проверьте правильность ввода.', 'danger')

    flash('Ошибка при изменении пароля. Пожалуйста, попробуйте еще раз.', 'danger')
    return redirect(url_for('my_profile'))


@app.route('/change_keyword', methods=['POST'])
def change_keyword():
    form = ChangeKeywordForm()

    if request.method == 'POST' and form.validate_on_submit():
        current_keyword = form.current_keyword.data
        new_keyword = form.new_keyword.data
        confirm_new_keyword = form.confirm_new_keyword.data
        user_id = session['user_id']

        # Получаем текущее хешированное ключевое слово пользователя из базы данных
        cursor.execute("SELECT keyword FROM Users WHERE id=?", (user_id,))
        current_hashed_keyword = cursor.fetchone()[0]

        # Проверяем, совпадает ли введенное текущее ключевое слово с сохраненным
        if check_password_hash(current_hashed_keyword, current_keyword):
            # Проверяем, совпадают ли новое ключевое слово и его подтверждение
            if new_keyword == confirm_new_keyword:
                # Обновляем ключевое слово в базе данных
                hashed_keyword = hash_password(new_keyword)
                cursor.execute("UPDATE Users SET keyword=? WHERE id=?", (hashed_keyword, user_id))
                connection.commit()

                flash('Ключевое слово успешно изменено!', 'success')
                return redirect(url_for('my_profile'))
            else:
                flash('Новое ключевое слово и подтверждение не совпадают. Пожалуйста, попробуйте еще раз.', 'danger')
        else:
            flash('Текущее ключевое слово введено неверно. Пожалуйста, проверьте правильность ввода.', 'danger')

    flash('Ошибка при изменении ключевого слова. Пожалуйста, попробуйте еще раз.', 'danger')
    return redirect(url_for('my_profile'))


@app.route('/exit')
def exit():
    # Удаляем user_id из сессии, чтобы выйти из аккаунта
    session.pop('user_id', None)
    flash('Вы вышли из аккаунта.', 'success')
    # Перенаправляем на главную страницу
    return redirect(url_for('index'))


def calculate_flight_duration(departure_date, departure_time, arrival_date, arrival_time):
    # Преобразуем даты и времена в объекты datetime
    departure_datetime = datetime.combine(departure_date, departure_time)
    arrival_datetime = datetime.combine(arrival_date, arrival_time)
    duration = arrival_datetime - departure_datetime
    return duration


def process_passenger_input(passenger_count_str, passenger_class):
    # Преобразование passenger_count в целое число
    passenger_count = int(passenger_count_str.split()[0])

    # Инициализация значений для каждого класса
    economy_passengers = 0
    comfort_passengers = 0
    business_passengers = 0
    first_class_passengers = 0

    # Обработка введенного класса
    if passenger_class == 'Эконом':
        economy_passengers = passenger_count
    elif passenger_class == 'Комфорт':
        comfort_passengers = passenger_count
    elif passenger_class == 'Бизнес класс':
        business_passengers = passenger_count
    elif passenger_class == 'Первый класс':
        first_class_passengers = passenger_count

    return economy_passengers, comfort_passengers, business_passengers, first_class_passengers


@app.route('/search', methods=['POST'])
def search():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите, чтобы выполнить поиск.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']


    # Получаем данные из формы поиска
    from_city = request.form.get('searchSection1')
    to_city = request.form.get('searchSection2')
    departure_date = request.form.get('searchSection3')
    return_date = request.form.get('searchSection4')
    passenger_count_str = request.form.get('searchSection5')
    passenger_class = request.form.get('searchSection6')

    # Обрабатываем введенные данные
    economy_passengers, comfort_passengers, business_passengers, first_class_passengers = process_passenger_input(
        passenger_count_str, passenger_class)

    # Сохранение данных в базу данных
    cursor.execute("""
        INSERT INTO PassengerCounts (user_id, economy_passengers, comfort_passengers, business_passengers, first_class_passengers)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, economy_passengers, comfort_passengers, business_passengers, first_class_passengers))
    connection.commit()

    # Запрос для поиска рейсов туда
    query_outbound = """
        SELECT *
        FROM (
            SELECT 
                Flights.flight_id,
                Flights.departure_date,
                Flights.departure_time,
                Flights.arrival_date,
                Flights.arrival_time,
                departure_airport.city AS departure_city,
                departure_airport.airport_code AS departure_airport_code,
                arrival_airport.airport_code AS arrival_airport_code,
                arrival_airport.city AS arrival_city,
                Airlines.airline_name, 
                Planes.plane_name,        
                Planes.has_baggage,
                CASE 
                    WHEN Planes.economy_price > 0 AND PassengerCounts.economy_passengers > 0 THEN Planes.economy_price
                    WHEN Planes.businessprice > 0 AND PassengerCounts.business_passengers > 0 THEN Planes.businessprice
                    WHEN Planes.first_price > 0 AND PassengerCounts.first_class_passengers > 0 THEN Planes.first_price
                    WHEN Planes.comfort_price > 0 AND PassengerCounts.comfort_passengers > 0 THEN Planes.comfort_price
                    ELSE NULL 
                END AS calculated_price
            FROM 
                Flights
            JOIN 
                Airports AS departure_airport ON Flights.departure_airport_id = departure_airport.airport_id
            JOIN 
                Airports AS arrival_airport ON Flights.arrival_airport_id = arrival_airport.airport_id
            JOIN 
                Airlines ON Flights.airline_id = Airlines.airline_id 
            JOIN 
                Planes ON Flights.plane_id = Planes.plane_id
            LEFT JOIN 
                Baggage ON Flights.flight_id = Baggage.flight_id
            LEFT JOIN 
                PassengerCounts ON PassengerCounts.user_id = user_id
            WHERE 
                departure_airport.city = ? 
                AND arrival_airport.city = ? 
                AND Flights.departure_date = ?
                AND (
                    Flights.departure_date > CONVERT(DATE, GETDATE()) OR
                    (Flights.departure_date = CONVERT(DATE, GETDATE()) AND DATEADD(HOUR, -1, Flights.departure_time) >= CONVERT(TIME, GETDATE()))
                )
                AND (
                    (COALESCE(Planes.economy_seats - Planes.economy_seats_occupied, 0) >= PassengerCounts.economy_passengers) OR
                    (COALESCE(Planes.business_seats - Planes.business_seats_occupied, 0) >= PassengerCounts.business_passengers) OR
                    (COALESCE(Planes.first_class_seats - Planes.first_class_seats_occupied, 0) >= PassengerCounts.first_class_passengers) OR
                    (COALESCE(Planes.comfort_class_seats - Planes.comfort_class_seats_occupied, 0) >= PassengerCounts.comfort_passengers)
                )
        ) AS subquery
        WHERE calculated_price IS NOT NULL
        GROUP BY 
            flight_id, 
            departure_date, 
            departure_time, 
            arrival_date, 
            arrival_time, 
            departure_city, 
            departure_airport_code, 
            arrival_city, 
            arrival_airport_code, 
            airline_name, 
            plane_name,
            has_baggage,
            calculated_price;
    """

    # Запрос для поиска рейсов обратно
    query_return = """
       SELECT *
        FROM (
            SELECT 
                Flights.flight_id,
                Flights.departure_date,
                Flights.departure_time,
                Flights.arrival_date,
                Flights.arrival_time,
                departure_airport.city AS departure_city,
                departure_airport.airport_code AS departure_airport_code,
                arrival_airport.airport_code AS arrival_airport_code,
                arrival_airport.city AS arrival_city,
                Airlines.airline_name, 
                Planes.plane_name,        
                Planes.has_baggage,
                CASE 
                    WHEN Planes.economy_price > 0 AND PassengerCounts.economy_passengers > 0 THEN Planes.economy_price
                    WHEN Planes.businessprice > 0 AND PassengerCounts.business_passengers > 0 THEN Planes.businessprice
                    WHEN Planes.first_price > 0 AND PassengerCounts.first_class_passengers > 0 THEN Planes.first_price
                    WHEN Planes.comfort_price > 0 AND PassengerCounts.comfort_passengers > 0 THEN Planes.comfort_price
                    ELSE NULL 
                END AS calculated_price
            FROM 
                Flights
            JOIN 
                Airports AS departure_airport ON Flights.departure_airport_id = departure_airport.airport_id
            JOIN 
                Airports AS arrival_airport ON Flights.arrival_airport_id = arrival_airport.airport_id
            JOIN 
                Airlines ON Flights.airline_id = Airlines.airline_id 
            JOIN 
                Planes ON Flights.plane_id = Planes.plane_id
            LEFT JOIN 
                Baggage ON Flights.flight_id = Baggage.flight_id
            LEFT JOIN 
                PassengerCounts ON PassengerCounts.user_id = user_id
            WHERE 
                departure_airport.city = ? 
                AND arrival_airport.city = ? 
                AND Flights.departure_date = ?
                AND (
                    Flights.departure_date > CONVERT(DATE, GETDATE()) OR
                    (Flights.departure_date = CONVERT(DATE, GETDATE()) AND DATEADD(HOUR, -1, Flights.departure_time) >= CONVERT(TIME, GETDATE()))
                )
                AND (
                    (COALESCE(Planes.economy_seats - Planes.economy_seats_occupied, 0) >= PassengerCounts.economy_passengers) OR
                    (COALESCE(Planes.business_seats - Planes.business_seats_occupied, 0) >= PassengerCounts.business_passengers) OR
                    (COALESCE(Planes.first_class_seats - Planes.first_class_seats_occupied, 0) >= PassengerCounts.first_class_passengers) OR
                    (COALESCE(Planes.comfort_class_seats - Planes.comfort_class_seats_occupied, 0) >= PassengerCounts.comfort_passengers)
                )
        ) AS subquery
        WHERE calculated_price IS NOT NULL
        GROUP BY 
            flight_id, 
            departure_date, 
            departure_time, 
            arrival_date, 
            arrival_time, 
            departure_city, 
            departure_airport_code, 
            arrival_city, 
            arrival_airport_code, 
            airline_name, 
            plane_name,
            has_baggage,
            calculated_price;
    """

    cursor.execute(query_outbound, (from_city, to_city, departure_date))
    outbound_flights = cursor.fetchall()

    outbound_flight_data = []
    for flight in outbound_flights:
        duration = calculate_flight_duration(
            flight[1],  # index 1 corresponds to 'departure_date'
            flight[2],  # index 2 corresponds to 'departure_time'
            flight[3],  # index 3 corresponds to 'arrival_date'
            flight[4]  # index 4 corresponds to 'arrival_time'
        )
        outbound_flight_data.append({'flight_info': flight, 'duration': duration})



    return_flights = None  # Initialize return_flights to None
    return_flight_data = []  # Initialize return_flight_data here

    if return_date:
        # Execute the database query only if return_date is not empty
        cursor.execute(query_return, (to_city, from_city, return_date))
        return_flights = cursor.fetchall()

        # Check if return_flights is not None before attempting to iterate over it
        if return_flights is not None:
            for flight in return_flights:
                duration = calculate_flight_duration(
                    flight[1],  # index 1 corresponds to 'departure_date'
                    flight[2],  # index 2 corresponds to 'departure_time'
                    flight[3],  # index 3 corresponds to 'arrival_date'
                    flight[4]  # index 4 corresponds to 'arrival_time'
                )
                return_flight_data.append({'flight_info': flight, 'duration': duration})

    # Удаление сохраненных данных
    cursor.execute("DELETE FROM PassengerCounts WHERE user_id = ?", (user_id,))
    connection.commit()

    # Return the page with the results
    return render_template('search_results.html', outbound_flights=outbound_flight_data,
                           return_flights=return_flight_data, return_date=return_date)


@app.route('/buy_ticket')
def buy_ticket():
    # Получение значения для flightId из параметров запроса
    flight_id_value = request.args.get('flightId')

    # Сохранение значения flightId в сессии
    session['flight_id'] = flight_id_value

    passenger_class_data = request.args.get('passengerClass')
    session['passengerClass'] = passenger_class_data

    adult = request.args.get('adult')
    session['adult'] = adult

    child = request.args.get('child')
    session['child'] = child

    infant = request.args.get('infant')
    session['infant'] = infant

    return render_template('buy_ticket.html')


@app.route('/process_passenger_data', methods=['GET', 'POST'])
def process_passenger_data():

    if 'user_id' not in session:
        return json.dumps({'success': False, 'message': 'User not logged in'})

    try:
        user_id = session['user_id']
        # Получение значения flightId из сессии
        flight_id_value = session.get('flight_id')
        passenger_class_data = session.get('passengerClass')

        adult = session.get('adult')
        child = session.get('child')
        infant = session.get('infant')

        # Извлечение данных из запроса JSON
        data = request.get_json()
        passenger_info = data.get('passenger_info', [])

        inserted_passenger_ids = []  # Инициализация переменной перед блоком try
        i = adult + child + infant

        # Вставка информации о пассажире в таблицу Passengers
        for i, passenger_data in enumerate(passenger_info.values()):

            cursor.execute('''
                    INSERT INTO Passengers
                    (first_name, last_name, middle_name, birthdate, sex, nationality, document, passport_number, expilation_date, telephone_number, contact_info, flight_id, user_id)
                     OUTPUT INSERTED.passenger_id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
                ''', (
                passenger_data.get(f'first_name_{i}'),
                passenger_data.get(f'last_name_{i}'),
                passenger_data.get(f'middle_name_{i}', ''),
                passenger_data.get(f'birthdate_{i}'),
                passenger_data.get(f'sex_{i}'),
                passenger_data.get(f'nationality_{i}'),
                passenger_data.get(f'document_{i}'),
                passenger_data.get(f'passport_number_{i}'),
                passenger_data.get(f'expilation_date_{i}'),
                passenger_data.get(f'telephone_number_{i}'),
                passenger_data.get(f'email_{i}'),
                flight_id_value,
                user_id
            ))

            # Получение только что вставленных passenger_id
            inserted_passenger_ids = [row[0] for row in cursor.fetchall()]

            # Вставка данных в таблицу Tickets
            for passenger_id in inserted_passenger_ids:
                cursor.execute('''
                    INSERT INTO Tickets (flight_id, passenger_id, status,user_id)
                    VALUES (?, ?, ?, ?)
                ''', (flight_id_value, passenger_id, passenger_class_data, user_id))

            # Вставка данных в таблицу TicketPurchaseHistory только для вновь вставленных пассажиров
            for passenger_id in inserted_passenger_ids:
                cursor.execute('''
                    INSERT INTO TicketPurchaseHistory
                    (ticket_id, purchase_date, passenger_id, payment_method, payment_status, user_id)
                    SELECT
                        Tickets.ticket_id,
                        GETDATE(),
                        Tickets.passenger_id,
                        'Банковская карта',
                        'Успешно',
                        Tickets.user_id
                    FROM
                        Tickets
                    WHERE
                        Tickets.passenger_id = ? AND Tickets.user_id = ?;
                ''', (passenger_id, user_id,))

        # Обновление информации о билетах в таблице Planes
        cursor.execute('''
             UPDATE Planes
                SET
                    economy_seats_occupied = (
                        SELECT COUNT(*)
                        FROM Tickets
                        JOIN Flights ON Tickets.flight_id = Flights.flight_id
                        WHERE Planes.plane_id = Flights.plane_id
                          AND Tickets.status = 'Эконом'
                    ),
                    business_seats_occupied = (
                        SELECT COUNT(*)
                        FROM Tickets
                        JOIN Flights ON Tickets.flight_id = Flights.flight_id
                        WHERE Planes.plane_id = Flights.plane_id
                          AND Tickets.status = 'Бизнес класс'
                    ),
                    first_class_seats_occupied = (
                        SELECT COUNT(*)
                        FROM Tickets
                        JOIN Flights ON Tickets.flight_id = Flights.flight_id
                        WHERE Planes.plane_id = Flights.plane_id
                          AND Tickets.status = 'Первый класс'
                    ),
                    comfort_class_seats_occupied = (
                        SELECT COUNT(*)
                        FROM Tickets
                        JOIN Flights ON Tickets.flight_id = Flights.flight_id
                        WHERE Planes.plane_id = Flights.plane_id
                          AND Tickets.status = 'Комфорт'
                    );
        ''')

        # Применение изменений к базе данных
        connection.commit()

        return json.dumps({'success': True, 'message': 'Data processed successfully'})

    except Exception as e:
        return json.dumps({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите, чтобы выполнить поиск.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    sql_query = '''
      SELECT
           Passengers.last_name,
           Passengers.first_name,
           DepartureAirport.city AS departure_city,
           DepartureAirport.airport_code AS departure_airport_code,
           ArrivalAirport.city AS arrival_city,
           ArrivalAirport.airport_code AS arrival_airport_code,
           Flights.departure_date,
           Flights.departure_time,
           Airlines.airline_name,
           Tickets.status,
           TicketPurchaseHistory.purchase_date,
           TicketPurchaseHistory.payment_method,
           TicketPurchaseHistory.payment_status,
           Planes.has_baggage
       FROM
           Tickets
       JOIN Passengers ON Tickets.passenger_id = Passengers.passenger_id
       JOIN Flights ON Tickets.flight_id = Flights.flight_id
       JOIN Airlines ON Flights.airline_id = Airlines.airline_id
       JOIN Airports AS DepartureAirport ON Flights.departure_airport_id = DepartureAirport.airport_id
       JOIN Airports AS ArrivalAirport ON Flights.arrival_airport_id = ArrivalAirport.airport_id
       JOIN Planes ON Flights.plane_id = Planes.plane_id
       LEFT JOIN TicketPurchaseHistory ON Tickets.ticket_id = TicketPurchaseHistory.ticket_id
       WHERE
           Tickets.user_id = ?
       ORDER BY TicketPurchaseHistory.purchase_date DESC, Tickets.ticket_id DESC;        '''

    # Выполнение запроса с использованием user_id
    cursor.execute(sql_query, (user_id,))
    result = cursor.fetchall()

    # Возвращение результатов в шаблон
    return render_template('cart.html', result=result)


@app.route('/admin_check', methods=['GET', 'POST'])
def admin_check():
    form = ForgotPasswordForm()

    if request.method == 'POST' and form.validate_on_submit():
        email = form.email.data
        keyword = form.keyword.data

        # Проверка наличия пользователя в базе данных
        cursor.execute("SELECT * FROM Users WHERE email=?", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user.keyword, form.keyword.data):
            if email == 'admin@gmail.com':
                # Перенаправление на страницу администратора
                return redirect(url_for('admin_profile'))
            else:
                session['user_id'] = user.id
                # Перенаправление на страницу ввода нового пароля
                return redirect(url_for('admin_profile'))

        else:
            # Перенаправление на страницу регистрации, так как пользователя нет
            flash('Администратор с таким email и ключевым словом не найден.', 'danger')
            return redirect(url_for('index'))

    return render_template('admin_check.html', form=form)


def get_airlines():
    with pyodbc.connect(conn_str) as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM Airlines')
        return cursor.fetchall()


def get_airports():
    with pyodbc.connect(conn_str) as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM Airports')
        return cursor.fetchall()


def get_planes():
    with pyodbc.connect(conn_str) as connection:
        cursor = connection.cursor()
        cursor.execute('''
                    SELECT 
                        p.plane_id,
                        p.plane_name,
                        p.plane_model,
                        a.airline_name, 
                        p.economy_seats,
                        p.business_seats,
                        p.first_class_seats,
                        p.comfort_class_seats,
                        p.economy_seats_occupied,
                        p.business_seats_occupied,
                        p.first_class_seats_occupied,
                        p.comfort_class_seats_occupied,
                        p.economy_price,
                        p.businessprice, 
                        p.first_price,
                        p.comfort_price,
                        p.has_baggage
                    FROM Planes p
                    JOIN Airlines a ON p.airline_id = a.airline_id
                ''')
        return cursor.fetchall()


def get_flights():
    with pyodbc.connect(conn_str) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT
                f.flight_id,
                f.departure_date,
                f.departure_time,
                f.arrival_date,
                f.arrival_time,
                f.flight_number,
                a1.airport_name AS departure_airport,
                a2.airport_name AS arrival_airport,
                al.airline_name,
                p.plane_name,
                p.plane_model
            FROM Flights f
            JOIN Airlines al ON f.airline_id = al.airline_id
            JOIN Airports a1 ON f.departure_airport_id = a1.airport_id
            JOIN Airports a2 ON f.arrival_airport_id = a2.airport_id
            JOIN Planes p ON f.plane_id = p.plane_id
        ''')
        return cursor.fetchall()


@app.route('/admin_profile')
def admin_profile():
    # Проверяем, авторизован ли пользователь
    if 'user_id' not in session:
        flash('Пожалуйста, войдите, чтобы просмотреть свой профиль.', 'danger')
        return redirect(url_for('login'))
    # Получаем данные об авиакомпаниях
    airlines = get_airlines()
    airports = get_airports()
    planes = get_planes()
    flights = get_flights()
    return render_template('admin_profile.html', airlines=airlines, airports=airports, planes=planes, flights=flights)


@app.route('/delete_airline/<int:airline_id>', methods=['DELETE'])
def delete_airline(airline_id):
    try:

        cursor.execute('DELETE FROM Airlines WHERE airline_id = ?', (airline_id,))

        connection.commit()
        return jsonify(success=True)
    except Exception as e:
        # Обработка ошибок, например, логирование или возврат HTTP-статуса 500
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


@app.route('/edit_airline/<int:airline_id>', methods=['PUT'])
def edit_airline(airline_id):
    try:
        # Получаем данные из запроса
        data = request.json

        # Редактируем запись в базе данных
        edit_query = '''
                    UPDATE Airlines
                    SET airline_name=?, airline_code=?, contact_info=?
                    WHERE airline_id = ?
                '''
        cursor.execute(edit_query, (
            data['edit_name'],
            data['edit_code'],
            data['edit_contact'],
            airline_id
        ))

        connection.commit()
        return jsonify(success=True)
    except Exception as e:
        # Обработка ошибок, например, логирование или возврат HTTP-статуса 500
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


@app.route('/add_airline', methods=['POST'])
def add_airline():
    try:
        # Получаем данные из запроса
        data = request.json

        # Добавляем новую запись в базу данных
        add_query = 'INSERT INTO Airlines (airline_name, airline_code, contact_info) VALUES (?, ?, ?)'
        cursor.execute(add_query, (
            data['add_name'],
            data['add_code'],
            data['add_contact']
        ))

        connection.commit()
        return jsonify(success=True)
    except Exception as e:
        # Обработка ошибок, например, логирование или возврат HTTP-статуса 500
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


@app.route('/update_airport/<int:airport_id>', methods=['PUT'])
def update_airport(airport_id):
    try:
        # Получаем данные из запроса
        data = request.json

        # Обновляем запись в базе данных
        update_query = '''
            UPDATE Airports
            SET airport_name=?, airport_code=?, city=?, address=?, contact_info=?
            WHERE airport_id=?
        '''
        cursor.execute(update_query, (
            data['edit_apname'],
            data['edit_apcode'],
            data['edit_apcity'],
            data['edit_apaddress'],
            data['edit_apcontact'],
            airport_id
        ))

        connection.commit()
        return jsonify(success=True)
    except Exception as e:
        # Обработка ошибок, например, логирование или возврат HTTP-статуса 500
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


@app.route('/add_airport', methods=['POST'])
def add_airport():
    try:
        # Получаем данные из запроса
        data = request.json

        # Добавляем новую запись в базу данных
        add_query = 'INSERT INTO Airports (airport_name, airport_code, city, address, contact_info) VALUES (?, ?, ?, ?, ?)'
        cursor.execute(add_query, (
            data['add_apname'],
            data['add_apcode'],
            data['add_apcity'],
            data['add_apaddress'],
            data['add_apcontact']
        ))

        connection.commit()
        return jsonify(success=True)
    except Exception as e:
        # Обработка ошибок, например, логирование или возврат HTTP-статуса 500
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


@app.route('/delete_airport/<int:airport_id>', methods=['DELETE'])
def delete_airport(airport_id):
    try:
        # Реализуйте логику удаления аэропорта по идентификатору
        delete_query = 'DELETE FROM Airports WHERE airport_id = ?'
        cursor.execute(delete_query, (airport_id,))
        connection.commit()
        return jsonify(success=True)
    except Exception as e:
        # Обработка ошибок, например, логирование или возврат HTTP-статуса 500
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


@app.route('/update_plane/<int:plane_id>', methods=['PUT'])
def update_plane(plane_id):
    try:
        data = request.json

        # Получаем airline_id по airline_name
        get_airline_id_query = 'SELECT airline_id FROM Airlines WHERE airline_name = ?'
        cursor.execute(get_airline_id_query, (data['edit_airline'],))
        airline_id = cursor.fetchone()

        if airline_id:
            # Обновляем запись в базе данных
            update_query = '''
                UPDATE Planes
                SET 
                    plane_name=?,
                    plane_model=?,
                    airline_id=?,  -- Это ваш фактический столбец, связывающий с таблицей Airlines
                    economy_seats=?,
                    business_seats=?,
                    first_class_seats=?,
                    comfort_class_seats=?,
                    economy_price=?,
                    businessprice=?,
                    first_price=?,
                    comfort_price=?,
                    has_baggage=?
                WHERE plane_id=?
            '''
            cursor.execute(update_query, (
                data['edit_pname'],
                data['edit_model'],
                airline_id[0],  # Используем полученный airline_id
                data['edit_economy_seats'],
                data['edit_business_seats'],
                data['edit_first_class_seats'],
                data['edit_comfort_class_seats'],
                data['edit_economy_price'],
                data['edit_business_price'],
                data['edit_first_price'],
                data['edit_comfort_price'],
                data['edit_has_baggage'],
                plane_id
            ))

            connection.commit()
            return jsonify(success=True)
        else:
            return jsonify(success=False, error='Airline not found')

    except Exception as e:
        # Обработка ошибок
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


@app.route('/add_plane', methods=['POST'])
def add_plane():
    try:
        # Получаем данные из запроса
        data = request.json

        # Получаем airline_id по airline_name
        get_airline_id_query = 'SELECT airline_id FROM Airlines WHERE airline_name = ?'
        cursor.execute(get_airline_id_query, (data['add_airline'],))
        airline_id = cursor.fetchone()

        if airline_id:
            # Добавляем новую запись в базу данных
            add_query = '''
                INSERT INTO Planes (
                    plane_name,
                    plane_model,
                    airline_id, 
                    economy_seats,
                    business_seats,
                    first_class_seats,
                    comfort_class_seats,
                    economy_price,
                    businessprice,
                    first_price,
                    comfort_price,
                    has_baggage
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(add_query, (
                data['add_pname'],
                data['add_model'],
                airline_id[0],  # Используем полученный airline_id
                data['add_economy_seats'],
                data['add_business_seats'],
                data['add_first_class_seats'],
                data['add_comfort_class_seats'],
                data['add_economy_price'],
                data['add_business_price'],
                data['add_first_price'],
                data['add_comfort_price'],
                data['add_has_baggage']
            ))

            connection.commit()
            return jsonify(success=True)
        else:
            return jsonify(success=False, error='Airline not found')
    except Exception as e:
        # Обработка ошибок, например, логирование или возврат HTTP-статуса 500
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


@app.route('/delete_plane/<int:plane_id>', methods=['DELETE'])
def delete_plane(plane_id):
    try:
        # Реализуйте логику удаления самолета по идентификатору
        delete_query = 'DELETE FROM Planes WHERE plane_id = ?'
        cursor.execute(delete_query, (plane_id,))
        connection.commit()
        return jsonify(success=True)
    except Exception as e:
        # Обработка ошибок, например, логирование или возврат HTTP-статуса 500
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


@app.route('/update_flight/<int:flight_id>', methods=['PUT'])
def update_flight(flight_id):
    try:
        data = request.json

        # Получаем airline_id по airline_name
        get_airline_id_query = 'SELECT airline_id FROM Airlines WHERE airline_name = ?'
        cursor.execute(get_airline_id_query, (data['edit_airline_f'],))
        airline_id = cursor.fetchone()

        # Получаем departure_airport_id по airport_name
        get_departure_airport_id_query = 'SELECT airport_id FROM Airports WHERE airport_name = ?'
        cursor.execute(get_departure_airport_id_query, (data['edit_departure_airport'],))
        departure_airport_id = cursor.fetchone()

        # Получаем arrival_airport_id по airport_name
        get_arrival_airport_id_query = 'SELECT airport_id FROM Airports WHERE airport_name = ?'
        cursor.execute(get_arrival_airport_id_query, (data['edit_arrival_airport'],))
        arrival_airport_id = cursor.fetchone()

        # Получаем plane_id по plane_name
        get_plane_id_query = 'SELECT plane_id FROM Planes WHERE plane_name = ?'
        cursor.execute(get_plane_id_query, (data['edit_plane'],))
        plane_id = cursor.fetchone()

        if airline_id and departure_airport_id and arrival_airport_id and plane_id:
            # Обновляем запись в базе данных
            update_query = '''
                UPDATE Flights
                SET 
                    departure_date=?,
                    departure_time=?,
                    arrival_date=?,
                    arrival_time=?,
                    flight_number=?,
                    airline_id=?, 
                    departure_airport_id=?,
                    arrival_airport_id=?,
                    plane_id=?
                WHERE flight_id=?
            '''
            cursor.execute(update_query, (
                data['edit_departure_date'],
                data['edit_departure_time'],
                data['edit_arrival_date'],
                data['edit_arrival_time'],
                data['edit_flight_number'],
                airline_id[0],
                departure_airport_id[0],
                arrival_airport_id[0],
                plane_id[0],
                flight_id
            ))

            connection.commit()
            return jsonify(success=True)
        else:
            return jsonify(success=False, error='Airline, Airport, or Plane not found')

    except Exception as e:
        # Обработка ошибок
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


@app.route('/add_flight', methods=['POST'])
def add_flight():
    try:
        # Получаем данные из запроса
        data = request.json

        # Получаем airline_id по airline_name
        get_airline_id_query = 'SELECT airline_id FROM Airlines WHERE airline_name = ?'
        cursor.execute(get_airline_id_query, (data['add_airline_f'],))
        airline_id = cursor.fetchone()

        # Получаем departure_airport_id по airport_name
        get_departure_airport_id_query = 'SELECT airport_id FROM Airports WHERE airport_name = ?'
        cursor.execute(get_departure_airport_id_query, (data['add_departure_airport'],))
        departure_airport_id = cursor.fetchone()

        # Получаем arrival_airport_id по airport_name
        get_arrival_airport_id_query = 'SELECT airport_id FROM Airports WHERE airport_name = ?'
        cursor.execute(get_arrival_airport_id_query, (data['add_arrival_airport'],))
        arrival_airport_id = cursor.fetchone()

        # Получаем plane_id по plane_name
        get_plane_id_query = 'SELECT plane_id FROM Planes WHERE plane_name = ?'
        cursor.execute(get_plane_id_query, (data['add_plane'],))
        plane_id = cursor.fetchone()

        if airline_id and departure_airport_id and arrival_airport_id and plane_id:
            # Добавляем новую запись в базу данных
            add_query = '''
                INSERT INTO Flights (
                    departure_date,
                    departure_time,
                    arrival_date,
                    arrival_time,
                    flight_number,
                    airline_id, 
                    departure_airport_id,
                    arrival_airport_id,
                    plane_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(add_query, (
                data['add_departure_date'],
                data['add_departure_time'],
                data['add_arrival_date'],
                data['add_arrival_time'],
                data['add_flight_number'],
                airline_id[0],
                departure_airport_id[0],
                arrival_airport_id[0],
                plane_id[0]
            ))

            connection.commit()
            return jsonify(success=True)
        else:
            return jsonify(success=False, error='Airline, Airport, or Plane not found')
    except Exception as e:
        # Обработка ошибок, например, логирование или возврат HTTP-статуса 500
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


@app.route('/delete_flight/<int:flight_id>', methods=['DELETE'])
def delete_flight(flight_id):
    try:
        # Реализуйте логику удаления рейса по идентификатору
        delete_query = 'DELETE FROM Flights WHERE flight_id = ?'
        cursor.execute(delete_query, (flight_id,))
        connection.commit()
        return jsonify(success=True)
    except Exception as e:
        # Обработка ошибок, например, логирование или возврат HTTP-статуса 500
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


@app.route('/analytics')
def analytics():
    # Подключение к базе данных
    connection = pyodbc.connect(conn_str)
    cursor = connection.cursor()

    # Выполнение запроса к базе данных для рейтинга городов
    cursor.execute('''
        SELECT
            a.city AS airport_city,
            COUNT(f.flight_id) AS flight_count
        FROM
            Flights f
        JOIN
            Airports a ON f.departure_airport_id = a.airport_id
        GROUP BY
            a.city
        ORDER BY
            flight_count DESC;
    ''')
    rows_airports = cursor.fetchall()

    # Создание DataFrame из данных для рейтинга городов
    data_airports = {
        'Города': [row.airport_city for row in rows_airports],
        'Количество рейсов': [row.flight_count for row in rows_airports]
    }

    # Создание графика для рейтинга городов
    fig_airports = px.bar(data_airports, x='Города', y='Количество рейсов', title='Рейтинг популярности стран',
                          color='Количество рейсов', color_discrete_sequence=['SlateBlue'])

    # Выполнение запроса к базе данных для рейтинга авиакомпаний
    cursor.execute('''
        SELECT
            a.airline_name AS airline_name,
            COUNT(f.flight_id) AS flight_count
        FROM
            Flights f
        JOIN
            Airlines a ON f.airline_id = a.airline_id
        GROUP BY
            a.airline_name
        ORDER BY
            flight_count DESC;
    ''')
    rows_airlines = cursor.fetchall()

    # Создание DataFrame из данных для рейтинга авиакомпаний
    data_airlines = {
        'Авиакомпании': [row.airline_name for row in rows_airlines],
        'Количество рейсов': [row.flight_count for row in rows_airlines]
    }

    # Создание графика для рейтинга авиакомпаний
    fig_airlines = px.bar(data_airlines, x='Авиакомпании', y='Количество рейсов', title='Рейтинг авиакомпаний',
                          color='Количество рейсов', color_discrete_sequence=['Chocolate'])

    # Выполнение запроса к базе данных для графика спроса
    cursor.execute('''
        SELECT
            a.airline_name AS airline_name,
            SUM(p.economy_seats_occupied + p.business_seats_occupied + p.first_class_seats_occupied + p.comfort_class_seats_occupied) AS total_seats_occupied
        FROM
            Flights f
        JOIN
            Airlines a ON f.airline_id = a.airline_id
        JOIN
            Planes p ON f.plane_id = p.plane_id
        GROUP BY
            a.airline_name
        ORDER BY
            total_seats_occupied DESC;
    ''')
    rows_demand = cursor.fetchall()

    # Создание DataFrame из данных для графика спроса
    data_demand = {
        'Авиакомпании': [row.airline_name for row in rows_demand],
        'Количество проданных билетов': [row.total_seats_occupied for row in rows_demand]
    }

    # Создание графика для графика спроса
    fig_demand = px.bar(data_demand, x='Авиакомпании', y='Количество проданных билетов', title='Спрос на авиабилеты',
                        color='Количество проданных билетов', color_discrete_sequence=['LightSkyBlue'])

    # Выполнение запроса к базе данных для истории покупки билетов
    cursor.execute('''
            SELECT
                purchase_date,
                COUNT(history_id) AS tickets_purchased
            FROM
                TicketPurchaseHistory
            GROUP BY
                purchase_date
            ORDER BY
                purchase_date;
        ''')
    rows_purchase_history = cursor.fetchall()

    # Проверка, что есть данные для обучения модели
    if len(rows_purchase_history) < 2:
        return "Недостаточно данных для построения прогноза"

    # Создание DataFrame из данных истории покупки билетов
    data_purchase_history = {
        'ds': [row.purchase_date for row in rows_purchase_history],
        'y': [row.tickets_purchased for row in rows_purchase_history]
    }

    # Создание DataFrame для прогноза
    df_purchase_history = pd.DataFrame(data_purchase_history)

    # Преобразование 'ds' в формат даты, если он еще не в этом формате
    df_purchase_history['ds'] = pd.to_datetime(df_purchase_history['ds'])

    # Разделение данных на тренировочный и тестовый набор
    train = df_purchase_history[:-3]  # Исключаем последние 30 дней для тестирования
    test = df_purchase_history[-3:]

    # Простой прогноз - линейный тренд
    x_train = np.arange(len(train))
    x_test = np.arange(len(train), len(train) + len(test))

    # Подгонка линейной модели
    model = LinearRegression()
    model.fit(x_train.reshape(-1, 1), train['y'])
    linear_trend = model.predict(x_test.reshape(-1, 1))

    # Создание графика
    fig_forecast = go.Figure()
    fig_forecast.add_trace(go.Scatter(x=train['ds'], y=train['y'], mode='lines', name='Фактические данные'))
    fig_forecast.add_trace(go.Scatter(x=test['ds'], y=test['y'], mode='lines', name='Тестовые данные'))
    fig_forecast.add_trace(go.Scatter(x=test['ds'], y=linear_trend, mode='lines', name='Прогноз (линейный тренд)'))
    fig_forecast.update_layout(title='Прогноз покупки билетов',
                               xaxis_title='Дата',
                               yaxis_title='Количество билетов')

    # Преобразование графиков в HTML
    plot_html_airports = fig_airports.to_html(full_html=False)
    plot_html_airlines = fig_airlines.to_html(full_html=False)
    plot_html_demand = fig_demand.to_html(full_html=False)
    # Преобразование графика в HTML
    plot_html_forecast = fig_forecast.to_html(full_html=False)


    # Закрытие соединения с базой данных
    cursor.close()
    connection.close()

    return render_template('analytics.html', plot_html_airports=plot_html_airports,
                           plot_html_airlines=plot_html_airlines, plot_html_demand=plot_html_demand, plot_html_forecast=plot_html_forecast)


# Класс для обработки типа Decimal, date и time при сериализации в JSON
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        elif isinstance(o, (date, time)):  # Используем кортеж для проверки, т.к. time также импортирован из datetime
            return o.isoformat()
        return super(CustomJSONEncoder, self).default(o)


# Маршрут для скачивания JSON файла для всей базы данных
@app.route('/download_entire_database_json')
def download_entire_database_json():
    filename = 'entire_database_data.json'

    # Ваш SQL-запрос для объединения данных из всех таблиц
    sql_queries = [
        "SELECT * FROM Airlines",
        "SELECT * FROM Airports",
        "SELECT * FROM Planes",
        "SELECT * FROM Flights",
        "SELECT * FROM Users",
        "SELECT * FROM Passengers",
        "SELECT * FROM Tickets",
        "SELECT * FROM TicketPurchaseHistory",
    ]

    # Подключаемся к базе данных и выполняем SQL-запросы
    connection = pyodbc.connect(conn_str)
    cursor = connection.cursor()

    data_from_db = []

    for sql_query in sql_queries:
        cursor.execute(sql_query)
        columns = [column[0] for column in cursor.description]
        data_from_db.extend([dict(zip(columns, row)) for row in cursor.fetchall()])

    # Закрываем соединение
    connection.close()

    # Создаем JSON файл с данными
    with open(filename, 'w') as file:
        json.dump(data_from_db, file, cls=CustomJSONEncoder)

    # Отправляем файл для скачивания
    return send_file(filename, as_attachment=True)


def insert_data(table_name, data):
    connection = pyodbc.connect(conn_str)
    cursor = connection.cursor()

    # Получаем информацию о столбцах таблицы
    cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' AND COLUMNPROPERTY(object_id(TABLE_NAME), COLUMN_NAME, 'IsIdentity') != 1")
    non_identity_columns = [column[0] for column in cursor.fetchall()]

    # Если data - это список, используем его, в противном случае создаем список из одного объекта
    data_list = data if isinstance(data, list) else [data]

    # Проверяем, есть ли все необходимые ключи в данных
    required_keys = set(non_identity_columns)
    for row in data_list:
        if not required_keys.issubset(row.keys()):
            connection.close()
            return f"Пропущен импорт в таблицу '{table_name}', так как не все необходимые ключи присутствуют в структуре данных."

    # Формируем строку SQL-запроса для вставки данных
    columns_without_identity = ', '.join(non_identity_columns)
    values_placeholder = ', '.join(['?' for _ in range(len(non_identity_columns))])
    sql_query = f"INSERT INTO {table_name} ({columns_without_identity}) VALUES ({values_placeholder})"

    try:
        # Вставляем данные в таблицу
        for row in data_list:
            # Передаем только значения, соответствующие не-identity столбцам
            values = [row[column] for column in non_identity_columns]

            # Выполняем запрос
            cursor.execute(sql_query, values)

        connection.commit()
        return f"Данные успешно импортированы в таблицу '{table_name}'."
    except Exception as e:
        connection.rollback()
        return f"Ошибка импорта данных в таблицу '{table_name}': {str(e)}"
    finally:
        connection.close()


def is_valid_json_data(json_data):
    if not isinstance(json_data, list) or not json_data:
        return False

    # Проверяем, что первый элемент является словарем
    if isinstance(json_data[0], dict):
        # Возвращаем True, если 'airline_id' присутствует в первом словаре
        return 'airline_id' in json_data[0]

    return False


@app.route('/import_data', methods=['POST'])
def import_data():
    # Получаем файл из формы
    uploaded_file = request.files['file']

    try:
        # Чтение данных из JSON-файла
        json_data = json.load(uploaded_file) if uploaded_file else None
    except json.JSONDecodeError as e:
        return f"Ошибка декодирования JSON: {str(e)}"

    # Ожидаемые ключи в данных
    expected_keys = ['airline_id']

    # Проверяем, есть ли данные для импорта
    if json_data is None or not is_valid_json_data(json_data):
        return "Отсутствуют или некорректные данные для импорта в базу данных."

    # Импорт данных в каждую таблицу
    for table_name in ['Airlines', 'Airports', 'Planes', 'Flights', 'Users', 'Passengers', 'Tickets', 'TicketPurchaseHistory']:
        result = insert_data(table_name, json_data)

    return "Данные успешно импортированы в базу данных."


@app.route('/importjson')
def importjson():
    return render_template('importjson.html')


if __name__ == '__main__':
    app.run(debug=True)

