"""
Модуль работы с базой данных
Система учёта техники v6.0
"""

import sqlite3
from datetime import datetime


class DB:
    """Класс для работы с базой данных SQLite"""
    
    def __init__(self, db_name="school_it_v6.db"):
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        """Инициализация таблиц базы данных"""
        # Таблица оборудования (ПК, ноутбуки, принтеры, МФУ)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inv_number TEXT UNIQUE,
                type TEXT,
                brand TEXT,
                model TEXT,
                serial_number TEXT,
                location TEXT,
                ip_address TEXT,
                status TEXT DEFAULT 'В работе',
                balance_date TEXT,
                cpu_info TEXT,
                motherboard TEXT,
                storage TEXT,
                ram_info TEXT,
                ports_info TEXT,
                os_name TEXT,
                battery_status TEXT,
                cartridge_model TEXT,
                last_refill_date TEXT
            )
        """)

        # Таблица сетевого оборудования
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inv_number TEXT UNIQUE,
                type TEXT,
                brand TEXT,
                model TEXT,
                serial_number TEXT,
                location TEXT,
                ip_address TEXT,
                status TEXT DEFAULT 'В работе',
                balance_date TEXT,
                ports_count TEXT,
                bandwidth TEXT,
                rack_info TEXT
            )
        """)

        # Таблица программного обеспечения
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS software (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equip_id INTEGER,
                name TEXT,
                version TEXT,
                FOREIGN KEY(equip_id) REFERENCES equipment(id)
            )
        """)

        # История изменений статусов оборудования
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equip_id INTEGER,
                old_status TEXT,
                new_status TEXT,
                change_date TEXT,
                reason TEXT,
                technician TEXT,
                FOREIGN KEY(equip_id) REFERENCES equipment(id)
            )
        """)

        # Таблица картриджей
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cartridges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT,
                printer_model TEXT,
                printer_id INTEGER,
                quantity INTEGER DEFAULT 1,
                last_refill_date TEXT,
                is_spare INTEGER DEFAULT 0,
                status TEXT DEFAULT 'В работе',
                linked_printer_inv TEXT,
                FOREIGN KEY(printer_id) REFERENCES equipment(id)
            )
        """)

        # История изменений статусов картриджей
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cartridge_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cartridge_id INTEGER,
                old_status TEXT,
                new_status TEXT,
                change_date TEXT,
                reason TEXT,
                technician TEXT,
                cost REAL DEFAULT 0,
                FOREIGN KEY(cartridge_id) REFERENCES cartridges(id)
            )
        """)

        # Журнал обслуживания и ремонтов (переименован в Журнал Учета и Обслуживания)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equip_id INTEGER,
                equip_type TEXT,
                date TEXT,
                work_type TEXT,
                description TEXT,
                technician TEXT,
                cost REAL DEFAULT 0,
                is_outsourced INTEGER DEFAULT 0,
                cartridge_id INTEGER,
                contract_type TEXT,
                FOREIGN KEY(equip_id) REFERENCES equipment(id),
                FOREIGN KEY(cartridge_id) REFERENCES cartridges(id)
            )
        """)

        # Таблица для учёта контрактов
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS contract_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                contract_type TEXT,
                work_type TEXT,
                description TEXT,
                technician TEXT,
                cost REAL DEFAULT 0
            )
        """)

        # Склад расходников
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                quantity INTEGER DEFAULT 0,
                unit TEXT,
                is_refillable INTEGER DEFAULT 0,
                supplier TEXT,
                cost REAL DEFAULT 0
            )
        """)

        # Инициализация склада по умолчанию
        self.cursor.execute("SELECT count(*) FROM stock")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO stock (name, quantity, unit, is_refillable) VALUES ('Кабель UTP 5e', 10, 'м', 0)")
            self.cursor.execute("INSERT INTO stock (name, quantity, unit, is_refillable) VALUES ('Коннектор RJ-45', 40, 'шт', 0)")
            self.cursor.execute("INSERT INTO stock (name, quantity, unit, is_refillable) VALUES ('Батарейки AA', 20, 'шт', 0)")
            self.cursor.execute("INSERT INTO stock (name, quantity, unit, is_refillable) VALUES ('Батарейки AAA', 20, 'шт', 0)")

        # Инициализация картриджей по умолчанию
        self.cursor.execute("SELECT count(*) FROM cartridges")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO cartridges (model, printer_model, quantity, is_spare, status) VALUES ('TK-1200', 'KYOCERA ECOSYS M2235dn', 1, 1, 'На хранении')")
            self.cursor.execute("INSERT INTO cartridges (model, printer_model, quantity, is_spare, status) VALUES ('TK-1150', 'KYOCERA ECOSYS M2635dn', 1, 1, 'На хранении')")
            self.cursor.execute("INSERT INTO cartridges (model, printer_model, quantity, is_spare, status) VALUES ('HP Q2612A', 'HP LaserJet 1020', 1, 1, 'На хранении')")

        self.conn.commit()

    # ==================== Оборудование ====================
    
    def add_equipment(self, data):
        """Добавление оборудования"""
        try:
            self.cursor.execute("""
                INSERT INTO equipment (inv_number, type, brand, model, serial_number, location, ip_address,
                status, balance_date,cpu_info, motherboard, storage, ram_info, ports_info, os_name,
                battery_status, cartridge_model, last_refill_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)

            equip_id = self.cursor.lastrowid
            cartridge_model = data[16]
            last_refill = data[17]
            equip_type = data[1]
            equip_model = data[3]
            inv_number = data[0]

            if cartridge_model and equip_type in ['Принтер', 'МФУ']:
                self.cursor.execute("SELECT id FROM cartridges WHERE model=? AND printer_id=?", (cartridge_model, equip_id))
                if not self.cursor.fetchone():
                    self.cursor.execute("""
                        INSERT INTO cartridges (model, printer_model, printer_id, quantity, last_refill_date, is_spare, status, linked_printer_inv)
                        VALUES (?, ?, ?, 1, ?, 0, 'В работе', ?)
                    """, (cartridge_model, equip_model, equip_id, last_refill, inv_number))
                    cart_id = self.cursor.lastrowid
                    self.log_cartridge_status_change(cart_id, None, 'В работе', 'Картридж зарегистрирован при добавлении принтера', 'Техник-программист')

            self.conn.commit()
            return True, ""
        except sqlite3.IntegrityError as e:
            return False, f"Такой инвентарный номер уже существует: {str(e)}"

    def update_equipment(self, data, equip_id):
        """Обновление оборудования"""
        try:
            self.cursor.execute("""
                UPDATE equipment SET
                inv_number=?, type=?, brand=?, model=?, serial_number=?, location=?, ip_address=?,
                balance_date=?, cpu_info=?, motherboard=?, storage=?, ram_info=?, ports_info=?, os_name=?,
                battery_status=?, cartridge_model=?, last_refill_date=?
                WHERE id=?
            """, data + (equip_id,))
            self.conn.commit()
            return True, ""
        except sqlite3.IntegrityError:
            return False, "Такой инвентарный номер уже существует"

    def delete_equipment(self, equip_id):
        """Удаление оборудования"""
        self.cursor.execute("DELETE FROM equipment WHERE id = ?", (equip_id,))
        self.conn.commit()

    def get_equipment(self):
        """Получение всего оборудования"""
        self.cursor.execute("SELECT * FROM equipment")
        return self.cursor.fetchall()

    def get_equipment_for_select(self):
        """Получение оборудования для выпадающего списка"""
        self.cursor.execute("SELECT id, inv_number, type, model FROM equipment")
        return self.cursor.fetchall()

    def get_printers_with_cartridges(self):
        """Получение принтеров с картриджами"""
        self.cursor.execute("""
            SELECT id, inv_number, model, cartridge_model
            FROM equipment
            WHERE type IN ('Принтер', 'МФУ') AND cartridge_model IS NOT NULL AND cartridge_model != ''
        """)
        return self.cursor.fetchall()

    def get_printer_cartridge_models(self):
        """Получение моделей картриджей для принтеров"""
        self.cursor.execute("SELECT DISTINCT cartridge_model, model FROM equipment WHERE type IN ('Принтер', 'МФУ') AND cartridge_model IS NOT NULL AND cartridge_model != ''")
        return self.cursor.fetchall()

    # ==================== История статусов ====================
    
    def log_status_change(self, equip_id, old_status, new_status, reason, technician):
        """Логирование изменения статуса оборудования"""
        self.cursor.execute("""
            INSERT INTO status_history (equip_id, old_status, new_status, change_date, reason, technician)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (equip_id, old_status, new_status, datetime.now().strftime("%Y-%m-%d %H:%M"), reason, technician))
        self.conn.commit()

    def get_status_history(self, equip_id):
        """Получение истории статусов оборудования"""
        self.cursor.execute("""
            SELECT change_date, old_status, new_status, reason, technician
            FROM status_history
            WHERE equip_id = ?
            ORDER BY change_date DESC
        """, (equip_id,))
        return self.cursor.fetchall()

    def update_equipment_status(self, equip_id, status, reason=""):
        """Обновление статуса оборудования"""
        self.cursor.execute("SELECT status FROM equipment WHERE id = ?", (equip_id,))
        res = self.cursor.fetchone()
        if res is None:
            return False, "Оборудование не найдено"
        old_status = res['status']
        self.cursor.execute("UPDATE equipment SET status = ? WHERE id = ?", (status, equip_id))
        self.conn.commit()
        self.log_status_change(equip_id, old_status, status, reason, "Техник-программист")
        return True, ""

    # ==================== Картриджи ====================
    
    def log_cartridge_status_change(self, cartridge_id, old_status, new_status, reason, technician, cost=0):
        """Логирование изменения статуса картриджа"""
        self.cursor.execute("""
            INSERT INTO cartridge_history (cartridge_id, old_status, new_status, change_date, reason, technician, cost)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cartridge_id, old_status, new_status, datetime.now().strftime("%Y-%m-%d %H:%M"), reason, technician, cost))
        self.conn.commit()

    def get_cartridge_history(self, cartridge_id):
        """Получение истории статусов картриджа"""
        self.cursor.execute("""
            SELECT change_date, old_status, new_status, reason, technician, cost
            FROM cartridge_history
            WHERE cartridge_id = ?
            ORDER BY change_date DESC
        """, (cartridge_id,))
        return self.cursor.fetchall()

    def get_cartridges(self):
        """Получение всех картриджей"""
        self.cursor.execute("SELECT * FROM cartridges")
        return self.cursor.fetchall()

    def get_cartridge_by_id(self, cartridge_id):
        """Получение картриджа по ID"""
        self.cursor.execute("SELECT * FROM cartridges WHERE id = ?", (cartridge_id,))
        return self.cursor.fetchone()

    def update_cartridge_status(self, cartridge_id, new_status, reason="", cost=0):
        """Обновление статуса картриджа"""
        self.cursor.execute("SELECT status, is_spare FROM cartridges WHERE id = ?", (cartridge_id,))
        res = self.cursor.fetchone()
        if res is None:
            return False, "Картридж не найден"
        old_status = res['status']
        is_spare = res['is_spare']
        self.cursor.execute("UPDATE cartridges SET status = ? WHERE id = ?", (new_status, cartridge_id))
        self.conn.commit()
        self.log_cartridge_status_change(cartridge_id, old_status, new_status, reason, "Техник-программист", cost)
        return True, ""

    def update_cartridge_refill_date(self, cartridge_id, refill_date):
        """Обновление даты заправки картриджа"""
        self.cursor.execute("UPDATE cartridges SET last_refill_date = ? WHERE id = ?", (refill_date, cartridge_id))
        self.conn.commit()

    def add_cartridge(self, model, printer_model, qty, is_spare=0, status='На хранении'):
        """Добавление картриджа"""
        try:
            self.cursor.execute("INSERT INTO cartridges (model, printer_model, quantity, is_spare, status) VALUES (?, ?, ?, ?, ?)",
                              (model, printer_model, qty, is_spare, status))
            self.conn.commit()
            return True, ""
        except sqlite3.IntegrityError:
            return False, "Такая модель картриджа уже существует"

    def delete_cartridge(self, cartridge_id):
        """Удаление картриджа"""
        self.cursor.execute("DELETE FROM cartridges WHERE id = ?", (cartridge_id,))
        self.conn.commit()

    def link_cartridge_to_printer(self, cartridge_id, printer_id, printer_inv, set_as_working=True):
        """Привязка картриджа к принтеру"""
        if set_as_working:
            self.cursor.execute("""
                UPDATE cartridges SET printer_id=?, linked_printer_inv=?, is_spare=0, status='В работе'
                WHERE id=?
            """, (printer_id, printer_inv, cartridge_id))
        else:
            self.cursor.execute("""
                UPDATE cartridges SET printer_id=?, linked_printer_inv=?
                WHERE id=?
            """, (printer_id, printer_inv, cartridge_id))
        self.conn.commit()

    def get_spare_cartridges_for_printer(self, cartridge_model):
        """Получение запасных картриджей для принтера"""
        self.cursor.execute("""
            SELECT id, model, printer_model, status
            FROM cartridges
            WHERE model=? AND is_spare=1 AND status='На хранении'
        """, (cartridge_model,))
        return self.cursor.fetchall()

    # ==================== Сетевое оборудование ====================
    
    def add_network_equipment(self, data):
        """Добавление сетевого оборудования"""
        try:
            self.cursor.execute("""
                INSERT INTO network_equipment (inv_number, type, brand, model, serial_number, location,
                ip_address, status, balance_date, ports_count, bandwidth, rack_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            self.conn.commit()
            return True, ""
        except sqlite3.IntegrityError:
            return False, "Такой инвентарный номер уже существует"

    def update_network_equipment(self, data, equip_id):
        """Обновление сетевого оборудования"""
        try:
            self.cursor.execute("""
                UPDATE network_equipment SET
                inv_number=?, type=?, brand=?, model=?, serial_number=?, location=?, ip_address=?,
                balance_date=?, ports_count=?, bandwidth=?, rack_info=?
                WHERE id=?
            """, data + (equip_id,))
            self.conn.commit()
            return True, ""
        except sqlite3.IntegrityError:
            return False, "Такой инвентарный номер уже существует"

    def delete_network_equipment(self, equip_id):
        """Удаление сетевого оборудования"""
        self.cursor.execute("DELETE FROM network_equipment WHERE id = ?", (equip_id,))
        self.conn.commit()

    def get_network_equipment(self):
        """Получение всего сетевого оборудования"""
        self.cursor.execute("SELECT * FROM network_equipment")
        return self.cursor.fetchall()

    # ==================== Программное обеспечение ====================
    
    def add_software(self, equip_id, name, version):
        """Добавление ПО"""
        self.cursor.execute("INSERT INTO software (equip_id, name, version) VALUES (?, ?, ?)", (equip_id, name, version))
        self.conn.commit()

    # ==================== Журнал обслуживания (Журнал Учета и Обслуживания) ====================
    
    def add_maintenance(self, data):
        """Добавление записи в журнал обслуживания"""
        self.cursor.execute("""
            INSERT INTO maintenance (equip_id, equip_type, date, work_type, description, technician, cost, is_outsourced, cartridge_id, contract_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        
        # Если есть стоимость и указан тип контракта - добавляем расход в контракт
        if data[6] and data[9]:  # cost > 0 and contract_type
            self.add_contract_expense(data[6], data[9], data[4], data[5])
        
        self.conn.commit()

    def get_maintenance(self, limit=100):
        """Получение записей журнала обслуживания"""
        self.cursor.execute("""
            SELECT m.id, m.date, e.inv_number, e.type, m.work_type, m.description, m.cost, m.is_outsourced, m.cartridge_id, m.contract_type
            FROM maintenance m
            JOIN equipment e ON m.equip_id = e.id
            ORDER BY m.date DESC
            LIMIT ?
        """, (limit,))
        return self.cursor.fetchall()

    def get_monthly_cost(self, contract_type=None):
        """Получение суммы затрат за текущий месяц по контракту"""
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if contract_type:
            self.cursor.execute("""
                SELECT SUM(cost) FROM contract_expenses
                WHERE date >= ? AND contract_type = ?
            """, (start_of_month.strftime("%Y-%m-%d"), contract_type))
        else:
            self.cursor.execute("""
                SELECT SUM(cost) FROM contract_expenses
                WHERE date >= ?
            """, (start_of_month.strftime("%Y-%m-%d"),))
        res = self.cursor.fetchone()[0]
        return res if res else 0.0

    def get_yearly_cost(self, contract_type=None):
        """Получение суммы затрат за текущий год по контракту"""
        now = datetime.now()
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        if contract_type:
            self.cursor.execute("""
                SELECT SUM(cost) FROM contract_expenses
                WHERE date >= ? AND contract_type = ?
            """, (start_of_year.strftime("%Y-%m-%d"), contract_type))
        else:
            self.cursor.execute("""
                SELECT SUM(cost) FROM contract_expenses
                WHERE date >= ?
            """, (start_of_year.strftime("%Y-%m-%d"),))
        res = self.cursor.fetchone()[0]
        return res if res else 0.0

    def add_contract_expense(self, cost, contract_type, work_type, description, technician="Техник-программист"):
        """Добавление расхода по контракту"""
        self.cursor.execute("""
            INSERT INTO contract_expenses (date, contract_type, work_type, description, technician, cost)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().strftime("%Y-%m-%d"), contract_type, work_type, description, technician, cost))
        self.conn.commit()

    def get_contract_expenses(self, contract_type=None, limit=100):
        """Получение расходов по контрактам"""
        if contract_type:
            self.cursor.execute("""
                SELECT id, date, contract_type, work_type, description, technician, cost
                FROM contract_expenses
                WHERE contract_type = ?
                ORDER BY date DESC
                LIMIT ?
            """, (contract_type, limit))
        else:
            self.cursor.execute("""
                SELECT id, date, contract_type, work_type, description, technician, cost
                FROM contract_expenses
                ORDER BY date DESC
                LIMIT ?
            """, (limit,))
        return self.cursor.fetchall()

    # ==================== Склад ====================
    
    def get_stock(self):
        """Получение товаров со склада"""
        self.cursor.execute("SELECT * FROM stock")
        return self.cursor.fetchall()

    def update_stock(self, name, qty_change):
        """Обновление количества товара на складе"""
        self.cursor.execute("SELECT quantity FROM stock WHERE name = ?", (name,))
        res = self.cursor.fetchone()
        if res is None:
            return False, "Товар не найден"
        current = res[0]
        if current + qty_change < 0:
            return False, f"Недостаточно на складе. Есть: {current}"
        self.cursor.execute("UPDATE stock SET quantity = quantity + ? WHERE name = ?", (qty_change, name))
        self.conn.commit()
        return True, ""

    def add_stock_item(self, name, qty, unit, supplier=None, cost=0):
        """Добавление нового товара на склад"""
        try:
            self.cursor.execute("INSERT INTO stock (name, quantity, unit, is_refillable, supplier, cost) VALUES (?, ?, ?, 0, ?, ?)", (name, qty, unit, supplier, cost))
            self.conn.commit()
            return True, ""
        except sqlite3.IntegrityError:
            return False, "Такой товар уже существует"

    def update_stock_with_supplier(self, name, qty_change, supplier=None, cost=0, contract_type=None):
        """Обновление количества товара на складе с записью в журнал и контракт"""
        self.cursor.execute("SELECT quantity, supplier, cost FROM stock WHERE name = ?", (name,))
        res = self.cursor.fetchone()
        if res is None:
            return False, "Товар не найден"
        current = res[0]
        if current + qty_change < 0:
            return False, f"Недостаточно на складе. Есть: {current}"
        
        # Обновляем количество
        self.cursor.execute("UPDATE stock SET quantity = quantity + ? WHERE name = ?", (qty_change, name))
        
        # Если приход (qty_change > 0) и указан поставщик/стоимость - обновляем данные
        if qty_change > 0 and (supplier or cost):
            sup = supplier if supplier else res[1]
            c = cost if cost else res[2]
            self.cursor.execute("UPDATE stock SET supplier = ?, cost = ? WHERE name = ?", (sup, c, name))
            
            # Если поставщик "ИП Ермаков Евгений Викторович" и есть стоимость - записываем в контракт
            if sup == "ИП Ермаков Евгений Викторович" and cost > 0:
                if contract_type == "refill":
                    self.add_contract_expense(cost, "Заправка", f"Закупка товара: {name}", "Техник-программист")
                elif contract_type == "repair":
                    self.add_contract_expense(cost, "Ремонт", f"Закупка товара: {name}", "Техник-программист")
        
        self.conn.commit()
        return True, ""

    def delete_stock_item(self, name):
        """Удаление товара со склада"""
        self.cursor.execute("DELETE FROM stock WHERE name = ?", (name,))
        self.conn.commit()

    # ==================== Отчёты ====================
    
    def get_inventory_report(self):
        """Отчёт по инвентаризации оборудования"""
        self.cursor.execute("""
            SELECT inv_number, type, brand, model, serial_number, location, ip_address, status, balance_date
            FROM equipment
            ORDER BY type, location
        """)
        return self.cursor.fetchall()

    def get_network_inventory_report(self):
        """Отчёт по инвентаризации сетевого оборудования"""
        self.cursor.execute("""
            SELECT inv_number, type, brand, model, serial_number, location, ip_address, status, balance_date
            FROM network_equipment
            ORDER BY type, location
        """)
        return self.cursor.fetchall()

    def get_equipment_by_type_report(self):
        """Отчёт по типам техники"""
        self.cursor.execute("""
            SELECT type, COUNT(*) as count,
                   SUM(CASE WHEN status='В работе' THEN 1 ELSE 0 END) as working,
                   SUM(CASE WHEN status='В ремонте' THEN 1 ELSE 0 END) as repair,
                   SUM(CASE WHEN status='В сервисе' THEN 1 ELSE 0 END) as service,
                   SUM(CASE WHEN status='С сервиса' THEN 1 ELSE 0 END) as from_service,
                   SUM(CASE WHEN status='Списано' THEN 1 ELSE 0 END) as written_off
            FROM equipment
            GROUP BY type
        """)
        return self.cursor.fetchall()

    def get_cartridge_status_report(self):
        """Отчёт по статусам картриджей"""
        self.cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM cartridges
            GROUP BY status
        """)
        return self.cursor.fetchall()
