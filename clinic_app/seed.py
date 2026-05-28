import os
from flask import Flask
from models import db, User, Patient, Doctor, Service, ScheduleSlot, Appointment, MedicalRecord, Visit, Document
from datetime import datetime, date, time, timedelta

def create_seed_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///clinic.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def seed_database():
    app = create_seed_app()
    with app.app_context():
        print("Инициализация базы данных...")
        # Создаем таблицы, если они еще не существуют
        db.create_all()
        print("Таблицы успешно созданы/проверены.")
        
        # Проверяем, есть ли уже пользователи в базе данных
        try:
            if User.query.first() is not None:
                print("База данных уже содержит данные, пропускаем наполнение.")
                return
        except Exception as e:
            print(f"Ошибка при проверке наличия данных (возможно, таблицы не готовы): {e}")
            # Пытаемся создать на всякий случай
            db.create_all()
        
        # 1. Создание услуг
        print("Создание услуг...")
        s_therapy = Service(
            title='Прием терапевта',
            description='Первичный прием, осмотр, измерение давления, постановка предварительного диагноза и направление к узким специалистам.',
            price=1500.00,
            duration_minutes=30
        )
        s_cardiology = Service(
            title='Консультация кардиолога',
            description='Специализированный прием врача-кардиолога, расшифровка ЭКГ, выдача рекомендаций при гипертонии и ИБС.',
            price=2200.00,
            duration_minutes=30
        )
        s_ecg = Service(
            title='ЭКГ с расшифровкой',
            description='Снятие электрокардиограммы на современном аппарате с последующей детальной расшифровкой и выдачей заключения.',
            price=1200.00,
            duration_minutes=30
        )
        s_analyzes = Service(
            title='Комплексный анализ крови',
            description='Забор венозной крови на клинический и биохимический анализ (холестерин, сахар, печеночные пробы).',
            price=1800.00,
            duration_minutes=30
        )
        db.session.add_all([s_therapy, s_cardiology, s_ecg, s_analyzes])
        db.session.commit()
        
        # 2. Создание пользователей и ролей
        print("Создание пользователей...")
        
        # Администратор
        u_admin = User(email='admin@clinic.ru', role='admin')
        u_admin.set_password('admin123')
        
        # Врачи
        u_doctor1 = User(email='doctor@clinic.ru', role='doctor')  # Основной врач
        u_doctor1.set_password('doctor123')
        
        u_doctor2 = User(email='doctor2@clinic.ru', role='doctor')
        u_doctor2.set_password('doctor223')
        
        # Пациенты
        u_patient1 = User(email='patient@clinic.ru', role='patient')  # Основной пациент (Амплеенков)
        u_patient1.set_password('patient123')
        
        u_patient2 = User(email='patient2@clinic.ru', role='patient')  # Сидоров
        u_patient2.set_password('patient223')
        
        db.session.add_all([u_admin, u_doctor1, u_doctor2, u_patient1, u_patient2])
        db.session.commit()
        
        # 3. Профили врачей
        print("Создание профилей врачей...")
        d_ivanov = Doctor(
            user_id=u_doctor1.id,
            full_name='Иванов Иван Иванович',
            specialization='Терапевт',
            cabinet='Кабинет 101'
        )
        d_petrov = Doctor(
            user_id=u_doctor2.id,
            full_name='Петров Петр Петрович',
            specialization='Кардиолог',
            cabinet='Кабинет 202'
        )
        db.session.add_all([d_ivanov, d_petrov])
        db.session.commit()
        
        # 4. Профили пациентов
        print("Создание профилей пациентов...")
        p_ampleenkov = Patient(
            user_id=u_patient1.id,
            full_name='Амплеенков Даниил Олегович',
            birth_date=date(2004, 5, 12),
            phone='+7 (999) 111-22-33'
        )
        p_sidorov = Patient(
            user_id=u_patient2.id,
            full_name='Сидоров Сидор Сидорович',
            birth_date=date(1995, 8, 20),
            phone='+7 (999) 444-55-66'
        )
        db.session.add_all([p_ampleenkov, p_sidorov])
        db.session.commit()
        
        # 5. Электронные медицинские карты (с расширенными полями)
        print("Создание медицинских карт...")
        mr_ampleenkov = MedicalRecord(
            patient_id=p_ampleenkov.id,
            card_number='МК-2026-0001',
            blood_type='A(II)',
            rh_factor='Rh+',
            allergies='Пенициллин, Анальгин',
            chronic_diseases='Хронический гастрит в стадии ремиссии, аллергический ринит.'
        )
        mr_sidorov = MedicalRecord(
            patient_id=p_sidorov.id,
            card_number='МК-2026-0002',
            blood_type='0(I)',
            rh_factor='Rh-',
            allergies='Нет выявлено',
            chronic_diseases='Не зарегистрировано'
        )
        db.session.add_all([mr_ampleenkov, mr_sidorov])
        db.session.commit()
        
        # 6. Создание слотов расписания на неделю вперед
        print("Создание расписания...")
        today = date.today()
        time_slots = [
            time(9, 0), time(9, 30), time(10, 0), time(10, 30),
            time(11, 0), time(11, 30), time(14, 0), time(14, 30),
            time(15, 0), time(15, 30)
        ]
        
        # Добавим расписание на 7 дней вперед для обоих врачей
        slots_list = []
        for day_offset in range(8):  # От сегодня на неделю вперед
            slot_date = today + timedelta(days=day_offset)
            
            # Пропускаем воскресенье
            if slot_date.weekday() == 6:
                continue
                
            for slot_time in time_slots:
                # Врач 1 (Иванов)
                slots_list.append(ScheduleSlot(
                    doctor_id=d_ivanov.id,
                    date=slot_date,
                    start_time=slot_time,
                    end_time=(datetime.combine(slot_date, slot_time) + timedelta(minutes=30)).time(),
                    status='free'
                ))
                # Врач 2 (Петров)
                slots_list.append(ScheduleSlot(
                    doctor_id=d_petrov.id,
                    date=slot_date,
                    start_time=slot_time,
                    end_time=(datetime.combine(slot_date, slot_time) + timedelta(minutes=30)).time(),
                    status='free'
                ))
        db.session.add_all(slots_list)
        db.session.commit()
        
        # 7. Симуляция исторического визита для Амплеенкова (чтобы кабинет был заполнен)
        print("Симуляция исторического визита...")
        yesterday = today - timedelta(days=1)
        
        # Вчерашний слот
        hist_slot = ScheduleSlot(
            doctor_id=d_ivanov.id,
            date=yesterday,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='booked'
        )
        db.session.add(hist_slot)
        db.session.commit()
        
        # Вчерашняя запись
        hist_appt = Appointment(
            patient_id=p_ampleenkov.id,
            doctor_id=d_ivanov.id,
            service_id=s_therapy.id,
            slot_id=hist_slot.id,
            status='completed',
            created_at=datetime.combine(yesterday, time(9, 0))
        )
        db.session.add(hist_appt)
        db.session.commit()
        
        # Результаты приема (посещение)
        hist_visit = Visit(
            record_id=mr_ampleenkov.id,
            appointment_id=hist_appt.id,
            complaints='Жалобы на сухой кашель, першение в горле, легкую слабость в течение 2 дней. Температура 37.1С.',
            diagnosis='Острый фарингит (ОРВИ легкого течения).',
            recommendations='1. Обильное теплое питье (чай с лимоном, ромашка).\n2. Полоскание горла раствором фурацилина 3-4 раза в день.\n3. Витамин C 1000 мг в сутки в течение 5 дней.\n4. Домашний режим до нормализации состояния.'
        )
        db.session.add(hist_visit)
        db.session.commit()
        
        # Прикрепленный документ к посещению
        hist_doc = Document(
            patient_id=p_ampleenkov.id,
            visit_id=hist_visit.id,
            file_path='visit_conclusion_1.pdf',
            file_type='Заключение врача'
        )
        db.session.add(hist_doc)
        db.session.commit()
        
        print("База данных успешно наполнена начальными данными!")
        print("Учетные записи для тестирования:")
        print("1. Администратор:  admin@clinic.ru  (пароль: admin123)")
        print("2. Врач (терапевт): doctor@clinic.ru (пароль: doctor123)")
        print("3. Врач (кардиолог): doctor2@clinic.ru(пароль: doctor223)")
        print("4. Пациент (ЛК):    patient@clinic.ru(пароль: patient123)")

if __name__ == "__main__":
    seed_database()
