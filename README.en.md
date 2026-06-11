# Rutabaga — Login and Email Generator

**Rutabaga** is a cross-platform CLI that generates AD logins and email addresses from mask templates with placeholders.

Languages: [Русский](README.md) · [中文](README.zh.md)

---

## Quick start

Standard generation:
```bash
python main.py -m '$l.$s' -d corp.local -o logins.txt
```

Generation with mail validation:
```bash
python main.py -m '$l.$s' -d corp.local -o logins.txt --validate -w 10 --sender check@access-workflow.com
```

Without `-V`, the console shows a banner, settings, and status; logins are written to the output file. With `-V`, logins go to stdout. Without `-o`, output goes to the home directory (`~/`), named from `-d` or a random ID.

`-o` accepts a **file** or **directory** (same in normal mode and with `--validate`):
- directory → auto-named file inside (`corp.local.txt`, or `corp.local_valid.txt` / `corp.local_invalid.txt`);
- file → used as-is (with `--validate` → `name_valid.txt` and `name_invalid.txt` alongside).

With `-v` / `--validate`, rutabaga generates addresses and checks them via SMTP (`-d` required). Only valid emails go to stdout; status goes to stderr.

---

## Placeholders

The mask supports **`$a`..`$z`** (one letter = one placeholder).

| Placeholder | Description | Data source |
|-------------|-------------|--------------|
| **`$n`** | First name | `Names_M.txt` / `Names_F.txt` |
| **`$s`** | Surname | `Surnames_M.txt` / `Surnames_F.txt` |
| **`$m`** | Patronymic | `Patronymics_M.txt` / `Patronymics_F.txt` |
| **`$l`** | Single letter | Alphabet from `-L` (default a–z) |

Any letter can be overridden or added via **`-p letter=path`** (e.g. `-p a=./dept.txt` for `$a`). Multiple files: `-p a=./t1.txt,./t2.txt` or repeat `-p a=...`.

**Mask examples:**

- `'$n.$s'` → `ivan.ivanov`, `maria.petrova`, ...
- `'$n.$s_$l'` → `ivan.ivanov_a`, `ivan.ivanov_b`, ...
- `'$l$l$l@domain.com'` → `aaa@domain.com`, `aab@domain.com`, ...
- `'$a_$n.$s'` with `-p a=./dept.txt` → `it_ivan.ivanov`, `hr_maria.petrova`, ...

On PowerShell use **single quotes**: `-m '$n.$s_$l'`.

---

## CLI options

| Option | Description |
|--------|-------------|
| **`-m`**, **`--mask`** | Mask template (required). |
| **`-o`**, **`--output`** | Output path: file or directory. Omitted: save to `~/` with auto name from `-d` or random ID. |
| **`-d`**, **`--domain`** | Domain (e.g. `corp.local` → appended as `@corp.local`). |
| **`-s`**, **`--sex`** | `m` / `f` / `both` (default `both`). |
| **`--data-root`** | Directory with data files. Default: `rutabaga/data`. |
| **`-L`**, **`--letters`** | Alphabet for `$l` (default a–z). |
| **`-p`**, **`--placeholder`** | Custom placeholder: `letter=path` (repeatable). |
| **`--no-unique`** | Do not deduplicate across data sets. |
| **`-V`**, **`--verbose`** | Print logins to console (otherwise only banner and status). |
| **`-v`**, **`--validate`** | SMTP-validate generated addresses (requires `-d`). |
| **`-w`**, **`--workers`** | Validation worker threads (default 15, with `--validate`). |
| **`--sender`** | MAIL FROM address for SMTP checks (with `--validate`). |

Full list: `python main.py -h`.

---

## Quick commands

| Task | Command |
|------|--------|
| Logins to `~/corp.local.txt` (no `-o`) | `python main.py -m '$n.$s' -d corp.local` |
| Logins to file (firstname.surname@domain) | `python main.py -m '$n.$s' -d corp.local -o logins.txt` |
| Male only, GOST 7.79 data | `python main.py -m '$n.$s_$l' -d example.com --data-root rutabaga/data_gost -s m -o out.txt` |
| Female only, GOST R 7.0.34 data | `python main.py -m '$n_$s' -d mail.ru --data-root rutabaga/data_gost_7034 -s f -o out.txt` |
| Few combinations (letters 0 and 1) | `python main.py -m '$n.$s_$l' -L 01 -o out.txt` |
| Logins to console (and to file) | `python main.py -m '$n.$s' -d corp.local -o out.txt -V` |
| Generation + SMTP validation (directory) | `python main.py -m '$n.$s' -d corp.local -v -o ./results` |
| SMTP validation (explicit file) | `python main.py -m '$n.$s' -d corp.local -v -o emails.txt` |

---

## Data

By default, files from **`rutabaga/data`** are used:

- `Names_M.txt`, `Surnames_M.txt`, `Patronymics_M.txt`
- `Names_F.txt`, `Surnames_F.txt`, `Patronymics_F.txt`

You can set a custom directory: **`--data-root /path/to/folder`**.

### GOST variants

- **`rutabaga/data_gost/`** — strict **GOST 7.79-2000** (System B) transliteration: й→j, no -off/-ow, -ey/-ei, etc. Use: `--data-root rutabaga/data_gost`.
- **`rutabaga/data_gost_7034/`** — same as `data_gost` plus **GOST R 7.0.34-2014** variants (й→I: Andrei, Sergei, -evich/-evna, etc.). Use: `--data-root rutabaga/data_gost_7034`.

The `data_gost` and `data_gost_7034` sets are shipped as-is; this repo does not include separate rebuild scripts.

---

Languages: [Русский](README.md) · [中文](README.zh.md)
