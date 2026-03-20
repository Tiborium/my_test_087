"""
Модули приложения Tech App v6

Доступные модули:
- database: Работа с базой данных
- equipment: Вкладка оборудования (ПК/Ноутбуки/Принтеры)
- network: Вкладка сетевого оборудования
- maintenance: Журнал обслуживания и ремонта
- stock: Склад
- cartridges: Управление картриджами
- reports: Отчёты
- contract: Мониторинг контракта
"""

from modules.database import DB
from modules.equipment import EquipmentTab
from modules.network import NetworkTab
from modules.maintenance import MaintenanceTab
from modules.stock import StockTab
from modules.cartridges import CartridgesTab
from modules.reports import ReportsTab
from modules.contract import ContractTab

__all__ = [
    'DB',
    'EquipmentTab',
    'NetworkTab',
    'MaintenanceTab',
    'StockTab',
    'CartridgesTab',
    'ReportsTab',
    'ContractTab'
]
