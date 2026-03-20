"""
Модуль управления картриджами
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class CartridgesTab:
    def __init__(self, parent, db, refresh_callback):
        self.parent = parent
        self.db = db
        self.refresh_all = refresh_callback
        self.editing_cartridge_id = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Создание интерфейса вкладки картриджей"""
        # Таблица
        cols = ("ID", "Модель", "Для принтера", "Принтер (Инв.)", "Статус", "Запасной", "Посл. заправка")
        self.tree_cart = ttk.Treeview(self.parent, columns=cols, show="headings")
        for c in cols:
            self.tree_cart.heading(c, text=c)
        self.tree_cart.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_cart.bind("<<TreeviewSelect>>", self.on_cartridge_select)

        # Панель операций
        frm = ttk.LabelFrame(self.parent, text="Операции с картриджами")
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

        # Добавление запасного картриджа
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
        """Обновление состояния кнопок"""
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
        """Обработка выбора картриджа в таблице"""
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
        """Отправка картриджа на заправку"""
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
        """Выдача запасного картриджа"""
        if self.editing_cartridge_id is None:
            return

        cartridge = self.db.get_cartridge_by_id(self.editing_cartridge_id)

        if cartridge['status'] != 'На хранении' or not cartridge['is_spare']:
            messagebox.showwarning("Внимание", "Можно выдавать только запасные картриджи со статусом 'На хранении'")
            return

        printers = self.db.get_printers_with_cartridges()
        printer_list = [f"{row['id']} - {row['inv_number']} - {row['model']} ({row['cartridge_model']})" 
                       for row in printers if row['cartridge_model'] == cartridge['model']]

        if not printer_list:
            messagebox.showwarning("Внимание", f"Нет принтеров с картриджем {cartridge['model']} в базе")
            return

        top = tk.Toplevel(self.parent)
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

            cursor = self.db.conn.cursor()
            cursor.execute("SELECT id FROM cartridges WHERE printer_id=? AND is_spare=0", (printer_id,))
            work_cart = cursor.fetchone()
            if work_cart:
                self.db.update_cartridge_status(work_cart[0], 'К заправке',
                    'Заменён на запасной, отправлен на заправку', 0)

            self.db.link_cartridge_to_printer(self.editing_cartridge_id, printer_id, printer_inv, set_as_working=False)

            messagebox.showinfo("Успех", f"Картридж выдан на принтер {printer_inv}")
            top.destroy()
            self.refresh_all()

        ttk.Button(top, text="Подтвердить", command=confirm_issue).grid(row=1, column=1, pady=10)
    
    def accept_from_refill(self):
        """Принятие картриджа с заправки"""
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
    
    def install_cartridge_from_tab(self):
        """Установка картриджа из вкладки картриджей"""
        if self.editing_cartridge_id is None:
            return

        cartridge = self.db.get_cartridge_by_id(self.editing_cartridge_id)

        if cartridge['status'] != 'С заправки':
            messagebox.showwarning("Внимание", "Можно установить только картриджи со статусом 'С заправки'")
            return

        spare_cart = None
        if not cartridge['is_spare'] and cartridge['printer_id']:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT id, model FROM cartridges
                WHERE printer_id=? AND is_spare=1 AND status='Задействован'
            """, (cartridge['printer_id'],))
            spare_cart = cursor.fetchone()

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
                self.db.update_cartridge_status(self.editing_cartridge_id, 'В работе',
                    'Картридж установлен в принтер после заправки', 0)

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
        """Показ истории картриджа"""
        if self.editing_cartridge_id is None:
            return
        cartridge = self.db.get_cartridge_by_id(self.editing_cartridge_id)
        history = self.db.get_cartridge_history(self.editing_cartridge_id)
        
        top = tk.Toplevel(self.parent)
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
        """Добавление нового картриджа"""
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
    
    def get_tree(self):
        """Возвращает дерево для обновления данных"""
        return self.tree_cart
    
    def get_editing_id(self):
        """Возвращает ID редактируемого картриджа"""
        return self.editing_cartridge_id
    
    def update_printer_combo(self, printer_list):
        """Обновление списка принтеров"""
        self.cart_printer_select['values'] = printer_list
