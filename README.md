# RUTABAGA 
### Генератор логинов для пентеста

**RUTABAGA** - это мощный инструмент для генерации логинов и email-адресов, основанный на ФИО и инициалах, предназначенный для тестирования систем на устойчивость к перебору паролей. Писалось как универсальный инструмент для работы с заказчиками из стран СНГ

### Использование
Для вызова помощи: `rutabaga.py -h` <br />
Генерация "Фамилия_Инициалы@mail.com":<br />
`rutaba.py --mask $f_$l$l --domain mail.com --sex f --output save.txt`<br />
`rutaba.py -m $f_$l$l -d mail.com -s m -o save.txt`<br />

**Параметры маски:**<br />
`$f` — Фамилия<br />
`$i` — Имя<br />
`$o` — Отчество<br />
`$l` — Инициалы<br />

**Параметры пола (опционально)** <br />
`m` — Мужской<br />
`f` — Женский<br />

**Опции**<br />
`-h`, `--help` — помощь<br />
`-d`, `--domain` — Добавить домен<br />
`-m`, `--mask` — Задать маску<br />
`-o`, `--output` — Указать путь для сохранения (по умолчанию сохраняет в `work.txt`) <br />
`-s`, `--sex` — Указать пол<br />

### Что делает RUTABAGA?

**Генерация логинов**<br />
RUTABAGA создает логины, используя комбинации фамилии, имени, отчества и инициалов. Это позволяет вам проверить все возможные комбинации, которые могут быть использованы реальными пользователями.<br />

**Разделение по полу**<br />
RUTABAGA использует справочные данные из файлов с фамилиями, именами и отчествами. <br />
`Data_F` - для женщин <br />
`Data_M` - для мужчин <br />
Дополнительные данные, такие как инициалы, хранятся в коде (строка `47`) <br />

**Поддержка кирилицы**<br />
Учтён фактор использования таких букв, как Е, Ю, Я, Ё в фамилиях и инициалах.<br />

**Генерация почтовых ящиков** <br />
Можно добавить почтовый домен как отдельный параметр или встроить его в маску.<br />

**Расширенная поддержка масок**<br />
Возможность создания более сложных масок для генерации логинов и почтовых адресов.<br />
Можно использовать символы-разделители и дублировать параметры маски<br />


<sup>Автор не несёт ответственности за неправомерное использование этого инструмента или любые действия, совершённые с его помощью</sup>
