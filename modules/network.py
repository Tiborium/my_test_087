"""
Модуль работы с сетевым оборудованием
"""
import tkinter as tk
from tkinter import ttk, messagebox


class NetworkTab:
    def __init__(self, parent, db, refresh_callback):
        self.parent = parent
        self.db = db
        self.refresh_all = refresh_callback
        self.editing_network_id = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Создание интерфейса вкладки сетевого оборудования"""
        frame_form = ttk.LabelFrame(self.parent, text="Добавление / Редактирование")
        frame_form.pack(fill="x", padx=10, pady=5)

        # Первая строка полей
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

        # Вторая строка полей
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

        # Специфичные поля
        self.net_frame_spec = ttk.Frame(frame_form)
        self.net_frame_spec.grid(row=2, column=0, columnspan=8, sticky="w", padx=5, pady=5)
        
        self.lbl_net_ports = ttk.Label(self.net_frame_spec, text="Кол-во портов:")
        self.ent_net_ports = ttk.Entry(self.net_frame_spec, width=10)
        self.lbl_net_bandwidth = ttk.Label(self.net_frame_spec, text="Пропускная:")
        self.ent_net_bandwidth = ttk.Entry(self.net_frame_spec, width=15)
        self.lbl_net_rack = ttk.Label(self.net_frame_spec, text="Инфо о шкафу:")
        self.ent_net_rack = ttk.Entry(self.net_frame_spec, width=25)

        # Кнопки
        btn_frame = ttk.Frame(frame_form)
        btn_frame.grid(row=3, column=0, columnspan=8, pady=10)
        ttk.Button(btn_frame, text="💾 Сохранить", command=self.save_network).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Редактировать", command=self.edit_network).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑 Удалить", command=self.delete_network).pack(side="left", padx=5)

        # Таблица
        cols = ("ID", "Инв.", "Тип", "Марка", "Модель", "Место", "IP", "Статус")
        self.tree_net = ttk.Treeview(self.parent, columns=cols, show="headings")
        for c in cols:
            self.tree_net.heading(c, text=c)
        self.tree_net.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_net.bind("<<TreeviewSelect>>", self.on_network_select)
    
    def on_net_type_change(self, event):
        """Обработка изменения типа сетевого оборудования"""
        for widget in self.net_frame_spec.winfo_children():
            widget.grid_remove()
        t = self.net_type.get()
        if t in ["Сервер", "Коммутатор", "Маршрутизатор", "WiFi-роутер"]:
            self.lbl_net_ports.grid(row=0, column=0, padx=5); self.ent_net_ports.grid(row=0, column=1, padx=5)
            self.lbl_net_bandwidth.grid(row=0, column=2, padx=5); self.ent_net_bandwidth.grid(row=0, column=3, padx=5)
        elif t == "Серверный шкаф":
            self.lbl_net_rack.grid(row=0, column=0, padx=5); self.ent_net_rack.grid(row=0, column=1, padx=5)
    
    def on_network_select(self, event):
        """Обработка выбора оборудования в таблице"""
        selected = self.tree_net.selection()
        if not selected:
            return
        item = self.tree_net.item(selected[0])
        values = item['values']
        self.editing_network_id = values[0]
        
        for row in self.db.get_network_equipment():
            if row['id'] == values[0]:
                self._fill_form(row)
                break
    
    def _fill_form(self, row):
        """Заполнение формы данными из БД"""
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
    
    def save_network(self):
        """Сохранение нового сетевого оборудования"""
        self.editing_network_id = None
        self._save_network_data()
    
    def edit_network(self):
        """Редактирование выбранного сетевого оборудования"""
        if self.editing_network_id is None:
            messagebox.showwarning("Внимание", "Выберите запись для редактирования")
            return
        self._save_network_data()
    
    def _save_network_data(self):
        """Общая логика сохранения данных"""
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
        """Очистка формы"""
        self.editing_network_id = None
        self.net_inv.delete(0, tk.END); self.net_brand.delete(0, tk.END); self.net_model.delete(0, tk.END)
        self.net_serial.delete(0, tk.END); self.net_loc.delete(0, tk.END); self.net_ip.delete(0, tk.END)
        self.net_balance.delete(0, tk.END); self.ent_net_ports.delete(0, tk.END)
        self.ent_net_bandwidth.delete(0, tk.END); self.ent_net_rack.delete(0, tk.END)
        self.net_type.set("")
    
    def delete_network(self):
        """Удаление сетевого оборудования"""
        if self.editing_network_id is None:
            messagebox.showwarning("Внимание", "Выберите запись для удаления")
            return
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту запись?"):
            self.db.delete_network_equipment(self.editing_network_id)
            messagebox.showinfo("Успех", "Оборудование удалено")
            self.refresh_all()
            self._clear_network_form()
    
    def get_tree(self):
        """Возвращает дерево для обновления данных"""
        return self.tree_net
    
    def get_editing_id(self):
        """Возвращает ID редактируемого оборудования"""
        return self.editing_network_id
