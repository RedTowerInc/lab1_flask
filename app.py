from flask import Flask, render_template, request, redirect, url_for, flash
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import os
import requests
from config import RECAPTCHA_SITE_KEY, RECAPTCHA_SECRET_KEY, SECRET_KEY  # Импорт конфигурации

app = Flask(__name__)
app.secret_key = SECRET_KEY  # Используем секретный ключ из конфигурации

# Папка для загруженных изображений
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Создаем папку, если она не существует
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def verify_recaptcha(response_token):
    """
    Проверка reCAPTCHA.
    """
    data = {
        'secret': RECAPTCHA_SECRET_KEY,
        'response': response_token
    }
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
    result = response.json()
    return result.get('success', False)

def plot_color_distribution(image, filename):
    """
    Строит график распределения цветов для изображения.
    """
    img = np.array(image)
    colors = ('r', 'g', 'b')
    channel_ids = (0, 1, 2)

    plt.figure()
    for channel_id, color in zip(channel_ids, colors):
        histogram, _ = np.histogram(img[:, :, channel_id], bins=256, range=(0, 256))
        plt.plot(histogram, color=color)
    plt.title('Распределение цветов')
    plt.xlabel('Значение цвета')
    plt.ylabel('Количество пикселей')
    plt.savefig(filename)
    plt.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Проверка reCAPTCHA
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha_response):
            flash('Ошибка проверки reCAPTCHA. Пожалуйста, попробуйте снова.', 'error')
            return redirect(url_for('index'))

        # Получаем загруженный файл и угол поворота
        file = request.files['image']
        angle = int(request.form['angle'])

        if file and angle:
            # Сохраняем загруженный файл
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(image_path)

            # Открываем изображение и поворачиваем его
            image = Image.open(image_path)
            rotated_image = image.rotate(angle, expand=True)
            rotated_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'rotated_' + file.filename)
            rotated_image.save(rotated_image_path)

            # Строим графики распределения цветов
            original_plot_path = os.path.join(app.config['UPLOAD_FOLDER'], 'original_plot.png')
            rotated_plot_path = os.path.join(app.config['UPLOAD_FOLDER'], 'rotated_plot.png')
            plot_color_distribution(image, original_plot_path)
            plot_color_distribution(rotated_image, rotated_plot_path)

            return render_template('index.html',
                                   original_image=file.filename,
                                   rotated_image='rotated_' + file.filename,
                                   original_plot='original_plot.png',
                                   rotated_plot='rotated_plot.png',
                                   recaptcha_site_key=RECAPTCHA_SITE_KEY)

    return render_template('index.html', recaptcha_site_key=RECAPTCHA_SITE_KEY)

if __name__ == '__main__':
    app.run(debug=True)