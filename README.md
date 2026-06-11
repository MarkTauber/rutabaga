# Rutabaga — генератор логинов и email

**Rutabaga** — кроссплатформенный CLI для генерации логинов AD и почтовых адресов по маскам с плейсхолдерами.

Языки: [English](README.en.md) · [中文](README.zh.md)

---

## Быстрый старт

Зависимость для валидации (DNS MX):

```bash
pip install dnspython
```

Стандартная генерация:

```bash
python main.py -m '$l.$s' -d corp.local -o logins.txt
```

Валидация сгенерированных адресов (базовый вариант — SMTP RCPT):

```bash
python main.py -m '$n.$s' -d corp.local -v -o ./out
```

Расширенный вариант (явные `MAIL FROM` / `EHLO`, перебор MX):

```bash
python main.py -m '$n.$s' -d corp.local -v -o ./out \
  -w 10 --sender check@example.com --helo mx.example.com --mx
```

Без `-V` в консоль выводятся баннер, настройки и статус; логины пишутся в файл. С `-V` логины идут в stdout. **`-v` и `-V` одновременно использовать нельзя.** Без `-o` файл сохраняется в домашний каталог (`~/`), имя — по `-d` или случайный ID.

Флаг `-o` принимает **файл** или **каталог** (одинаково в обычном режиме и с `-v`):
- каталог → файл с автоименем (`corp.local.txt` или при `-v`: `corp.local_valid.txt`, `corp.local_invalid.txt`, `corp.local_inconclusive.txt`);
- файл → используется как есть (при `-v` рядом создаются `имя_valid.txt`, `имя_invalid.txt`, `имя_inconclusive.txt`).

---

## Валидация почты

С флагом **`-v`** / **`--validate`** rutabaga генерирует адреса и проверяет существование ящика (нужен **`-d`**). Подтверждённые адреса дублируются в stdout; полный лог — в stderr.

### Методы `-v [METHOD …]`

| Вызов | Методы | Поведение |
|-------|--------|-----------|
| `-v` | SMTP | RCPT TO + проверка catch-all |
| `-v SMTP` | SMTP | то же |
| `-v VRFY` | VRFY | только `VRFY` (без RCPT) |
| `-v VRFY EXPN` | VRFY, EXPN | только перечисленные; SMTP не добавляется |
| `-v SMTP VRFY` | SMTP, VRFY | RCPT, при неуспехе — `VRFY` на том же MX |

На одном MX: **EHLO** → (**STARTTLS**, если не отключён) → методы по порядку в одной сессии.

По умолчанию **`--sender`** и **`--helo`** — заглушки; для реальных MX лучше задавать явно.

### STARTTLS

- По умолчанию: если MX объявляет `STARTTLS` после EHLO — сессия шифруется.
- **`--no-starttls`** — plain SMTP (только вместе с `-v`).

### Флаги валидации

| Флаг | Назначение |
|------|------------|
| **`--mx`** | При RCPT 5xx пробовать следующий MX (только метод SMTP) |
| **`--sender`** | Адрес `MAIL FROM` |
| **`--helo`** | Имя хоста для `EHLO`/`HELO` |
| **`-w`** | Потоки (по умолчанию 15) |

### Выходные файлы

| Файл | Содержимое |
|------|------------|
| `*_valid.txt` | Подтверждённые адреса (по одному на строку) |
| `*_invalid.txt` | TSV: `email`, `status`, `reason` |
| `*_inconclusive.txt` | TSV; SMTP-коды 252, 421, 450–452 |

### Статусы

| Статус | Файл | Смысл |
|--------|------|-------|
| подтверждён | `valid` | Ящик, скорее всего, существует |
| `INVALID` | `invalid` | Явный отказ сервера |
| `CATCH_ALL` | `invalid` | Домен принимает любой адрес |
| `INCONCLUSIVE` | `inconclusive` | Нельзя утверждать exists / not exists |
| `UNKNOWN` | `invalid` | Все MX недоступны |

### Ограничения

RCPT и VRFY с внешнего IP ненадёжны для крупных почтовиков (Gmail, Outlook и т.п.); лучше работают на корпоративных MX. Команды **VRFY** и **EXPN** на большинстве серверов отключены.

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
| **`-v`**, **`--validate`** [METHOD…] | Валидация адресов (требует `-d`). Без METHOD — `SMTP` (STARTTLS). С METHOD — только перечисленные: `SMTP`, `VRFY`, `EXPN`. |
| **`-w`**, **`--workers`** | Потоки валидации (по умолчанию 15, только с `-v`). |
| **`--sender`** | Адрес MAIL FROM для SMTP-проверки (только с `-v`). |
| **`--helo`** | Имя хоста для EHLO/HELO при SMTP-проверке (только с `-v`). |
| **`--mx`** | При RCPT 5xx пробовать следующий MX (только с `-v`, метод SMTP). |
| **`--no-starttls`** | Не использовать STARTTLS, даже если MX его предлагает (только с `-v`). |

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
| Генерация + валидация (каталог) | `python main.py -m '$n.$s' -d corp.local -v -o ./results` |
| Валидация (явный базовый файл) | `python main.py -m '$n.$s' -d corp.local -v -o emails.txt` |
| VRFY + EXPN без RCPT | `python main.py -m '$n.$s' -d corp.local -v VRFY EXPN -o ./out` |
| SMTP + VRFY | `python main.py -m '$n.$s' -d corp.local -v SMTP VRFY -o ./out` |
| Без STARTTLS | `python main.py -m '$n.$s' -d corp.local -v --no-starttls -o ./out` |
| Перебор MX при RCPT 5xx | `python main.py -m '$n.$s' -d corp.local -v --mx -o ./out` |

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
