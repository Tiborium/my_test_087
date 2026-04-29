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
        cols = ("Название", "Количество", "Ед.", "Поставщик", "Стоимость")
        self.tree_stock = ttk.Treeview(self.parent, columns=cols, show="headings")
        for c in cols:
            self.tree_stock.heading(c, text=c)
        self.tree_stock.column("Поставщик", width=200)
        self.tree_stock.column("Стоимость", width=100)
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
        
        # Поставщик
        ttk.Label(frm, text="Поставщик:").pack(side="left", padx=5)
        suppliers = ["ИП Ермаков Евгений Викторович", "Другое", ""]
        self.stock_supplier = ttk.Combobox(frm, values=suppliers, state="readonly", width=25)
        self.stock_supplier.set("ИП Ермаков Евгений Викторович")
        self.stock_supplier.pack(side="left", padx=5)
        self.stock_supplier.bind("<<ComboboxSelected>>", self.on_supplier_change)
        
        # Поле для "Другое"
        self.stock_supplier_other = ttk.Entry(frm, width=20)
        self.stock_supplier_other.pack(side="left", padx=5)
        self.stock_supplier_other.pack_forget()  # Скрыто по умолчанию
        
        # Стоимость
        ttk.Label(frm, text="Стоимость:").pack(side="left", padx=5)
        self.stock_cost = ttk.Entry(frm, width=10)
        self.stock_cost.pack(side="left", padx=5)
        
        # Тип контракта
        ttk.Label(frm, text="Контракт:").pack(side="left", padx=5)
        self.stock_contract = ttk.Combobox(frm, values=["refill", "repair"], state="readonly", width=10)
        self.stock_contract.set("refill")
        self.stock_contract.pack(side="left", padx=5)
        
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
        
        # Поставщик для нового товара
        ttk.Label(frm2, text="Поставщик:").grid(row=0, column=6, padx=5, pady=5)
        self.new_stock_supplier = ttk.Combobox(frm2, values=suppliers, state="readonly", width=20)
        self.new_stock_supplier.set("ИП Ермаков Евгений Викторович")
        self.new_stock_supplier.grid(row=0, column=7, padx=5, pady=5)
        self.new_stock_supplier.bind("<<ComboboxSelected>>", lambda e: self.toggle_other_supplier(e, self.new_stock_supplier_other_add))
        
        self.new_stock_supplier_other_add = ttk.Entry(frm2, width=15)
        self.new_stock_supplier_other_add.grid(row=0, column=8, padx=5, pady=5)
        self.new_stock_supplier_other_add.grid_remove()
        
        ttk.Label(frm2, text="Стоимость:").grid(row=0, column=9, padx=5, pady=5)
        self.new_stock_cost = ttk.Entry(frm2, width=10)
        self.new_stock_cost.grid(row=0, column=10, padx=5, pady=5)
        
        ttk.Button(frm2, text="Добавить", command=self.add_new_stock_item).grid(row=0, column=11, padx=10, pady=5)
    
    def on_supplier_change(self, event):
        """Обработка изменения поставщика"""
        if self.stock_supplier.get() == "Другое":
            self.stock_supplier_other.pack(side="left", padx=5)
        else:
            self.stock_supplier_other.pack_forget()
    
    def toggle_other_supplier(self, event, entry_widget):
        """Переключение видимости поля для другого поставщика"""
        if event.widget.get() == "Другое":
            entry_widget.grid()
        else:
            entry_widget.grid_remove()
    
    def get_supplier_value(self, combo_widget, other_widget):
        """Получение значения поставщика"""
        supplier = combo_widget.get()
        if supplier == "Другое":
            return other_widget.get() if other_widget.get() else None
        elif supplier == "":
            return None
        return supplier
    
    def stock_operation(self, direction):
        """Операция прихода/расхода товара"""
        name = self.stock_item.get()
        if not name:
            messagebox.showwarning("Внимание", "Выберите товар")
            return
        
        supplier = self.get_supplier_value(self.stock_supplier, self.stock_supplier_other)
        
        try:
            cost = float(self.stock_cost.get()) if self.stock_cost.get() else 0.0
        except ValueError:
            cost = 0.0
        
        contract_type = self.stock_contract.get()
        
        try:
            qty = int(self.stock_qty.get()) * direction
            
            # Используем новый метод с поддержкой поставщика и стоимости
            success, msg = self.db.update_stock_with_supplier(name, qty, supplier, cost, contract_type if qty > 0 else None)
            
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
        supplier = self.get_supplier_value(self.new_stock_supplier, self.new_stock_supplier_other_add)
        cost = float(self.new_stock_cost.get()) if self.new_stock_cost.get() else 0.0
        
        if name and unit:
            success, msg = self.db.add_stock_item(name, qty, unit, supplier, cost)
            if success:
                messagebox.showinfo("OK", "Товар добавлен на склад")
                self.refresh_all()
                self.new_stock_name.delete(0, tk.END)
                self.new_stock_cost.delete(0, tk.END)
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
