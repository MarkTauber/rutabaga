# Rutabaga — Login and Email Generator

**Rutabaga** is a cross-platform CLI that generates AD logins and email addresses from mask templates with placeholders.

Languages: [Русский](README.md) · [中文](README.zh.md)

---

## Quick start

Validation dependency (DNS MX):

```bash
pip install dnspython
```

Standard generation:

```bash
python main.py -m '$l.$s' -d corp.local -o logins.txt
```

Validate generated addresses (basic — SMTP RCPT):

```bash
python main.py -m '$n.$s' -d corp.local -v -o ./out
```

Extended validation (explicit MAIL FROM / EHLO, MX fallback):

```bash
python main.py -m '$n.$s' -d corp.local -v -o ./out \
  -w 10 --sender check@example.com --helo mx.example.com --mx
```

Without `-V`, the console shows a banner, settings, and status; logins are written to the output file. With `-V`, logins go to stdout. **`-v` and `-V` cannot be used together.** Without `-o`, output goes to the home directory (`~/`), named from `-d` or a random ID.

`-o` accepts a **file** or **directory** (same in normal mode and with `-v`):
- directory → auto-named file (`corp.local.txt`, or with `-v`: `corp.local_valid.txt`, `corp.local_invalid.txt`, `corp.local_inconclusive.txt`);
- file → used as-is (with `-v` → `name_valid.txt`, `name_invalid.txt`, `name_inconclusive.txt` alongside).

---

## Email validation

With **`-v`** / **`--validate`**, rutabaga generates addresses and checks mailbox existence (`-d` required). Confirmed addresses are also printed to stdout; full status log goes to stderr.

### Methods `-v [METHOD …]`

| Invocation | Methods | Behavior |
|------------|---------|----------|
| `-v` | SMTP | RCPT TO + catch-all probe |
| `-v SMTP` | SMTP | same |
| `-v VRFY` | VRFY | `VRFY` only (no RCPT) |
| `-v VRFY EXPN` | VRFY, EXPN | listed methods only; SMTP is not added |
| `-v SMTP VRFY` | SMTP, VRFY | RCPT, then `VRFY` on the same MX if RCPT fails |

Per MX: **EHLO** → (**STARTTLS** unless disabled) → methods in order within one session.

Default **`--sender`** and **`--helo`** are placeholders; set them explicitly for real MX hosts.

### STARTTLS

- By default: if the MX advertises `STARTTLS` after EHLO, the session is upgraded to TLS.
- **`--no-starttls`** — plain SMTP (only with `-v`).

### Validation flags

| Flag | Purpose |
|------|---------|
| **`--mx`** | On RCPT 5xx, try the next MX host (SMTP method only) |
| **`--sender`** | `MAIL FROM` address |
| **`--helo`** | Hostname for `EHLO`/`HELO` |
| **`-w`** | Worker threads (default 15) |

### Output files

| File | Contents |
|------|----------|
| `*_valid.txt` | Confirmed addresses (one per line) |
| `*_invalid.txt` | TSV: `email`, `status`, `reason` |
| `*_inconclusive.txt` | TSV; SMTP codes 252, 421, 450–452 |

### Statuses

| Status | File | Meaning |
|--------|------|---------|
| confirmed | `valid` | Mailbox likely exists |
| `INVALID` | `invalid` | Explicit server rejection |
| `CATCH_ALL` | `invalid` | Domain accepts any address |
| `INCONCLUSIVE` | `inconclusive` | Cannot assert exists / not exists |
| `UNKNOWN` | `invalid` | All MX hosts unreachable |

### Limitations

RCPT and VRFY from external IPs are unreliable for large providers (Gmail, Outlook, etc.); corporate MX hosts work better. **VRFY** and **EXPN** are disabled on most servers.

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
| **`-v`**, **`--validate`** [METHOD…] | Validate addresses (requires `-d`). No METHOD: `SMTP` (STARTTLS). With METHOD: only listed — `SMTP`, `VRFY`, `EXPN`. |
| **`-w`**, **`--workers`** | Validation worker threads (default 15, with `-v`). |
| **`--sender`** | MAIL FROM address for SMTP checks (with `-v`). |
| **`--helo`** | EHLO/HELO hostname for SMTP checks (with `-v`). |
| **`--mx`** | On RCPT 5xx, try next MX host (with `-v`, SMTP method only). |
| **`--no-starttls`** | Do not upgrade to TLS even if the server advertises STARTTLS (with `-v`). |

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
| Generation + validation (directory) | `python main.py -m '$n.$s' -d corp.local -v -o ./results` |
| Validation (explicit base file) | `python main.py -m '$n.$s' -d corp.local -v -o emails.txt` |
| VRFY + EXPN without RCPT | `python main.py -m '$n.$s' -d corp.local -v VRFY EXPN -o ./out` |
| SMTP + VRFY | `python main.py -m '$n.$s' -d corp.local -v SMTP VRFY -o ./out` |
| Without STARTTLS | `python main.py -m '$n.$s' -d corp.local -v --no-starttls -o ./out` |
| Try next MX on RCPT 5xx | `python main.py -m '$n.$s' -d corp.local -v --mx -o ./out` |

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
