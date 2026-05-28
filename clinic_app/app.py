import os
import json
from datetime import datetime, date, time, timedelta
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, Patient, Doctor, Service, ScheduleSlot, Appointment, MedicalRecord, Visit, Document, Specialization

app = Flask(__name__)
app.config.from_object(Config)

# Инициализация плагинов
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth_page'
login_manager.login_message = "Пожалуйста, авторизуйтесь для доступа к этой странице."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Создание папки для загрузок и фиктивного файла заключения при запуске
def init_directories():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    dummy_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'visit_conclusion_1.pdf')
    if not os.path.exists(dummy_pdf_path):
        with open(dummy_pdf_path, 'w', encoding='utf-8') as f:
            f.write("ПОЛИКЛИНИКА нового поколения\n\nЗАКЛЮЧЕНИЕ ТЕРАПЕВТА\n\n"
                    "Пациент: Амплеенков Даниил Олегович\n"
                    "Диагноз: Острый фарингит (ОРВИ легкого течения)\n"
                    "Рекомендации: Обильное теплое питье, витамины, полоскание горла.")

# -------------------------------------------------------------
# 1. Публичные маршруты
# -------------------------------------------------------------

@app.route('/')
def index():
    services = Service.query.all()
    doctors = Doctor.query.all()
    return render_template('index.html', services=services, doctors=doctors)

