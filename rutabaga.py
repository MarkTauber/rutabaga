#TODO
# - переделать имя файла вывода по умолчанию
# ? разделить йотированные и обычные вариации ФИО
# 

import itertools
import argparse
import textwrap
import re
import os

os.system("cls")

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawTextHelpFormatter,
    description=textwrap.dedent('''   __       ___       __        __         _\\|/_ 
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
        ''')
)

# Аргументы
parser.add_argument("-m", "--mask", type=str, required=True)
parser.add_argument("-d", "--domain", type=str, required=False, metavar="DOMAIN")
parser.add_argument("-o", "--output", type=str, required=False, metavar="PATH")
parser.add_argument("-s", "--sex", type=str, choices=["m", "f"], required=False)
parser.add_argument("-i", "--iotized", type=str, required=False, metavar="")
args = parser.parse_args()

dom = ""

if args.domain:
    dom = args.domain
    if dom != "":
        if "@" not in dom:
            dom = "@" + dom

# Йотированные буквы (Е Ё Ю Я)
if args.iotized:
    symbols = ["a", "e", "r", "t", "y", "u", "i", "o", "p", "s", "d", "f", "g", "h", "j", "k", "l", "z", "c", "v", "b", "n", "m", "ye", "ya", "yu", "yo", "w", "q"]
else:
    symbols = ["a", "e", "r", "t", "y", "u", "i", "o", "p", "s", "d", "f", "g", "h", "j", "k", "l", "z", "c", "v", "b", "n", "m", "w", "q"]

# Загружаем данные из файлов
def load_data(sex=None):
    if sex == "m":
        with open('.\\Data_M\\Familias_M.txt', 'r') as file:
            familias = [line.strip() for line in file]
        with open('.\\Data_M\\Names_M.txt', 'r') as file:
            names = [line.strip() for line in file]
        with open('.\\Data_M\\Surnames_M.txt', 'r') as file:
            surnames = [line.strip() for line in file]
    elif sex == "f":
        with open('.\\Data_F\\Familias_F.txt', 'r') as file:
            familias = [line.strip() for line in file]
        with open('.\\Data_F\\Names_F.txt', 'r') as file:
            names = [line.strip() for line in file]
        with open('.\\Data_F\\Surnames_F.txt', 'r') as file:
            surnames = [line.strip() for line in file]
    else:  # Если sex не задан, используем оба пола
        with open('.\\Data_M\\Familias_M.txt', 'r') as file:
            familias_m = [line.strip() for line in file]
        with open('.\\Data_M\\Names_M.txt', 'r') as file:
            names_m = [line.strip() for line in file]
        with open('.\\Data_M\\Surnames_M.txt', 'r') as file:
            surnames_m = [line.strip() for line in file]

        with open('.\\Data_F\\Familias_F.txt', 'r') as file:
            familias_f = [line.strip() for line in file]
        with open('.\\Data_F\\Names_F.txt', 'r') as file:
            names_f = [line.strip() for line in file]
        with open('.\\Data_F\\Surnames_F.txt', 'r') as file:
            surnames_f = [line.strip() for line in file]

        familias = familias_m + familias_f
        names = names_m + names_f
        surnames = surnames_m + surnames_f
    return familias, names, surnames

# Получаем шаблон от пользователя
template = args.mask

# Разбиваем шаблон на части, учитывая символы после $
parts = re.split(r'\$([a-z]+)', template)

# Словарь для хранения данных по каждому плейсхолдеру
data = {
    'f': [],
    'i': [],
    'o': [],
    'l': symbols
}

# Генерируем все возможные варианты для каждой части
def generate_variants(sex=None):
    global data
    familias, names, surnames = load_data(sex)
    data['f'] = familias
    data['i'] = names
    data['o'] = surnames
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
    return variants

# Используем множество для хранения уникальных логинов
unique_logins = set()

def generate_and_write(sex, file):
    variants = generate_variants(sex)
    for combination in itertools.product(*variants):
        # Соединяем части в логин
        login = ''.join(combination) + dom
        # Проверяем, есть ли логин в множестве
        if login not in unique_logins:
            # Если логина нет, добавляем его в множество
            unique_logins.add(login)
            print(login)
            file.write(login+'\n')

# Запись в выбранный файл -о 
if args.output:
    try:
        with open(args.output, 'a') as filezx:
            if args.sex == "m":
                generate_and_write("m", filezx)
            elif args.sex == "f":
                generate_and_write("f", filezx)
            else:  # Если sex не задан, генерируем для обоих полов
                generate_and_write("m", filezx)
                generate_and_write("f", filezx)
    except FileNotFoundError:
        print(f"ERROR: cant create '{args.output}' or something.")
    except PermissionError:
        print(f"ERROR: No access to '{args.output}'.")     
        
# Запись в темп work.txt
else:
    # Цикл по всем комбинациям
    with open('work.txt', 'a') as filezx:
        if args.sex == "m":
            generate_and_write("m", filezx)
        elif args.sex == "f":
            generate_and_write("f", filezx)
        else:  # Если sex не задан, генерируем для обоих полов
            generate_and_write("m", filezx)
            generate_and_write("f", filezx)

# Вывод результата
print(f"\nLogins generated: {len(unique_logins)}")
