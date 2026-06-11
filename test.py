import argparse
import concurrent.futures
import csv
import os
import sys

from rutabaga.validate import DEFAULT_SENDER, DEFAULT_WORKERS, check_email


def main():
    parser = argparse.ArgumentParser(description="SMTP Email Validator (RedTeam Edition)")
    parser.add_argument("-i", "--input", required=True, help="Путь к файлу со списком email (по одному в строке)")
    parser.add_argument("-o", "--output", required=True, help="Путь к выходному CSV файлу")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS, help="Количество потоков (по умолчанию 15)")
    parser.add_argument("-s", "--sender", default=DEFAULT_SENDER, help="Email отправителя (MAIL FROM)")

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"[!] Ошибка: Файл '{args.input}' не найден.")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        emails = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not emails:
        print("[!] Ошибка: Список email пуст.")
        sys.exit(1)

    print(f"[*] Загружено {len(emails)} адресов. Начало валидации...")
    print(f"[*] Результаты сохраняются в: {args.output}\n")
    print(f"{'СТАТУС':<12} | {'EMAIL':<35} | ПРИЧИНА")
    print("-" * 75)

    with open(args.output, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(["Email", "Status", "Reason"])

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(check_email, email, sender=args.sender): email for email in emails}

            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                print(f"[{res['status']:<10}] {res['email']:<35} | {res['reason']}")
                writer.writerow([res["email"], res["status"], res["reason"]])
                f_out.flush()

    print("-" * 75)
    print(f"[*] Валидация завершена. Итоговый файл: {args.output}")


if __name__ == "__main__":
    main()