@app.route('/auth')
def auth_page():
    if current_user.is_authenticated:
        if current_user.role == 'patient':
            return redirect(url_for('patient_cabinet'))
        elif current_user.role == 'doctor':
            return redirect(url_for('doctor_cabinet'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin_panel'))
    return render_template('auth.html')

# -------------------------------------------------------------
# 2. Логика авторизации
# -------------------------------------------------------------



@app.route('/login', methods=['POST'])
def login_route():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        flash('Неверный адрес электронной почты или пароль.', 'error')
        return redirect(url_for('auth_page'))
        
    login_user(user)
    flash(f'Добро пожаловать в систему!', 'success')
    
    if user.role == 'patient':
        return redirect(url_for('patient_cabinet'))
    elif user.role == 'doctor':
        return redirect(url_for('doctor_cabinet'))
    elif user.role == 'admin':
        return redirect(url_for('admin_panel'))
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register_route():
    full_name = request.form.get('full_name')
    birth_date_str = request.form.get('birth_date')
    phone = request.form.get('phone')
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Валидация уникальности почты
    if User.query.filter_by(email=email).first():
        flash('Пользователь с таким Email уже зарегистрирован.', 'error')
        return redirect(url_for('auth_page'))
        
    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        
        # 1. Создаем пользователя
        new_user = User(email=email, role='patient')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        # 2. Создаем профиль пациента
        new_patient = Patient(
            user_id=new_user.id,
            full_name=full_name,
            birth_date=birth_date,
            phone=phone
        )
        db.session.add(new_patient)
        db.session.commit()
        
        # 3. Создаем медкарту (генерация уникального номера)
        pat_count = Patient.query.count()
        card_number = f"МК-2026-{pat_count:04d}"
        new_record = MedicalRecord(
            patient_id=new_patient.id,
            card_number=card_number,
            blood_type='Не указана',
            rh_factor='Rh+',
            allergies='Не выявлено',
            chronic_diseases='Не зарегистрировано'
        )
        db.session.add(new_record)
        db.session.commit()
        
        login_user(new_user)
        flash('Вы успешно зарегистрировались! Добро пожаловать.', 'success')
        return redirect(url_for('patient_cabinet'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка регистрации: {str(e)}', 'error')
        return redirect(url_for('auth_page'))

@app.route('/logout')
@login_required
def logout_route():
    logout_user()
    flash('Вы вышли из личного кабинета.', 'info')
    return redirect(url_for('index'))

# -------------------------------------------------------------
# 3. Кабинет пациента и Запись на приём
# -------------------------------------------------------------

@app.route('/cabinet')
@login_required
def patient_cabinet():
    if current_user.role != 'patient':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
        
    patient = current_user.patient
    # Ближайшая активная запись (первая из списка будущих)
    upcoming_appt = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.status != 'completed',
        Appointment.status != 'cancelled'
    ).join(ScheduleSlot).filter(ScheduleSlot.date >= date.today()).order_by(ScheduleSlot.date, ScheduleSlot.start_time).first()
    
    # История приемов
    past_appts = Appointment.query.filter_by(patient_id=patient.id, status='completed')\
        .join(ScheduleSlot).order_by(ScheduleSlot.date.desc(), ScheduleSlot.start_time.desc()).all()
        
    record = patient.medical_record
    documents = Document.query.filter_by(patient_id=patient.id).all()
    
    return render_template('patient_cabinet.html', 
                           upcoming_appt=upcoming_appt, 
                           past_appts=past_appts, 
                           record=record, 
                           documents=documents)

@app.route('/booking')
@login_required
def booking_page():
    if current_user.role != 'patient':
        flash('Запись доступна только пациентам.', 'error')
        return redirect(url_for('index'))
        
    doctors = Doctor.query.all()
    services = Service.query.all()
    
    # Собираем слоты на сегодня и будущие даты
    slots = ScheduleSlot.query.filter(ScheduleSlot.date >= date.today()).all()
    
    # Сериализуем слоты в JSON для фильтрации на стороне клиента
    slots_list = []
    for s in slots:
        slots_list.append({
            'id': s.id,
            'doctor_id': s.doctor_id,
            'date': s.date.strftime('%Y-%m-%d'),
            'time': s.start_time.strftime('%H:%M'),
            'status': s.status
        })
        
    return render_template('booking.html', 
                           doctors=doctors, 
                           services=services, 
                           today=date.today().strftime('%Y-%m-%d'),
                           slots_json=json.dumps(slots_list))

@app.route('/confirm_booking', methods=['POST'])
@login_required
def confirm_booking():
    slot_id = request.form.get('slot_id')
    doctor_id = request.form.get('doctor_id')
    service_id = request.form.get('service_id')
    
    slot = ScheduleSlot.query.get(slot_id)
    if not slot or slot.status != 'free':
        flash('Выбранный временной слот уже занят. Пожалуйста, выберите другое время.', 'error')
        return redirect(url_for('booking_page'))
        
    # Защита от записи в прошлое (дата и время)
    slot_datetime = datetime.combine(slot.date, slot.start_time)
    if slot_datetime < datetime.now():
        flash('Выбранное время приема уже прошло. Невозможно записаться в прошлое.', 'error')
        return redirect(url_for('booking_page'))
        
    try:
        # Создаем запись на прием
        appt = Appointment(
            patient_id=current_user.patient.id,
            doctor_id=int(doctor_id),
            service_id=int(service_id),
            slot_id=int(slot_id),
            status='confirmed'
        )
        db.session.add(appt)
        
        # Меняем статус слота
        slot.status = 'booked'
        db.session.commit()
        
        flash('Вы успешно записались на приём! Подробности в Вашем личном кабинете.', 'success')
        return redirect(url_for('patient_cabinet'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при подтверждении записи: {str(e)}', 'error')
        return redirect(url_for('booking_page'))

@app.route('/cancel_booking/<int:appt_id>', methods=['POST'])
@login_required
def cancel_booking(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    
    # Права доступа
    if appt.patient_id != current_user.patient.id:
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('patient_cabinet'))
        
    # Защита: нельзя отменить уже завершенный прием
    if appt.status == 'completed':
        flash('Нельзя отменить уже завершенный прием.', 'error')
        return redirect(url_for('patient_cabinet'))
        
    try:
        slot = appt.slot
        if slot:
            slot.status = 'free'
            
        db.session.delete(appt)
        db.session.commit()
        
        flash('Запись на приём успешно отменена.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка отмены записи: {str(e)}', 'error')
        
    return redirect(url_for('patient_cabinet'))

@app.route('/download/<int:doc_id>')
@login_required
def download_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    
    # Права доступа (скачивать могут только сам пациент, его врач или админ)
    if current_user.role == 'patient' and doc.patient_id != current_user.patient.id:
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
        
    # Если передан параметр preview=1, открываем файл inline в браузере
    preview = request.args.get('preview', '0') == '1'
    as_attachment = not preview
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], doc.file_path, as_attachment=as_attachment)

# -------------------------------------------------------------
# 4. Кабинет врача
# -------------------------------------------------------------

@app.route('/doctor')
@login_required
def doctor_cabinet():
    if current_user.role != 'doctor':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
        
    doctor = current_user.doctor
    
    # Режим просмотра: 'day' (конкретный день) или 'week' (вся неделя)
    view_type = request.args.get('view', 'day')
    selected_date_str = request.args.get('date')
    
    today = date.today()
    
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today
        
    prev_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)
    week_end = today + timedelta(days=7)
    
    if view_type == 'week':
        # Записи на ближайшие 7 дней (включая сегодня)
        appts = Appointment.query.join(ScheduleSlot).filter(
            Appointment.doctor_id == doctor.id,
            ScheduleSlot.date >= today,
            ScheduleSlot.date <= week_end
        ).order_by(ScheduleSlot.date, ScheduleSlot.start_time).all()
    else:
        # Записи на конкретный день
        appts = Appointment.query.join(ScheduleSlot).filter(
            Appointment.doctor_id == doctor.id,
            ScheduleSlot.date == selected_date
        ).order_by(ScheduleSlot.start_time).all()
    
    # Проверяем, передан ли активный приём
    active_appt_id = request.args.get('active_appt_id')
    active_appt = None
    record = None
    past_visits = []
    if active_appt_id:
        active_appt = Appointment.query.get(active_appt_id)
        if not active_appt or active_appt.doctor_id != doctor.id:
            flash('Приём не найден или принадлежит другому врачу.', 'error')
            return redirect(url_for('doctor_cabinet', view=view_type, date=selected_date_str))
        
        # Получаем данные медкарты и историю прошлых визитов пациента
        record = active_appt.patient.medical_record
        past_visits = Visit.query.join(Appointment).filter(
            Appointment.patient_id == active_appt.patient.id,
            Appointment.status == 'completed'
        ).order_by(Visit.created_at.desc()).all()
            
    return render_template(
        'doctor_cabinet.html',
        appts=appts,
        active_appt=active_appt,
        record=record,
        past_visits=past_visits,
        view_type=view_type,
        selected_date=selected_date,
        prev_date=prev_date,
        next_date=next_date,
        today=today,
        week_end=week_end
    )

@app.route('/doctor/save_visit', methods=['POST'])
@login_required
def save_visit():
    if current_user.role != 'doctor':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
        
    appt_id = request.form.get('appointment_id')
    complaints = request.form.get('complaints')
    diagnosis = request.form.get('diagnosis')
    recommendations = request.form.get('recommendations')
    
    appt = Appointment.query.get_or_404(appt_id)
    if appt.doctor_id != current_user.doctor.id:
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('doctor_cabinet'))
        
    # Защита: нельзя повторно оформить уже завершенный прием
    if appt.status == 'completed':
        flash('Этот прием уже успешно завершен и занесен в историю.', 'error')
        return redirect(url_for('doctor_cabinet'))
        
    try:
        # 1. Создаем результат посещения (Visit)
        record = appt.patient.medical_record
        visit = Visit(
            record_id=record.id,
            appointment_id=appt.id,
            complaints=complaints,
            diagnosis=diagnosis,
            recommendations=recommendations
        )
        db.session.add(visit)
        
        # 2. Обрабатываем прикрепленный файл
        file = request.files.get('document_file')
        file_type = request.form.get('file_type')
        
        if file and file.filename != '':
            # Безопасное сохранение
            filename = f"pat_{appt.patient.id}_visit_{appt.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            new_doc = Document(
                patient_id=appt.patient.id,
                visit=visit,
                file_path=filename,
                file_type=file_type
            )
            db.session.add(new_doc)
            
        # 3. Меняем статус приёма на completed
        appt.status = 'completed'
        db.session.commit()
        
        flash(f'Приём пациента {appt.patient.full_name} успешно завершен и занесен в историю.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при сохранении заключения приёма: {str(e)}', 'error')
        
    return redirect(url_for('doctor_cabinet'))

