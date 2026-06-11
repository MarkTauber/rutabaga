from __future__ import annotations

import concurrent.futures
import random
import smtplib
import socket
import string
import time
from pathlib import Path
from typing import Dict, FrozenSet, Iterator, List, Optional, TextIO, Tuple

import dns.resolver

DEFAULT_SENDER = "validator@your-controlled-domain.com" # Оставлю как есть
DEFAULT_HELO = "your-controlled-domain.com"
TIMEOUT = 8
DEFAULT_WORKERS = 15
MAX_INFLIGHT_MULTIPLIER = 4

VALID_STATUS = "VALID"
INCONCLUSIVE_STATUS = "INCONCLUSIVE"
INCONCLUSIVE_RCPT_CODES = frozenset({252, 421, 450, 451, 452})

METHOD_SMTP = "SMTP"
METHOD_VRFY = "VRFY"
METHOD_EXPN = "EXPN"
DEFAULT_VALIDATE_METHODS = frozenset({METHOD_SMTP})


def normalize_validate_methods(methods: List[str]) -> FrozenSet[str]:
    """Turn CLI --validate args into a method set. Bare -v → SMTP; else only listed methods."""
    if not methods:
        return frozenset({METHOD_SMTP})
    return frozenset(m.upper() for m in methods)


def get_mx_records(domain: str) -> list[str]:
    try:
        records = dns.resolver.resolve(domain, "MX")
        return [str(r.exchange).rstrip(".") for r in sorted(records, key=lambda r: r.preference)]
    except Exception:
        return []


def _inconclusive_reason(code: int, *, command: str = "RCPT") -> str:
    if code == 252:
        return f"Сервер не проверял адрес ({command} {code})"
    if code == 421:
        return f"Сервис временно недоступен ({command} {code})"
    return f"Временная ошибка SMTP ({command} {code})"


def _smtp_setup(server: smtplib.SMTP, helo: str, *, use_starttls: bool = True) -> None:
    code, _ = server.ehlo(helo)
    if code >= 400:
        server.helo(helo)
    if use_starttls and server.has_extn("starttls"):
        server.starttls()
        server.ehlo(helo)


def _classify_smtp_code(code: int, *, command: str) -> Optional[Dict[str, str]]:
    if code == 250:
        return None
    if code in INCONCLUSIVE_RCPT_CODES:
        return {
            "status": INCONCLUSIVE_STATUS,
            "reason": _inconclusive_reason(code, command=command),
        }
    if code >= 500:
        return {
            "status": "INVALID",
            "reason": f"Отклонен {command} ({code})",
        }
    return {
        "status": "INVALID",
        "reason": f"Отклонен {command} ({code})",
    }


def _check_rcpt(
    server: smtplib.SMTP,
    email: str,
    *,
    sender: str,
    random_email: str,
) -> Dict[str, str]:
    server.mail(sender)
    code_target, _ = server.rcpt(email)

    if code_target == 250:
        server.rset()
        server.mail(sender)
        code_random, _ = server.rcpt(random_email)

        if code_random == 250:
            return {
                "status": "CATCH_ALL",
                "reason": "Домен принимает всё",
            }

        return {
            "status": VALID_STATUS,
            "reason": "Существует (RCPT)",
        }

    classified = _classify_smtp_code(code_target, command="RCPT")
    if classified:
        return classified

    return {
        "status": "INVALID",
        "reason": f"Отклонен RCPT ({code_target})",
    }


def _check_vrfy(server: smtplib.SMTP, email: str) -> Dict[str, str]:
    code, _ = server.verify(email)

    if code == 250:
        return {
            "status": VALID_STATUS,
            "reason": "Существует (VRFY)",
        }

    classified = _classify_smtp_code(code, command="VRFY")
    if classified:
        return classified

    return {
        "status": "INVALID",
        "reason": f"Отклонен VRFY ({code})",
    }


