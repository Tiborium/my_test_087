"""
Модуль склада
"""
import tkinter as tk
from tkinter import ttk, messagebox


class StockTab:
    def __init__(self, parent, db, refresh_callback):
        self.parent = parent
        self.db = db
        self.refresh_all = refresh_callback
        
        self.setup_ui()
    
    def setup_ui(self):
        """Создание интерфейса вкладки склада"""
        # Таблица
        cols = ("Название", "Количество", "Ед.")
        self.tree_stock = ttk.Treeview(self.parent, columns=cols, show="headings")
        for c in cols:
            self.tree_stock.heading(c, text=c)
        self.tree_stock.pack(fill="both", expand=True, padx=10, pady=10)

        # Панель операций
        frm = ttk.Frame(self.parent)
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

        # Добавление нового товара
        frm2 = ttk.LabelFrame(self.parent, text="Добавить новый товар")
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
        """Операция прихода/расхода товара"""
        name = self.stock_item.get()
        if not name:
            messagebox.showwarning("Внимание", "Выберите товар")
            return
        try:
            qty = int(self.stock_qty.get()) * direction
            success, msg = self.db.update_stock(name, qty)
            if success:
                action = "Приходовано" if direction > 0 else "Списано"
                messagebox.showinfo("OK", f"{action}: {abs(qty)} {name}")
                self.refresh_all()
            else:
                messagebox.showerror("Ошибка", msg)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def add_new_stock_item(self):
        """Добавление нового товара на склад"""
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
        """Удаление товара со склада"""
        name = self.stock_item.get()
        if not name:
            messagebox.showwarning("Внимание", "Выберите товар для удаления")
            return
        if messagebox.askyesno("Подтверждение", f"Удалить товар '{name}' со склада?"):
            self.db.delete_stock_item(name)
            messagebox.showinfo("OK", "Товар удалён")
            self.refresh_all()
    
    def get_tree(self):
        """Возвращает дерево для обновления данных"""
        return self.tree_stock
    
    def update_stock_combo(self, items):
        """Обновление списка товаров"""
        self.stock_item['values'] = items