# -------------------------------------------------------------
# 5. Панель администратора
# -------------------------------------------------------------

@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
        
    doctors = Doctor.query.all()
    # Список всех слотов на сегодня и будущее
    slots = ScheduleSlot.query.filter(ScheduleSlot.date >= date.today())\
        .order_by(ScheduleSlot.date, ScheduleSlot.start_time).all()
        
    return render_template('admin_panel.html', 
                           doctors=doctors, 
                           slots=slots, 
                           today=date.today().strftime('%Y-%m-%d'))

@app.route('/admin/add_slot', methods=['POST'])
@login_required
def add_slot():
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
        
    doctor_id = request.form.get('doctor_id')
    date_str = request.form.get('date')
    start_time_str = request.form.get('start_time')
    
    try:
        slot_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        # Вычисляем время окончания слота (+30 минут)
        end_time = (datetime.combine(slot_date, start_time) + timedelta(minutes=30)).time()
        
        # Проверяем наложение расписания
        existing = ScheduleSlot.query.filter_by(
            doctor_id=int(doctor_id), 
            date=slot_date, 
            start_time=start_time
        ).first()
        
        if existing:
            flash('Данный временной интервал для этого врача уже добавлен в расписание клиники.', 'error')
            return redirect(url_for('admin_panel'))
            
        new_slot = ScheduleSlot(
            doctor_id=int(doctor_id),
            date=slot_date,
            start_time=start_time,
            end_time=end_time,
            status='free'
        )
        db.session.add(new_slot)
        db.session.commit()
        
        flash('Временной интервал успешно добавлен в расписание клиники!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении интервала: {str(e)}', 'error')
        
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_slot/<int:slot_id>', methods=['POST'])
@login_required
def delete_slot(slot_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
        
    slot = ScheduleSlot.query.get_or_404(slot_id)
    if slot.status != 'free':
        flash('Невозможно удалить слот, на который уже записан пациент.', 'error')
        return redirect(url_for('admin_panel'))
        
    try:
        db.session.delete(slot)
        db.session.commit()
        flash('Временной интервал удален из расписания.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка удаления слота: {str(e)}', 'error')
        
    return redirect(url_for('admin_panel'))

# -------------------------------------------------------------
# 6. Административные CRUD маршруты для врачей, услуг и записей
# -------------------------------------------------------------

@app.route('/admin/doctors')
@login_required
def admin_doctors():
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
    doctors = Doctor.query.all()
    specializations = Specialization.query.all()
    return render_template('admin_doctors.html', doctors=doctors, specializations=specializations)

@app.route('/admin/doctors/add', methods=['POST'])
@login_required
def admin_add_doctor():
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
    full_name = request.form.get('full_name')
    specialization = request.form.get('specialization')
    email = request.form.get('email')
    password = request.form.get('password')
    cabinet = request.form.get('cabinet')

    if User.query.filter_by(email=email).first():
        flash('Пользователь с таким Email уже существует.', 'error')
        return redirect(url_for('admin_doctors'))

    try:
        # Создаем учетную запись с ролью doctor
        new_user = User(email=email, role='doctor')
        new_user.set_password(password) # Безопасное хеширование пароля
        db.session.add(new_user)
        db.session.commit()

        # Создаем профиль врача
        new_doctor = Doctor(
            user_id=new_user.id,
            full_name=full_name,
            specialization=specialization,
            cabinet=cabinet
        )
        db.session.add(new_doctor)
        db.session.commit()
        flash(f'Врач {full_name} успешно зарегистрирован в системе!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при регистрации врача: {str(e)}', 'error')

    return redirect(url_for('admin_doctors'))

@app.route('/admin/doctors/delete/<int:doctor_id>', methods=['POST'])
@login_required
def admin_delete_doctor(doctor_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
    doc = Doctor.query.get_or_404(doctor_id)
    if doc.appointments:
        flash('Невозможно удалить врача, так как к нему уже записаны пациенты.', 'error')
        return redirect(url_for('admin_doctors'))

    try:
        user = doc.user
        db.session.delete(doc)
        if user:
            db.session.delete(user)
        db.session.commit()
        flash('Профиль врача и его учетная запись успешно удалены.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении врача: {str(e)}', 'error')

    return redirect(url_for('admin_doctors'))

# -------------------------------------------------------------
# 5.5. Административные маршруты для управления категориями (специализациями)
# -------------------------------------------------------------

@app.route('/admin/specializations')
@login_required
def admin_specializations():
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
    
    specializations = Specialization.query.order_by(Specialization.name).all()
    
    # Собираем статистику о количестве врачей в каждой категории
    specs_with_counts = []
    for spec in specializations:
        doc_count = Doctor.query.filter_by(specialization=spec.name).count()
        specs_with_counts.append({
            'id': spec.id,
            'name': spec.name,
            'doc_count': doc_count
        })
        
    return render_template('admin_specializations.html', specializations=specs_with_counts)

@app.route('/admin/specializations/add', methods=['POST'])
@login_required
def admin_add_specialization():
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
        
    name = request.form.get('name', '').strip()
    if not name:
        flash('Название категории не может быть пустым.', 'error')
        return redirect(url_for('admin_specializations'))
        
    existing = Specialization.query.filter_by(name=name).first()
    if existing:
        flash('Такая категория уже зарегистрирована в системе.', 'error')
        return redirect(url_for('admin_specializations'))
        
    try:
        new_spec = Specialization(name=name)
        db.session.add(new_spec)
        db.session.commit()
        flash(f'Категория «{name}» успешно добавлена!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при создании категории: {str(e)}', 'error')
        
    return redirect(url_for('admin_specializations'))

@app.route('/admin/specializations/delete/<int:spec_id>', methods=['POST'])
@login_required
def admin_delete_specialization(spec_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
        
    spec = Specialization.query.get_or_404(spec_id)
    
    has_doctors = Doctor.query.filter_by(specialization=spec.name).first()
    if has_doctors:
        flash(f'Невозможно удалить категорию «{spec.name}», так как к ней привязаны практикующие врачи.', 'error')
        return redirect(url_for('admin_specializations'))
        
    try:
        db.session.delete(spec)
        db.session.commit()
        flash(f'Категория «{spec.name}» успешно удалена.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка удаления категории: {str(e)}', 'error')
        
    return redirect(url_for('admin_specializations'))

@app.route('/admin/doctors/change_password/<int:doctor_id>', methods=['POST'])
@login_required
def admin_change_doctor_password(doctor_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
        
    doc = Doctor.query.get_or_404(doctor_id)
    password = request.form.get('password')
    
    if not password or len(password) < 6:
        flash('Пароль должен состоять минимум из 6 символов.', 'error')
        return redirect(url_for('admin_doctors'))
        
    try:
        user = doc.user
        if user:
            user.set_password(password)
            db.session.commit()
            flash(f'Пароль для врача {doc.full_name} успешно изменен.', 'success')
        else:
            flash('Учетная запись врача не найдена.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при смене пароля: {str(e)}', 'error')
        
    return redirect(url_for('admin_doctors'))

@app.route('/admin/services')
@login_required
def admin_services():
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
    services = Service.query.all()
    return render_template('admin_services.html', services=services)

@app.route('/admin/services/add', methods=['POST'])
@login_required
def admin_add_service():
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
    title = request.form.get('title')
    price = request.form.get('price')
    duration_minutes = request.form.get('duration_minutes')
    description = request.form.get('description')

    try:
        new_service = Service(
            title=title,
            price=float(price),
            duration_minutes=int(duration_minutes),
            description=description
        )
        db.session.add(new_service)
        db.session.commit()
        flash('Медицинская услуга успешно создана!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка добавления услуги: {str(e)}', 'error')

    return redirect(url_for('admin_services'))

@app.route('/admin/services/edit/<int:service_id>', methods=['POST'])
@login_required
def admin_edit_service(service_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
    srv = Service.query.get_or_404(service_id)
    title = request.form.get('title')
    price = request.form.get('price')
    duration_minutes = request.form.get('duration_minutes')
    description = request.form.get('description')

    try:
        srv.title = title
        srv.price = float(price)
        srv.duration_minutes = int(duration_minutes)
        srv.description = description
        db.session.commit()
        flash('Услуга успешно обновлена!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка обновления услуги: {str(e)}', 'error')

    return redirect(url_for('admin_services'))

@app.route('/admin/services/delete/<int:service_id>', methods=['POST'])
@login_required
def admin_delete_service(service_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
    srv = Service.query.get_or_404(service_id)
    if srv.appointments:
        flash('Невозможно удалить услугу, так как по ней уже зарегистрированы приёмы.', 'error')
        return redirect(url_for('admin_services'))

    try:
        db.session.delete(srv)
        db.session.commit()
        flash('Медицинская услуга успешно удалена.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка удаления услуги: {str(e)}', 'error')

    return redirect(url_for('admin_services'))

@app.route('/admin/appointments')
@login_required
def admin_appointments():
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
    appts = Appointment.query.join(ScheduleSlot).order_by(ScheduleSlot.date.desc(), ScheduleSlot.start_time.desc()).all()
    return render_template('admin_appointments.html', appts=appts)

@app.route('/admin/appointments/confirm/<int:appt_id>', methods=['POST'])
@login_required
def admin_confirm_appointment(appt_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
    appt = Appointment.query.get_or_404(appt_id)
    try:
        appt.status = 'confirmed'
        db.session.commit()
        flash('Запись пациента успешно подтверждена!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка подтверждения записи: {str(e)}', 'error')

    return redirect(url_for('admin_appointments'))

@app.route('/admin/appointments/cancel/<int:appt_id>', methods=['POST'])
@login_required
def admin_cancel_appointment(appt_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('index'))
    appt = Appointment.query.get_or_404(appt_id)
    try:
        slot = appt.slot
        if slot:
            slot.status = 'free'
        db.session.delete(appt) # Удаляем саму запись, чтобы не нарушать unique constraint на slot_id!
        db.session.commit()
        flash('Запись пациента успешно отменена, временной интервал освобожден.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка отмены записи: {str(e)}', 'error')

    return redirect(url_for('admin_appointments'))

# -------------------------------------------------------------
# Инициализация и запуск приложения
# -------------------------------------------------------------

# Обработчик ошибок 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', content="<div class='text-center py-5'><h1 class='display-1 text-danger font-bold'>404</h1><h3>Страница не найдена</h3><p class='text-muted'>Запрашиваемый URL-адрес отсутствует на нашем сервере.</p><a href='/' class='btn btn-primary mt-3'>На главную страницу</a></div>"), 404

if __name__ == '__main__':
    # Автоматическое создание папок загрузки при запуске
    init_directories()
    
    # Запускаем Flask-сервер в режиме разработки
    app.run(host='0.0.0.0', debug=True, port=5000)
