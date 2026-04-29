"""
Модуль мониторинга контракта
"""
import tkinter as tk
from tkinter import ttk, messagebox


class ContractTab:
    def __init__(self, parent, db, refill_limit_month=15000, repair_limit_year=100000, refill_limit_year=100000):
        self.parent = parent
        self.db = db
        self.refill_limit_month = refill_limit_month
        self.repair_limit_year = repair_limit_year
        self.refill_limit_year = refill_limit_year
        
        self.setup_ui()
    
    def setup_ui(self):
        """Создание интерфейса вкладки контракта"""
        lbl = ttk.Label(self.parent, text="МОНИТОРИНГ КОНТРАКТОВ", font=("Arial", 18, "bold"))
        lbl.pack(pady=20)
        
        # Фрейм для контракта на заправку
        frame_refill = ttk.LabelFrame(self.parent, text="Контракт на заправку картриджей")
        frame_refill.pack(fill="x", padx=20, pady=10)
        
        self.lbl_refill_month = ttk.Label(frame_refill, text="", font=("Arial", 14))
        self.lbl_refill_month.pack(pady=5)
        
        self.lbl_refill_year = ttk.Label(frame_refill, text="", font=("Arial", 14))
        self.lbl_refill_year.pack(pady=5)
        
        # Фрейм для контракта на ремонт
        frame_repair = ttk.LabelFrame(self.parent, text="Контракт на ремонт оргтехники")
        frame_repair.pack(fill="x", padx=20, pady=10)
        
        self.lbl_repair_year = ttk.Label(frame_repair, text="", font=("Arial", 14))
        self.lbl_repair_year.pack(pady=5)
        
        ttk.Button(self.parent, text="🔄 Обновить данные", command=self.refresh).pack(pady=20)
        
        # Таблица расходов
        cols = ("Дата", "Контракт", "Тип работ", "Описание", "Стоимость")
        self.tree_contract = ttk.Treeview(self.parent, columns=cols, show="headings")
        for c in cols:
            self.tree_contract.heading(c, text=c)
        self.tree_contract.column("Контракт", width=150)
        self.tree_contract.pack(fill="both", expand=True, padx=20, pady=20)
    
    def refresh(self):
        """Обновление данных контракта"""
        from datetime import datetime
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Заправка - месяц
        spent_refill_month = self.db.get_monthly_cost("refill")
        remaining_refill_month = self.refill_limit_month - spent_refill_month
        color_refill_month = "green" if remaining_refill_month >= 0 else "red"
        
        text_refill_month = f"Потрачено в этом месяце: {spent_refill_month:.2f} руб. (лимит: {self.refill_limit_month} руб.)\n"
        text_refill_month += f"Остаток лимита: {remaining_refill_month:.2f} руб."
        self.lbl_refill_month.config(text=text_refill_month, foreground=color_refill_month)
        
        # Заправка - год
        spent_refill_year = self.db.get_yearly_cost("refill")
        remaining_refill_year = self.refill_limit_year - spent_refill_year
        color_refill_year = "green" if remaining_refill_year >= 0 else "red"
        
        text_refill_year = f"Потрачено в этом году: {spent_refill_year:.2f} руб. (лимит: {self.refill_limit_year} руб.)\n"
        text_refill_year += f"Остаток лимита: {remaining_refill_year:.2f} руб."
        self.lbl_refill_year.config(text=text_refill_year, foreground=color_refill_year)
        
        # Ремонт - год
        spent_repair_year = self.db.get_yearly_cost("repair")
        remaining_repair_year = self.repair_limit_year - spent_repair_year
        color_repair_year = "green" if remaining_repair_year >= 0 else "red"
        
        text_repair_year = f"Потрачено в этом году: {spent_repair_year:.2f} руб. (лимит: {self.repair_limit_year} руб.)\n"
        text_repair_year += f"Остаток лимита: {remaining_repair_year:.2f} руб."
        self.lbl_repair_year.config(text=text_repair_year, foreground=color_repair_year)
        
        # Предупреждения о превышении лимитов
        warnings = []
        if remaining_refill_month < 0:
            warnings.append("⚠️ Лимит контракта на заправку (месяц) превышен!")
        if remaining_refill_year < 0:
            warnings.append("⚠️ Лимит контракта на заправку (год) превышен!")
        if remaining_repair_year < 0:
            warnings.append("⚠️ Лимит контракта на ремонт (год) превышен!")
        
        if warnings:
            messagebox.showwarning("ВНИМАНИЕ", "\n".join(warnings))
        
        # Очистка таблицы
        for row in self.tree_contract.get_children():
            self.tree_contract.delete(row)
        
        # Заполнение таблицы всеми расходами
        for row in self.db.get_contract_expenses(limit=200):
            contract_name = "Заправка" if row[2] == "refill" else "Ремонт"
            cost = f"{row[6]:.2f}" if row[6] else "0.00"
            self.tree_contract.insert("", "end", values=(row[1], contract_name, row[3], row[4], cost))
    
    def get_tree(self):
        """Возвращает дерево для обновления данных"""
        return self.tree_contract
