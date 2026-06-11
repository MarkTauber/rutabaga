import argparse
import csv
import os
import sys

def filter_results(input_file, output_file, exclude_statuses):
    if not os.path.isfile(input_file):
        print(f"[!] Ошибка: Файл '{input_file}' не найден.")
        sys.exit(1)

    kept_count = 0
    excluded_count = 0

    exclude_list = [status.upper() for status in exclude_statuses]

    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        
        reader = csv.DictReader(f_in)
        
        if not reader.fieldnames or 'Email' not in reader.fieldnames or 'Status' not in reader.fieldnames:
            print("[!] Ошибка: Неверный формат CSV. Ожидаются колонки 'Email' и 'Status'.")
            sys.exit(1)

        for row in reader:
            status = row['Status'].strip().upper()
            email = row['Email'].strip()
            
            if status in exclude_list:
                excluded_count += 1
                continue
            
            f_out.write(f"{email}\n")
            kept_count += 1

    print(f"[*] Обработка завершена.")
    print(f"[*] Сохранено адресов для дальнейшей работы: {kept_count}")
    print(f"[*] Отфильтровано (исключено): {excluded_count}")
    print(f"[*] Результат записан в: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Фильтр результатов SMTP валидации (RedTeam Edition)")
    parser.add_argument("-i", "--input", required=True, help="Входной CSV файл с результатами валидации")
    parser.add_argument("-o", "--output", required=True, help="Выходной текстовый файл со списком email")
    parser.add_argument("-e", "--exclude", nargs='+', default=['INVALID', 'UNKNOWN'], 
                        help="Статусы для исключения (по умолчанию: INVALID UNKNOWN)")
    
    args = parser.parse_args()
    filter_results(args.input, args.output, args.exclude)
