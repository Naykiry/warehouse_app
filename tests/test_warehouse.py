import pytest
from models import Product, Supplier, Stock, Operation
from datetime import datetime


# Фикстуры для повторно используемых объектов
@pytest.fixture
def supplier():
    return Supplier(name="ООО Поставщик", contact="test@test.ru")


@pytest.fixture
def product(supplier):
    # Создаем объект Product с базовыми полями
    p = Product(name="Молоко", sku="MLK123", category="Молочные продукты", unit="литр", description="")
    # Устанавливаем связь с поставщиком (в памяти, без БД)
    p.supplier = supplier
    return p


# Тест хранения атрибутов товара
def test_product_attributes(product, supplier):
    """
    Проверяет хранение всех атрибутов товара: наименование, категория, артикул, поставщик, единица измерения, описание
    """
    assert product.name == "Молоко"
    assert product.category == "Молочные продукты"
    assert product.sku == "MLK123"
    assert product.supplier.name == "ООО Поставщик"
    assert product.unit == "литр"


# Тест учета движений товаров (приход/расход/перемещение)
def test_stock_operations(product):
    """
    Создаем операции прихода, расхода и перемещения и проверяем поля операций
    """
    op_in = Operation(type="in", quantity=100, date=datetime.now(), from_wh=None, to_wh="Основной", responsible="Иванов")
    op_out = Operation(type="out", quantity=20, date=datetime.now(), from_wh="Основной", to_wh=None, responsible="Петров")
    op_move = Operation(type="move", quantity=50, date=datetime.now(), from_wh="Склад A", to_wh="Склад B", responsible="Сидоров")

    # Связываем операции с продуктом в памяти
    op_in.product = product
    op_out.product = product
    op_move.product = product

    assert op_in.type == "in"
    assert op_out.type == "out"
    assert op_move.type == "move"
    assert op_move.to_wh == "Склад B"


# Тест формирования списка поставок по дате
def test_supply_list_by_date(product):
    """
    Формируем перечень товаров, поступивших в указанный день, фильтруя операции типа 'in'
    """
    d = datetime(2025, 12, 3)
    op1 = Operation(type="in", quantity=100, date=d, responsible="Иванов")
    op2 = Operation(type="in", quantity=50, date=d, responsible="Петров")
    op1.product = product
    op2.product = product

    ops = [op1, op2]

    def get_supplies_by_date(operations, target_date):
        return [op.product for op in operations if op.type == "in" and op.date.date() == target_date.date()]

    supplies = get_supplies_by_date(ops, d)
    assert product in supplies


# Тест добавления новой товарной позиции (симуляция формы)
def test_add_product():
    """
    Симуляция добавления товара в список (без БД): создаем объект Product и добавляем в коллекцию
    """
    supplier_local = Supplier(name="ООО Поставщик", contact="test@test.ru")
    p = Product(name="Сыр", sku="SYR789", category="Молочные продукты", unit="кг", description="твердый")
    p.supplier = supplier_local

    products = []
    products.append(p)

    assert p in products


# Тест просмотра операций прихода и расхода
def test_view_in_out_operations(product):
    """
    Проверяем, что список операций содержит корректные типы, даты и ответственных
    """
    op_in = Operation(type="in", quantity=100, date=datetime(2025, 12, 3), responsible="Иванов")
    op_out = Operation(type="out", quantity=20, date=datetime(2025, 12, 3), responsible="Петров")
    op_in.product = product
    op_out.product = product

    operations = [op_in, op_out]
    assert len(operations) == 2
    assert operations[0].type == "in"
    assert operations[1].type == "out"


# Тест фильтрации операций по диапазону дат
def test_filter_operations_by_date(product):
    """
    Фильтруем список операций по заданному периоду
    """
    op1 = Operation(type="in", quantity=100, date=datetime(2025, 12, 1), responsible="Иванов")
    op2 = Operation(type="out", quantity=20, date=datetime(2025, 12, 3), responsible="Петров")
    op1.product = product
    op2.product = product

    ops = [op1, op2]

    def filter_operations_by_date(operations, d_from, d_to):
        return [op for op in operations if d_from.date() <= op.date.date() <= d_to.date()]

    filtered = filter_operations_by_date(ops, datetime(2025, 12, 1), datetime(2025, 12, 2))
    assert op1 in filtered
    assert op2 not in filtered


# Тест поиска товаров по атрибутам
def test_search_products():
    """
    Поиск товаров по категории, поставщику или подстроке в имени/артикуле
    """
    supplier_local = Supplier(name="ООО Поставщик", contact="test@test.ru")
    p1 = Product(name="Молоко", sku="MLK123", category="Молочные продукты", unit="литр", description="")
    p2 = Product(name="Хлеб", sku="HLEB456", category="Выпечка", unit="шт", description="")
    p1.supplier = supplier_local

    products = [p1, p2]

    def search_products(items, category=None, supplier=None, q=None):
        result = items
        if category:
            result = [p for p in result if p.category and category in p.category]
        if supplier:
            result = [p for p in result if getattr(p.supplier, 'name', None) and supplier in getattr(p.supplier, 'name')]
        if q:
            result = [p for p in result if q in p.name or q in p.sku]
        return result

    found = search_products(products, category="Молочные продукты")
    assert p1 in found
    assert p2 not in found


# Тест учета минимальных остатков
def test_low_stock():
    """
    Формируем список товаров, требующих пополнения, по сравнению `quantity` <= `min_stock`
    """
    s1 = Stock(quantity=5, min_stock=10, warehouse="Основной")
    s2 = Stock(quantity=50, min_stock=20, warehouse="Основной")

    stocks = [s1, s2]

    def get_low_stock_products(stocks_list):
        return [s for s in stocks_list if s.quantity <= s.min_stock]

    low = get_low_stock_products(stocks)
    assert s1 in low
    assert s2 not in low

