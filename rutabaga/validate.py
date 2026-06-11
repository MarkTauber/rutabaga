from __future__ import annotations

import concurrent.futures
import random
import smtplib
import socket
import string
import time
from pathlib import Path
from typing import Dict, Iterator, Optional, TextIO, Tuple

import dns.resolver

DEFAULT_SENDER = "validator@your-controlled-domain.com" # Оставлю как есть
DEFAULT_HELO = "your-controlled-domain.com"
TIMEOUT = 8
DEFAULT_WORKERS = 15
MAX_INFLIGHT_MULTIPLIER = 4

VALID_STATUS = "VALID"


def get_mx_records(domain: str) -> list[str]:
    try:
        records = dns.resolver.resolve(domain, "MX")
        return [str(r.exchange).rstrip(".") for r in sorted(records, key=lambda r: r.preference)]
    except Exception:
        return []


def check_email(
    email: str,
    *,
    sender: str = DEFAULT_SENDER,
    helo: str = DEFAULT_HELO,
) -> Dict[str, str]:
    try:
        _, domain = email.split("@", 1)
    except ValueError:
        return {
            "email": email, 
            "status": "INVALID", 
            "reason": "Некорректный формат"
            }

    mx_records = get_mx_records(domain)
    if not mx_records:
        return {
            "email": email, 
            "status": "INVALID", 
            "reason": "Отсутствуют MX записи"
            }

    random_local = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
    random_email = f"{random_local}@{domain}"

    for mx in mx_records:
        try:
            time.sleep(random.uniform(0.3, 1.5))

            with smtplib.SMTP(mx, timeout=TIMEOUT) as server:
                server.ehlo(helo)
                server.mail(sender)
                code_target, _ = server.rcpt(email)

                if code_target == 250:
                    server.rset()
                    server.mail(sender)
                    code_random, _ = server.rcpt(random_email)
                    server.quit()

                    if code_random == 250:
                        return {
                            "email": email,
                            "status": "CATCH_ALL",
                            "reason": "Домен принимает всё",
                        }

                    return {
                        "email": email, 
                        "status": VALID_STATUS, 
                        "reason": "Существует"
                        }

                if code_target in (450, 451, 452):
                    return {
                        "email": email,
                        "status": "GREYLISTED",
                        "reason": "Временная ошибка (4xx)",
                    }
                return {
                    "email": email,
                    "status": "INVALID",
                    "reason": f"Отклонен ({code_target})",
                }

        except socket.timeout:
            continue
        except smtplib.SMTPServerDisconnected:
            continue
        except Exception:
            continue

    return {
        "email": email, 
        "status": "UNKNOWN", 
        "reason": "Все MX недоступны"
        }


def _write_result(
    result: Dict[str, str],
    valid_file: TextIO,
    invalid_file: TextIO,
    *,
    print_valid: bool,
) -> bool:

    email = result["email"]
    is_valid = result["status"] == VALID_STATUS

    if is_valid:
        valid_file.write(email + "\n")
        valid_file.flush()
        if print_valid:
            print(email)
    else:
        invalid_file.write(f"{email}\t{result['status']}\t{result['reason']}\n")
        invalid_file.flush()

    return is_valid


def validate_stream(
    emails: Iterator[str],
    *,
    valid_path: Path,
    invalid_path: Path,
    workers: int = DEFAULT_WORKERS,
    sender: str = DEFAULT_SENDER,
    helo: str = DEFAULT_HELO,
    print_valid: bool = True,
) -> Dict[str, int]:

    stats = {
        "generated": 0,
        "valid": 0,
        "invalid": 0,
        "catch_all": 0,
        "greylisted": 0,
        "unknown": 0,
    }
    
    max_inflight = max(workers * MAX_INFLIGHT_MULTIPLIER, workers)

    with open(valid_path, "w", encoding="utf-8") as valid_file, open(
        invalid_path, "w", encoding="utf-8"
    ) as invalid_file:
        invalid_file.write("# email\tstatus\treason\n")

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
                    elif status == "GREYLISTED":
                        stats["greylisted"] += 1
                    elif status == "UNKNOWN":
                        stats["unknown"] += 1
                    else:
                        stats["invalid"] += 1

                    if _write_result(
                        result,
                        valid_file,
                        invalid_file,
                        print_valid=print_valid,
                    ):
                        pass

            for email in emails:
                stats["generated"] += 1
                
                future = executor.submit(
                    check_email, 
                    email, 
                    sender=sender, 
                    helo=helo
                    )

                pending[future] = email

                if len(pending) >= max_inflight:
                    drain_completed(block=False)

            drain_completed(block=True)

    return stats


def _take_first_completed(pending: Dict[concurrent.futures.Future, str],) -> Iterator[concurrent.futures.Future]:
    done, _ = concurrent.futures.wait(pending.keys(),return_when=concurrent.futures.FIRST_COMPLETED,)
    yield from done
