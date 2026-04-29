"""
Модуль работы с оборудованием (ПК, ноутбуки, принтеры)
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class EquipmentTab:
    def __init__(self, parent, db, refresh_callback):
        self.parent = parent
        self.db = db
        self.refresh_all = refresh_callback
        self.editing_equipment_id = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Создание интерфейса вкладки оборудования"""
        frame_form = ttk.LabelFrame(self.parent, text="Добавление / Редактирование")
        frame_form.pack(fill="x", padx=10, pady=5)

        # Первая строка полей
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

        # Вторая строка полей
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

        # Специфичные поля
        self.frame_specific = ttk.Frame(frame_form)
        self.frame_specific.grid(row=2, column=0, columnspan=10, sticky="w", padx=5, pady=5)
        
        self._create_specific_fields()

        # Кнопки
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

        # Таблица
        cols = ("ID", "Инв.", "Тип", "Марка", "Модель", "Кабинет", "Статус")
        self.tree_eq = ttk.Treeview(self.parent, columns=cols, show="headings")
        for c in cols:
            self.tree_eq.heading(c, text=c)
        self.tree_eq.column("ID", width=40)
        self.tree_eq.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_eq.bind("<<TreeviewSelect>>", self.on_equipment_select)
    
    def _create_specific_fields(self):
        """Создание специфичных полей для разных типов оборудования"""
        self.lbl_mobo = ttk.Label(self.frame_specific, text="Мат.плата:")
        self.ent_mobo = ttk.Entry(self.frame_specific, width=20)
        self.lbl_storage = ttk.Label(self.frame_specific, text="Носитель:")
        self.ent_storage = ttk.Entry(self.frame_specific, width=25)
        self.lbl_ram = ttk.Label(self.frame_specific, text="RAM:")
        self.ent_ram = ttk.Entry(self.frame_specific, width=25)
        self.lbl_os = ttk.Label(self.frame_specific, text="ОС:")
        self.ent_os = ttk.Entry(self.frame_specific, width=20)
        self.lbl_ports = ttk.Label(self.frame_specific, text="Порты:")
        self.ent_ports = ttk.Entry(self.frame_specific, width=30)
        self.lbl_bat = ttk.Label(self.frame_specific, text="Батарея:")
        self.combo_bat = ttk.Combobox(self.frame_specific, values=["OK", "Износ", "Не держит (сеть)"], state="readonly", width=15)
        self.lbl_cart = ttk.Label(self.frame_specific, text="Картридж:")
        self.ent_cart = ttk.Entry(self.frame_specific, width=15)
        self.lbl_refill = ttk.Label(self.frame_specific, text="Посл. заправка:")
        self.ent_refill = ttk.Entry(self.frame_specific, width=12)
    
    def on_type_change(self, event):
        """Обработка изменения типа оборудования"""
        for widget in self.frame_specific.winfo_children():
            widget.grid_remove()
        t = self.combo_type.get()
        if t in ["ПК", "Ноутбук"]:
            self.lbl_mobo.grid(row=0, column=0, padx=5); self.ent_mobo.grid(row=0, column=1, padx=5)
            self.lbl_storage.grid(row=0, column=2, padx=5); self.ent_storage.grid(row=0, column=3, padx=5)
            self.lbl_ram.grid(row=0, column=4, padx=5); self.ent_ram.grid(row=0, column=5, padx=5)
            self.lbl_os.grid(row=0, column=6, padx=5); self.ent_os.grid(row=0, column=7, padx=5)
            self.lbl_ports.grid(row=1, column=0, padx=5, pady=5); self.ent_ports.grid(row=1, column=1, padx=5, pady=5)
            if t == "Ноутбук":
                self.lbl_bat.grid(row=1, column=2, padx=5, pady=5); self.combo_bat.grid(row=1, column=3, padx=5, pady=5)
        elif t in ["МФУ", "Принтер"]:
            self.lbl_cart.grid(row=0, column=0, padx=5); self.ent_cart.grid(row=0, column=1, padx=5)
            self.lbl_refill.grid(row=0, column=2, padx=5); self.ent_refill.grid(row=0, column=3, padx=5)
    
    def on_equipment_select(self, event):
        """Обработка выбора оборудования в таблице"""
        selected = self.tree_eq.selection()
        if not selected:
            self.btn_install.config(state="disabled")
            return
        item = self.tree_eq.item(selected[0])
        values = item['values']
        self.editing_equipment_id = values[0]
        
        for row in self.db.get_equipment():
            if row['id'] == values[0]:
                self._fill_form(row)
                break
        
        current_status = self.combo_status.get()
        if current_status in ["В ремонте", "С сервиса"]:
            self.btn_install.config(state="normal")
        else:
            self.btn_install.config(state="disabled")
    
    def _fill_form(self, row):
        """Заполнение формы данными из БД"""
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
            self.ent_os.delete(0, tk.END); self.ent_os.insert(0, row['os_name'] if row['os_name'] else "")
            self.ent_ports.delete(0, tk.END); self.ent_ports.insert(0, row['ports_info'] if row['ports_info'] else "")
            if row['type'] == "Ноутбук":
                self.combo_bat.set(row['battery_status'] if row['battery_status'] else "")
        elif row['type'] in ["МФУ", "Принтер"]:
            self.ent_cart.delete(0, tk.END); self.ent_cart.insert(0, row['cartridge_model'] if row['cartridge_model'] else "")
            self.ent_refill.delete(0, tk.END); self.ent_refill.insert(0, row['last_refill_date'] if row['last_refill_date'] else "")
    
    def save_equipment(self):
        """Сохранение нового оборудования"""
        self.editing_equipment_id = None
        self._save_equipment_data()
    
    def edit_equipment(self):
        """Редактирование выбранного оборудования"""
        if self.editing_equipment_id is None:
            messagebox.showwarning("Внимание", "Выберите запись для редактирования в таблице")
            return
        self._save_equipment_data()
    
    def _save_equipment_data(self):
        """Общая логика сохранения данных"""
        data_update = (
            self.ent_inv.get(), self.combo_type.get(), self.ent_brand.get(), self.ent_model.get(),
            self.ent_serial.get(), self.ent_loc.get(), self.ent_ip.get(), self.ent_balance.get(),
            self.ent_mobo.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_storage.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_ram.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_os.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_ports.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
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
            self.ent_os.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
            self.ent_ports.get() if self.combo_type.get() in ["ПК", "Ноутбук"] else None,
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
        """Очистка формы"""
        self.editing_equipment_id = None
        self.ent_inv.delete(0, tk.END); self.ent_brand.delete(0, tk.END); self.ent_model.delete(0, tk.END)
        self.ent_serial.delete(0, tk.END); self.ent_loc.delete(0, tk.END); self.ent_ip.delete(0, tk.END)
        self.ent_balance.delete(0, tk.END); self.ent_mobo.delete(0, tk.END); self.ent_storage.delete(0, tk.END)
        self.ent_ram.delete(0, tk.END); self.ent_os.delete(0, tk.END); self.ent_ports.delete(0, tk.END)
        self.ent_cart.delete(0, tk.END); self.ent_refill.delete(0, tk.END)
        self.combo_type.set(""); self.combo_status.set("В работе")
        self.btn_install.config(state="disabled")
    
    def change_status(self):
        """Изменение статуса оборудования"""
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
        """Установка техники после ремонта/сервиса"""
        if self.editing_equipment_id is None:
            messagebox.showwarning("Внимание", "Выберите оборудование в таблице")
            return
        current_status = self.combo_status.get()
        if current_status == "В ремонте":
            confirm = messagebox.askyesno("Подтверждение", 
                "Техника была в ремонте у техника.\nВы проверили работоспособность и готовы установить в кабинет?\n\nСтатус изменится на: В работе")
            if confirm:
                reason = "Ремонт/ТО завершены, техника установлена в кабинет"
                self.db.update_equipment_status(self.editing_equipment_id, "В работе", reason)
                self.db.add_maintenance((self.editing_equipment_id, self.combo_type.get(), 
                    datetime.now().strftime("%Y-%m-%d"), "Установка после ремонта", reason, 
                    "Техник-программист", 0, 0, None))
                messagebox.showinfo("Успех", "Техника установлена! Статус: В работе")
        elif current_status == "С сервиса":
            confirm = messagebox.askyesno("Подтверждение", 
                "Техника возвращена из сервиса и проверена.\nГотовы установить в кабинет?\n\nСтатус изменится на: В работе")
            if confirm:
                reason = "Техника проверена после сервиса, установлена в кабинет"
                self.db.update_equipment_status(self.editing_equipment_id, "В работе", reason)
                self.db.add_maintenance((self.editing_equipment_id, self.combo_type.get(), 
                    datetime.now().strftime("%Y-%m-%d"), "Установка после сервиса", reason, 
                    "Техник-программист", 0, 0, None))
                messagebox.showinfo("Успех", "Техника установлена! Статус: В работе")
        self.refresh_all()
    
    def delete_equipment(self):
        """Удаление оборудования"""
        if self.editing_equipment_id is None:
            messagebox.showwarning("Внимание", "Выберите запись для удаления в таблице")
            return
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту запись?"):
            self.db.delete_equipment(self.editing_equipment_id)
            messagebox.showinfo("Успех", "Оборудование удалено")
            self.refresh_all()
            self._clear_equipment_form()
    
    def add_software_popup(self):
        """Добавление ПО для ПК/Ноутбука"""
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
        
        top = tk.Toplevel(self.parent)
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
    
    def get_tree(self):
        """Возвращает дерево для обновления данных"""
        return self.tree_eq
    
    def get_editing_id(self):
        """Возвращает ID редактируемого оборудования"""
        return self.editing_equipment_id
    
    def get_current_status(self):
        """Возвращает текущий выбранный статус"""
        return self.combo_status.get()
    
    def get_current_type(self):
        """Возвращает текущий выбранный тип"""
        return self.combo_type.get()
    
    def get_inv_number(self):
        """Возвращает инвентарный номер"""
        return self.ent_inv.get()
