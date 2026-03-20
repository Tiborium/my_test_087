import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, date

CONTRACT_LIMIT_MONTH = 50000
DB_NAME = "school_it_v6.db"

class DB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
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
                motherboard TEXT,
                storage TEXT,
                ram_info TEXT,
                ports_info TEXT,
                os_name TEXT,
                os_version TEXT,
                battery_status TEXT,
                cartridge_model TEXT,
                last_refill_date TEXT
            )
        """)
        
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
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS software (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equip_id INTEGER,
                name TEXT,
                version TEXT,
                FOREIGN KEY(equip_id) REFERENCES equipment(id)
            )
        """)
        
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
                FOREIGN KEY(equip_id) REFERENCES equipment(id),
                FOREIGN KEY(cartridge_id) REFERENCES cartridges(id)
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                quantity INTEGER DEFAULT 0,
                unit TEXT,
                is_refillable INTEGER DEFAULT 0
            )
        """)
        
        self.cursor.execute("SELECT count(*) FROM stock")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO stock (name, quantity, unit, is_refillable) VALUES ('Кабель UTP 5e', 10, 'м', 0)")
            self.cursor.execute("INSERT INTO stock (name, quantity, unit, is_refillable) VALUES ('Коннектор RJ-45', 40, 'шт', 0)")
            self.cursor.execute("INSERT INTO stock (name, quantity, unit, is_refillable) VALUES ('Батарейки AA', 20, 'шт', 0)")
            self.cursor.execute("INSERT INTO stock (name, quantity, unit, is_refillable) VALUES ('Батарейки AAA', 20, 'шт', 0)")
        
        self.cursor.execute("SELECT count(*) FROM cartridges")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO cartridges (model, printer_model, quantity, is_spare, status) VALUES ('TK-1200', 'KYOCERA ECOSYS M2235dn', 1, 1, 'На хранении')")
            self.cursor.execute("INSERT INTO cartridges (model, printer_model, quantity, is_spare, status) VALUES ('TK-1150', 'KYOCERA ECOSYS M2635dn', 1, 1, 'На хранении')")
            self.cursor.execute("INSERT INTO cartridges (model, printer_model, quantity, is_spare, status) VALUES ('HP Q2612A', 'HP LaserJet 1020', 1, 1, 'На хранении')")
        
        self.conn.commit()

    def add_equipment(self, data):
        try:
            self.cursor.execute("""
                INSERT INTO equipment (inv_number, type, brand, model, serial_number, location, ip_address,
                status, balance_date, motherboard, storage, ram_info, ports_info, os_name, os_version,
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
        try:
            self.cursor.execute("""
                UPDATE equipment SET 
                inv_number=?, type=?, brand=?, model=?, serial_number=?, location=?, ip_address=?,
                balance_date=?, motherboard=?, storage=?, ram_info=?, ports_info=?, os_name=?, 
                os_version=?, battery_status=?, cartridge_model=?, last_refill_date=?
                WHERE id=?
            """, data + (equip_id,))
            self.conn.commit()
            return True, ""
        except sqlite3.IntegrityError:
            return False, "Такой инвентарный номер уже существует"

    def delete_equipment(self, equip_id):
        self.cursor.execute("DELETE FROM equipment WHERE id = ?", (equip_id,))
        self.conn.commit()

    def get_equipment(self):
        self.cursor.execute("SELECT * FROM equipment")
        return self.cursor.fetchall()

    def get_equipment_for_select(self):
        self.cursor.execute("SELECT id, inv_number, type, model FROM equipment")
        return self.cursor.fetchall()

    def get_printers_with_cartridges(self):
        self.cursor.execute("""
            SELECT id, inv_number, model, cartridge_model 
            FROM equipment 
            WHERE type IN ('Принтер', 'МФУ') AND cartridge_model IS NOT NULL AND cartridge_model != ''
        """)
        return self.cursor.fetchall()

    def get_printer_cartridge_models(self):
        self.cursor.execute("SELECT DISTINCT cartridge_model, model FROM equipment WHERE type IN ('Принтер', 'МФУ') AND cartridge_model IS NOT NULL AND cartridge_model != ''")
        return self.cursor.fetchall()

    def log_status_change(self, equip_id, old_status, new_status, reason, technician):
        self.cursor.execute("""
            INSERT INTO status_history (equip_id, old_status, new_status, change_date, reason, technician)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (equip_id, old_status, new_status, datetime.now().strftime("%Y-%m-%d %H:%M"), reason, technician))
        self.conn.commit()

    def get_status_history(self, equip_id):
        self.cursor.execute("""
            SELECT change_date, old_status, new_status, reason, technician
            FROM status_history
            WHERE equip_id = ?
            ORDER BY change_date DESC
        """, (equip_id,))
        return self.cursor.fetchall()

    def update_equipment_status(self, equip_id, status, reason=""):
        self.cursor.execute("SELECT status FROM equipment WHERE id = ?", (equip_id,))
        res = self.cursor.fetchone()
        if res is None:
            return False, "Оборудование не найдено"
        old_status = res['status']
        self.cursor.execute("UPDATE equipment SET status = ? WHERE id = ?", (status, equip_id))
        self.conn.commit()
        self.log_status_change(equip_id, old_status, status, reason, "Техник-программист")
        return True, ""

    def log_cartridge_status_change(self, cartridge_id, old_status, new_status, reason, technician, cost=0):
        self.cursor.execute("""
            INSERT INTO cartridge_history (cartridge_id, old_status, new_status, change_date, reason, technician, cost)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cartridge_id, old_status, new_status, datetime.now().strftime("%Y-%m-%d %H:%M"), reason, technician, cost))
        self.conn.commit()

    def get_cartridge_history(self, cartridge_id):
        self.cursor.execute("""
            SELECT change_date, old_status, new_status, reason, technician, cost
            FROM cartridge_history
            WHERE cartridge_id = ?
            ORDER BY change_date DESC
        """, (cartridge_id,))
        return self.cursor.fetchall()

    def get_cartridges(self):
        self.cursor.execute("SELECT * FROM cartridges")
        return self.cursor.fetchall()

    def get_cartridge_by_id(self, cartridge_id):
        self.cursor.execute("SELECT * FROM cartridges WHERE id = ?", (cartridge_id,))
        return self.cursor.fetchone()

    def update_cartridge_status(self, cartridge_id, new_status, reason="", cost=0):
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
        self.cursor.execute("UPDATE cartridges SET last_refill_date = ? WHERE id = ?", (refill_date, cartridge_id))
        self.conn.commit()

    def add_cartridge(self, model, printer_model, qty, is_spare=0, status='На хранении'):
        try:
            self.cursor.execute("INSERT INTO cartridges (model, printer_model, quantity, is_spare, status) VALUES (?, ?, ?, ?, ?)", 
                              (model, printer_model, qty, is_spare, status))
            self.conn.commit()
            return True, ""
        except sqlite3.IntegrityError:
            return False, "Такая модель картриджа уже существует"

    def delete_cartridge(self, cartridge_id):
        self.cursor.execute("DELETE FROM cartridges WHERE id = ?", (cartridge_id,))
        self.conn.commit()

    def link_cartridge_to_printer(self, cartridge_id, printer_id, printer_inv, set_as_working=True):
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
        self.cursor.execute("""
            SELECT id, model, printer_model, status 
            FROM cartridges 
            WHERE model=? AND is_spare=1 AND status='На хранении'
        """, (cartridge_model,))
        return self.cursor.fetchall()

    def add_network_equipment(self, data):
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
        self.cursor.execute("DELETE FROM network_equipment WHERE id = ?", (equip_id,))
        self.conn.commit()

    def get_network_equipment(self):
        self.cursor.execute("SELECT * FROM network_equipment")
        return self.cursor.fetchall()

    def add_software(self, equip_id, name, version):
        self.cursor.execute("INSERT INTO software (equip_id, name, version) VALUES (?, ?, ?)", (equip_id, name, version))
        self.conn.commit()

    def add_maintenance(self, data):
        self.cursor.execute("""
            INSERT INTO maintenance (equip_id, equip_type, date, work_type, description, technician, cost, is_outsourced, cartridge_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        self.conn.commit()

    def get_maintenance(self, limit=100):
        self.cursor.execute("""
            SELECT m.id, m.date, e.inv_number, e.type, m.work_type, m.description, m.cost, m.is_outsourced, m.cartridge_id
            FROM maintenance m
            JOIN equipment e ON m.equip_id = e.id
            ORDER BY m.date DESC
            LIMIT ?
        """, (limit,))
        return self.cursor.fetchall()

    def get_monthly_cost(self):
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.cursor.execute("""
            SELECT SUM(cost) FROM maintenance 
            WHERE date >= ? AND is_outsourced = 1
        """, (start_of_month.strftime("%Y-%m-%d"),))
        res = self.cursor.fetchone()[0]
        return res if res else 0.0

    def get_stock(self):
        self.cursor.execute("SELECT * FROM stock")
        return self.cursor.fetchall()

    def update_stock(self, name, qty_change):
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

    def add_stock_item(self, name, qty, unit):
        try:
            self.cursor.execute("INSERT INTO stock (name, quantity, unit, is_refillable) VALUES (?, ?, ?, 0)", (name, qty, unit))
            self.conn.commit()
            return True, ""
        except sqlite3.IntegrityError:
            return False, "Такой товар уже существует"

    def delete_stock_item(self, name):
        self.cursor.execute("DELETE FROM stock WHERE name = ?", (name,))
        self.conn.commit()

    def get_inventory_report(self):
        self.cursor.execute("""
            SELECT inv_number, type, brand, model, serial_number, location, ip_address, status, balance_date
            FROM equipment
            ORDER BY type, location
        """)
        return self.cursor.fetchall()

    def get_network_inventory_report(self):
        self.cursor.execute("""
            SELECT inv_number, type, brand, model, serial_number, location, ip_address, status, balance_date
            FROM network_equipment
            ORDER BY type, location
        """)
        return self.cursor.fetchall()

    def get_equipment_by_type_report(self):
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
        self.cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM cartridges
            GROUP BY status
        """)
        return self.cursor.fetchall()


