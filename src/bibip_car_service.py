from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale, FileIndexForObject, FileForObject
from operator import itemgetter
from exeptions import ObjectIsNotExists, DuplicateValue
from typing import Union
from decimal import Decimal
from datetime import datetime


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path

    def _get_position_for_insert_id(
            self,
            list_index: list,
            id: Union[int, str]
            ) -> int:
        """Функция принимает три параметра:
        - self: экземпляр класса CarService;
        - list_index: отсортированный список уникальных
        идентификаторов (id, vin, sale_number);
        - id: значение идентификатора, которое необходимо вставить
        в список, сохраняя порядок сортировки.
        Функция возвращает индекс, на который необходимо
        вставить id в список list_index.
        Либо вызывает исключение DuplicateValue, если
        такое значение уже имеется в списке.
        """
        if len(list_index) == 0 or id < list_index[0]:
            return 0
        if id > list_index[-1]:
            return len(list_index)
        left = 0
        right = len(list_index) - 1
        while right - left > 1:
            mid = (left + right) // 2
            if list_index[mid] == id:
                raise DuplicateValue
            if list_index[mid] < id:
                left = mid
            else:
                right = mid
        return right

    def _find_element_in_sorted_list(
            self,
            list_id: list,
            id: Union[str, int]
            ) -> int:
        """Функция принимает три параметра:
        - self: экземпляр класса CarService;
        - list_id: отсортированный список уникальных идентификаторов
          (id, vin, sale_number);
        - id: значение идентификатора, которое необходимо найти в списке.
        Функция возвращает индекс элемента списка list_id, равного id.
        Либо вызывает исключение ObjectIsNotExists, если такого значения нет.
        """
        left = 0
        right = len(list_id) - 1
        while left <= right:
            mid = (left + right) // 2
            if list_id[mid] == id:
                return mid
            if list_id[mid] < id:
                left = mid + 1
            else:
                right = mid - 1
        raise ObjectIsNotExists

    def _get_list_keys(self, all_lines: list, type_of_index: str) -> list:
        """Функция принимает три параметра:
        - self: экземпляр класса CarService;
        - all_lines: список строк, в начале которых указан индентификатор;
        - type_of_index: 'str' или 'int' в зависимости от типа индентификатора.
        Функция из каждой строки списка all_lines извлекает идентификатор,
        приводит его значение к указанному типу (type_of_index)
        и возвращает список этих идентификаторов.
        """
        all_indexes = []
        for line in all_lines:
            if type_of_index == 'int':
                all_indexes.append(int(line.split(';')[0]))
            if type_of_index == 'str':
                all_indexes.append(line.split(';')[0])
        return all_indexes

    def _get_line_number_by_identifier(
            self,
            identifier: Union[int, str],
            object: FileIndexForObject,
            ) -> Union[int, None]:
        """Функция принимает три параметра:
        - self: экземпляр класса CarService;
        - identifier: идентификатор объекта;
        - object: тип объекта для поиска в файле с индексами.
        Функция возращает номер строки, в которой находится информация
        об объекте с указанным идентификатором в соответствующем файле.
        Либо возвращает None, если файл или объект не найден.
        """
        try:
            with open(self.root_directory_path + object, 'r') as file_index:
                all_lines = file_index.readlines()
                if isinstance(identifier, str):
                    all_id = self._get_list_keys(all_lines, 'str')
                if isinstance(identifier, int):
                    all_id = self._get_list_keys(all_lines, 'int')
                line_number = self._find_element_in_sorted_list(
                    all_id,
                    identifier
                    )
                return int(all_lines[line_number].split(';')[1]) - 1
        except (ObjectIsNotExists, FileNotFoundError):
            return None

    def _create_string(self, list_info: list, min_length=0) -> str:
        """Функция принимает три параметра:
        - self: экземпляр класса CarService;
        - list_info: информация об объекте в виде строкового списка;
        - min_length: минимальная длина строки, которая должна получиться.
        Функция возращает строку с информацией об объекте
        в виде, готовом для записи в БД.
        """
        if min_length == 0:
            return ';'.join(list_info) + '\n'
        else:
            return ';'.join(list_info).ljust(min_length-1) + '\n'

    def _delete_index(self,
                      object: FileIndexForObject,
                      identifier: Union[int, str]
                      ):
        """Функция принимает три параметра:
        - self: экземпляр класса CarService;
        - object: тип объекта, индекс которого нужно удалить;
        - identifier: идентификатор объекта, индекс которого нужно удалить.
        Функция удаляет запись с индексом по указанному идентификатору.
        Либо вызывает исключение FileNotFoundError, если файл не найден.
        Либо вызывает исключение ObjectIsNotExists,
        если объект с таким идентификатором не существует.
        """
        # записали все индексы в список и удалили нужный
        try:
            with open(self.root_directory_path + object, 'r') as file_index:
                all_lines = file_index.readlines()
                if isinstance(identifier, int):
                    all_index = self._get_list_keys(all_lines, 'int')
                if isinstance(identifier, str):
                    all_index = self._get_list_keys(all_lines, 'str')
                index_for_delete = self._find_element_in_sorted_list(
                    all_index,
                    identifier
                    )
                del all_lines[index_for_delete]
        except FileNotFoundError:
            raise FileNotFoundError
        except ObjectIsNotExists:
            raise ObjectIsNotExists

        # собрали заново файл с индексами с учетом удаленного
        try:
            with open(self.root_directory_path + object, 'w+') as file_index:
                for line in all_lines:
                    file_index.write(line)
        except FileNotFoundError:
            raise FileNotFoundError

    def _insert_new_index(
            self,
            object: FileIndexForObject,
            identifier: Union[int, str],
            new_string: str
            ):
        """Функция принимает четыре параметра:
        - self: экземпляр класса CarService;
        - object: тип объекта, индекс которого нужно вставить;
        - identifier: идентификатор объекта, индекс которого нужно вставить;
        - new_string: строка, которую нужно вставить.
        Функция вставляет запись с индексом по указанному идентификатору.
        Либо вызывает исключение FileNotFoundError, если файл не найден.
        Либо вызывает исключение DuplicateValue,
        если объект с таким идентификатором уже существует.
        """
        # вставляем индекс указанного идентификатора
        try:
            with open(self.root_directory_path + object, 'a+') as file_index:
                file_index.seek(0)
                all_lines = file_index.readlines()
                if isinstance(identifier, int):
                    all_index = self._get_list_keys(all_lines, 'int')
                if isinstance(identifier, str):
                    all_index = self._get_list_keys(all_lines, 'str')
                position = self._get_position_for_insert_id(
                    all_index,
                    identifier
                    )
                all_lines.insert(position, new_string)
        except FileNotFoundError:
            raise FileNotFoundError
        except DuplicateValue:
            raise DuplicateValue

        # записываем изменения в файл
        try:
            with open(self.root_directory_path + object, 'w+') as file_index:
                file_index.writelines(all_lines)
        except FileNotFoundError:
            raise FileNotFoundError

    def _change_status_car(self, vin: str, status: CarStatus):
        """Функция принимает три параметра:
        - self: экземпляр класса CarService;
        - vin: идентификатор автомобиля;
        - status: статус, который необходимо установить.
        Функция вставляет запись с индексом по указанному идентификатору.
        Либо вызывает исключение FileNotFoundError, если файл не найден.
        Либо вызывает исключение ObjectIsNotExists,
        если объект с таким идентификатором не существует.
        """
        try:
            ind = self._get_line_number_by_identifier(vin, FileIndexForObject.car)
            if ind is None:
                return None
            with open(self.root_directory_path + FileForObject.car, 'r+') as file_cars:
                file_cars.seek(ind * 500)
                car_info = file_cars.read(500).strip().split(';')
                car_info[4] = status
                new_string = self._create_string(car_info, 500)
                file_cars.seek(ind * 500)
                file_cars.write(new_string)
        except FileNotFoundError:
            raise FileNotFoundError
        except ObjectIsNotExists:
            raise ObjectIsNotExists

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Union[Model, None]:
        """Функция принимает два параметра:
        - self: экземпляр класса CarService;
        - model: экземпляр класса Model.
        Функция вставляет запись о модели и сохраняет соответствующий индекс.
        Либо возвращает None, если такая модель уже существует в БД.
        """
        # проверяем, что такой модели еще нет в БД
        if self._get_line_number_by_identifier(model.id, FileIndexForObject.model) is None:
            # вставка модели
            with open(self.root_directory_path + FileForObject.model, 'a') as file_models:
                model_string = (f'{model.id};{model.name};'
                                f'{model.brand}').ljust(499) + '\n'
                file_models.write(model_string)
                line_number = file_models.tell() // 500
                # вставка индекса
                new_string = (f'{model.id};{line_number}\n')
                self._insert_new_index(
                    FileIndexForObject.model,
                    model.id,
                    new_string)
                return model
        return None

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Union[Car, None]:
        """Функция принимает два параметра:
        - self: экземпляр класса CarService;
        - car: экземпляр класса Car.
        Функция вставляет запись об авто и сохраняет соответствующий индекс.
        Либо возвращает None, если такой авто уже существует в БД.
        """
        # проверяем, что такого автомобиля еще нет в БД
        if self._get_line_number_by_identifier(car.vin, FileIndexForObject.car) is None:
            # вставка авто
            with open(self.root_directory_path + FileForObject.car, 'a') as file_cars:
                car_string = (f'{car.vin};{car.model};'
                              f'{car.price};{car.date_start};'
                              f'{car.status}').ljust(499) + '\n'
                file_cars.write(car_string)
                line_number = file_cars.tell() // 500
                # вставка индекса
                new_string = (f'{car.vin};{line_number}\n')
                self._insert_new_index(
                    FileIndexForObject.car,
                    car.vin,
                    new_string
                    )
                return car
        return None

    # Задание 2. Сохранение продаж
    def sell_car(self, sale: Sale):
        """Функция принимает два параметра:
        - self: экземпляр класса CarService;
        - sale: экземпляр класса Sale.
        Функция вставляет запись о продаже и сохраняет соответствующий индекс.
        Либо возвращает None, если такая продажа уже существует в БД.
        """
        # проверяем, что такой продажи еще нет в БД
        if self._get_line_number_by_identifier(sale.sales_number, FileIndexForObject.sale) is None:
            # вставка продажи
            with open(self.root_directory_path + FileForObject.sale, 'a') as file_sales:
                sale_string = (f'{sale.sales_number};{sale.car_vin};'
                                f'{sale.sales_date};'
                                f'{sale.cost};0').ljust(499) + '\n'
                file_sales.write(sale_string)
                line_number = file_sales.tell() // 500
                # вставка индекса
                new_string = (f'{sale.sales_number};{line_number}\n')
                self._insert_new_index(
                    FileIndexForObject.sale,
                    sale.sales_number,
                    new_string
                    )
                # меняем статус авто на sold
                self._change_status_car(sale.car_vin, CarStatus.sold)
        return None

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        """Функция принимает два параметра:
        - self: экземпляр класса CarService;
        - status: статус автомобиля.
        Функция возвращает список автомобилей с указанным статусом.
        Либо возвращает пустой список, если файл не существует.
        """
        available_cars = []
        try:
            with open(self.root_directory_path + FileForObject.car, 'r') as file_cars:
                for line in file_cars.readlines():
                    car_info = line.strip().split(';')
                    if car_info[4] == status:
                        current_car = Car(
                            vin=car_info[0],
                            model=int(car_info[1]),
                            price=Decimal(car_info[2]),
                            date_start=datetime(
                                int(car_info[3][:4]),
                                int(car_info[3][5:7]),
                                int(car_info[3][8:10])
                                ),
                            status=status)
                        available_cars.append(current_car)
        except FileNotFoundError:
            return []
        return available_cars

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> Union[CarFullInfo, None]:
        """Функция принимает два параметра:
        - self: экземпляр класса CarService;
        - vin: идентификатор автомобиля.
        Функция возвращает экземпляр класса CarFullInfo.
        Либо возвращает None, если файл или объект не найдены.
        """
        try:
            # Получаем информацию об авто из файла 'cars.txt'
            with open(self.root_directory_path + FileForObject.car, 'r') as file_cars:
                ind = self._get_line_number_by_identifier(
                    vin,
                    FileIndexForObject.car
                    )
                if ind is None:
                    return None
                file_cars.seek(ind * 500)
                car_info = file_cars.read(500).strip().split(';')
        except FileNotFoundError:
            return None
        except ObjectIsNotExists:
            return None

        try:
            # Получаем информацию о модели из файла 'models.txt'
            with open(self.root_directory_path + FileForObject.model, 'r') as file_models:
                ind = self._get_line_number_by_identifier(
                    int(car_info[1]),
                    FileIndexForObject.model
                    )
                if ind is None:
                    return None
                file_models.seek(ind * 500)
                model_info = file_models.read(500).strip().split(';')
        except FileNotFoundError:
            return None
        except ObjectIsNotExists:
            return None

        # Получаем информацию о продаже из файла 'sales.txt'
        sales_date = None
        sales_cost = None
        try:
            with open(self.root_directory_path + FileForObject.sale, 'r') as file_sales:
                for line in file_sales.readlines():
                    sale_info = line.strip().split(';')
                    if sale_info[1] == vin and sale_info[4] == '0':
                        sales_date = sale_info[2]
                        sales_cost = sale_info[3]
        except FileNotFoundError:
            pass

        current_car = CarFullInfo(
            vin=car_info[0],
            car_model_name=model_info[1],
            car_model_brand=model_info[2],
            price=Decimal(car_info[2]),
            date_start=car_info[3],
            status=car_info[4],
            sales_date=sales_date,
            sales_cost=sales_cost)

        return current_car

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str):
        """Функция принимает три параметра:
        - self: экземпляр класса CarService;
        - vin: идентификатор автомобиля, который нужно заменить;
        - new_vin: новый идентификатор автомобиля.
        Функция меняет идентификатор автомобиля в БД
        и меняет соответсвующий индекс.
        Либо возвращает None, если файл или объект не найдены.
        """
        # Обновляем vin в файле 'car.txt'
        try:
            with open(self.root_directory_path + FileForObject.car, 'r+') as file_cars:
                car_line_number = self._get_line_number_by_identifier(
                    vin,
                    FileIndexForObject.car
                    )
                if car_line_number is None:
                    return None
                file_cars.seek(500 * car_line_number)
                car_info = file_cars.read(500).strip().split(';')
                car_info[0] = new_vin
                new_car_string = self._create_string(car_info, min_length=500)
                # Записываем изменения в файл
                file_cars.seek(500 * car_line_number)
                file_cars.write(new_car_string)
        except FileNotFoundError:
            return None
        except ObjectIsNotExists:
            return None

        # Обновляем индекс в файле 'car_index.txt'
        self._delete_index(FileIndexForObject.car, vin)
        new_string = f'{new_vin};{car_line_number + 1}\n'
        self._insert_new_index(
            FileIndexForObject.car,
            new_vin,
            new_string
            )

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str):
        """Функция принимает два параметра:
        - self: экземпляр класса CarService;
        - sales_number: идентификатор продажи, которую нужно удалить.
        Функция ставит флаг is_deleted = true для указанной продажи,
        удаляет индекс этой продажи, меняет статус авто на 'available'.
        Либо возвращает None, если файл или объект не найдены.
        """
        # удаляем продажу (ставим флаг is_deleted = true)
        try:
            with open(self.root_directory_path + FileForObject.sale, 'r+') as file_sales:
                ind = self._get_line_number_by_identifier(
                    sales_number,
                    FileIndexForObject.sale
                    )
                if ind is None:
                    return None
                file_sales.seek(ind * 500)
                sales_info = file_sales.read(500).strip().split(';')
                # пометка is_deleted = true
                sales_info[-1] = '1'
                # записываем в файл
                file_sales.seek(ind * 500)
                file_sales.write(self._create_string(sales_info, 500))
                # удаляем индекс продажи и меняем статус авто на 'available'
                self._delete_index(FileIndexForObject.sale, sales_number)
            self._change_status_car(sales_info[1], CarStatus.available)
        except FileNotFoundError:
            return None
        except ObjectIsNotExists:
            return None

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        """Функция принимает один параметр:
        - self: экземпляр класса CarService.
        Функция считает количество продаж каждой модели авто
        и суммарную их стомость.
        Выбирает три модели, которые продавались чаще всего.
        Если модели имеют одинаковое количество продаж,
        выбирает более дорогие модели.
        Либо возвращает пустой список, если файл не существует.
        """
        # считает количество продаж и суммарную стоимость каждой модели авто
        number_sales_by_models = {}
        try:
            with open(self.root_directory_path + FileForObject.sale, 'r') as file_sales:
                for line in file_sales.readlines():
                    sale_info = line.strip().split(';')
                    vin = sale_info[1]
                    cost = Decimal(sale_info[3])
                    is_deleted = int(sale_info[4])
                    if not is_deleted:
                        car_info = self.get_car_info(vin)
                        if car_info is None:
                            continue
                        model_name = car_info.car_model_name 
                        if model_name in number_sales_by_models:
                            number_sales_by_models[model_name][0] += 1
                            number_sales_by_models[model_name][1] += cost
                        else:
                            number_sales_by_models[model_name] = [
                                1,
                                cost,
                                car_info.car_model_brand
                                ]
        except FileNotFoundError:
            return []

        # выбирает три модели, которые продавались чаще всего, если модели
        # имеют одинаковое количество продаж, выбирает более дорогие модели
        top_3 = sorted(
            number_sales_by_models.items(),
            key=itemgetter(1),
            reverse=True)[0:3]

        list_top_models = []
        for top in top_3:
            current_model = ModelSaleStats(
                car_model_name=top[0],
                brand=str(top[1][2]),
                sales_number=int(top[1][0])
                )
            list_top_models.append(current_model)

        return list_top_models
