# Rutabaga — 登录名与邮箱生成器

**Rutabaga** 是一个跨平台 CLI，根据带占位符的掩码模板生成 AD 登录名和电子邮件地址。

语言： [Русский](README.md) · [English](README.en.md)

---

## 快速开始

验证依赖（DNS MX）：

```bash
pip install dnspython
```

标准生成：

```bash
python main.py -m '$l.$s' -d corp.local -o logins.txt
```

验证生成的地址（基础 — SMTP RCPT）：

```bash
python main.py -m '$n.$s' -d corp.local -v -o ./out
```

扩展验证（显式 MAIL FROM / EHLO、MX 回退）：

```bash
python main.py -m '$n.$s' -d corp.local -v -o ./out \
  -w 10 --sender check@example.com --helo mx.example.com --mx
```

不加 `-V` 时，控制台只显示横幅、设置和状态，登录名写入输出文件。加 `-V` 时登录名输出到 stdout。**`-v` 与 `-V` 不能同时使用。** 省略 `-o` 时，结果保存到用户主目录（`~/`），文件名来自 `-d` 或随机 ID。

`-o` 可指定**文件**或**目录**（普通模式与 `-v` 相同）：
- 目录 → 自动命名（`corp.local.txt`，或配合 `-v`：`corp.local_valid.txt`、`corp.local_invalid.txt`、`corp.local_inconclusive.txt`）；
- 文件 → 直接使用（配合 `-v` 时生成 `name_valid.txt`、`name_invalid.txt`、`name_inconclusive.txt`）。

---

## 邮件验证

使用 **`-v`** / **`--validate`** 时，rutabaga 生成地址并检查邮箱是否存在（需要 **`-d`**）。已确认的地址同时输出到 stdout；完整状态日志在 stderr。

### 方法 `-v [METHOD …]`

| 调用 | 方法 | 行为 |
|------|------|------|
| `-v` | SMTP | RCPT TO + catch-all 探测 |
| `-v SMTP` | SMTP | 同上 |
| `-v VRFY` | VRFY | 仅 `VRFY`（无 RCPT） |
| `-v VRFY EXPN` | VRFY, EXPN | 仅所列方法；不自动添加 SMTP |
| `-v SMTP VRFY` | SMTP, VRFY | RCPT 失败后于同一 MX 尝试 `VRFY` |

每个 MX：**EHLO** →（**STARTTLS**，除非禁用）→ 在同一会话中按顺序执行方法。

默认 **`--sender`** 与 **`--helo`** 为占位值；连接真实 MX 时建议显式指定。

### STARTTLS

- 默认：MX 在 EHLO 后宣告 `STARTTLS` 时，会话升级为 TLS。
- **`--no-starttls`** — 纯 SMTP（仅配合 `-v`）。

### 验证相关参数

| 参数 | 用途 |
|------|------|
| **`--mx`** | RCPT 返回 5xx 时尝试下一个 MX（仅 SMTP 方法） |
| **`--sender`** | `MAIL FROM` 地址 |
| **`--helo`** | `EHLO`/`HELO` 主机名 |
| **`-w`** | 线程数（默认 15） |

### 输出文件

| 文件 | 内容 |
|------|------|
| `*_valid.txt` | 已确认地址（每行一个） |
| `*_invalid.txt` | TSV：`email`、`status`、`reason` |
| `*_inconclusive.txt` | TSV；SMTP 码 252、421、450–452 |

### 状态

| 状态 | 文件 | 含义 |
|------|------|------|
| 已确认 | `valid` | 邮箱很可能存在 |
| `INVALID` | `invalid` | 服务器明确拒绝 |
| `CATCH_ALL` | `invalid` | 域接受任意地址 |
| `INCONCLUSIVE` | `inconclusive` | 无法断定存在/不存在 |
| `UNKNOWN` | `invalid` | 所有 MX 不可达 |

### 限制

从外部 IP 使用 RCPT/VRFY 对大型邮件服务商（Gmail、Outlook 等）不可靠；企业 MX 效果更好。**VRFY** 与 **EXPN** 在大多数服务器上已禁用。

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
| **`-V`**、**`--verbose`** | 将登录名打印到控制台（否则只显示横幅和状态）。 |
| **`-v`**、**`--validate`** [METHOD…] | 验证地址（需要 `-d`）。无 METHOD：`SMTP`（含 STARTTLS）。有 METHOD：仅所列 `SMTP`、`VRFY`、`EXPN`。 |
| **`-w`**、**`--workers`** | 验证线程数（默认 15，仅配合 `-v`）。 |
| **`--sender`** | SMTP 验证的 MAIL FROM 地址（仅配合 `-v`）。 |
| **`--helo`** | SMTP 验证的 EHLO/HELO 主机名（仅配合 `-v`）。 |
| **`--mx`** | RCPT 返回 5xx 时尝试下一个 MX（仅配合 `-v`，SMTP 方法）。 |
| **`--no-starttls`** | 即使服务器提供 STARTTLS 也不升级为 TLS（仅配合 `-v`）。 |

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
| 生成 + 验证（目录） | `python main.py -m '$n.$s' -d corp.local -v -o ./results` |
| 验证（显式基础文件） | `python main.py -m '$n.$s' -d corp.local -v -o emails.txt` |
| VRFY + EXPN（无 RCPT） | `python main.py -m '$n.$s' -d corp.local -v VRFY EXPN -o ./out` |
| SMTP + VRFY | `python main.py -m '$n.$s' -d corp.local -v SMTP VRFY -o ./out` |
| 不使用 STARTTLS | `python main.py -m '$n.$s' -d corp.local -v --no-starttls -o ./out` |
| RCPT 5xx 时尝试下一 MX | `python main.py -m '$n.$s' -d corp.local -v --mx -o ./out` |

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