def _check_expn(server: smtplib.SMTP, email: str) -> Dict[str, str]:
    local, _ = email.split("@", 1)
    code, _ = server.docmd("EXPN", local)

    if code == 250:
        return {
            "status": VALID_STATUS,
            "reason": "Существует (EXPN)",
        }

    classified = _classify_smtp_code(code, command="EXPN")
    if classified:
        return classified

    return {
        "status": "INVALID",
        "reason": f"Отклонен EXPN ({code})",
    }


def _is_definitive(result: Dict[str, str]) -> bool:
    return result["status"] in (VALID_STATUS, "CATCH_ALL", INCONCLUSIVE_STATUS)


def _extract_code(reason: str) -> Optional[int]:
    if "(" not in reason or not reason.endswith(")"):
        return None
    try:
        return int(reason.rsplit("(", 1)[-1].rstrip(")"))
    except ValueError:
        return None


def _check_on_mx(
    mx: str,
    email: str,
    *,
    sender: str,
    helo: str,
    random_email: str,
    methods: FrozenSet[str],
    use_starttls: bool = True,
) -> Tuple[Optional[Dict[str, str]], Optional[int]]:
    with smtplib.SMTP(mx, timeout=TIMEOUT) as server:
        _smtp_setup(server, helo, use_starttls=use_starttls)

        last_result: Optional[Dict[str, str]] = None
        last_rcpt_5xx: Optional[int] = None

        if METHOD_SMTP in methods:
            rcpt_result = _check_rcpt(
                server,
                email,
                sender=sender,
                random_email=random_email,
            )
            last_result = rcpt_result
            if _is_definitive(rcpt_result):
                return rcpt_result, None
            rcpt_code = _extract_code(rcpt_result.get("reason", ""))
            if rcpt_code is not None and rcpt_code >= 500:
                last_rcpt_5xx = rcpt_code

        if METHOD_VRFY in methods:
            vrfy_result = _check_vrfy(server, email)
            last_result = vrfy_result
            if _is_definitive(vrfy_result):
                return vrfy_result, last_rcpt_5xx

        if METHOD_EXPN in methods:
            expn_result = _check_expn(server, email)
            last_result = expn_result
            if _is_definitive(expn_result):
                return expn_result, last_rcpt_5xx

        return last_result, last_rcpt_5xx


def check_email(
    email: str,
    *,
    sender: str = DEFAULT_SENDER,
    helo: str = DEFAULT_HELO,
    try_all_mx: bool = False,
    methods: FrozenSet[str] = DEFAULT_VALIDATE_METHODS,
    use_starttls: bool = True,
) -> Dict[str, str]:
    try:
        _, domain = email.split("@", 1)
    except ValueError:
        return {
            "email": email,
            "status": "INVALID",
            "reason": "Некорректный формат",
        }

    mx_records = get_mx_records(domain)
    if not mx_records:
        return {
            "email": email,
            "status": "INVALID",
            "reason": "Отсутствуют MX записи",
        }

    random_local = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
    random_email = f"{random_local}@{domain}"
    last_rcpt_5xx: Optional[int] = None
    last_result: Optional[Dict[str, str]] = None
    all_mx_rcpt_5xx = True

    for mx in mx_records:
        try:
            time.sleep(random.uniform(0.3, 1.5))

            result, mx_rcpt_5xx = _check_on_mx(
                mx,
                email,
                sender=sender,
                helo=helo,
                random_email=random_email,
                methods=methods,
                use_starttls=use_starttls,
            )

            if result is not None:
                last_result = result
                if _is_definitive(result):
                    return {"email": email, **result}

            if mx_rcpt_5xx is not None:
                last_rcpt_5xx = mx_rcpt_5xx
                if try_all_mx:
                    continue
                if result is not None:
                    return {"email": email, **result}
            else:
                all_mx_rcpt_5xx = False

            if result is not None and not try_all_mx:
                return {"email": email, **result}

        except socket.timeout:
            all_mx_rcpt_5xx = False
            continue
        except smtplib.SMTPServerDisconnected:
            all_mx_rcpt_5xx = False
            continue
        except Exception:
            all_mx_rcpt_5xx = False
            continue

    if try_all_mx and all_mx_rcpt_5xx and last_rcpt_5xx is not None:
        return {
            "email": email,
            "status": "INVALID",
            "reason": f"Отклонен всеми MX ({last_rcpt_5xx})",
        }

    if last_result is not None:
        return {"email": email, **last_result}

    return {
        "email": email,
        "status": "UNKNOWN",
        "reason": "Все MX недоступны",
    }


