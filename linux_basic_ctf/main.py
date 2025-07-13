import os
import math

# Fayl tizimi simulyatsiyasi: Lug'atlar yordamida yaratilgan virtual fayl tizimi
file_system = {
    "home": {
        "user": {
            "documents": {
                "report.docx": "Yillik hisobot.",
                "notes.txt": "Ba'zi shaxsiy eslatmalar."
            },
            "desktop": {
                "flag.txt": "CTF{Birinchi_flag_qollaringizda!}",
                "lesson_1.txt": "ls buyrug'i joriy katalogdagi fayllar va papkalarni ko'rsatadi. cd buyrug'i katalogga kiradi. Keyingi flagni /var/log/ ga qidir.",
                "images": {},
                "videos": {}
            },
            "downloads": {
                "archive.zip": "Yuklab olingan arxiv.",
                "setup.exe": "Windows dastur fayli."
            }
        }
    },
    "var": {
        "log": {
            "system.log": "Tizim faoliyati haqida ma'lumotlar...",
            "secret_note.txt": "Keyingi flagni /etc/conf/ichidan_toping.conf da qidiring."
        },
        "cache": {}
    },
    "etc": {
        "conf": {
            "ichidan_toping.conf": "CTF{Ikkinchi_flag_mana_shu_yerda!}"
        },
        "passwd": "root:x:0:0:root:/root:/bin/bash",
        "hosts": "127.00.1 localhost"
    },
    "root": {
        "secret_root_flag.txt": "CTF{ROOT_Katalogidagi_Flag!}"
    },
    "bin": {
        "ls": "Executable ls command",
        "cat": "Executable cat command"
    }
}

# Joriy katalogning yo'li
current_directory_path = ["home", "user"]

# Terminal uchun ba'zi sozlamalar
USER_NAME = "user"
HOST_NAME = "ctf-linux"

# ANSI rang kodlari
COLOR_DARK_BLUE = "\033[34m" # Papkalar uchun to'q ko'k
COLOR_WHITE = "\033[97m"     # Fayllar uchun oq (avvalgi ochiq ko'k o'rniga)
COLOR_GREEN = "\033[92m"    # Promptdagi foydalanuvchi/hostname uchun yashil
COLOR_RESET = "\033[0m"     # Rangni tiklash

def get_node_by_path(path_parts):
    """Berilgan yo'l bo'yicha tugunni (fayl yoki katalog) qaytaradi."""
    node = file_system
    for part in path_parts:
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node

def get_current_node():
    """Joriy katalogning lug'at obyektini qaytaradi."""
    return get_node_by_path(current_directory_path)

def get_display_path_string():
    """Joriy katalogning Linux terminaliga mos yo'l ko'rinishini qaytaradi."""
    if not current_directory_path:
        return "/"
    
    if current_directory_path == ["home", "user"]:
        return "~"
    
    return "/" + "/".join(current_directory_path)

def resolve_path(input_path):
    """
    Kiritilgan yo'lni (nisbiy yoki absolut) to'liq, ajratilgan yo'l qismlariga o'zgartiradi.
    """
    if not input_path:
        return current_directory_path[:]

    if input_path.startswith("/"):
        parts = [p for p in input_path.split("/") if p]
        return parts
    else:
        temp_path = current_directory_path[:]
        for part in input_path.split("/"):
            if part == "..":
                if len(temp_path) > 0:
                    temp_path.pop()
            elif part == ".":
                pass
            elif part:
                temp_path.append(part)
        return temp_path

def ls_command(path_arg=None):
    """
    Katalog ichidagi fayl va papkalarni ko'rsatadi.
    Argumentlarsiz ishlatilsa: Joriy katalog ichidagilarni ko'rsatadi.
    Argument bilan ishlatilsa: Belgilangan katalog yoki faylni ko'rsatadi.
    """
    target_resolved_path = None
    
    if path_arg is None or path_arg == ".":
        target_resolved_path = current_directory_path
    else:
        target_resolved_path = resolve_path(path_arg)
    
    target_node = get_node_by_path(target_resolved_path)

    if target_node is None:
        print(f"ls: '{path_arg if path_arg else ''}': Bunday fayl yoki katalog topilmadi")
    elif isinstance(target_node, dict): # Bu katalog
        if not target_node:
            print("Bo'sh katalog.")
        else:
            items = []
            for item_name in sorted(target_node.keys()):
                if isinstance(target_node[item_name], dict):
                    items.append(f"{COLOR_DARK_BLUE}{item_name}/{COLOR_RESET}") # Papka uchun to'q ko'k rang
                else:
                    items.append(f"{COLOR_WHITE}{item_name}{COLOR_RESET}") # Fayl uchun oq rang

            COLUMNS = 3
            
            max_len = 0
            for item in items:
                # ANSI kodlarini olib tashlab uzunlikni hisoblaymiz
                clean_item = item.replace(COLOR_DARK_BLUE, "").replace(COLOR_WHITE, "").replace(COLOR_RESET, "").replace("/", "")
                max_len = max(max_len, len(clean_item))
            
            column_width = max_len + 4 

            num_items = len(items)
            
            if num_items == 0:
                print("Bo'sh katalog.")
                return

            print() # Natijadan oldin bir bo'sh qator tashlash
            rows_per_column = math.ceil(num_items / COLUMNS)
            
            for r in range(rows_per_column):
                line = []
                for c in range(COLUMNS):
                    idx = r + c * rows_per_column
                    if idx < num_items:
                        item_display = items[idx]
                        clean_item = item_display.replace(COLOR_DARK_BLUE, "").replace(COLOR_WHITE, "").replace(COLOR_RESET, "")
                        padding_needed = column_width - len(clean_item)
                        line.append(item_display + " " * padding_needed)
                    else:
                        line.append(" " * column_width)
                print("".join(line))

    elif isinstance(target_node, str): # Bu fayl
        print(f"{COLOR_WHITE}{path_arg.split('/')[-1]}{COLOR_RESET}") # Fayl nomini oq rangda ko'rsatamiz

