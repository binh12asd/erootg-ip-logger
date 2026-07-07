from flask import Flask, request, render_template, send_file, jsonify, session, redirect, url_for
import sqlite3
import json
import os
from datetime import datetime
from functools import lru_cache
import requests
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'erootg_secret_key_2025'  # Cần cho session

# ====== CẤU HÌNH ======
DB_PATH = "erootg.db"
ADMIN_PASSWORD = "EROTG1234"  # Mật khẩu đăng nhập

# ====== PHẦN KIỂM TRA ĐĂNG NHẬP ======
def is_logged_in():
    return session.get('logged_in', False)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('view_logs'))
        else:
            return render_template('login.html', error='Sai mật khẩu!')
    return render_template('login.html', error=None)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login_page'))

# ====== CÁC ROUTE KHÁC (GIỮ NGUYÊN) ======
# ... (toàn bộ code cũ từ đây, chỉ sửa route /logs)
