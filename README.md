# Rutabaga — генератор логинов и email

**Rutabaga** — кроссплатформенный CLI для генерации логинов AD и почтовых адресов по маскам с плейсхолдерами.

Языки: [English](README.en.md) · [中文](README.zh.md)

---

## Быстрый старт

Стандартная генерация:
```bash
python main.py -m '$l.$s' -d corp.local -o logins.txt
```

Валидация сгенерированных почтовых адресов:
```bash
python main.py -m '$l.$s' -d corp.local -o logins.txt --validate -w 10 --sender check@access-workflow.com
```

Без `-V` в консоль выводятся баннер, настройки и статус; логины пишутся в файл. С `-V` логины идут в stdout. Без `-o` файл сохраняется в домашний каталог (`~/`), имя — по `-d` или случайный ID.

Флаг `-o` принимает **файл** или **каталог** (одинаково в обычном режиме и с `--validate`):
- каталог → внутри создаётся файл с автоименем (`corp.local.txt` или `corp.local_valid.txt` / `corp.local_invalid.txt`);
- файл → используется как есть (с `--validate` — `имя_valid.txt` и `имя_invalid.txt` рядом).

С `-v` / `--validate` rutabaga генерирует адреса и сразу проверяет их по SMTP (нужен `-d`). В stdout попадают только валидные почты; полный лог — в stderr.

---

## Плейсхолдеры

В маске поддерживаются **`$a`..`$z`** (одна буква = один плейсхолдер).

| Плейсхолдер | Описание | Источник данных |
|-------------|----------|-----------------|
| **`$n`** | Имя | `Names_M.txt` / `Names_F.txt` |
| **`$s`** | Фамилия | `Surnames_M.txt` / `Surnames_F.txt` |
| **`$m`** | Отчество | `Patronymics_M.txt` / `Patronymics_F.txt` |
| **`$l`** | Одна буква | алфавит из `-L` (по умолчанию a–z) |

Любую букву можно переопределить или добавить через **`-p letter=path`** (например, `-p a=./dept.txt` для `$a`). Несколько файлов: `-p a=./t1.txt,./t2.txt` или повторять `-p a=...`.

**Примеры масок:**

- `'$n.$s'` → `ivan.ivanov`, `maria.petrova`, ...
- `'$n.$s_$l'` → `ivan.ivanov_a`, `ivan.ivanov_b`, ...
- `'$l$l$l@domain.com'` → `aaa@domain.com`, `aab@domain.com`, ...
- `'$a_$n.$s'` с `-p a=./dept.txt` → `it_ivan.ivanov`, `hr_maria.petrova`, ...

В PowerShell используйте **одинарные кавычки**: `-m '$n.$s_$l'`.

---

## Параметры CLI

| Параметр | Описание |
|----------|----------|
| **`-m`**, **`--mask`** | Маска (обязательно). |
| **`-o`**, **`--output`** | Путь вывода: файл или каталог. Без `-o` — `~/` с автоименем по `-d` или случайному ID. |
| **`-d`**, **`--domain`** | Домен (например `corp.local` → подставится как `@corp.local`). |
| **`-s`**, **`--sex`** | `m` / `f` / `both` (по умолчанию `both`). |
| **`--data-root`** | Папка с файлами данных. По умолчанию `rutabaga/data`. |
| **`-L`**, **`--letters`** | Алфавит для `$l` (по умолчанию a–z). |
| **`-p`**, **`--placeholder`** | Кастомный плейсхолдер: `letter=path` (можно повторять). |
| **`--no-unique`** | Не убирать дубликаты между наборами. |
| **`-V`**, **`--verbose`** | Выводить логины в консоль (иначе только баннер и статус). |
| **`-v`**, **`--validate`** | SMTP-валидация сгенерированных адресов (требует `-d`). |
| **`-w`**, **`--workers`** | Потоки валидации (по умолчанию 15, только с `--validate`). |
| **`--sender`** | Адрес MAIL FROM для SMTP-проверки (только с `--validate`). |

Полный список: `python main.py -h`.

---

## Быстрые команды

| Задача | Команда |
|--------|--------|
| Логины в `~/corp.local.txt` (без `-o`) | `python main.py -m '$n.$s' -d corp.local` |
| Логины в файл (имя.фамилия@домен) | `python main.py -m '$n.$s' -d corp.local -o logins.txt` |
| Только мужские, данные по ГОСТ 7.79 | `python main.py -m '$n.$s_$l' -d example.com --data-root rutabaga/data_gost -s m -o out.txt` |
| Только женские, ГОСТ Р 7.0.34 | `python main.py -m '$n_$s' -d mail.ru --data-root rutabaga/data_gost_7034 -s f -o out.txt` |
| Мало комбинаций (алфавит 0 и 1) | `python main.py -m '$n.$s_$l' -L 01 -o out.txt` |
| Логины в консоль (и в файл) | `python main.py -m '$n.$s' -d corp.local -o out.txt -V` |
| Генерация + SMTP-валидация (каталог) | `python main.py -m '$n.$s' -d corp.local -v -o ./results` |
| SMTP-валидация (явный файл) | `python main.py -m '$n.$s' -d corp.local -v -o emails.txt` |

---

## Данные

По умолчанию используются файлы из **`rutabaga/data`**:

- `Names_M.txt`, `Surnames_M.txt`, `Patronymics_M.txt`
- `Names_F.txt`, `Surnames_F.txt`, `Patronymics_F.txt`

Можно указать свою папку: **`--data-root /path/to/folder`**.

### Варианты по ГОСТ

- **`rutabaga/data_gost/`** — только транслитерация **ГОСТ 7.79-2000** (система Б): й→j, без -off/-ow, -ey/-ei и т.п. Подключение: `--data-root rutabaga/data_gost`.
- **`rutabaga/data_gost_7034/`** — то же, что в `data_gost`, плюс варианты по **ГОСТ Р 7.0.34-2014** (й→I: Andrei, Sergei, -evich/-evna и т.д.). Подключение: `--data-root rutabaga/data_gost_7034`.

Наборы `data_gost` и `data_gost_7034` поставляются готовыми; отдельные скрипты пересборки в этом репозитории не входят.

---

Языки: [English](README.en.md) · [中文](README.zh.md)