class App:
    def __init__(self, root):
        self.db = DB()
        self.root = root
        self.root.title("АИС Техник-Программист v6.0")
        self.root.geometry("1500x900")

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(expand=1, fill="both")

        self.tab_equipment = ttk.Frame(self.tabs)
        self.tab_network = ttk.Frame(self.tabs)
        self.tab_maintenance = ttk.Frame(self.tabs)
        self.tab_stock = ttk.Frame(self.tabs)
        self.tab_cartridges = ttk.Frame(self.tabs)
        self.tab_reports = ttk.Frame(self.tabs)
        self.tab_contract = ttk.Frame(self.tabs)

        self.tabs.add(self.tab_equipment, text="🖥 ПК/Ноутбуки/Принтеры")
        self.tabs.add(self.tab_network, text="🌐 Сетевое оборудование")
        self.tabs.add(self.tab_maintenance, text="🛠 Журнал по обслуживанию и ремонту")
        self.tabs.add(self.tab_stock, text="📦 Склад")
        self.tabs.add(self.tab_cartridges, text="🖨 Картриджи")
        self.tabs.add(self.tab_reports, text="📊 Отчёты")
        self.tabs.add(self.tab_contract, text="💰 Контракт")

        self.setup_equipment_tab()
        self.setup_network_tab()
        self.setup_maintenance_tab()
        self.setup_stock_tab()
        self.setup_cartridges_tab()
        self.setup_reports_tab()
        self.setup_contract_tab()
        
        self.refresh_all()

    def setup_equipment_tab(self):
        frame_form = ttk.LabelFrame(self.tab_equipment, text="Добавление / Редактирование")
        frame_form.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_form, text="Инв. №:").grid(row=0, column=0, padx=5, pady=2)
        self.ent_inv = ttk.Entry(frame_form, width=15)
        self.ent_inv.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(frame_form, text="Тип:").grid(row=0, column=2, padx=5, pady=2)
        self.combo_type = ttk.Combobox(frame_form, values=["ПК", "Ноутбук", "МФУ", "Принтер"], state="readonly", width=12)
        self.combo_type.grid(row=0, column=3, padx=5, pady=2)
        self.combo_type.bind("<<ComboboxSelected>>", self.on_type_change)

        ttk.Label(frame_form, text="Статус:").grid(row=0, column=4, padx=5, pady=2)
        self.combo_status = ttk.Combobox(frame_form, values=["В работе", "В ремонте", "В сервисе", "С сервиса", "Списано"], state="readonly", width=12)
        self.combo_status.grid(row=0, column=5, padx=5, pady=2)
        self.combo_status.set("В работе")

        ttk.Label(frame_form, text="Марка:").grid(row=0, column=6, padx=5, pady=2)
        self.ent_brand = ttk.Entry(frame_form, width=15)
        self.ent_brand.grid(row=0, column=7, padx=5, pady=2)

        ttk.Label(frame_form, text="Модель:").grid(row=0, column=8, padx=5, pady=2)
        self.ent_model = ttk.Entry(frame_form, width=15)
        self.ent_model.grid(row=0, column=9, padx=5, pady=2)

        ttk.Label(frame_form, text="S/N:").grid(row=1, column=0, padx=5, pady=2)
        self.ent_serial = ttk.Entry(frame_form, width=15)
        self.ent_serial.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(frame_form, text="Кабинет:").grid(row=1, column=2, padx=5, pady=2)
        self.ent_loc = ttk.Entry(frame_form, width=15)
        self.ent_loc.grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(frame_form, text="IP:").grid(row=1, column=4, padx=5, pady=2)
        self.ent_ip = ttk.Entry(frame_form, width=15)
        self.ent_ip.grid(row=1, column=5, padx=5, pady=2)

        ttk.Label(frame_form, text="На балансе с:").grid(row=1, column=6, padx=5, pady=2)
        self.ent_balance = ttk.Entry(frame_form, width=15)
        self.ent_balance.grid(row=1, column=7, padx=5, pady=2)

        self.frame_specific = ttk.Frame(frame_form)
        self.frame_specific.grid(row=2, column=0, columnspan=10, sticky="w", padx=5, pady=5)
        
        self.lbl_mobo = ttk.Label(self.frame_specific, text="Мат.плата:")
        self.ent_mobo = ttk.Entry(self.frame_specific, width=20)
        self.lbl_storage = ttk.Label(self.frame_specific, text="Носитель:")
        self.ent_storage = ttk.Entry(self.frame_specific, width=25)
        self.lbl_ram = ttk.Label(self.frame_specific, text="RAM:")
        self.ent_ram = ttk.Entry(self.frame_specific, width=25)
        self.lbl_ports = ttk.Label(self.frame_specific, text="Порты:")
        self.ent_ports = ttk.Entry(self.frame_specific, width=30)
        self.lbl_os = ttk.Label(self.frame_specific, text="ОС:")
        self.ent_os = ttk.Entry(self.frame_specific, width=12)
        self.ent_os_ver = ttk.Entry(self.frame_specific, width=10)
        self.lbl_bat = ttk.Label(self.frame_specific, text="Батарея:")
        self.combo_bat = ttk.Combobox(self.frame_specific, values=["OK", "Износ", "Не держит (сеть)"], state="readonly", width=15)
        self.lbl_cart = ttk.Label(self.frame_specific, text="Картридж:")
        self.ent_cart = ttk.Entry(self.frame_specific, width=15)
        self.lbl_refill = ttk.Label(self.frame_specific, text="Посл. заправка:")
        self.ent_refill = ttk.Entry(self.frame_specific, width=12)

        btn_frame = ttk.Frame(frame_form)
        btn_frame.grid(row=3, column=0, columnspan=10, pady=10)
        ttk.Button(btn_frame, text="💾 Сохранить", command=self.save_equipment).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Редактировать", command=self.edit_equipment).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑 Удалить", command=self.delete_equipment).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📦 Добавить ПО", command=self.add_software_popup).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Изменить статус", command=self.change_status).pack(side="left", padx=5)
        self.btn_install = ttk.Button(btn_frame, text="✅ Техника установлена", command=self.install_equipment)
        self.btn_install.pack(side="left", padx=5)
        self.btn_install.config(state="disabled")

        cols = ("ID", "Инв.", "Тип", "Марка", "Модель", "Кабинет", "Статус")
        self.tree_eq = ttk.Treeview(self.tab_equipment, columns=cols, show="headings")
        for c in cols: self.tree_eq.heading(c, text=c)
        self.tree_eq.column("ID", width=40)
        self.tree_eq.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_eq.bind("<<TreeviewSelect>>", self.on_equipment_select)
        self.editing_equipment_id = None

    def on_type_change(self, event):
        for widget in self.frame_specific.winfo_children():
            widget.grid_remove()
        t = self.combo_type.get()
        if t in ["ПК", "Ноутбук"]:
            self.lbl_mobo.grid(row=0, column=0, padx=5); self.ent_mobo.grid(row=0, column=1, padx=5)
            self.lbl_storage.grid(row=0, column=2, padx=5); self.ent_storage.grid(row=0, column=3, padx=5)
            self.lbl_ram.grid(row=0, column=4, padx=5); self.ent_ram.grid(row=0, column=5, padx=5)
            self.lbl_ports.grid(row=1, column=0, padx=5, pady=5); self.ent_ports.grid(row=1, column=1, padx=5, pady=5)
            self.lbl_os.grid(row=1, column=2, padx=5, pady=5); self.ent_os.grid(row=1, column=3, padx=5, pady=5)
            self.ent_os_ver.grid(row=1, column=4, padx=5, pady=5)
            if t == "Ноутбук":
                self.lbl_bat.grid(row=1, column=5, padx=5, pady=5); self.combo_bat.grid(row=1, column=6, padx=5, pady=5)
        elif t in ["МФУ", "Принтер"]:
            self.lbl_cart.grid(row=0, column=0, padx=5); self.ent_cart.grid(row=0, column=1, padx=5)
            self.lbl_refill.grid(row=0, column=2, padx=5); self.ent_refill.grid(row=0, column=3, padx=5)

    def on_equipment_select(self, event):
        selected = self.tree_eq.selection()
        if not selected:
            self.btn_install.config(state="disabled")
            return
        item = self.tree_eq.item(selected[0])
        values = item['values']
        self.editing_equipment_id = values[0]
        for row in self.db.get_equipment():
            if row['id'] == values[0]:
                self.ent_inv.delete(0, tk.END); self.ent_inv.insert(0, row['inv_number'])
                self.combo_type.set(row['type']); self.on_type_change(None)
                self.combo_status.set(row['status'])
                self.ent_brand.delete(0, tk.END); self.ent_brand.insert(0, row['brand'] if row['brand'] else "")
                self.ent_model.delete(0, tk.END); self.ent_model.insert(0, row['model'] if row['model'] else "")
                self.ent_serial.delete(0, tk.END); self.ent_serial.insert(0, row['serial_number'] if row['serial_number'] else "")
                self.ent_loc.delete(0, tk.END); self.ent_loc.insert(0, row['location'] if row['location'] else "")
                self.ent_ip.delete(0, tk.END); self.ent_ip.insert(0, row['ip_address'] if row['ip_address'] else "")
                self.ent_balance.delete(0, tk.END); self.ent_balance.insert(0, row['balance_date'] if row['balance_date'] else "")
                if row['type'] in ["ПК", "Ноутбук"]:
                    self.ent_mobo.delete(0, tk.END); self.ent_mobo.insert(0, row['motherboard'] if row['motherboard'] else "")
                    self.ent_storage.delete(0, tk.END); self.ent_storage.insert(0, row['storage'] if row['storage'] else "")
                    self.ent_ram.delete(0, tk.END); self.ent_ram.insert(0, row['ram_info'] if row['ram_info'] else "")
                    self.ent_ports.delete(0, tk.END); self.ent_ports.insert(0, row['ports_info'] if row['ports_info'] else "")
                    self.ent_os.delete(0, tk.END); self.ent_os.insert(0, row['os_name'] if row['os_name'] else "")
                    self.ent_os_ver.delete(0, tk.END); self.ent_os_ver.insert(0, row['os_version'] if row['os_version'] else "")
                    if row['type'] == "Ноутбук":
                        self.combo_bat.set(row['battery_status'] if row['battery_status'] else "")
                elif row['type'] in ["МФУ", "Принтер"]:
                    self.ent_cart.delete(0, tk.END); self.ent_cart.insert(0, row['cartridge_model'] if row['cartridge_model'] else "")
                    self.ent_refill.delete(0, tk.END); self.ent_refill.insert(0, row['last_refill_date'] if row['last_refill_date'] else "")
                break
        current_status = self.combo_status.get()
        if current_status in ["В ремонте", "С сервиса"]:
            self.btn_install.config(state="normal")
        else:
            self.btn_install.config(state="disabled")

    def save_equipment(self):
        self.editing_equipment_id = None
        self._save_equipment_data()

    def edit_equipment(self):
        if self.editing_equipment_id is None:
            messagebox.showwarning("Внимание", "Выберите запись для редактирования в таблице")
            return
        self._save_equipment_data()

    def _save_equipment_data(self):
        data_update = (
            self.ent_inv.get(), self.combo_type.get(), self.ent_brand.get(), self.ent_model.get(),
            self.ent_serial.get(), self.ent_loc.get(), self.ent_ip.get(), self.ent_balance.get(),
            self.ent_mobo.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_storage.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_ram.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_ports.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_os.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_os_ver.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.combo_bat.get() if self.combo_type.get() == "Ноутбук" else None,
            self.ent_cart.get() if self.combo_type.get() in ["МФУ", "Принтер"] else None,
            self.ent_refill.get() if self.combo_type.get() in ["МФУ", "Принтер"] else None
        )
        data_insert = (
            self.ent_inv.get(), self.combo_type.get(), self.ent_brand.get(), self.ent_model.get(),
            self.ent_serial.get(), self.ent_loc.get(), self.ent_ip.get(), "В работе", self.ent_balance.get(),
            self.ent_mobo.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_storage.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_ram.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_ports.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_os.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_os_ver.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.combo_bat.get() if self.combo_type.get() == "Ноутбук" else None,
            self.ent_cart.get() if self.combo_type.get() in ["МФУ", "Принтер"] else None,
            self.ent_refill.get() if self.combo_type.get() in ["МФУ", "Принтер"] else None
        )
        if self.editing_equipment_id is None:
            success, msg = self.db.add_equipment(data_insert)
            if success:
                messagebox.showinfo("Успех", "Оборудование добавлено")
                self.refresh_all()
                self._clear_equipment_form()
            else:
                messagebox.showerror("Ошибка", msg)
        else:
            success, msg = self.db.update_equipment(data_update, self.editing_equipment_id)
            if success:
                messagebox.showinfo("Успех", "Оборудование обновлено")
                self.refresh_all()
                self._clear_equipment_form()
            else:
                messagebox.showerror("Ошибка", msg)

    def _clear_equipment_form(self):
        self.editing_equipment_id = None
        self.ent_inv.delete(0, tk.END); self.ent_brand.delete(0, tk.END); self.ent_model.delete(0, tk.END)
        self.ent_serial.delete(0, tk.END); self.ent_loc.delete(0, tk.END); self.ent_ip.delete(0, tk.END)
        self.ent_balance.delete(0, tk.END); self.ent_mobo.delete(0, tk.END); self.ent_storage.delete(0, tk.END)
        self.ent_ram.delete(0, tk.END); self.ent_ports.delete(0, tk.END); self.ent_os.delete(0, tk.END)
        self.ent_os_ver.delete(0, tk.END); self.ent_cart.delete(0, tk.END); self.ent_refill.delete(0, tk.END)
        self.combo_type.set(""); self.combo_status.set("В работе")
        self.btn_install.config(state="disabled")

    def change_status(self):
        if self.editing_equipment_id is None:
            messagebox.showwarning("Внимание", "Выберите запись для изменения статуса в таблице")
            return
        new_status = self.combo_status.get()
        reason = f"Ручное изменение статуса через интерфейс"
        success, msg = self.db.update_equipment_status(self.editing_equipment_id, new_status, reason)
        if success:
            messagebox.showinfo("Успех", f"Статус изменён на: {new_status}")
            self.refresh_all()
        else:
            messagebox.showerror("Ошибка", msg)

    def install_equipment(self):
        if self.editing_equipment_id is None:
            messagebox.showwarning("Внимание", "Выберите оборудование в таблице")
            return
        current_status = self.combo_status.get()
        if current_status == "В ремонте":
            confirm = messagebox.askyesno("Подтверждение", "Техника была в ремонте у техника.\nВы проверили работоспособность и готовы установить в кабинет?\n\nСтатус изменится на: В работе")
            if confirm:
                reason = "Ремонт/ТО завершены, техника установлена в кабинет"
                self.db.update_equipment_status(self.editing_equipment_id, "В работе", reason)
                self.db.add_maintenance((self.editing_equipment_id, self.combo_type.get(), datetime.now().strftime("%Y-%m-%d"), "Установка после ремонта", reason, "Техник-программист", 0, 0, None))
                messagebox.showinfo("Успех", "Техника установлена! Статус: В работе")
        elif current_status == "С сервиса":
            confirm = messagebox.askyesno("Подтверждение", "Техника возвращена из сервиса и проверена.\nГотовы установить в кабинет?\n\nСтатус изменится на: В работе")
            if confirm:
                reason = "Техника проверена после сервиса, установлена в кабинет"
                self.db.update_equipment_status(self.editing_equipment_id, "В работе", reason)
                self.db.add_maintenance((self.editing_equipment_id, self.combo_type.get(), datetime.now().strftime("%Y-%m-%d"), "Установка после сервиса", reason, "Техник-программист", 0, 0, None))
                messagebox.showinfo("Успех", "Техника установлена! Статус: В работе")
        self.refresh_all()

    def delete_equipment(self):
        if self.editing_equipment_id is None:
            messagebox.showwarning("Внимание", "Выберите запись для удаления в таблице")
            return
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту запись?"):
            self.db.delete_equipment(self.editing_equipment_id)
            messagebox.showinfo("Успех", "Оборудование удалено")
            self.refresh_all()
            self._clear_equipment_form()

    def add_software_popup(self):
        if self.editing_equipment_id is None:
            messagebox.showwarning("Внимание", "Выберите ПК/Ноутбук в таблице")
            return
        selected = self.tree_eq.selection()
        if not selected:
            return
        item = self.tree_eq.item(selected[0])
        eq_type = item['values'][2]
        if eq_type not in ["ПК", "Ноутбук"]:
            messagebox.showwarning("Внимание", "ПО добавляется только для ПК/Ноутбуков")
            return
        top = tk.Toplevel(self.root)
        top.title("Добавить ПО")
        ttk.Label(top, text="Название:").grid(row=0, column=0, padx=5, pady=5)
        e_name = ttk.Entry(top, width=30)
        e_name.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(top, text="Версия:").grid(row=1, column=0, padx=5, pady=5)
        e_ver = ttk.Entry(top, width=15)
        e_ver.grid(row=1, column=1, padx=5, pady=5)
        def save():
            self.db.add_software(self.editing_equipment_id, e_name.get(), e_ver.get())
            messagebox.showinfo("OK", "ПО добавлено")
            top.destroy()
        ttk.Button(top, text="Сохранить", command=save).grid(row=2, column=1, pady=10)

    def setup_network_tab(self):
        frame_form = ttk.LabelFrame(self.tab_network, text="Добавление / Редактирование")
        frame_form.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_form, text="Инв. №:").grid(row=0, column=0, padx=5, pady=2)
        self.net_inv = ttk.Entry(frame_form, width=15)
        self.net_inv.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(frame_form, text="Тип:").grid(row=0, column=2, padx=5, pady=2)
        self.net_type = ttk.Combobox(frame_form, values=["Сервер", "Коммутатор", "Маршрутизатор", "WiFi-роутер", "Серверный шкаф"], state="readonly", width=15)
        self.net_type.grid(row=0, column=3, padx=5, pady=2)
        self.net_type.bind("<<ComboboxSelected>>", self.on_net_type_change)

        ttk.Label(frame_form, text="Марка:").grid(row=0, column=4, padx=5, pady=2)
        self.net_brand = ttk.Entry(frame_form, width=15)
        self.net_brand.grid(row=0, column=5, padx=5, pady=2)

        ttk.Label(frame_form, text="Модель:").grid(row=0, column=6, padx=5, pady=2)
        self.net_model = ttk.Entry(frame_form, width=15)
        self.net_model.grid(row=0, column=7, padx=5, pady=2)

        ttk.Label(frame_form, text="S/N:").grid(row=1, column=0, padx=5, pady=2)
        self.net_serial = ttk.Entry(frame_form, width=15)
        self.net_serial.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(frame_form, text="Место:").grid(row=1, column=2, padx=5, pady=2)
        self.net_loc = ttk.Entry(frame_form, width=15)
        self.net_loc.grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(frame_form, text="IP:").grid(row=1, column=4, padx=5, pady=2)
        self.net_ip = ttk.Entry(frame_form, width=15)
        self.net_ip.grid(row=1, column=5, padx=5, pady=2)

        ttk.Label(frame_form, text="На балансе с:").grid(row=1, column=6, padx=5, pady=2)
        self.net_balance = ttk.Entry(frame_form, width=15)
        self.net_balance.grid(row=1, column=7, padx=5, pady=2)

        self.net_frame_spec = ttk.Frame(frame_form)
        self.net_frame_spec.grid(row=2, column=0, columnspan=8, sticky="w", padx=5, pady=5)
        self.lbl_net_ports = ttk.Label(self.net_frame_spec, text="Кол-во портов:")
        self.ent_net_ports = ttk.Entry(self.net_frame_spec, width=10)
        self.lbl_net_bandwidth = ttk.Label(self.net_frame_spec, text="Пропускная:")
        self.ent_net_bandwidth = ttk.Entry(self.net_frame_spec, width=15)
        self.lbl_net_rack = ttk.Label(self.net_frame_spec, text="Инфо о шкафу:")
        self.ent_net_rack = ttk.Entry(self.net_frame_spec, width=25)

        btn_frame = ttk.Frame(frame_form)
        btn_frame.grid(row=3, column=0, columnspan=8, pady=10)
        ttk.Button(btn_frame, text="💾 Сохранить", command=self.save_network).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Редактировать", command=self.edit_network).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑 Удалить", command=self.delete_network).pack(side="left", padx=5)

        cols = ("ID", "Инв.", "Тип", "Марка", "Модель", "Место", "IP", "Статус")
        self.tree_net = ttk.Treeview(self.tab_network, columns=cols, show="headings")
        for c in cols: self.tree_net.heading(c, text=c)
        self.tree_net.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_net.bind("<<TreeviewSelect>>", self.on_network_select)
        self.editing_network_id = None

    def on_net_type_change(self, event):
        for widget in self.net_frame_spec.winfo_children():
            widget.grid_remove()
        t = self.net_type.get()
        if t in ["Сервер", "Коммутатор", "Маршрутизатор", "WiFi-роутер"]:
            self.lbl_net_ports.grid(row=0, column=0, padx=5); self.ent_net_ports.grid(row=0, column=1, padx=5)
            self.lbl_net_bandwidth.grid(row=0, column=2, padx=5); self.ent_net_bandwidth.grid(row=0, column=3, padx=5)
        elif t == "Серверный шкаф":
            self.lbl_net_rack.grid(row=0, column=0, padx=5); self.ent_net_rack.grid(row=0, column=1, padx=5)

    def on_network_select(self, event):
        selected = self.tree_net.selection()
        if not selected:
            return
        item = self.tree_net.item(selected[0])
        values = item['values']
        self.editing_network_id = values[0]
        for row in self.db.get_network_equipment():
            if row['id'] == values[0]:
                self.net_inv.delete(0, tk.END); self.net_inv.insert(0, row['inv_number'])
                self.net_type.set(row['type']); self.on_net_type_change(None)
                self.net_brand.delete(0, tk.END); self.net_brand.insert(0, row['brand'] if row['brand'] else "")
                self.net_model.delete(0, tk.END); self.net_model.insert(0, row['model'] if row['model'] else "")
                self.net_serial.delete(0, tk.END); self.net_serial.insert(0, row['serial_number'] if row['serial_number'] else "")
                self.net_loc.delete(0, tk.END); self.net_loc.insert(0, row['location'] if row['location'] else "")
                self.net_ip.delete(0, tk.END); self.net_ip.insert(0, row['ip_address'] if row['ip_address'] else "")
                self.net_balance.delete(0, tk.END); self.net_balance.insert(0, row['balance_date'] if row['balance_date'] else "")
                if row['type'] != "Серверный шкаф":
                    self.ent_net_ports.delete(0, tk.END); self.ent_net_ports.insert(0, row['ports_count'] if row['ports_count'] else "")
                    self.ent_net_bandwidth.delete(0, tk.END); self.ent_net_bandwidth.insert(0, row['bandwidth'] if row['bandwidth'] else "")
                else:
                    self.ent_net_rack.delete(0, tk.END); self.ent_net_rack.insert(0, row['rack_info'] if row['rack_info'] else "")
                break

    def save_network(self):
        self.editing_network_id = None
        self._save_network_data()

    def edit_network(self):
        if self.editing_network_id is None:
            messagebox.showwarning("Внимание", "Выберите запись для редактирования")
            return
        self._save_network_data()

    def _save_network_data(self):
        serial = self.net_serial.get() if self.net_type.get() != "Серверный шкаф" else None
        ip = self.net_ip.get() if self.net_type.get() != "Серверный шкаф" else None
        data_update = (
            self.net_inv.get(), self.net_type.get(), self.net_brand.get(), self.net_model.get(),
            serial, self.net_loc.get(), ip, self.net_balance.get(),
            self.ent_net_ports.get() if self.net_type.get() != "Серверный шкаф" else None,
            self.ent_net_bandwidth.get() if self.net_type.get() != "Серверный шкаф" else None,
            self.ent_net_rack.get() if self.net_type.get() == "Серверный шкаф" else None
        )
        data_insert = (
            self.net_inv.get(), self.net_type.get(), self.net_brand.get(), self.net_model.get(),
            serial, self.net_loc.get(), ip, "В работе", self.net_balance.get(),
            self.ent_net_ports.get() if self.net_type.get() != "Серверный шкаф" else None,
            self.ent_net_bandwidth.get() if self.net_type.get() != "Серверный шкаф" else None,
            self.ent_net_rack.get() if self.net_type.get() == "Серверный шкаф" else None
        )
        if self.editing_network_id is None:
            success, msg = self.db.add_network_equipment(data_insert)
            if success:
                messagebox.showinfo("Успех", "Сетевое оборудование добавлено")
                self.refresh_all()
                self._clear_network_form()
            else:
                messagebox.showerror("Ошибка", msg)
        else:
            success, msg = self.db.update_network_equipment(data_update, self.editing_network_id)
            if success:
                messagebox.showinfo("Успех", "Оборудование обновлено")
                self.refresh_all()
                self._clear_network_form()
            else:
                messagebox.showerror("Ошибка", msg)

    def _clear_network_form(self):
        self.editing_network_id = None
        self.net_inv.delete(0, tk.END); self.net_brand.delete(0, tk.END); self.net_model.delete(0, tk.END)
        self.net_serial.delete(0, tk.END); self.net_loc.delete(0, tk.END); self.net_ip.delete(0, tk.END)
        self.net_balance.delete(0, tk.END); self.ent_net_ports.delete(0, tk.END)
        self.ent_net_bandwidth.delete(0, tk.END); self.ent_net_rack.delete(0, tk.END)
        self.net_type.set("")

    def delete_network(self):
        if self.editing_network_id is None:
            messagebox.showwarning("Внимание", "Выберите запись для удаления")
            return
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту запись?"):
            self.db.delete_network_equipment(self.editing_network_id)
            messagebox.showinfo("Успех", "Оборудование удалено")
            self.refresh_all()
            self._clear_network_form()

    def setup_maintenance_tab(self):
        frame = ttk.LabelFrame(self.tab_maintenance, text="Новая запись в журнал")
        frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame, text="Оборудование:").grid(row=0, column=0, padx=5, pady=5)
        self.maint_equipment = ttk.Combobox(frame, state="readonly", width=50)
        self.maint_equipment.grid(row=0, column=1, columnspan=3, padx=5, pady=5)

        ttk.Label(frame, text="Тип работ:").grid(row=1, column=0, padx=5, pady=5)
        self.maint_type = ttk.Combobox(frame, values=["Диагностика", "Заправка", "Ремонт", "ТО", "Замена узла", "Настройка ПО", "Отправка в сервис", "Возврат из сервиса", "Замена картриджа"], state="readonly", width=20)
        self.maint_type.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Описание:").grid(row=1, column=2, padx=5, pady=5)
        self.maint_desc = ttk.Entry(frame, width=50)
        self.maint_desc.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(frame, text="Картридж:").grid(row=2, column=0, padx=5, pady=5)
        self.maint_cartridge = ttk.Combobox(frame, state="readonly", width=30)
        self.maint_cartridge.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Стоимость (руб):").grid(row=2, column=2, padx=5, pady=5)
        self.maint_cost = ttk.Entry(frame, width=15, state="disabled")
        self.maint_cost.grid(row=2, column=3, padx=5, pady=5)

        self.var_out = tk.BooleanVar()
        self.var_out.trace_add("write", self.toggle_cost)
        ttk.Checkbutton(frame, text="Внешний сервис (списание с контракта)", variable=self.var_out).grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        ttk.Label(frame, text="Техник:").grid(row=3, column=2, padx=5, pady=5)
        self.maint_tech = ttk.Entry(frame, width=20)
        self.maint_tech.insert(0, "Техник-программист")
        self.maint_tech.grid(row=3, column=3, padx=5, pady=5)

        ttk.Button(frame, text="Внести запись", command=self.save_maintenance).grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(frame, text="📥 Принято с сервиса", command=self.accept_from_service).grid(row=4, column=2, pady=10)
        ttk.Button(frame, text="✅ Картридж установлен", command=self.install_cartridge).grid(row=4, column=3, pady=10)

        cols = ("ID", "Дата", "Инв.№", "Тип", "Работы", "Описание", "Стоимость", "Сервис")
        self.tree_maint = ttk.Treeview(self.tab_maintenance, columns=cols, show="headings")
        for c in cols: self.tree_maint.heading(c, text=c)
        self.tree_maint.pack(fill="both", expand=True, padx=10, pady=10)

    def toggle_cost(self, *args):
        if self.var_out.get():
            self.maint_cost.config(state="normal")
        else:
            self.maint_cost.config(state="disabled")
            self.maint_cost.delete(0, tk.END)

    def save_maintenance(self):
        selected = self.maint_equipment.get()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите оборудование из списка")
            return
        parts = selected.split(" - ")
        if len(parts) < 2:
            messagebox.showerror("Ошибка", "Некорректный формат выбора")
            return
        equip_id = int(parts[0])
        equip_type = parts[2] if len(parts) > 2 else "Unknown"
        cost = 0.0
        if self.var_out.get():
            try:
                cost = float(self.maint_cost.get()) if self.maint_cost.get() else 0.0
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректная стоимость")
                return
        work_type = self.maint_type.get()
        cartridge_id = None
        cart_selected = self.maint_cartridge.get()
        if cart_selected:
            cart_parts = cart_selected.split(" - ")
            if len(cart_parts) > 0:
                cartridge_id = int(cart_parts[0])
        if work_type == "Отправка в сервис" and self.var_out.get():
            self.db.update_equipment_status(equip_id, "В сервисе", "Отправлено в сервисный центр")
            messagebox.showinfo("Инфо", "Статус изменён на: В сервисе")
        data = (equip_id, equip_type, datetime.now().strftime("%Y-%m-%d"), work_type,
                self.maint_desc.get(), self.maint_tech.get(), cost, 1 if self.var_out.get() else 0, cartridge_id)
        self.db.add_maintenance(data)
        messagebox.showinfo("Успех", "Запись добавлена в журнал")
        self.refresh_all()
        self.maint_desc.delete(0, tk.END)
        self.maint_cost.delete(0, tk.END)

    def accept_from_service(self):
        selected = self.maint_equipment.get()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите оборудование из списка")
            return
        parts = selected.split(" - ")
        if len(parts) < 2:
            messagebox.showerror("Ошибка", "Некорректный формат выбора")
            return
        equip_id = int(parts[0])
        try:
            cost = float(self.maint_cost.get()) if self.maint_cost.get() else 0.0
        except ValueError:
            cost = 0.0
        confirm = messagebox.askyesno("Подтверждение", f"Техника принята из сервисного центра.\nСтоимость ремонта: {cost:.2f} руб.\n\nСтатус изменится на: С сервиса")
        if confirm:
            self.db.update_equipment_status(equip_id, "С сервиса", f"Принято из сервиса. Стоимость: {cost:.2f} руб.")
            self.db.add_maintenance((equip_id, "Unknown", datetime.now().strftime("%Y-%m-%d"), "Возврат из сервиса", f"Техника принята из СЦ. Стоимость: {cost:.2f} руб.", "Техник-программист", cost, 1, None))
            messagebox.showinfo("Успех", "Техника принята! Статус: С сервиса (требуется проверка)")
            self.refresh_all()

    def install_cartridge(self):
        cart_selected = self.maint_cartridge.get()
        if not cart_selected:
            messagebox.showwarning("Внимание", "Выберите картридж из списка")
            return
        cart_parts = cart_selected.split(" - ")
        if len(cart_parts) < 1:
            messagebox.showerror("Ошибка", "Некорректный формат выбора картриджа")
            return
        cartridge_id = int(cart_parts[0])
        cartridge = self.db.get_cartridge_by_id(cartridge_id)
        if not cartridge:
            messagebox.showerror("Ошибка", "Картридж не найден")
            return
        current_status = cartridge['status']
        if current_status == 'С заправки':
            confirm = messagebox.askyesno("Подтверждение", 
                f"Картридж {cartridge['model']} проверен и готов к установке.\n\n"
                f"Статус изменится на: {'В работе' if not cartridge['is_spare'] else 'На хранении'}")
            if confirm:
                new_status = 'В работе' if not cartridge['is_spare'] else 'На хранении'
                reason = f"Картридж установлен после заправки"
                self.db.update_cartridge_status(cartridge_id, new_status, reason, 0)
                if cartridge['is_spare']:
                    messagebox.showinfo("Инфо", "Запасной картридж возвращён на хранение. Рабочий картридж установлен в принтер.")
                self.db.add_maintenance((cartridge['printer_id'], 'Принтер', datetime.now().strftime("%Y-%m-%d"), 
                    "Замена картриджа", f"Установлен картридж {cartridge['model']} после заправки", 
                    "Техник-программист", 0, 0, cartridge_id))
                messagebox.showinfo("Успех", f"Картридж установлен! Статус: {new_status}")
                self.refresh_all()
        else:
            messagebox.showwarning("Внимание", 
                f"Картридж должен быть в статусе 'С заправки'.\nТекущий статус: {current_status}")

    def setup_stock_tab(self):
        cols = ("Название", "Количество", "Ед.")
        self.tree_stock = ttk.Treeview(self.tab_stock, columns=cols, show="headings")
        for c in cols: self.tree_stock.heading(c, text=c)
        self.tree_stock.pack(fill="both", expand=True, padx=10, pady=10)

        frm = ttk.Frame(self.tab_stock)
        frm.pack(fill="x", padx=10, pady=5)
        ttk.Label(frm, text="Товар:").pack(side="left", padx=5)
        self.stock_item = ttk.Combobox(frm, state="readonly", width=30)
        self.stock_item.pack(side="left", padx=5)
        ttk.Label(frm, text="Кол-во:").pack(side="left", padx=5)
        self.stock_qty = ttk.Spinbox(frm, from_=1, to=1000, width=5)
        self.stock_qty.pack(side="left", padx=5)
        ttk.Button(frm, text="➕ Приход", command=lambda: self.stock_operation(1)).pack(side="left", padx=5)
        ttk.Button(frm, text="➖ Расход", command=lambda: self.stock_operation(-1)).pack(side="left", padx=5)
        ttk.Button(frm, text="🗑 Удалить", command=self.delete_stock_item).pack(side="left", padx=5)

        frm2 = ttk.LabelFrame(self.tab_stock, text="Добавить новый товар")
        frm2.pack(fill="x", padx=10, pady=10)
        ttk.Label(frm2, text="Название:").grid(row=0, column=0, padx=5, pady=5)
        self.new_stock_name = ttk.Entry(frm2, width=25)
        self.new_stock_name.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(frm2, text="Кол-во:").grid(row=0, column=2, padx=5, pady=5)
        self.new_stock_qty = ttk.Spinbox(frm2, from_=1, to=1000, width=5)
        self.new_stock_qty.grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(frm2, text="Ед.:").grid(row=0, column=4, padx=5, pady=5)
        self.new_stock_unit = ttk.Combobox(frm2, values=["шт", "м", "упак", "коробка"], width=10)
        self.new_stock_unit.grid(row=0, column=5, padx=5, pady=5)
        ttk.Button(frm2, text="Добавить", command=self.add_new_stock_item).grid(row=0, column=6, padx=10, pady=5)

    def stock_operation(self, direction):
        name = self.stock_item.get()
        if not name:
            messagebox.showwarning("Внимание", "Выберите товар")
            return
        try:
            qty = int(self.stock_qty.get()) * direction
            success, msg = self.db.update_stock(name, qty)
            if success:
                messagebox.showinfo("OK", f"{'Приходовано' if direction > 0 else 'Списано'}: {abs(qty)} {name}")
                self.refresh_all()
            else:
                messagebox.showerror("Ошибка", msg)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def add_new_stock_item(self):
        name = self.new_stock_name.get()
        qty = int(self.new_stock_qty.get())
        unit = self.new_stock_unit.get()
        if name and unit:
            success, msg = self.db.add_stock_item(name, qty, unit)
            if success:
                messagebox.showinfo("OK", "Товар добавлен на склад")
                self.refresh_all()
            else:
                messagebox.showerror("Ошибка", msg)

    def delete_stock_item(self):
        name = self.stock_item.get()
        if not name:
            messagebox.showwarning("Внимание", "Выберите товар для удаления")
            return
        if messagebox.askyesno("Подтверждение", f"Удалить товар '{name}' со склада?"):
            self.db.delete_stock_item(name)
            messagebox.showinfo("OK", "Товар удалён")
            self.refresh_all()

    def setup_cartridges_tab(self):
        cols = ("ID", "Модель", "Для принтера", "Принтер (Инв.)", "Статус", "Запасной", "Посл. заправка")
        self.tree_cart = ttk.Treeview(self.tab_cartridges, columns=cols, show="headings")
        for c in cols: self.tree_cart.heading(c, text=c)
        self.tree_cart.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_cart.bind("<<TreeviewSelect>>", self.on_cartridge_select)
        self.editing_cartridge_id = None

        frm = ttk.LabelFrame(self.tab_cartridges, text="Операции с картриджами")
        frm.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(frm, text="Картридж:").grid(row=0, column=0, padx=5, pady=5)
        self.cart_info = ttk.Label(frm, text="Не выбран", width=50, anchor="w")
        self.cart_info.grid(row=0, column=1, columnspan=3, padx=5, pady=5)
        
        ttk.Label(frm, text="Стоимость заправки:").grid(row=1, column=0, padx=5, pady=5)
        self.cart_cost = ttk.Entry(frm, width=15)
        self.cart_cost.grid(row=1, column=1, padx=5, pady=5)
        
        self.btn_refill = ttk.Button(frm, text="🖨 Заправить", command=self.send_to_refill)
        self.btn_refill.grid(row=1, column=2, padx=5, pady=5)
        
        self.btn_issue = ttk.Button(frm, text="📤 Выдача картриджа", command=self.issue_spare_cartridge)
        self.btn_issue.grid(row=1, column=3, padx=5, pady=5)
        
        self.btn_accept = ttk.Button(frm, text="📥 С заправки", command=self.accept_from_refill)
        self.btn_accept.grid(row=1, column=4, padx=5, pady=5)
        
        self.btn_install = ttk.Button(frm, text="✅ Картридж установлен", command=self.install_cartridge_from_tab)
        self.btn_install.grid(row=1, column=5, padx=5, pady=5)
        
        self.btn_history = ttk.Button(frm, text="📜 История", command=self.show_cartridge_history)
        self.btn_history.grid(row=1, column=6, padx=5, pady=5)
        
        self._update_cartridge_buttons()

        frm2 = ttk.LabelFrame(frm, text="Добавить запасной картридж")
        frm2.grid(row=2, column=0, columnspan=7, pady=10, sticky="w")
        
        ttk.Label(frm2, text="Модель:").grid(row=0, column=0, padx=5, pady=5)
        self.new_cart_model = ttk.Entry(frm2, width=15)
        self.new_cart_model.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frm2, text="Для принтера:").grid(row=0, column=2, padx=5, pady=5)
        self.cart_printer_select = ttk.Combobox(frm2, state="readonly", width=30)
        self.cart_printer_select.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(frm2, text="Кол-во:").grid(row=0, column=4, padx=5, pady=5)
        self.new_cart_qty = ttk.Spinbox(frm2, from_=1, to=50, width=5)
        self.new_cart_qty.grid(row=0, column=5, padx=5, pady=5)
        
        ttk.Button(frm2, text="Добавить", command=self.add_new_cartridge).grid(row=0, column=6, padx=10, pady=5)

    def _update_cartridge_buttons(self):
        if self.editing_cartridge_id is None:
            self.btn_refill.config(state="disabled")
            self.btn_issue.config(state="disabled")
            self.btn_accept.config(state="disabled")
            self.btn_install.config(state="disabled")
            self.btn_history.config(state="disabled")
            self.cart_info.config(text="Не выбран")
            self.cart_cost.config(state="disabled")
            return
        
        cartridge = self.db.get_cartridge_by_id(self.editing_cartridge_id)
        if not cartridge:
            return
        
        status = cartridge['status']
        is_spare = cartridge['is_spare']
        
        self.cart_info.config(text=f"{cartridge['model']} ({cartridge['printer_model']}) - {status} - {'Запасной' if is_spare else 'Рабочий'}")
        
        self.btn_refill.config(state="disabled")
        self.btn_issue.config(state="disabled")
        self.btn_accept.config(state="disabled")
        self.btn_install.config(state="disabled")
        self.btn_history.config(state="normal")
        self.cart_cost.config(state="disabled")
        
        if status == 'В работе':
            self.btn_refill.config(state="normal")
        elif status == 'К заправке':
            self.btn_refill.config(state="normal")
        elif status == 'На заправке':
            self.btn_accept.config(state="normal")
            self.cart_cost.config(state="normal")
        elif status == 'С заправки':
            self.btn_install.config(state="normal")
            self.cart_cost.config(state="normal")
        elif status == 'На хранении' and is_spare:
            self.btn_issue.config(state="normal")
        elif status == 'Задействован':
            pass

    def on_cartridge_select(self, event):
        selected = self.tree_cart.selection()
        if not selected:
            self.editing_cartridge_id = None
            self._update_cartridge_buttons()
            return
        item = self.tree_cart.item(selected[0])
        values = item['values']
        self.editing_cartridge_id = values[0]
        self._update_cartridge_buttons()

    def send_to_refill(self):
        if self.editing_cartridge_id is None:
            return
        cartridge = self.db.get_cartridge_by_id(self.editing_cartridge_id)
        current_status = cartridge['status']
        if current_status == 'В работе':
            confirm = messagebox.askyesno("Подтверждение", 
                f"Картридж {cartridge['model']} будет снят с принтера.\n"
                f"Статус изменится на: К заправке")
            if confirm:
                self.db.update_cartridge_status(self.editing_cartridge_id, 'К заправке', 
                    'Картридж снят с принтера, готовится к заправке')
                messagebox.showinfo("Успех", "Картридж подготовлен к заправке")
                self.refresh_all()
        elif current_status == 'К заправке':
            confirm = messagebox.askyesno("Подтверждение", 
                f"Картридж {cartridge['model']} будет отвезён в сервис.\n"
                f"Статус изменится на: На заправке")
            if confirm:
                self.db.update_cartridge_status(self.editing_cartridge_id, 'На заправке', 
                    'Картридж отвезён в сервисный центр на заправку')
                messagebox.showinfo("Успех", "Картридж отправлен в сервис")
                self.refresh_all()

    def issue_spare_cartridge(self):
        if self.editing_cartridge_id is None:
            return
        
        cartridge = self.db.get_cartridge_by_id(self.editing_cartridge_id)
        
        if cartridge['status'] != 'На хранении' or not cartridge['is_spare']:
            messagebox.showwarning("Внимание", "Можно выдавать только запасные картриджи со статусом 'На хранении'")
            return
        
        printers = self.db.get_printers_with_cartridges()
        printer_list = [f"{row['id']} - {row['inv_number']} - {row['model']} ({row['cartridge_model']})" for row in printers if row['cartridge_model'] == cartridge['model']]
        
        if not printer_list:
            messagebox.showwarning("Внимание", f"Нет принтеров с картриджем {cartridge['model']} в базе")
            return
        
        top = tk.Toplevel(self.root)
        top.title("Выдача картриджа")
        ttk.Label(top, text="Выберите принтер:").grid(row=0, column=0, padx=5, pady=5)
        combo_printer = ttk.Combobox(top, values=printer_list, state="readonly", width=60)
        combo_printer.grid(row=0, column=1, padx=5, pady=5)
        combo_printer.current(0)
        
        def confirm_issue():
            selected = combo_printer.get()
            parts = selected.split(" - ")
            printer_id = int(parts[0])
            printer_inv = parts[1]
            
            self.db.update_cartridge_status(self.editing_cartridge_id, 'Задействован', 
                f'Выдан на принтер {printer_inv}', 0)
            
            self.cursor = self.db.conn.cursor()
            self.cursor.execute("SELECT id FROM cartridges WHERE printer_id=? AND is_spare=0", (printer_id,))
            work_cart = self.cursor.fetchone()
            if work_cart:
                self.db.update_cartridge_status(work_cart[0], 'К заправке', 
                    'Заменён на запасной, отправлен на заправку', 0)
            
            self.db.link_cartridge_to_printer(self.editing_cartridge_id, printer_id, printer_inv, set_as_working=False)
            
            messagebox.showinfo("Успех", f"Картридж выдан на принтер {printer_inv}")
            top.destroy()
            self.refresh_all()
        
        ttk.Button(top, text="Подтвердить", command=confirm_issue).grid(row=1, column=1, pady=10)

    def accept_from_refill(self):
        if self.editing_cartridge_id is None:
            return
        cartridge = self.db.get_cartridge_by_id(self.editing_cartridge_id)
        if cartridge['status'] != 'На заправке':
            messagebox.showwarning("Внимание", "Можно принять только картриджи со статусом 'На заправке'")
            return
        try:
            cost = float(self.cart_cost.get()) if self.cart_cost.get() else 0.0
        except ValueError:
            cost = 0.0
        confirm = messagebox.askyesno("Подтверждение", 
            f"Картридж {cartridge['model']} принят из сервиса.\n"
            f"Стоимость заправки: {cost:.2f} руб.\n"
            f"Статус изменится на: С заправки")
        if confirm:
            self.db.update_cartridge_status(self.editing_cartridge_id, 'С заправки', 
                f'Принят из сервиса. Стоимость: {cost:.2f} руб.', cost)
            self.db.update_cartridge_refill_date(self.editing_cartridge_id, datetime.now().strftime("%Y-%m-%d"))
            self.db.add_maintenance((cartridge['printer_id'], 'Принтер', datetime.now().strftime("%Y-%m-%d"), 
                'Заправка картриджа', f'Картридж {cartridge['model']} заправлен. Стоимость: {cost:.2f} руб.', 
                'Техник-программист', cost, 1, self.editing_cartridge_id))
            messagebox.showinfo("Успех", f"Картридж принят! Статус: С заправки")
            self.refresh_all()

    # ========== ИСПРАВЛЕНО: Автоматическая замена запасного картриджа ==========
    def install_cartridge_from_tab(self):
        """Установка картриджа из вкладки картриджей"""
        if self.editing_cartridge_id is None:
            return
        
        cartridge = self.db.get_cartridge_by_id(self.editing_cartridge_id)
        
        if cartridge['status'] != 'С заправки':
            messagebox.showwarning("Внимание", "Можно установить только картриджи со статусом 'С заправки'")
            return
        
        # ПРОВЕРКА НА ЗАПАСНОЙ КАРТРИДЖ
        spare_cart = None
        if not cartridge['is_spare'] and cartridge['printer_id']:
            self.cursor = self.db.conn.cursor()
            self.cursor.execute("""
                SELECT id, model FROM cartridges 
                WHERE printer_id=? AND is_spare=1 AND status='Задействован'
            """, (cartridge['printer_id'],))
            spare_cart = self.cursor.fetchone()
        
        confirm_text = f"Картридж {cartridge['model']} проверен и готов к установке.\n\n"
        if spare_cart:
            confirm_text += f"⚠️ ВНИМАНИЕ: На принтере установлен запасной картридж.\n"
            confirm_text += f"После установки:\n"
            confirm_text += f"  • Рабочий картридж: В работе\n"
            confirm_text += f"  • Запасной картридж: На хранении\n\n"
        confirm_text += f"Статус изменится на: {'В работе' if not cartridge['is_spare'] else 'На хранении'}"
        
        confirm = messagebox.askyesno("Подтверждение", confirm_text)
        
        if confirm:
            if cartridge['is_spare']:
                self.db.update_cartridge_status(self.editing_cartridge_id, 'На хранении', 
                    'Запасной картридж возвращён на хранение после заправки', 0)
                self.db.link_cartridge_to_printer(self.editing_cartridge_id, None, None, set_as_working=False)
                messagebox.showinfo("Успех", "Запасной картридж возвращён на хранение")
            else:
                # 1. Меняем статус рабочего на "В работе"
                self.db.update_cartridge_status(self.editing_cartridge_id, 'В работе', 
                    'Картридж установлен в принтер после заправки', 0)
                
                # 2. Если был запасной - возвращаем его на хранение
                if spare_cart:
                    self.db.update_cartridge_status(spare_cart[0], 'На хранении', 
                        'Заменён рабочим картриджем после заправки', 0)
                    self.db.link_cartridge_to_printer(spare_cart[0], None, None, set_as_working=False)
                    
                    self.db.add_maintenance((cartridge['printer_id'], 'Принтер', 
                        datetime.now().strftime("%Y-%m-%d"), "Замена картриджа", 
                        f"Рабочий картридж {cartridge['model']} установлен после заправки. "
                        f"Запасной картридж возвращён на хранение.", 
                        "Техник-программист", 0, 0, self.editing_cartridge_id))
                    
                    messagebox.showinfo("Успех", 
                        "Рабочий картридж установлен в принтер!\n"
                        "Запасной картридж возвращён на хранение.")
                else:
                    messagebox.showinfo("Успех", "Картридж установлен в принтер")
            
            self.refresh_all()

    def show_cartridge_history(self):
        if self.editing_cartridge_id is None:
            return
        cartridge = self.db.get_cartridge_by_id(self.editing_cartridge_id)
        history = self.db.get_cartridge_history(self.editing_cartridge_id)
        top = tk.Toplevel(self.root)
        top.title(f"История картриджа {cartridge['model']}")
        top.geometry("800x500")
        text = tk.Text(top, height=25, width=100)
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert(tk.END, "=" * 100 + "\n")
        text.insert(tk.END, f"ИСТОРИЯ КАРТРИДЖА: {cartridge['model']}\n")
        text.insert(tk.END, f"Принтер: {cartridge['printer_model']} ({cartridge['linked_printer_inv']})\n")
        text.insert(tk.END, f"Запасной: {'Да' if cartridge['is_spare'] else 'Нет'}\n")
        text.insert(tk.END, "=" * 100 + "\n\n")
        headers = ["Дата", "Было", "Стало", "Причина", "Стоимость", "Техник"]
        text.insert(tk.END, " | ".join(headers) + "\n")
        text.insert(tk.END, "-" * 100 + "\n")
        for row in history:
            cost = f"{row[5]:.2f}" if row[5] else "-"
            text.insert(tk.END, f" | ".join([str(x) if x else "-" for x in row[:5]]) + f" | {cost}\n")
        ttk.Button(top, text="Закрыть", command=top.destroy).pack(pady=10)

    def add_new_cartridge(self):
        model = self.new_cart_model.get()
        printer_info = self.cart_printer_select.get()
        qty = int(self.new_cart_qty.get())
        if not model or not printer_info:
            messagebox.showwarning("Внимание", "Заполните модель и выберите принтер")
            return
        parts = printer_info.split(" - ")
        printer_model = parts[2] if len(parts) > 2 else "Unknown"
        success, msg = self.db.add_cartridge(model, printer_model, qty, is_spare=1, status='На хранении')
        if success:
            messagebox.showinfo("OK", "Запасной картридж добавлен")
            self.refresh_all()
            self.new_cart_model.delete(0, tk.END)
        else:
            messagebox.showerror("Ошибка", msg)

    def delete_cartridge(self, cartridge_id):
        if self.editing_cartridge_id is None:
            messagebox.showwarning("Внимание", "Выберите картридж для удаления в таблице")
            return
        if messagebox.askyesno("Подтверждение", f"Удалить картридж?"):
            self.db.delete_cartridge(self.editing_cartridge_id)
            messagebox.showinfo("OK", "Картридж удалён")
            self.refresh_all()
            self.editing_cartridge_id = None

    def setup_reports_tab(self):
        frm = ttk.Frame(self.tab_reports)
        frm.pack(fill="x", padx=10, pady=10)
        ttk.Button(frm, text="📋 Инвентаризация (Оборудование)", command=self.show_inventory_report).pack(side="left", padx=5)
        ttk.Button(frm, text="🌐 Инвентаризация (Сеть)", command=self.show_network_inventory_report).pack(side="left", padx=5)
        ttk.Button(frm, text="📊 По типам техники", command=self.show_type_report).pack(side="left", padx=5)
        ttk.Button(frm, text="🖨 По статусам картриджей", command=self.show_cartridge_status_report).pack(side="left", padx=5)
        ttk.Button(frm, text="📜 История статусов (выбранное)", command=self.show_status_history).pack(side="left", padx=5)
        self.report_text = tk.Text(self.tab_reports, height=30, width=140)
        self.report_text.pack(fill="both", expand=True, padx=10, pady=10)

    def show_inventory_report(self):
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "=" * 120 + "\n")
        self.report_text.insert(tk.END, "ОТЧЁТ ПО ИНВЕНТАРИЗАЦИИ ОБОРУДОВАНИЯ\n")
        self.report_text.insert(tk.END, f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        self.report_text.insert(tk.END, "=" * 120 + "\n\n")
        data = self.db.get_inventory_report()
        headers = ["Инв.№", "Тип", "Марка", "Модель", "S/N", "Кабинет", "IP", "Статус", "На балансе с"]
        self.report_text.insert(tk.END, " | ".join(headers) + "\n")
        self.report_text.insert(tk.END, "-" * 170 + "\n")
        for row in data:
            self.report_text.insert(tk.END, " | ".join(str(x) if x else "-" for x in row) + "\n")
        self.report_text.insert(tk.END, "\n" + "=" * 120 + "\n")
        self.report_text.insert(tk.END, f"Всего позиций: {len(data)}\n")

    def show_network_inventory_report(self):
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "=" * 120 + "\n")
        self.report_text.insert(tk.END, "ОТЧЁТ ПО ИНВЕНТАРИЗАЦИИ СЕТЕВОГО ОБОРУДОВАНИЯ\n")
        self.report_text.insert(tk.END, f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        self.report_text.insert(tk.END, "=" * 120 + "\n\n")
        data = self.db.get_network_inventory_report()
        headers = ["Инв.№", "Тип", "Марка", "Модель", "S/N", "Место", "IP", "Статус", "На балансе с"]
        self.report_text.insert(tk.END, " | ".join(headers) + "\n")
        self.report_text.insert(tk.END, "-" * 170 + "\n")
        for row in data:
            self.report_text.insert(tk.END, " | ".join(str(x) if x else "-" for x in row) + "\n")
        self.report_text.insert(tk.END, "\n" + "=" * 120 + "\n")
        self.report_text.insert(tk.END, f"Всего позиций: {len(data)}\n")

    def show_type_report(self):
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "=" * 100 + "\n")
        self.report_text.insert(tk.END, "ОТЧЁТ ПО ТЕХНИКЕ (ПО ТИПАМ)\n")
        self.report_text.insert(tk.END, f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        self.report_text.insert(tk.END, "=" * 100 + "\n\n")
        data = self.db.get_equipment_by_type_report()
        headers = ["Тип", "Всего", "В работе", "В ремонте", "В сервисе", "С сервиса", "Списано"]
        self.report_text.insert(tk.END, " | ".join(headers) + "\n")
        self.report_text.insert(tk.END, "-" * 100 + "\n")
        for row in data:
            self.report_text.insert(tk.END, " | ".join(str(x) for x in row) + "\n")

    def show_cartridge_status_report(self):
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "=" * 80 + "\n")
        self.report_text.insert(tk.END, "ОТЧЁТ ПО СТАТУСАМ КАРТРИДЖЕЙ\n")
        self.report_text.insert(tk.END, f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        self.report_text.insert(tk.END, "=" * 80 + "\n\n")
        data = self.db.get_cartridge_status_report()
        headers = ["Статус", "Количество"]
        self.report_text.insert(tk.END, " | ".join(headers) + "\n")
        self.report_text.insert(tk.END, "-" * 50 + "\n")
        for row in data:
            self.report_text.insert(tk.END, f" | {row[0]} | {row[1]}\n")

    def show_status_history(self):
        if self.editing_equipment_id is None:
            messagebox.showwarning("Внимание", "Выберите оборудование в таблице для просмотра истории")
            return
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "=" * 100 + "\n")
        self.report_text.insert(tk.END, f"ИСТОРИЯ ИЗМЕНЕНИЯ СТАТУСОВ\n")
        self.report_text.insert(tk.END, f"Оборудование: Инв. № {self.ent_inv.get()}\n")
        self.report_text.insert(tk.END, f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        self.report_text.insert(tk.END, "=" * 100 + "\n\n")
        data = self.db.get_status_history(self.editing_equipment_id)
        headers = ["Дата", "Было", "Стало", "Причина", "Техник"]
        self.report_text.insert(tk.END, " | ".join(headers) + "\n")
        self.report_text.insert(tk.END, "-" * 100 + "\n")
        for row in data:
            self.report_text.insert(tk.END, " | ".join(str(x) if x else "-" for x in row) + "\n")
        if not data:
            self.report_text.insert(tk.END, "\nИстория изменений не найдена\n")

    def setup_contract_tab(self):
        lbl = ttk.Label(self.tab_contract, text="МОНИТОРИНГ КОНТРАКТА НА СЕРВИС", font=("Arial", 18, "bold"))
        lbl.pack(pady=20)
        self.lbl_budget = ttk.Label(self.tab_contract, text="", font=("Arial", 16))
        self.lbl_budget.pack(pady=10)
        self.lbl_limit = ttk.Label(self.tab_contract, text=f"Лимит в месяц: {CONTRACT_LIMIT_MONTH} руб.", font=("Arial", 14))
        self.lbl_limit.pack(pady=5)
        ttk.Button(self.tab_contract, text="🔄 Обновить данные", command=self.refresh_contract).pack(pady=20)
        cols = ("Дата", "Инв.№", "Тип работ", "Описание", "Стоимость")
        self.tree_contract = ttk.Treeview(self.tab_contract, columns=cols, show="headings")
        for c in cols: self.tree_contract.heading(c, text=c)
        self.tree_contract.pack(fill="both", expand=True, padx=20, pady=20)

    def refresh_contract(self):
        spent = self.db.get_monthly_cost()
        remaining = CONTRACT_LIMIT_MONTH - spent
        color = "green" if remaining >= 0 else "red"
        text = f"Потрачено в этом месяце: {spent:.2f} руб.\n"
        text += f"Остаток лимита: {remaining:.2f} руб."
        self.lbl_budget.config(text=text, foreground=color)
        if remaining < 0:
            messagebox.showwarning("ВНИМАНИЕ", "Лимит контракта превышен!\nРекомендуется отложить плановые ремонты до следующего месяца.")
        for row in self.tree_contract.get_children(): self.tree_contract.delete(row)
        for row in self.db.get_maintenance(100):
            if row[7]:
                cost = f"{row[6]:.2f}" if row[6] else "0.00"
                self.tree_contract.insert("", "end", values=(row[1], row[2], row[4], row[5], cost))

    def refresh_all(self):
        for row in self.tree_eq.get_children(): self.tree_eq.delete(row)
        for row in self.db.get_equipment():
            self.tree_eq.insert("", "end", values=(row['id'], row['inv_number'], row['type'], row['brand'], row['model'], row['location'], row['status']))

        for row in self.tree_net.get_children(): self.tree_net.delete(row)
        for row in self.db.get_network_equipment():
            self.tree_net.insert("", "end", values=(row['id'], row['inv_number'], row['type'], row['brand'], row['model'], row['location'], row['ip_address'], row['status']))

        for row in self.tree_maint.get_children(): self.tree_maint.delete(row)
        for row in self.db.get_maintenance():
            service = "Да" if row[7] else "Нет"
            cost = f"{row[6]:.2f}" if row[6] else "-"
            self.tree_maint.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4], row[5], cost, service))

        for row in self.tree_stock.get_children(): self.tree_stock.delete(row)
        stock_data = self.db.get_stock()
        items = []
        for row in stock_data:
            self.tree_stock.insert("", "end", values=(row['name'], row['quantity'], row['unit']))
            items.append(row['name'])
        self.stock_item['values'] = items

        for row in self.tree_cart.get_children(): self.tree_cart.delete(row)
        cart_data = self.db.get_cartridges()
        for row in cart_data:
            spare_mark = "✓" if row['is_spare'] else ""
            self.tree_cart.insert("", "end", values=(
                row['id'], row['model'], row['printer_model'], 
                row['linked_printer_inv'] if row['linked_printer_inv'] else "-",
                row['status'], spare_mark, row['last_refill_date'] if row['last_refill_date'] else "-"
            ))
        
        printer_data = self.db.get_printers_with_cartridges()
        printer_list = [f"{row['id']} - {row['inv_number']} - {row['model']} ({row['cartridge_model']})" for row in printer_data]
        self.cart_printer_select['values'] = printer_list
        
        cart_list = [f"{row['id']} - {row['model']} ({row['printer_model']})" for row in cart_data]
        self.maint_cartridge['values'] = cart_list
        
        self._update_cartridge_buttons()

        equip_data = self.db.get_equipment_for_select()
        equip_list = [f"{row['id']} - {row['inv_number']} - {row['type']}" for row in equip_data]
        self.maint_equipment['values'] = equip_list

        self.refresh_contract()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
