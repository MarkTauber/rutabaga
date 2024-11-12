import itertools
import threading
import argparse
import textwrap
import datetime
import os
import re

# TODO
# ? разделить йотированные и обычные вариации ФИО
#

if __name__ == '__main__':
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
parser.add_argument("-m", "--mask", type=str, required=True)
parser.add_argument("-d", "--domain", type=str, required=False, metavar="DOMAIN")
parser.add_argument("-o", "--output", type=str, required=False, metavar="PATH")
parser.add_argument("-s", "--sex", type=str, choices=["m", "f"], required=False)
parser.add_argument(
    "-i",
    "--iotized",
    required=False,
    action="store_const",
    const=True,
    default=False,
)
parser.add_argument("-t", "--threads", type=int, default=4)

args = parser.parse_args()
time = datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
dom = ""

iotized_symbols = ["ye", "ya", "yu", "yo"]  # Йотированные буквы (Е Ё Ю Я)

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
    dom = args.domain.strip()
    if dom and "@" not in dom:
        dom = "@" + dom


if args.iotized:
    symbols.extend(iotized_symbols)


# Загружаем данные из файлов
def load_data(sex=None):
    if sex == "m":
        path = ".\\Data_M\\"
    elif sex == "f":
        path = ".\\Data_F\\"
    else:
        path = None

    if path:
        with open(path + "Familias_" + sex + ".txt", "r") as file:
            familias = [line.strip() for line in file]
        with open(path + "Names_" + sex + ".txt", "r") as file:
            names = [line.strip() for line in file]
        with open(path + "Surnames_" + sex + ".txt", "r") as file:
            surnames = [line.strip() for line in file]
    else:
        familias = []
        names = []
        surnames = []
        for gender in ("M", "F"):
            with open(f".\\Data_{gender}\\Familias_{gender}.txt", "r") as file:
                familias.extend([line.strip() for line in file])
            with open(f".\\Data_{gender}\\Names_{gender}.txt", "r") as file:
                names.extend([line.strip() for line in file])
            with open(f".\\Data_{gender}\\Surnames_{gender}.txt", "r") as file:
                surnames.extend([line.strip() for line in file])

    return familias, names, surnames


# Получаем шаблон от пользователя
template = args.mask

# Проверка на валидность шаблона
if "$" not in template:
    print("Ошибка: Шаблон должен содержать хотя бы одну переменную.")
    exit(1)

# Разбиваем шаблон на части, учитывая символы после $
parts = re.split(r"\$([a-z]+)", template)

# Используем множество для хранения уникальных логинов
unique_logins = set()
lock = threading.Lock()


def generate_and_write(sex, file):
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
        login = "".join(combination) + dom
        # Проверяем, есть ли логин в множестве
        with lock:
            if login not in unique_logins:
                # Если логина нет, добавляем его в множество
                unique_logins.add(login)
                print(login)
                file.write(login + "\n")


def worker(sex, file):
    generate_and_write(sex, file)


if __name__ == "__main__":
    threads = []
    output_file = args.output or f"rutabaga_[{time}].txt"
    try:
        with open(output_file, "a") as filezx:
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

    print(f"\nrutabaga_[{time}].txt \n\nLogins generated: {len(unique_logins)}")
