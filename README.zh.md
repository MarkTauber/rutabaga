# Rutabaga — 登录名与邮箱生成器

**Rutabaga** 是一个跨平台 CLI，根据带占位符的掩码模板生成 AD 登录名和电子邮件地址。

语言： [Русский](README.md) · [English](README.en.md)

---

## 快速开始


标准生成
```bash
python main.py -m '$n.$s' -d corp.local -o logins.txt
```

带邮件验证的生成
```bash
python main.py -m '$l.$s' -d corp.local -o logins.txt --validate -w 10 --sender check@access-workflow.com
```

不加 `-V` 时，控制台只显示横幅、设置和状态，登录名写入输出文件。加 `-V` 时登录名输出到 stdout。省略 `-o` 时，结果保存到用户主目录（`~/`），文件名来自 `-d` 或随机 ID。

`-o` 可指定**文件**或**目录**（普通模式与 `--validate` 相同）：
- 目录 → 在其中自动命名（`corp.local.txt`，或 `corp.local_valid.txt` / `corp.local_invalid.txt`）；
- 文件 → 直接使用（配合 `--validate` 时生成 `name_valid.txt` 与 `name_invalid.txt`）。

配合 `-v` / `--validate` 时，rutabaga 生成地址并通过 SMTP 验证（需要 `-d`）。仅有效邮箱输出到 stdout；完整日志在 stderr。

---

## 占位符

掩码支持 **`$a`..`$z`**（一个字母对应一个占位符）。

| 占位符 | 说明     | 数据来源 |
|--------|----------|----------|
| **`$n`** | 名字     | `Names_M.txt` / `Names_F.txt` |
| **`$s`** | 姓氏     | `Surnames_M.txt` / `Surnames_F.txt` |
| **`$m`** | 父称     | `Patronymics_M.txt` / `Patronymics_F.txt` |
| **`$l`** | 单字母   | 由 `-L` 指定的字母表（默认 a–z） |

可通过 **`-p letter=path`** 覆盖或新增任意字母（如 `-p a=./dept.txt` 对应 `$a`）。多文件：`-p a=./t1.txt,./t2.txt` 或多次使用 `-p a=...`。

**掩码示例：**

- `'$n.$s'` → `ivan.ivanov`、`maria.petrova` …
- `'$n.$s_$l'` → `ivan.ivanov_a`、`ivan.ivanov_b` …
- `'$l$l$l@domain.com'` → `aaa@domain.com`、`aab@domain.com` …
- `'$a_$n.$s'` 配合 `-p a=./dept.txt` → `it_ivan.ivanov`、`hr_maria.petrova` …

在 PowerShell 中请使用**单引号**：`-m '$n.$s_$l'`。

---

## 命令行参数

| 参数 | 说明 |
|------|------|
| **`-m`**、**`--mask`** | 掩码模板（必填）。 |
| **`-o`**、**`--output`** | 输出路径：文件或目录。省略时保存到 `~/`，按 `-d` 或随机 ID 自动命名。 |
| **`-d`**、**`--domain`** | 域名（如 `corp.local` 会变成 `@corp.local`）。 |
| **`-s`**、**`--sex`** | `m` / `f` / `both`（默认 `both`）。 |
| **`--data-root`** | 数据文件所在目录。默认：`rutabaga/data`。 |
| **`-L`**、**`--letters`** | `$l` 的字母表（默认 a–z）。 |
| **`-p`**、**`--placeholder`** | 自定义占位符：`letter=path`（可多次使用）。 |
| **`--no-unique`** | 不跨数据集去重。 |
| **`-v`**、**`--verbose`** | 将登录名打印到控制台（否则只显示横幅和状态）。 |

完整列表：`python main.py -h`。

---

## 常用命令

| 用途 | 命令 |
|------|------|
| 登录名保存到 `~/corp.local.txt`（无 `-o`） | `python main.py -m '$n.$s' -d corp.local` |
| 登录名写入文件（名.姓@域名） | `python main.py -m '$n.$s' -d corp.local -o logins.txt` |
| 仅男性，ГОСТ 7.79 数据 | `python main.py -m '$n.$s_$l' -d example.com --data-root rutabaga/data_gost -s m -o out.txt` |
| 仅女性，ГОСТ Р 7.0.34 数据 | `python main.py -m '$n_$s' -d mail.ru --data-root rutabaga/data_gost_7034 -s f -o out.txt` |
| 少量组合（字母 0 和 1） | `python main.py -m '$n.$s_$l' -L 01 -o out.txt` |
| 登录名输出到控制台（并写入文件） | `python main.py -m '$n.$s' -d corp.local -o out.txt -V` |
| 生成 + SMTP 验证（目录） | `python main.py -m '$n.$s' -d corp.local -v -o ./results` |
| SMTP 验证（指定文件） | `python main.py -m '$n.$s' -d corp.local -v -o emails.txt` |

---

## 数据

默认使用 **`rutabaga/data`** 下的文件：

- `Names_M.txt`、`Surnames_M.txt`、`Patronymics_M.txt`
- `Names_F.txt`、`Surnames_F.txt`、`Patronymics_F.txt`

可指定自定义目录：**`--data-root /path/to/folder`**。

### ГОСТ 变体

- **`rutabaga/data_gost/`** — 仅 **ГОСТ 7.79-2000**（系统 B）转写：й→j，无 -off/-ow、-ey/-ei 等。使用：`--data-root rutabaga/data_gost`。
- **`rutabaga/data_gost_7034/`** — 与 `data_gost` 相同，另加 **ГОСТ Р 7.0.34-2014** 变体（й→I：Andrei、Sergei、-evich/-evna 等）。使用：`--data-root rutabaga/data_gost_7034`。

`data_gost` 与 `data_gost_7034` 随仓库提供，本仓库不包含单独的重建脚本。

---

语言： [Русский](README.md) · [English](README.en.md)
