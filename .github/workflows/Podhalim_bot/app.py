from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import mysql.connector
import os
import sys
import random
import secrets
import hashlib
import string
import matplotlib.pyplot as plt
import io
import base64
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')

# База данных
CONFIG = {
    'user': 'j1007852',
    'password': 'el|N#2}-F8',
    'host': 'srv201-h-st.jino.ru',
    'database': 'j1007852_13423'
}


# _________________________________________________________________________________

# Создает таблицу для хранения характеристик (если такая НЕ существует)
def create_table():
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS характеристики (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),  -- Новый столбец для имени
                strength INT,
                constitution INT,
                dexterity INT,
                intelligence INT,
                wisdom INT,
                charisma INT
            )
        ''')
        conn.commit()
        print("Таблица 'характеристики' создана или уже существует.")
    except mysql.connector.Error as err:
        print(f"Ошибка при создании таблицы: {err}")
    finally:
        if conn:
            cursor.close()
            conn.close()


# Создает таблицу logs (если такой НЕ существует)
def create_logs_table():
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor()
        cursor.execute('''
           CREATE TABLE IF NOT EXISTS logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                username VARCHAR(255),
                command VARCHAR(255) NOT NULL,
                timestamp DATETIME NOT NULL
            )
        ''')
        conn.commit()
        print("Таблица 'logs' создана или уже существует.")
    except mysql.connector.Error as err:
        print(f"Ошибка при создании таблицы 'logs': {err}")
    finally:
        if conn:
            cursor.close()
            conn.close()


# Создает таблицу flaskusers (если такой НЕ существует)
def create_flaskusers_table():
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flaskusers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                password VARCHAR(255) NOT NULL,
                salt VARCHAR(255) NOT NULL,
                role INT DEFAULT 0
            )
        ''')
        conn.commit()
        print("Таблица 'flaskusers' создана или уже существует.")
    except mysql.connector.Error as err:
        print(f"Ошибка при создании таблицы 'flaskusers': {err}")
    finally:
        if conn:
            cursor.close()
            conn.close()


# Создание пользователя
def create_user(username, password, role=0):  # Добавлен параметр role
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor()
        salt, hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO flaskusers (username, password, salt, role) VALUES (%s, %s, %s, %s)",
            (username, hashed_password, salt, role)
        )
        conn.commit()
        print(f"Пользователь '{username}' создан с ролью {role}.")
        return True
    except mysql.connector.Error as err:
        print(f"Ошибка при создании пользователя: {err}")
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()


# Функция для создания графика
def create_plot():
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT command, COUNT(*) as count FROM logs GROUP BY command")
        data = cursor.fetchall()

        commands = [row['command'] for row in data]
        counts = [row['count'] for row in data]

        plt.figure(figsize=(8, 6))
        plt.bar(commands, counts)
        plt.xlabel('Command')
        plt.ylabel('Count')
        plt.title('Usage of Commands')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png')
        img_buf.seek(0)
        img_data = base64.b64encode(img_buf.read()).decode('utf-8')
        plt.close()  # Закрываем figure, чтобы не было утечки памяти
        return img_data
    except mysql.connector.Error as err:
        print(f"Ошибка при создании графика: {err}")
        return None
    finally:
        if conn:
             cursor.close()
             conn.close()


