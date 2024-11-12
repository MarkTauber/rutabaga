import argparse
import itertools
import sys
import os
import re
import threading
from datetime import datetime
import textwrap

if __name__ == "__main__":
    os.system("cls")

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawTextHelpFormatter,
    description=textwrap.dedent(
        """   __       ___       __        __         _\\|/_ 
  |__) |  |  |   /\\  |__)  /\\  / _`  /\\   (     )
  |  \\ \\__/  |  /~~\\ |__) /~~\\ \\__> /~~\\   '-,-'
  
  Email address and login generator.
  
example: 
  rutabaga.py -d domain.com -s f -m $f_$l$l -o save.txt

Mask parameters:
  $f - Last name
  $i - First name
  $o - Middle name
  $l - Letters

Gender parameters (optional):
  m - Male
  f - Female
        """
    ),
)

# Аргументы
# Маска
parser.add_argument(
    "-m",
    "--mask",
    type=str,
    required=True,
)

# Домен почты
parser.add_argument(
    "-d",
    "--domain",
    type=str,
    required=False,
    metavar="DOMAIN",
)

# Файл вывода
parser.add_argument(
    "-o",
    "--output",
    type=str,
    required=False,
    metavar="PATH",
)

# Пол
parser.add_argument(
    "-s",
    "--sex",
    type=str,
    choices=[
        "m",  # Мужской
        "f",  # Женский
    ],
    required=False,
)

# Йотированные буквы в инициалах
parser.add_argument(
    "-i",
    "--iotized",
    required=False,
    action="store_const",
    const=True,
    default=False,
)

# Потоки
parser.add_argument(
    "-t",
    "--threads",
    type=int,
    default=4,
)

args = parser.parse_args()
time = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
DOM = ""

iotized_symbols = [
    "ye",
    "ya",
    "yu",
    "yo",
]  # Йотированные буквы (Е Ё Ю Я)

symbols = [
    "a",
    "e",
    "r",
    "t",
    "y",
    "u",
    "i",
    "o",
    "p",
    "s",
    "d",
    "f",
    "g",
    "h",
    "j",
    "k",
    "l",
    "z",
    "c",
    "v",
    "b",
    "n",
    "m",
    "w",
    "q",
]


if args.domain:
    DOM = args.domain.strip()
    if DOM and "@" not in DOM:
        DOM = "@" + DOM


if args.iotized:
    symbols.extend(iotized_symbols)


# Загружаем данные из файлов
def load_data(sex=None):
    """Загружает данные о фамилиях, именах и отчествах из файлов.

    Загружает данные о фамилиях, именах и отчествах из файлов,
    расположенных в подкаталогах Data_M и Data_F,
    в зависимости от переданного параметра sex.

    Args:
        sex (str, optional): Пол ("m" или "f"). Если не указан,
            загружаются данные для обоих полов.  По умолчанию None.

    Returns:
        tuple: Кортеж из трех списков: фамилий, имен и отчеств.
               Возвращает пустые списки, если файлы не найдены.
    """
    if sex == "m":
        path = ".\\Data_M\\"
    elif sex == "f":
        path = ".\\Data_F\\"
    else:
        path = None

    if path:
        with open(path + "Familias_" + sex + ".txt", "r", encoding="UTF-8") as file:
            familias = [line.strip() for line in file]
        with open(path + "Names_" + sex + ".txt", "r", encoding="UTF-8") as file:
            names = [line.strip() for line in file]
        with open(path + "Surnames_" + sex + ".txt", "r", encoding="UTF-8") as file:
            surnames = [line.strip() for line in file]
    else:
        familias = []
        names = []
        surnames = []
        for gender in ("M", "F"):
            with open(
                f".\\Data_{gender}\\Familias_{gender}.txt", "r", encoding="UTF-8"
            ) as file:
                familias.extend([line.strip() for line in file])
            with open(
                f".\\Data_{gender}\\Names_{gender}.txt", "r", encoding="UTF-8"
            ) as file:
                names.extend([line.strip() for line in file])
            with open(
                f".\\Data_{gender}\\Surnames_{gender}.txt", "r", encoding="UTF-8"
            ) as file:
                surnames.extend([line.strip() for line in file])

    return familias, names, surnames


# Получаем шаблон от пользователя
template = args.mask

# Проверка на валидность шаблона
if "$" not in template:
    sys.exit("Ошибка: Шаблон должен содержать хотя бы одну переменную.")

# Разбиваем шаблон на части, учитывая символы после $
parts = re.split(r"\$([a-z]+)", template)

# Используем множество для хранения уникальных логинов
unique_logins = set()
lock = threading.Lock()


def generate_and_write(sex, file):
    """Генерирует и записывает уникальные логины в файл.

    Генерирует уникальные логины, используя данные о фамилиях,
    именах, отчествах и символах, и записывает их в файл.

    Args:
        sex (str): Пол ("m" или "f"), используемый для загрузки данных.
        file (file object): Открытый файл для записи сгенерированных логинов.
    """
    # Создаем локальный словарь для каждого потока
    data = {
        "f": [],
        "i": [],
        "o": [],
        "l": symbols,
    }
    familias, names, surnames = load_data(sex)
    data["f"] = familias
    data["i"] = names
    data["o"] = surnames
    variants = []
    for i, part in enumerate(parts):
        if i % 2 == 1:  # Если индекс нечетный - это плейсхолдер
            key = part
            if key in data:
                variants.append(data[key])
            else:
                print(f"Unknown placeholder: {key}")
                variants.append([part])
        else:  # Если индекс четный - это обычный текст
            variants.append([part])
    for combination in itertools.product(*variants):
        # Соединяем части в логин
        login = "".join(combination) + DOM
        # Проверяем, есть ли логин в множестве
        with lock:
            if login not in unique_logins:
                # Если логина нет, добавляем его в множество
                unique_logins.add(login)
                print(login)
                file.write(login + "\n")


def worker(sex, file):
    """Запускает генерацию и запись уникальных логинов для заданного пола.

    Функция-обертка, которая запускает генерацию и запись уникальных логинов
    в файл с помощью функции `generate_and_write` для указанного пола.

    Args:
        sex (str): Пол ("m" или "f"), используемый для загрузки данных.
        file (file object): Открытый файл для записи сгенерированных логинов.
    """
    generate_and_write(sex, file)


if __name__ == "__main__":
    threads = []
    output_file = args.output or f"rutabaga_[{time}].txt"
    try:
        with open(output_file, "a", encoding="UTF-8") as filezx:
            for sex in args.sex or ["m", "f"]:
                for _ in range(args.threads):
                    thread = threading.Thread(target=worker, args=(sex, filezx))
                    threads.append(thread)
                    thread.start()
            for thread in threads:
                thread.join()
    except FileNotFoundError:
        print(f"ERROR: cant create '{output_file}' or something.")
    except PermissionError:
        print(f"ERROR: No access to '{output_file}'.")

    print(f"\n{output_file} \n\nLogins generated: {len(unique_logins)}")
