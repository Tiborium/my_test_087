"""
Модуль мониторинга контракта
"""
import tkinter as tk
from tkinter import ttk, messagebox


class ContractTab:
    def __init__(self, parent, db, contract_limit=50000):
        self.parent = parent
        self.db = db
        self.contract_limit = contract_limit
        
        self.setup_ui()
    
    def setup_ui(self):
        """Создание интерфейса вкладки контракта"""
        lbl = ttk.Label(self.parent, text="МОНИТОРИНГ КОНТРАКТА НА СЕРВИС", font=("Arial", 18, "bold"))
        lbl.pack(pady=20)
        
        self.lbl_budget = ttk.Label(self.parent, text="", font=("Arial", 16))
        self.lbl_budget.pack(pady=10)
        
        self.lbl_limit = ttk.Label(self.parent, text=f"Лимит в месяц: {self.contract_limit} руб.", font=("Arial", 14))
        self.lbl_limit.pack(pady=5)
        
        ttk.Button(self.parent, text="🔄 Обновить данные", command=self.refresh).pack(pady=20)
        
        cols = ("Дата", "Инв.№", "Тип работ", "Описание", "Стоимость")
        self.tree_contract = ttk.Treeview(self.parent, columns=cols, show="headings")
        for c in cols:
            self.tree_contract.heading(c, text=c)
        self.tree_contract.pack(fill="both", expand=True, padx=20, pady=20)
    
    def refresh(self):
        """Обновление данных контракта"""
        spent = self.db.get_monthly_cost()
        remaining = self.contract_limit - spent
        color = "green" if remaining >= 0 else "red"
        
        text = f"Потрачено в этом месяце: {spent:.2f} руб.\n"
        text += f"Остаток лимита: {remaining:.2f} руб."
        self.lbl_budget.config(text=text, foreground=color)
        
        if remaining < 0:
            messagebox.showwarning("ВНИМАНИЕ", 
                "Лимит контракта превышен!\nРекомендуется отложить плановые ремонты до следующего месяца.")
        
        # Очистка таблицы
        for row in self.tree_contract.get_children():
            self.tree_contract.delete(row)
        
        # Заполнение таблицы
        for row in self.db.get_maintenance(100):
            if row[7]:  # is_outsourced
                cost = f"{row[6]:.2f}" if row[6] else "0.00"
                self.tree_contract.insert("", "end", values=(row[1], row[2], row[4], row[5], cost))
    
    def get_tree(self):
        """Возвращает дерево для обновления данных"""
        return self.tree_contract