def _write_result(
    result: Dict[str, str],
    valid_file: TextIO,
    invalid_file: TextIO,
    inconclusive_file: TextIO,
    *,
    print_valid: bool,
) -> bool:
    email = result["email"]
    status = result["status"]
    is_valid = status == VALID_STATUS

    if is_valid:
        valid_file.write(email + "\n")
        valid_file.flush()
        if print_valid:
            print(email)
    elif status == INCONCLUSIVE_STATUS:
        inconclusive_file.write(f"{email}\t{status}\t{result['reason']}\n")
        inconclusive_file.flush()
    else:
        invalid_file.write(f"{email}\t{status}\t{result['reason']}\n")
        invalid_file.flush()

    return is_valid


def validate_stream(
    emails: Iterator[str],
    *,
    valid_path: Path,
    invalid_path: Path,
    inconclusive_path: Path,
    workers: int = DEFAULT_WORKERS,
    sender: str = DEFAULT_SENDER,
    helo: str = DEFAULT_HELO,
    try_all_mx: bool = False,
    methods: FrozenSet[str] = DEFAULT_VALIDATE_METHODS,
    use_starttls: bool = True,
    print_valid: bool = True,
) -> Dict[str, int]:
    stats = {
        "generated": 0,
        "valid": 0,
        "invalid": 0,
        "catch_all": 0,
        "inconclusive": 0,
        "unknown": 0,
    }

    max_inflight = max(workers * MAX_INFLIGHT_MULTIPLIER, workers)

    with (
        open(valid_path, "w", encoding="utf-8") as valid_file,
        open(invalid_path, "w", encoding="utf-8") as invalid_file,
        open(inconclusive_path, "w", encoding="utf-8") as inconclusive_file,
    ):
        invalid_file.write("# email\tstatus\treason\n")
        inconclusive_file.write("# email\tstatus\treason\n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            pending: Dict[concurrent.futures.Future, str] = {}

            def drain_completed(block: bool = False) -> None:
                if not pending:
                    return

                iterator = (
                    concurrent.futures.as_completed(pending)
                    if block
                    else _take_first_completed(pending)
                )

                for future in iterator:
                    pending.pop(future, None)
                    result = future.result()
                    status = result["status"]
                    if status == VALID_STATUS:
                        stats["valid"] += 1
                    elif status == "CATCH_ALL":
                        stats["catch_all"] += 1
                    elif status == INCONCLUSIVE_STATUS:
                        stats["inconclusive"] += 1
                    elif status == "UNKNOWN":
                        stats["unknown"] += 1
                    else:
                        stats["invalid"] += 1

                    _write_result(
                        result,
                        valid_file,
                        invalid_file,
                        inconclusive_file,
                        print_valid=print_valid,
                    )

            for email in emails:
                stats["generated"] += 1

                future = executor.submit(
                    check_email,
                    email,
                    sender=sender,
                    helo=helo,
                    try_all_mx=try_all_mx,
                    methods=methods,
                    use_starttls=use_starttls,
                )

                pending[future] = email

                if len(pending) >= max_inflight:
                    drain_completed(block=False)

            drain_completed(block=True)

    return stats


def _take_first_completed(
    pending: Dict[concurrent.futures.Future, str],
) -> Iterator[concurrent.futures.Future]:
    done, _ = concurrent.futures.wait(
        pending.keys(),
        return_when=concurrent.futures.FIRST_COMPLETED,
    )
    yield from done