# Сохраняет в БД значения характеристик
def save_specifications(name, strength, constitution, dexterity, intelligence, wisdom, charisma):
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor()
        query = '''
            INSERT INTO характеристики (name, strength, constitution, dexterity, intelligence, wisdom, charisma)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(query, (name, strength, constitution, dexterity, intelligence, wisdom, charisma))
        conn.commit()
        print("Характеристики сохранены в базе данных.")
    except mysql.connector.Error as err:
        print(f"Ошибка при сохранении характеристик: {err}")
    finally:
        if conn:
            cursor.close()
            conn.close()


# Добавлена функция для сохранения логов
def save_log(user_id, username, command):
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs (user_id, username, command) VALUES (%s, %s, %s)",
            (user_id, username, command)
        )
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Ошибка при сохранении лога: {err}")
    finally:
        if conn:
            cursor.close()
            conn.close()


# Хеширование паролей
def hash_password(password):
    salt = secrets.token_hex(16)
    salted_password = salt + password
    hashed_password = hashlib.sha256(salted_password.encode()).hexdigest()
    return salt, hashed_password


def verify_password(stored_salt, stored_hash, password):
    salted_password = stored_salt + password
    hashed_password = hashlib.sha256(salted_password.encode()).hexdigest()
    return hashed_password == stored_hash


# Получает характеристики по ID.
def get_specifications(spec_id):
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM характеристики WHERE id = %s', (spec_id,))
        return cursor.fetchone()  # Возвращает одну запись
    except mysql.connector.Error as err:
        print(f"Ошибка при получении характеристик: {err}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()


# Возвращает последний вставленный ID из таблицы характеристик.
def get_last_inserted_id():
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(id) FROM характеристики')
        last_id = cursor.fetchone()[0]
        return last_id
    except mysql.connector.Error as err:
        print(f"Ошибка при получении последнего ID: {err}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()


# Возвращает случайное имя из файла Names.txt.
def get_random_name():
    with open("Names.txt", "r") as file:
        names = file.readlines()
    return random.choice(names).strip()


# Генерирует случайные значения для характеристик
def get_random_specifications():
    strength = random.randint(10, 99)
    constitution = random.randint(10, 99)
    dexterity = random.randint(10, 99)
    intelligence = random.randint(10, 99)
    wisdom = random.randint(10, 99)
    charisma = random.randint(10, 99)
    return strength, constitution, dexterity, intelligence, wisdom, charisma


# Получение данных из таблицы logs
def get_logs_data(sort_by, order, user_id=None, start_date=None, end_date=None):
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM logs WHERE 1=1"
        params = []

        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)
        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date)
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date)

        query += f" ORDER BY {sort_by} {order}"
        cursor.execute(query, params)
        logs = cursor.fetchall()
        return logs

    except mysql.connector.Error as err:
        print(f"Ошибка при получении данных: {err}")
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()


def get_user_by_username(username):
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM flaskusers WHERE username = %s", (username,))
        user = cursor.fetchone()
        return user
    except mysql.connector.Error as err:
        print(f"Ошибка при получении пользователя: {err}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()


def get_all_users():
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT user_id, username FROM logs")
        users = cursor.fetchall()
        return users
    except mysql.connector.Error as err:
        print(f"Ошибка при получении пользователей: {err}")
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()


def get_all_characteristics(sort_by='id', order='ASC'):
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = f"SELECT * FROM характеристики ORDER BY {sort_by} {order}"
        cursor.execute(query)
        characteristics = cursor.fetchall()
        return characteristics
    except mysql.connector.Error as err:
        print(f"Ошибка при получении характеристик: {err}")
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()


# Удаляет строчку из таблицы "характеристики"
def delete_characteristic(char_id):
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM характеристики WHERE id = %s", (char_id,))
        conn.commit()
        print(f"Характеристика с ID {char_id} была удалена")
        return True
    except mysql.connector.Error as err:
        print(f"Ошибка при удалении характеристики: {err}")
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()


def update_characteristic(char_id, name, strength, constitution, dexterity, intelligence, wisdom, charisma):
    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE характеристики SET name=%s, strength=%s, constitution=%s, dexterity=%s, intelligence=%s, wisdom=%s, charisma=%s WHERE id=%s",
            (name, strength, constitution, dexterity, intelligence, wisdom, charisma, char_id)
        )
        conn.commit()
        print(f"Характеристика с ID {char_id} была обновлена")
        return True
    except mysql.connector.Error as err:
        print(f"Ошибка при обновлении характеристики: {err}")
        return False
    finally:
         if conn:
            cursor.close()
            conn.close()


def is_admin():
    return session.get('user_role') == 1


def is_editor():
    return session.get('user_role') == 2

# def is_regular_user():
#     return session.get('user_role') == 0


# _________________________________________________________________________________


@app.route('/')
def index():
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'ASC')
    logs = get_logs_data(sort_by, order)
    return render_template('index.html', logs=logs, sort_by=sort_by, order=order, is_admin=is_admin(), is_editor = is_editor())


# Обработчик команды /submit
@app.route('/submit', methods=['POST'])
def submit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    name = get_random_name()
    strength, constitution, dexterity, intelligence, wisdom, charisma = get_random_specifications()
    save_specifications(name, strength, constitution, dexterity, intelligence, wisdom, charisma)
    return redirect(url_for('results'))


# Обработчик команды для получения последнего вставленного ID
@app.route('/results')
def results():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    last_id = get_last_inserted_id()
    TakenSpecifications = get_specifications(last_id)
    return render_template('results.html', specifications=TakenSpecifications)


# Обработчик команды /random_character
@app.route('/random_character', methods=['GET'])
def random_character():
    if 'user_id' not in session:
        return jsonify({'message': 'Вы не авторизованы'}), 401

    try:
        conn = mysql.connector.connect(**CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM характеристики ORDER BY RAND() LIMIT 1')
        result = cursor.fetchone()
        if result:
            return jsonify(result)
        else:
            return jsonify({'message': 'Нет характеристик в базе данных.'}), 404
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()


@app.route('/statistic', methods=['GET'])
def statistic():
    if not is_admin():
        return "Нет доступа к статистике", 403

    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'ASC')
    user_id = request.args.get('user_id', type=int)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    start_date = None
    end_date = None

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            return "Неверный формат начальной даты", 400
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            return "Неверный формат конечной даты", 400

    logs = get_logs_data(sort_by, order, user_id, start_date, end_date)
    users = get_all_users()
    log_data_for_chart = {}  # Для данных графика

    for log in logs:
        date = log['timestamp'].strftime('%Y-%m-%d')
        if date not in log_data_for_chart:
            log_data_for_chart[date] = 0
        log_data_for_chart[date] += 1


    log_data_for_chart_json = json.dumps(list(log_data_for_chart.items()))

    return render_template('statistic.html', logs=logs, users=users, sort_by=sort_by, order=order,
                           user_id=user_id, start_date=start_date_str, end_date=end_date_str, log_data_for_chart_json=log_data_for_chart_json)


@app.route('/characteristics', methods=['GET','POST'])
def characteristics():
    if not is_admin() and not is_editor():
        return "Нет доступа к характеристикам", 403

    if request.method == 'POST':
        action = request.form.get('action')
        char_id = request.form.get('char_id', type=int)

        if action == 'delete' and char_id:
            if delete_characteristic(char_id):
                return redirect(url_for('characteristics'))  # refresh page

        if action == 'update' and char_id:
            name = request.form.get('name')
            strength = request.form.get('strength', type=int)
            constitution = request.form.get('constitution', type=int)
            dexterity = request.form.get('dexterity', type=int)
            intelligence = request.form.get('intelligence', type=int)
            wisdom = request.form.get('wisdom', type=int)
            charisma = request.form.get('charisma', type=int)

            if all([name, strength, constitution, dexterity, intelligence, wisdom, charisma]):
              if update_characteristic(char_id, name, strength, constitution, dexterity, intelligence, wisdom, charisma):
                return redirect(url_for('characteristics'))


    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'ASC')
    characteristics = get_all_characteristics(sort_by, order)
    return render_template('characteristics.html', characteristics=characteristics, sort_by=sort_by, order=order)


# --- Авторизация ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)

        if user and verify_password(user['salt'], user['password'], password):
           session['user_id'] = user['id']
           session['user_role'] = user['role']
           print(f"Пользователь {username} зашел в систему с ролью {user['role']}")
           return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Неправильное имя пользователя или пароль")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if create_user(username, password):
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error="Ошибка при создании пользователя.")
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    return redirect(url_for('index'))


# Запуск
if __name__ == '__main__':
    create_table()
    create_logs_table()
    create_flaskusers_table()
    app.run(debug=True)