def cd_command(target_path):
    """
    Kataloglar bo'ylab harakatlanadi.
    """
    global current_directory_path
    
    if not target_path or target_path == "~":
        current_directory_path = ["home", "user"]
        return

    resolved_path_parts = resolve_path(target_path)
    
    if not resolved_path_parts and (target_path == ".." or target_path == "/"):
         current_directory_path = []
         return

    test_node = get_node_by_path(resolved_path_parts)

    if test_node and isinstance(test_node, dict):
        current_directory_path = resolved_path_parts
    else:
        print(f"cd: '{target_path}': Bunday fayl yoki katalog yo'q")

def cat_command(filename):
    """
    Faylning ichidagi kontentni ko'rsatadi.
    """
    current_node = get_current_node()
    if current_node and filename in current_node and isinstance(current_node[filename], str):
        print(current_node[filename])
    else:
        print(f"cat: '{filename}': Bunday fayl yoki katalog topilmadi")

def mkdir_command(dirname):
    """
    Yangi katalog (papka) yaratadi.
    """
    current_node = get_current_node()
    if current_node is None:
        print("Xatolik: Joriy katalog topilmadi.")
        return

    if dirname in current_node:
        print(f"mkdir: '{dirname}': Fayl mavjud")
    else:
        current_node[dirname] = {}
        print(f"Katalog '{dirname}' yaratildi.")

def touch_command(filename, content=""):
    """
    Yangi bo'sh fayl yaratadi yoki mavjud faylga yangi kontent yozadi.
    """
    current_node = get_current_node()
    if current_node is None:
        print("Xatolik: Joriy katalog topilmadi.")
        return

    if filename in current_node and isinstance(current_node[filename], dict):
        print(f"touch: '{filename}': Bu katalog, fayl emas.")
    else:
        current_node[filename] = content
        print(f"Fayl '{filename}' yaratildi yoki yangilandi.")

def help_command():
    """
    Mavjud buyruqlar haqida ma'lumot beradi.
    """
    print("""
Mavjud buyruqlar:
  ls [yo'l]        - Joriy yoki belgilangan katalog ichidagi fayl va papkalarni ko'rsatadi.
                     Argumentlarsiz 'ls' joriy katalogdagilarni ko'rsatadi.
  cd [yo'l]        - Kataloglar bo'ylab harakatlanadi. '..' orqali yuqoriga chiqish.
                     'cd' (argumentsiz) yoki 'cd ~' /home/user ga qaytaradi.
  cat <faylnomi>   - Faylning ichidagi kontentni ko'rsatadi.
  mkdir <papkanomi> - Yangi bo'sh papka (katalog) yaratadi.
  touch <faylnomi> [kontent] - Yangi fayl yaratadi yoki mavjud faylga kontent yozadi.
  help             - Mavjud buyruqlar ro'yxatini ko'rsatadi.
  clear            - Terminal ekranini tozalaydi.
  exit             - Dasturdan chiqadi.
""")

def clear_command():
    """Terminal ekranini tozalaydi."""
    os.system('cls' if os.name == 'nt' else 'clear')


def run_ctf_terminal():
    """Asosiy terminal sikli."""
    print("Xush kelibsiz! Bu Linux buyruqlarini o'rganishga yordam beruvchi CTF terminali.")
    print("Boshlash uchun 'ls', 'cd', 'cat' kabi buyruqlarni sinab ko'ring. 'help' buyrug'i yordam beradi.")
    
    while True:
        display_path = get_display_path_string()
        
        # user@hostname:~/katalog$ formatidagi prompt
        # Promptdagi yo'l to'q ko'k rangda
        prompt = f"{COLOR_GREEN}{USER_NAME}@{HOST_NAME}{COLOR_RESET}:{COLOR_DARK_BLUE}{display_path}{COLOR_RESET}$ "
        
        user_input = input(prompt).strip()
        
        if not user_input:
            continue

        parts = user_input.split(" ", 1)
        command = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        if command == "exit":
            print("Terminaldan chiqildi. CTF o'yini tugadi.")
            break
        elif command == "ls":
            ls_command(args)
        elif command == "cd":
            cd_command(args)
        elif command == "cat":
            cat_command(args)
        elif command == "mkdir":
            mkdir_command(args)
        elif command == "touch":
            filename_parts = args.split(" ", 1)
            touch_filename = filename_parts[0]
            touch_content = filename_parts[1] if len(filename_parts) > 1 else ""
            touch_command(touch_filename, touch_content)
        elif command == "help":
            help_command()
        elif command == "clear":
            clear_command()
        else:
            print(f"{command}: Buyruq topilmadi")

# Dasturni ishga tushirish
if __name__ == "__main__":
    run_ctf_terminal()