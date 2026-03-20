"""
Модуль журнала обслуживания и ремонта
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class MaintenanceTab:
    def __init__(self, parent, db, refresh_callback):
        self.parent = parent
        self.db = db
        self.refresh_all = refresh_callback
        
        self.setup_ui()
    
    def setup_ui(self):
        """Создание интерфейса вкладки обслуживания"""
        frame = ttk.LabelFrame(self.parent, text="Новая запись в журнал")
        frame.pack(fill="x", padx=10, pady=10)

        # Оборудование
        ttk.Label(frame, text="Оборудование:").grid(row=0, column=0, padx=5, pady=5)
        self.maint_equipment = ttk.Combobox(frame, state="readonly", width=50)
        self.maint_equipment.grid(row=0, column=1, columnspan=3, padx=5, pady=5)

        # Тип работ
        ttk.Label(frame, text="Тип работ:").grid(row=1, column=0, padx=5, pady=5)
        self.maint_type = ttk.Combobox(frame, values=["Диагностика", "Заправка", "Ремонт", "ТО", "Замена узла", "Настройка ПО", "Отправка в сервис", "Возврат из сервиса", "Замена картриджа"], state="readonly", width=20)
        self.maint_type.grid(row=1, column=1, padx=5, pady=5)

        # Описание
        ttk.Label(frame, text="Описание:").grid(row=1, column=2, padx=5, pady=5)
        self.maint_desc = ttk.Entry(frame, width=50)
        self.maint_desc.grid(row=1, column=3, padx=5, pady=5)

        # Картридж
        ttk.Label(frame, text="Картридж:").grid(row=2, column=0, padx=5, pady=5)
        self.maint_cartridge = ttk.Combobox(frame, state="readonly", width=30)
        self.maint_cartridge.grid(row=2, column=1, padx=5, pady=5)

        # Стоимость
        ttk.Label(frame, text="Стоимость (руб):").grid(row=2, column=2, padx=5, pady=5)
        self.maint_cost = ttk.Entry(frame, width=15, state="disabled")
        self.maint_cost.grid(row=2, column=3, padx=5, pady=5)

        # Внешний сервис
        self.var_out = tk.BooleanVar()
        self.var_out.trace_add("write", self.toggle_cost)
        ttk.Checkbutton(frame, text="Внешний сервис (списание с контракта)", variable=self.var_out).grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        # Техник
        ttk.Label(frame, text="Техник:").grid(row=3, column=2, padx=5, pady=5)
        self.maint_tech = ttk.Entry(frame, width=20)
        self.maint_tech.insert(0, "Техник-программист")
        self.maint_tech.grid(row=3, column=3, padx=5, pady=5)

        # Кнопки
        ttk.Button(frame, text="Внести запись", command=self.save_maintenance).grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(frame, text="📥 Принято с сервиса", command=self.accept_from_service).grid(row=4, column=2, pady=10)
        ttk.Button(frame, text="✅ Картридж установлен", command=self.install_cartridge).grid(row=4, column=3, pady=10)

        # Таблица
        cols = ("ID", "Дата", "Инв.№", "Тип", "Работы", "Описание", "Стоимость", "Сервис")
        self.tree_maint = ttk.Treeview(self.parent, columns=cols, show="headings")
        for c in cols:
            self.tree_maint.heading(c, text=c)
        self.tree_maint.pack(fill="both", expand=True, padx=10, pady=10)
    
    def toggle_cost(self, *args):
        """Переключение доступности поля стоимости"""
        if self.var_out.get():
            self.maint_cost.config(state="normal")
        else:
            self.maint_cost.config(state="disabled")
            self.maint_cost.delete(0, tk.END)
    
    def save_maintenance(self):
        """Сохранение записи в журнал"""
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
        """Принятие техники из сервиса"""
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
        
        confirm = messagebox.askyesno("Подтверждение", 
            f"Техника принята из сервисного центра.\nСтоимость ремонта: {cost:.2f} руб.\n\nСтатус изменится на: С сервиса")
        if confirm:
            self.db.update_equipment_status(equip_id, "С сервиса", f"Принято из сервиса. Стоимость: {cost:.2f} руб.")
            self.db.add_maintenance((equip_id, "Unknown", datetime.now().strftime("%Y-%m-%d"), 
                "Возврат из сервиса", f"Техника принята из СЦ. Стоимость: {cost:.2f} руб.", 
                "Техник-программист", cost, 1, None))
            messagebox.showinfo("Успех", "Техника принята! Статус: С сервиса (требуется проверка)")
            self.refresh_all()
    
    def install_cartridge(self):
        """Установка картриджа после заправки"""
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
    
    def get_tree(self):
        """Возвращает дерево для обновления данных"""
        return self.tree_maint
    
    def update_equipment_combo(self, equipment_list):
        """Обновление списка оборудования"""
        self.maint_equipment['values'] = equipment_list
    
    def update_cartridge_combo(self, cartridge_list):
        """Обновление списка картриджей"""
        self.maint_cartridge['values'] = cartridge_list
