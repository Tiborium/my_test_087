"""
Модуль отчётов
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class ReportsTab:
    def __init__(self, parent, db, get_equipment_id_callback):
        self.parent = parent
        self.db = db
        self.get_equipment_id = get_equipment_id_callback
        
        self.setup_ui()
    
    def setup_ui(self):
        """Создание интерфейса вкладки отчётов"""
        frm = ttk.Frame(self.parent)
        frm.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(frm, text="📋 Инвентаризация (Оборудование)", command=self.show_inventory_report).pack(side="left", padx=5)
        ttk.Button(frm, text="🌐 Инвентаризация (Сеть)", command=self.show_network_inventory_report).pack(side="left", padx=5)
        ttk.Button(frm, text="📊 По типам техники", command=self.show_type_report).pack(side="left", padx=5)
        ttk.Button(frm, text="🖨 По статусам картриджей", command=self.show_cartridge_status_report).pack(side="left", padx=5)
        ttk.Button(frm, text="📜 История статусов (выбранное)", command=self.show_status_history).pack(side="left", padx=5)
        
        self.report_text = tk.Text(self.parent, height=30, width=140)
        self.report_text.pack(fill="both", expand=True, padx=10, pady=10)
    
    def show_inventory_report(self):
        """Отчёт по инвентаризации оборудования"""
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
        """Отчёт по инвентаризации сетевого оборудования"""
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
        """Отчёт по типам техники"""
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
        """Отчёт по статусам картриджей"""
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
        """История изменения статусов оборудования"""
        equip_id = self.get_equipment_id()
        if equip_id is None:
            messagebox.showwarning("Внимание", "Выберите оборудование в таблице для просмотра истории")
            return
        
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "=" * 100 + "\n")
        self.report_text.insert(tk.END, f"ИСТОРИЯ ИЗМЕНЕНИЯ СТАТУСОВ\n")
        self.report_text.insert(tk.END, f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        self.report_text.insert(tk.END, "=" * 100 + "\n\n")
        
        data = self.db.get_status_history(equip_id)
        headers = ["Дата", "Было", "Стало", "Причина", "Техник"]
        self.report_text.insert(tk.END, " | ".join(headers) + "\n")
        self.report_text.insert(tk.END, "-" * 100 + "\n")
        for row in data:
            self.report_text.insert(tk.END, " | ".join(str(x) if x else "-" for x in row) + "\n")
        if not data:
            self.report_text.insert(tk.END, "\nИстория изменений не найдена\n")
