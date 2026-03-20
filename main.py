"""
Главный файл приложения АИС Техник-Программист v6.0
Модульная версия
"""
import tkinter as tk
from tkinter import ttk
from modules import (
    DB, EquipmentTab, NetworkTab, MaintenanceTab, 
    StockTab, CartridgesTab, ReportsTab, ContractTab
)


CONTRACT_LIMIT_MONTH = 50000


class App:
    def __init__(self, root):
        self.db = DB()
        self.root = root
        self.root.title("АИС Техник-Программист v6.0 (Модульная)")
        self.root.geometry("1500x900")

        # Создание вкладок
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
        self.tabs.add(self.tab_maintenance, text="🛠 Журнал обслуживания")
        self.tabs.add(self.tab_stock, text="📦 Склад")
        self.tabs.add(self.tab_cartridges, text="🖨 Картриджи")
        self.tabs.add(self.tab_reports, text="📊 Отчёты")
        self.tabs.add(self.tab_contract, text="💰 Контракт")

        # Инициализация модулей
        self.equipment_module = EquipmentTab(self.tab_equipment, self.db, self.refresh_all)
        self.network_module = NetworkTab(self.tab_network, self.db, self.refresh_all)
        self.maintenance_module = MaintenanceTab(self.tab_maintenance, self.db, self.refresh_all)
        self.stock_module = StockTab(self.tab_stock, self.db, self.refresh_all)
        self.cartridges_module = CartridgesTab(self.tab_cartridges, self.db, self.refresh_all)
        self.reports_module = ReportsTab(self.tab_reports, self.db, self.get_equipment_id)
        self.contract_module = ContractTab(self.tab_contract, self.db, CONTRACT_LIMIT_MONTH)

        self.refresh_all()

    def get_equipment_id(self):
        """Получение ID выбранного оборудования для отчётов"""
        return self.equipment_module.get_editing_id()

    def refresh_all(self):
        """Обновление всех таблиц и списков"""
        # Обновление таблицы оборудования
        for row in self.equipment_module.get_tree().get_children():
            self.equipment_module.get_tree().delete(row)
        for row in self.db.get_equipment():
            self.equipment_module.get_tree().insert("", "end", values=(
                row['id'], row['inv_number'], row['type'], row['brand'], 
                row['model'], row['location'], row['status']
            ))

        # Обновление таблицы сетевого оборудования
        for row in self.network_module.get_tree().get_children():
            self.network_module.get_tree().delete(row)
        for row in self.db.get_network_equipment():
            self.network_module.get_tree().insert("", "end", values=(
                row['id'], row['inv_number'], row['type'], row['brand'], 
                row['model'], row['location'], row['ip_address'], row['status']
            ))

        # Обновление журнала обслуживания
        for row in self.maintenance_module.get_tree().get_children():
            self.maintenance_module.get_tree().delete(row)
        for row in self.db.get_maintenance():
            service = "Да" if row[7] else "Нет"
            cost = f"{row[6]:.2f}" if row[6] else "-"
            self.maintenance_module.get_tree().insert("", "end", values=(
                row[0], row[1], row[2], row[3], row[4], row[5], cost, service
            ))

        # Обновление склада
        for row in self.stock_module.get_tree().get_children():
            self.stock_module.get_tree().delete(row)
        stock_data = self.db.get_stock()
        items = []
        for row in stock_data:
            self.stock_module.get_tree().insert("", "end", values=(
                row['name'], row['quantity'], row['unit']
            ))
            items.append(row['name'])
        self.stock_module.update_stock_combo(items)

        # Обновление картриджей
        for row in self.cartridges_module.get_tree().get_children():
            self.cartridges_module.get_tree().delete(row)
        cart_data = self.db.get_cartridges()
        for row in cart_data:
            spare_mark = "✓" if row['is_spare'] else ""
            self.cartridges_module.get_tree().insert("", "end", values=(
                row['id'], row['model'], row['printer_model'],
                row['linked_printer_inv'] if row['linked_printer_inv'] else "-",
                row['status'], spare_mark, row['last_refill_date'] if row['last_refill_date'] else "-"
            ))

        # Обновление списков для combo
        printer_data = self.db.get_printers_with_cartridges()
        printer_list = [f"{row['id']} - {row['inv_number']} - {row['model']} ({row['cartridge_model']})" 
                       for row in printer_data]
        self.cartridges_module.update_printer_combo(printer_list)

        cart_list = [f"{row['id']} - {row['model']} ({row['printer_model']})" for row in cart_data]
        self.maintenance_module.update_cartridge_combo(cart_list)

        # Обновление кнопки состояния картриджей
        self.cartridges_module._update_cartridge_buttons()

        # Обновление списка оборудования для журнала
        equip_data = self.db.get_equipment_for_select()
        equip_list = [f"{row['id']} - {row['inv_number']} - {row['type']}" for row in equip_data]
        self.maintenance_module.update_equipment_combo(equip_list)

        # Обновление контракта
        self.contract_module.refresh()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
