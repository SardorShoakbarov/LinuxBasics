#!/usr/bin/env python3
"""
CTF Terminal Simulator - Fixed Version
A simulation of a Linux terminal for CTF challenges with improved command support
"""

import os
import math
import datetime
import stat
import re
import sys
import shlex

try:
    if sys.platform == "win32":
        import pyreadline3
    else:
        import readline
except ImportError:
    pass

REAL_OS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "OS")
current_directory_path = REAL_OS_PATH

USER_NAME = "user"
HOST_NAME = "ctf-linux"

# Style uchun rang kodlari
COLOR_PROMPT_USER_HOST = "\033[32m"
COLOR_PROMPT_PATH = "\033[34m"
COLOR_DIR = "\033[94m"
COLOR_FILE = "\033[0m"
COLOR_EXEC = "\033[32m"
COLOR_RESET = "\033[0m"
COLOR_CYAN = "\033[36m"

COLOR_HACKING_RED = "\033[31m"
COLOR_HACKING_GREEN = "\033[32m"
COLOR_HACKING_YELLOW = "\033[33m"
COLOR_HACKING_CYAN = "\033[36m"
COLOR_HACKING_MAGENTA = "\033[35m"
COLOR_HACKING_BOLD = "\033[1m"

# --- Global o'zgaruvchilar ---
COMMAND_HISTORY = []
ALIASES = {
    'll': 'ls -la',
    'la': 'ls -a',
    'l': 'ls -l'
}

# --- Yordamchi funksiyalar ---

def get_display_path_string():
    """Path displayni olish"""
    if current_directory_path == REAL_OS_PATH:
        return "~"
    relative_path = os.path.relpath(current_directory_path, REAL_OS_PATH)
    if relative_path == ".":
        return "~"
    return f"~/{relative_path}"

def resolve_real_path(input_path):
    """Haqiqiy path ni aniqlash"""
    if input_path.startswith("/"):
        if input_path.lower().startswith("/os"):
            relative_part = input_path[len("/OS"):] if input_path.startswith("/OS") else input_path[len("/os"):]
            if not relative_part:
                return REAL_OS_PATH
            return os.path.abspath(os.path.join(REAL_OS_PATH, relative_part.lstrip('/')))
        else:
            return input_path
    else:
        return os.path.abspath(os.path.join(current_directory_path, input_path))

def get_permissions_string(st_mode, item_path):
    """Ruxsatlar stringini olish"""
    perms = ['-'] * 10
    
    if stat.S_ISDIR(st_mode):
        perms[0] = 'd'
    elif stat.S_ISLNK(st_mode):
        perms[0] = 'l'

    # User permissions
    perms[1] = 'r' if (st_mode & stat.S_IRUSR) else '-'
    perms[2] = 'w' if (st_mode & stat.S_IWUSR) else '-'
    perms[3] = 'x' if (st_mode & stat.S_IXUSR) else '-'

    # Group permissions
    perms[4] = 'r' if (st_mode & stat.S_IRGRP) else '-'
    perms[5] = 'w' if (st_mode & stat.S_IWGRP) else '-'
    perms[6] = 'x' if (st_mode & stat.S_IXGRP) else '-'

    # Other permissions
    perms[7] = 'r' if (st_mode & stat.S_IROTH) else '-'
    perms[8] = 'w' if (st_mode & stat.S_IWOTH) else '-'
    perms[9] = 'x' if (st_mode & stat.S_IXOTH) else '-'

    # Special bits
    if (st_mode & stat.S_ISUID) and perms[3] == 'x': perms[3] = 's'
    elif (st_mode & stat.S_ISUID) and perms[3] == '-': perms[3] = 'S'
    if (st_mode & stat.S_ISGID) and perms[6] == 'x': perms[6] = 's'
    elif (st_mode & stat.S_ISGID) and perms[6] == '-': perms[6] = 'S'
    if (st_mode & stat.S_ISVTX) and perms[9] == 'x': perms[9] = 't'
    elif (st_mode & stat.S_ISVTX) and perms[9] == '-': perms[9] = 'T'

    return "".join(perms)

def safe_file_operation(func, filename, operation_name):
    """Xavfsiz fayl operatsiyasi"""
    resolved_file = resolve_real_path(filename)
    if not resolved_file.startswith(REAL_OS_PATH):
        print(f"{operation_name}: '{filename}': Permission denied (Cannot access files outside OS folder)")
        return None
    if not os.path.exists(resolved_file):
        print(f"{operation_name}: '{filename}': No such file or directory")
        return None
    if os.path.isdir(resolved_file):
        print(f"{operation_name}: '{filename}': Is a directory")
        return None
    return resolved_file

# --- Buyruq funksiyalari ---

def ls_command(args_str=None):
    """ls buyrug'i"""
    show_hidden = False
    long_format = False
    
    if args_str:
        try:
            args = shlex.split(args_str)
        except ValueError:
            args = args_str.split()
    else:
        args = []

    # Argumentlarni parse qilish
    parsed_args = []
    for arg in args:
        if arg.startswith("-"):
            for char in arg[1:]:
                if char == 'a': show_hidden = True
                elif char == 'l': long_format = True
                else:
                    print(f"ls: invalid option -- '{char}'")
                    return
        else:
            parsed_args.append(arg)

    # Target path aniqlash
    if not parsed_args:
        target_path = current_directory_path
    elif len(parsed_args) == 1:
        target_path = resolve_real_path(parsed_args[0])
    else:
        # Bir nechta path
        for path_arg in parsed_args:
            resolved_path = resolve_real_path(path_arg)
            if not resolved_path.startswith(REAL_OS_PATH):
                print(f"ls: '{path_arg}': Permission denied")
                continue
            if not os.path.exists(resolved_path):
                print(f"ls: '{path_arg}': No such file or directory")
                continue
            
            print(f"\n{path_arg}:")
            _ls_display_items(resolved_path, show_hidden, long_format)
        return

    # Yagona path uchun
    if not target_path.startswith(REAL_OS_PATH):
        print(f"ls: Permission denied")
        return

    if not os.path.exists(target_path):
        print(f"ls: No such file or directory")
        return
            
    if os.path.isfile(target_path):
        _display_single_file_ls(target_path, long_format)
    elif os.path.isdir(target_path):
        _ls_display_items(target_path, show_hidden, long_format)

def _ls_display_items(directory_path, show_hidden, long_format):
    """ls natijalari ko'rsatish"""
    items = []
    try:
        all_items = os.listdir(directory_path)
                    
        for item_name in sorted(all_items):
            if not show_hidden and item_name.startswith('.'):
                continue
                            
            full_item_path = os.path.join(directory_path, item_name)
                            
            display_name = item_name
            if os.path.isdir(full_item_path):
                display_name = f"{COLOR_DIR}{item_name}/{COLOR_RESET}"
            elif os.path.islink(full_item_path):
                try:
                    target_link = os.readlink(full_item_path)
                    display_name = f"{COLOR_CYAN}{item_name}{COLOR_RESET} -> {target_link}"
                except OSError:
                    display_name = f"{COLOR_CYAN}{item_name}{COLOR_RESET}"
            elif os.path.isfile(full_item_path):
                if os.access(full_item_path, os.X_OK):
                    display_name = f"{COLOR_EXEC}{item_name}{COLOR_RESET}"
                else:
                    display_name = f"{COLOR_FILE}{item_name}{COLOR_RESET}"
            else:
                display_name = f"{COLOR_FILE}{item_name}{COLOR_RESET}"
                            
            if long_format:
                try:
                    stat_info = os.lstat(full_item_path) if os.path.islink(full_item_path) else os.stat(full_item_path)
                    perms = get_permissions_string(stat_info.st_mode, full_item_path)
                    nlink = stat_info.st_nlink
                    owner_name = "user"
                    group_name = "user"
                    size = stat_info.st_size
                    mod_time = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime('%b %d %H:%M')
                                            
                    long_entry = f"{perms} {nlink:2} {owner_name:8} {group_name:8} {size:8} {mod_time} {display_name}"
                    items.append(long_entry)
                except OSError:
                    items.append(f"????????? {display_name} (Permission denied)")
            else:
                items.append(display_name)
                    
        # Chiqarish
        if not items:
            return

        if long_format:
            for item in items:
                print(item)
        else:
            # Ustunlar formatida
            COLUMNS = 3
            max_len = max(len(re.sub(r'\x1b\[[0-9;]*m', '', item.split(" -> ")[0])) for item in items)
            column_width = max_len + 4
            rows_per_column = math.ceil(len(items) / COLUMNS)
                    
            for r in range(rows_per_column):
                line = []
                for c in range(COLUMNS):
                    idx = r + c * rows_per_column
                    if idx < len(items):
                        item_display = items[idx]
                        clean_item = re.sub(r'\x1b\[[0-9;]*m', '', item_display.split(" -> ")[0])
                        padding_needed = column_width - len(clean_item)
                        line.append(item_display + " " * padding_needed)
                print("".join(line))
            
    except PermissionError:
        print(f"ls: Permission denied")
    except OSError as e:
        print(f"ls: Error: {e}")

def _display_single_file_ls(file_path, long_format):
    """Bitta fayl uchun ls"""
    item_name = os.path.basename(file_path)
    display_name = f"{COLOR_EXEC}{item_name}{COLOR_RESET}" if os.access(file_path, os.X_OK) else f"{COLOR_FILE}{item_name}{COLOR_RESET}"

    if long_format:
        try:
            stat_info = os.stat(file_path)
            perms = get_permissions_string(stat_info.st_mode, file_path)
            nlink = stat_info.st_nlink
            owner_name = "user"
            group_name = "user"
            size = stat_info.st_size
            mod_time = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime('%b %d %H:%M')
            print(f"{perms} {nlink:2} {owner_name:8} {group_name:8} {size:8} {mod_time} {display_name}")
        except OSError:
            print(f"ls: Permission denied")
    else:
        print(display_name)

def cd_command(target_path):
    """cd buyrug'i"""
    global current_directory_path
    if not target_path or target_path == "~":
        current_directory_path = REAL_OS_PATH
        return
    
    resolved_target = resolve_real_path(target_path)
    
    if not resolved_target.startswith(REAL_OS_PATH):
        if os.path.exists(resolved_target):
            print(f"cd: '{target_path}': Permission denied")
        else:
            print(f"cd: '{target_path}': No such file or directory")
        return

    if not os.path.exists(resolved_target):
        print(f"cd: '{target_path}': No such file or directory")
        return
    if os.path.isdir(resolved_target):
        current_directory_path = resolved_target
    else:
        print(f"cd: '{target_path}': Not a directory")

def cat_command(filename):
    """cat buyrug'i"""
    resolved_file = safe_file_operation(lambda: None, filename, "cat")
    if resolved_file is None:
        return
    
    try:
        with open(resolved_file, 'r', encoding='utf-8', errors='ignore') as f:
            print(f.read(), end='')
    except PermissionError:
        print(f"cat: '{filename}': Permission denied")
    except Exception as e:
        print(f"cat: '{filename}': Error: {e}")

def mkdir_command(args_str):
    """mkdir buyrug'i"""
    if not args_str:
        print("mkdir: missing operand")
        return
    
    dir_names = args_str.split()
    for dirname in dir_names:
        full_path = os.path.join(current_directory_path, dirname)
        if not full_path.startswith(REAL_OS_PATH):
            print(f"mkdir: '{dirname}': Permission denied")
            continue
        if os.path.exists(full_path):
            print(f"mkdir: '{dirname}': File exists")
        else:
            try:
                os.mkdir(full_path)
            except PermissionError:
                print(f"mkdir: '{dirname}': Permission denied")
            except OSError as e:
                print(f"mkdir: '{dirname}': {e}")

def touch_command(args_str):
    """touch buyrug'i"""
    if not args_str:
        print("touch: missing file operand")
        return
    
    filename = args_str.strip()
    full_path = os.path.join(current_directory_path, filename)
    
    if not full_path.startswith(REAL_OS_PATH):
        print(f"touch: '{filename}': Permission denied")
        return
    
    if os.path.isdir(full_path):
        print(f"touch: '{filename}': Is a directory")
    else:
        try:
            with open(full_path, 'a', encoding='utf-8'):
                pass
            os.utime(full_path, None)
        except PermissionError:
            print(f"touch: '{filename}': Permission denied")
        except Exception as e:
            print(f"touch: '{filename}': {e}")

def grep_command(args_str):
    """grep buyrug'i"""
    if not args_str:
        print("grep: missing operand")
        return
    
    try:
        args = shlex.split(args_str)
    except ValueError:
        args = args_str.split()
    
    if len(args) < 2:
        print("grep: missing operand")
        return
    
    pattern = args[0]
    filename = args[1]
    
    resolved_file = safe_file_operation(lambda: None, filename, "grep")
    if resolved_file is None:
        return

    try:
        with open(resolved_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if pattern in line:
                    print(line.rstrip('\n'))
    except PermissionError:
        print(f"grep: '{filename}': Permission denied")
    except Exception as e:
        print(f"grep: '{filename}': {e}")

def awk_command(args_str):
    """AWK buyrug'i - soddalashtirilgan versiya"""
    if not args_str:
        print("awk: missing operand")
        return
    
    try:
        args = shlex.split(args_str)
    except ValueError:
        args = args_str.split()
    
    if len(args) < 2:
        print("awk: missing operand")
        return
    
    # Field separator va boshqa opsiyalarni parse qilish
    field_separator = None
    script = None
    filename = None
    
    i = 0
    while i < len(args):
        if args[i] == '-F':
            if i + 1 < len(args):
                field_separator = args[i + 1]
                i += 2
            else:
                print("awk: option requires an argument -- 'F'")
                return
        elif args[i].startswith('-F'):
            # -F',' yoki -F, formatida
            field_separator = args[i][2:]
            i += 1
        elif script is None:
            script = args[i]
            i += 1
        elif filename is None:
            filename = args[i]
            i += 1
        else:
            i += 1
    
    if script is None or filename is None:
        print("awk: missing script or filename")
        return
    
    if field_separator is None:
        field_separator = r'\s+'  # Default whitespace
    elif field_separator.startswith("'") and field_separator.endswith("'"):
        field_separator = field_separator[1:-1]  # Remove quotes
    elif field_separator.startswith('"') and field_separator.endswith('"'):
        field_separator = field_separator[1:-1]  # Remove quotes
    
    resolved_file = safe_file_operation(lambda: None, filename, "awk")
    if resolved_file is None:
        return

    try:
        with open(resolved_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip('\n')
                
                # Field splitting
                if field_separator == r'\s+':
                    fields = line.split()
                elif field_separator == ',':
                    fields = line.split(',')
                else:
                    fields = re.split(field_separator, line)
                
                # Simple AWK script processing
                if script == '{print}' or script == '{print $0}':
                    print(line)
                elif script.startswith('{print $'):
                    # Extract field number
                    field_match = re.search(r'\$(\d+)', script)
                    if field_match:
                        field_num = int(field_match.group(1))
                        if field_num == 0:
                            print(line)
                        elif 1 <= field_num <= len(fields):
                            print(fields[field_num - 1].strip())
                elif script.startswith('{print $1'):
                    # Print multiple fields
                    field_matches = re.findall(r'\$(\d+)', script)
                    output_fields = []
                    for field_str in field_matches:
                        field_num = int(field_str)
                        if field_num == 0:
                            output_fields.append(line)
                        elif 1 <= field_num <= len(fields):
                            output_fields.append(fields[field_num - 1].strip())
                    print(' '.join(output_fields))
                elif '/' in script:
                    # Pattern matching
                    pattern_match = re.search(r'/([^/]+)/', script)
                    if pattern_match:
                        pattern = pattern_match.group(1)
                        if pattern in line:
                            if '{print}' in script or script.endswith('/'):
                                print(line)
                else:
                    # Basic pattern matching
                    if script in line:
                        print(line)
                    elif script == 'NR':
                        print(line_num)
                    elif script == 'NF':
                        print(len(fields))
    except PermissionError:
        print(f"awk: '{filename}': Permission denied")
    except Exception as e:
        print(f"awk: '{filename}': {e}")

def find_command(args_str):
    """find buyrug'i"""
    if not args_str:
        path_to_search = current_directory_path
        name_pattern = None
    else:
        try:
            args = shlex.split(args_str)
        except ValueError:
            args = args_str.split()
        
        path_to_search = current_directory_path
        name_pattern = None
        
        # Parse arguments
        i = 0
        while i < len(args):
            if args[i] == '-name':
                if i + 1 < len(args):
                    name_pattern = args[i + 1].strip('"\'')
                    # Convert wildcards to regex
                    name_pattern = name_pattern.replace('*', '.*').replace('?', '.')
                    i += 2
                else:
                    print("find: missing argument to '-name'")
                    return
            elif not args[i].startswith('-'):
                path_to_search = resolve_real_path(args[i])
                i += 1
            else:
                i += 1

    if not path_to_search.startswith(REAL_OS_PATH):
        print("find: Permission denied")
        return

    if not os.path.exists(path_to_search):
        print("find: No such file or directory")
        return

    try:
        for root, dirs, files in os.walk(path_to_search):
            # Search in files
            for name in files:
                if name_pattern:
                    if re.match(name_pattern + '$', name):
                        rel_path = os.path.relpath(os.path.join(root, name), REAL_OS_PATH)
                        print(f"~/{rel_path}")
                else:
                    rel_path = os.path.relpath(os.path.join(root, name), REAL_OS_PATH)
                    print(f"~/{rel_path}")
            
            # Search in directories
            for name in dirs:
                if name_pattern:
                    if re.match(name_pattern + '$', name):
                        rel_path = os.path.relpath(os.path.join(root, name), REAL_OS_PATH)
                        print(f"~/{rel_path}")
                else:
                    rel_path = os.path.relpath(os.path.join(root, name), REAL_OS_PATH)
                    print(f"~/{rel_path}")
    except PermissionError:
        print("find: Permission denied")
    except Exception as e:
        print(f"find: {e}")

def wc_command(args_str):
    """wc buyrug'i"""
    if not args_str:
        print("wc: missing operand")
        return
    
    try:
        args = shlex.split(args_str)
    except ValueError:
        args = args_str.split()
    
    show_lines = True
    show_words = True
    show_chars = True
    
    files = []
    for arg in args:
        if arg == '-l':
            show_lines = True
            show_words = False
            show_chars = False
        elif arg == '-w':
            show_lines = False
            show_words = True
            show_chars = False
        elif arg == '-c' or arg == '-m':
            show_lines = False
            show_words = False
            show_chars = True
        else:
            files.append(arg)
    
    if not files:
        print("wc: missing file operand")
        return
    
    for filename in files:
        resolved_file = safe_file_operation(lambda: None, filename, "wc")
        if resolved_file is None:
            continue
        
        try:
            with open(resolved_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.count('\n')
                words = len(content.split())
                chars = len(content)
                
                output = []
                if show_lines:
                    output.append(str(lines))
                if show_words:
                    output.append(str(words))
                if show_chars:
                    output.append(str(chars))
                
                print(f"{' '.join(output)} {filename}")
        except PermissionError:
            print(f"wc: '{filename}': Permission denied")
        except Exception as e:
            print(f"wc: '{filename}': {e}")

def sort_command(args_str):
    """sort buyrug'i"""
    if not args_str:
        print("sort: missing operand")
        return
    
    filename = args_str.strip()
    resolved_file = safe_file_operation(lambda: None, filename, "sort")
    if resolved_file is None:
        return
    
    try:
        with open(resolved_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            sorted_lines = sorted(lines)
            for line in sorted_lines:
                print(line.rstrip('\n'))
    except PermissionError:
        print(f"sort: '{filename}': Permission denied")
    except Exception as e:
        print(f"sort: '{filename}': {e}")

def tail_command(args_str):
    """tail buyrug'i"""
    if not args_str:
        print("tail: missing operand")
        return
    
    try:
        args = shlex.split(args_str)
    except ValueError:
        args = args_str.split()
    
    num_lines = 10
    filename = None
    
    i = 0
    while i < len(args):
        if args[i] == '-n':
            if i + 1 < len(args):
                try:
                    num_lines = int(args[i + 1])
                    i += 2
                except ValueError:
                    print(f"tail: invalid number of lines: '{args[i + 1]}'")
                    return
            else:
                print("tail: option requires an argument -- 'n'")
                return
        elif args[i].startswith('-n'):
            try:
                num_lines = int(args[i][2:])
                i += 1
            except ValueError:
                print(f"tail: invalid number of lines: '{args[i][2:]}'")
                return
        else:
            filename = args[i]
            break
    
    if filename is None:
        print("tail: missing file operand")
        return
    
    resolved_file = safe_file_operation(lambda: None, filename, "tail")
    if resolved_file is None:
        return
    
    try:
        with open(resolved_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for line in lines[-num_lines:]:
                print(line.rstrip('\n'))
    except PermissionError:
        print(f"tail: '{filename}': Permission denied")
    except Exception as e:
        print(f"tail: '{filename}': {e}")

def head_command(args_str):
    """head buyrug'i"""
    if not args_str:
        print("head: missing operand")
        return
    
    try:
        args = shlex.split(args_str)
    except ValueError:
        args = args_str.split()
    
    num_lines = 10
    filename = None
    
    i = 0
    while i < len(args):
        if args[i] == '-n':
            if i + 1 < len(args):
                try:
                    num_lines = int(args[i + 1])
                    i += 2
                except ValueError:
                    print(f"head: invalid number of lines: '{args[i + 1]}'")
                    return
            else:
                print("head: option requires an argument -- 'n'")
                return
        elif args[i].startswith('-n'):
            try:
                num_lines = int(args[i][2:])
                i += 1
            except ValueError:
                print(f"head: invalid number of lines: '{args[i][2:]}'")
                return
        else:
            filename = args[i]
            break
    
    if filename is None:
        print("head: missing file operand")
        return
    
    resolved_file = safe_file_operation(lambda: None, filename, "head")
    if resolved_file is None:
        return
    
    try:
        with open(resolved_file, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                if i >= num_lines:
                    break
                print(line.rstrip('\n'))
    except PermissionError:
        print(f"head: '{filename}': Permission denied")
    except Exception as e:
        print(f"head: '{filename}': {e}")

def echo_command(args_str):
    """echo buyrug'i"""
    if not args_str:
        print()
        return
    
    # Redirection check
    if '>' in args_str:
        parts = args_str.split('>', 1)
        text_to_write = parts[0].strip()
        redirect_target = parts[1].strip()
        
        append_mode = False
        if redirect_target.startswith('>'):
            append_mode = True
            redirect_target = redirect_target[1:].strip()
        
        # Remove quotes from text
        if text_to_write.startswith('"') and text_to_write.endswith('"'):
            text_to_write = text_to_write[1:-1]
        elif text_to_write.startswith("'") and text_to_write.endswith("'"):
            text_to_write = text_to_write[1:-1]
        
        resolved_file = resolve_real_path(redirect_target)
        if not resolved_file.startswith(REAL_OS_PATH):
            print(f"echo: '{redirect_target}': Permission denied")
            return
        
        try:
            mode = 'a' if append_mode else 'w'
            with open(resolved_file, mode, encoding='utf-8') as f:
                f.write(text_to_write + '\n')
        except PermissionError:
            print(f"echo: '{redirect_target}': Permission denied")
        except Exception as e:
            print(f"echo: {e}")
    else:
        # Regular echo
        text = args_str
        # Remove quotes if present
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        elif text.startswith("'") and text.endswith("'"):
            text = text[1:-1]
        print(text)

def alias_command(args_str):
    """alias buyrug'i"""
    global ALIASES
    if not args_str:
        # Show all aliases
        for key, value in ALIASES.items():
            print(f"alias {key}='{value}'")
        return

    if '=' not in args_str:
        # Show specific alias
        if args_str in ALIASES:
            print(f"alias {args_str}='{ALIASES[args_str]}'")
        else:
            print(f"alias: {args_str}: not found")
        return

    # Create new alias
    try:
        key, value = args_str.split('=', 1)
        value = value.strip().strip("'\"")
        ALIASES[key.strip()] = value
    except ValueError:
        print("alias: invalid syntax")

def history_command(args_str=None):
    """history buyrug'i"""
    if not COMMAND_HISTORY:
        return
    
    for i, cmd in enumerate(COMMAND_HISTORY):
        print(f" {i+1}  {cmd}")

def env_command(args_str=None):
    """env buyrug'i"""
    print(f"USER={USER_NAME}")
    print(f"HOME={REAL_OS_PATH}")
    print(f"PWD={current_directory_path}")
    print("PATH=/usr/local/bin:/usr/bin:/bin")
    print("TERM=xterm-256color")
    print("SHELL=/bin/bash")

def which_command(program_name):
    """which buyrug'i"""
    if not program_name:
        print("which: missing operand")
        return
    
    if program_name in COMMAND_MAP:
        print(f"/usr/bin/{program_name}")
    elif program_name in ALIASES:
        print(f"alias {program_name}='{ALIASES[program_name]}'")
    else:
        return  # No output like real which

def help_command(args_str=None):
    """help buyrug'i"""
    print("Little Red CTF Shell - Available Commands:")
    commands = sorted([cmd for cmd in COMMAND_MAP.keys() if cmd != 'exit'])
    
    max_len = max(len(cmd) for cmd in commands) + 4
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80

    cols = max(1, terminal_width // max_len)
    
    for i, command in enumerate(commands):
        print(f"{command:<{max_len}}", end="")
        if (i + 1) % cols == 0:
            print()
    print("\n\nFor more information, use 'man <command>'.")

def clear_command(args_str=None):
    """clear buyrug'i"""
    os.system('cls' if os.name == 'nt' else 'clear')

def man_command(args_str):
    """man buyrug'i"""
    if not args_str:
        print("What manual page do you want?")
        return
    
    command_name = args_str.strip()
    
    # Basic man pages
    man_pages = {
        "ls": "List directory contents",
        "cd": "Change directory",
        "cat": "Display file contents",
        "grep": "Search patterns in files",
        "awk": "Pattern scanning and processing",
        "find": "Search for files and directories",
        "wc": "Word, line, character, and byte count",
        "sort": "Sort lines of text",
        "head": "Output first part of files",
        "tail": "Output last part of files",
        "echo": "Display line of text",
        "mkdir": "Create directories",
        "touch": "Create empty files or update timestamps",
        "help": "Show available commands",
        "clear": "Clear terminal screen",
        "history": "Show command history",
        "alias": "Create command aliases",
        "env": "Display environment variables",
        "which": "Locate command"
    }
    
    if command_name in man_pages:
        print(f"{command_name.upper()}(1)")
        print(f"NAME\n       {command_name} - {man_pages[command_name]}")
        print(f"\nSYNOPSIS\n       {command_name} [options] [arguments]")
        print(f"\nDESCRIPTION\n       {man_pages[command_name]}")
    else:
        print(f"No manual entry for {command_name}")

def ps_command(args_str=None):
    """ps buyrug'i simulatsiyasi"""
    print("  PID TTY          TIME CMD")
    print(" 1234 pts/0    00:00:01 bash")
    print(" 5678 pts/0    00:00:00 ctf-terminal")

def kill_command(args_str):
    """kill buyrug'i simulatsiyasi"""
    if not args_str:
        print("kill: missing operand")
        return
    print(f"kill: simulated command - would kill process {args_str}")

def chmod_command(args_str):
    """chmod buyrug'i simulatsiyasi"""
    if not args_str:
        print("chmod: missing operand")
        return
    print(f"chmod: simulated command - would change permissions: {args_str}")

def chown_command(args_str):
    """chown buyrug'i simulatsiyasi"""
    if not args_str:
        print("chown: missing operand")
        return
    print(f"chown: simulated command - would change ownership: {args_str}")

# Pipeline support
def execute_piped_commands(commands_list):
    """Pipeline buyruqlarini bajarish"""
    input_data = ""
    
    for i, (cmd, args) in enumerate(commands_list):
        if cmd == "cat" and i == 0:
            # First command in pipeline
            resolved_file = safe_file_operation(lambda: None, args, "cat")
            if resolved_file is None:
                return
            
            try:
                with open(resolved_file, 'r', encoding='utf-8', errors='ignore') as f:
                    input_data = f.read()
            except Exception as e:
                print(f"cat: {e}")
                return
        
        elif cmd == "grep" and input_data:
            # Grep from piped input
            pattern = args
            output_lines = []
            for line in input_data.splitlines():
                if pattern in line:
                    output_lines.append(line)
            input_data = "\n".join(output_lines)
        
        elif cmd == "sort" and input_data:
            # Sort piped input
            lines = sorted(input_data.splitlines())
            input_data = "\n".join(lines)
        
        elif cmd == "head" and input_data:
            # Head from piped input
            lines = input_data.splitlines()
            num_lines = 10
            if args.startswith('-n'):
                try:
                    num_lines = int(args[2:])
                except ValueError:
                    num_lines = 10
            input_data = "\n".join(lines[:num_lines])
        
        elif cmd == "tail" and input_data:
            # Tail from piped input
            lines = input_data.splitlines()
            num_lines = 10
            if args.startswith('-n'):
                try:
                    num_lines = int(args[2:])
                except ValueError:
                    num_lines = 10
            input_data = "\n".join(lines[-num_lines:])
        
        elif cmd == "wc" and input_data:
            # Word count from piped input
            lines = input_data.count('\n')
            words = len(input_data.split())
            chars = len(input_data)
            
            if args == '-l':
                print(lines)
            elif args == '-w':
                print(words)
            elif args == '-c' or args == '-m':
                print(chars)
            else:
                print(f"{lines} {words} {chars}")
            return
        
        else:
            print(f"Command '{cmd}' not supported in pipeline")
            return
    
    # Print final output
    if input_data:
        print(input_data)

# Command mapping
COMMAND_MAP = {
    "ls": ls_command,
    "cd": cd_command,
    "cat": cat_command,
    "mkdir": mkdir_command,
    "touch": touch_command,
    "grep": grep_command,
    "awk": awk_command,
    "find": find_command,
    "wc": wc_command,
    "sort": sort_command,
    "tail": tail_command,
    "head": head_command,
    "echo": echo_command,
    "alias": alias_command,
    "history": history_command,
    "env": env_command,
    "which": which_command,
    "help": help_command,
    "clear": clear_command,
    "man": man_command,
    "ps": ps_command,
    "kill": kill_command,
    "chmod": chmod_command,
    "chown": chown_command,
    "ll": lambda args: ls_command("-la " + (args or "")),
    "la": lambda args: ls_command("-a " + (args or "")),
    "l": lambda args: ls_command("-l " + (args or "")),
}

def execute_command(command, args, from_source=False):
    """Buyruqni bajarish"""
    # Check aliases
    if command in ALIASES:
        full_alias_cmd = ALIASES[command]
        alias_cmd_parts = full_alias_cmd.split(' ', 1)
        actual_command = alias_cmd_parts[0]
        actual_args = alias_cmd_parts[1] + " " + args if len(alias_cmd_parts) > 1 else args
        
        if actual_command == command:
            print(f"Error: alias '{command}' creates an infinite loop.")
            return

        command = actual_command
        args = actual_args

    # Handle exit
    if command == "exit":
        if not from_source:
            print("Exiting terminal.")
            sys.exit(0)
        else:
            print("exit: Command ignored in sourced file.")
            return
    
    # Execute command
    if command in COMMAND_MAP:
        try:
            if args:
                COMMAND_MAP[command](args)
            else:
                COMMAND_MAP[command]()
        except TypeError:
            # Command doesn't take arguments
            COMMAND_MAP[command]()
        except Exception as e:
            print(f"Error executing '{command}': {e}")
    else:
        print(f"{command}: Command not found")

def setup_environment():
    """Muhitni sozlash"""
    if not os.path.exists(REAL_OS_PATH):
        print(f"Creating OS directory structure...")
        try:
            os.makedirs(REAL_OS_PATH)
            
            # Create directory structure
            dirs = [
                "home/user",
                "etc",
                "var/log",
                "tmp",
                "challenge"
            ]
            
            for dir_path in dirs:
                os.makedirs(os.path.join(REAL_OS_PATH, dir_path), exist_ok=True)
            
            # Create sample files
            files = {
                "etc/motd.txt": "Welcome to the CTF terminal simulator!\n",
                "home/user/profile.txt": "User profile information\n",
                "home/user/test.txt": "Line 1\nLine 2\nLine 3\n",
                "challenge/flag.txt": "CTF_FLAG{welcome_to_the_simulation}\n",
                "challenge/data.txt": "apple\nbanana\ncherry\napple\ndate\n"
            }
            
            for file_path, content in files.items():
                full_path = os.path.join(REAL_OS_PATH, file_path)
                with open(full_path, 'w') as f:
                    f.write(content)
            
            print("Environment setup complete!")
        except Exception as e:
            print(f"Error setting up environment: {e}")
            sys.exit(1)
    elif not os.path.isdir(REAL_OS_PATH):
        print(f"Error: '{REAL_OS_PATH}' exists but is not a directory.")
        sys.exit(1)

def run_ctf_terminal():
    """Asosiy terminal tsikli"""
    ascii_logo = rf"""
{COLOR_HACKING_CYAN}▖  ▖  ▜     {COLOR_RESET}{COLOR_HACKING_RED}       ▗     ▄    ▌▄▖    {COLOR_RESET}
{COLOR_HACKING_CYAN}▌▞▖▌█▌▐ ▛▘▛▌▛▛▌█▌  {COLOR_RESET}{COLOR_HACKING_RED}▜▘▛▌  ▌▌█▌▛▌▚ █▌▛▘{COLOR_RESET}
{COLOR_HACKING_CYAN}▛ ▝▌▙▖▐▖▙▖▙▌▌▌▌▙▖  {COLOR_RESET}{COLOR_HACKING_RED}▐▖▙▌  ▙▘▙▖▙▌▄▌▙▖▙▖{COLOR_RESET} {COLOR_HACKING_GREEN}{COLOR_HACKING_BOLD}Little Red{COLOR_RESET}

{COLOR_HACKING_YELLOW}{COLOR_HACKING_BOLD}remember they're listening!!!{COLOR_RESET}
"""
    print(ascii_logo)
    print(f"{COLOR_HACKING_YELLOW}Type 'help' for available commands.{COLOR_RESET}")
    
    while True:
        try:
            display_path = get_display_path_string()
            prompt = f"{COLOR_PROMPT_USER_HOST}{USER_NAME}@{HOST_NAME}{COLOR_RESET}:{COLOR_PROMPT_PATH}{display_path}{COLOR_RESET}$ "
            
            user_input = input(prompt).strip()
            
            if not user_input:
                continue

            # Add to history
            COMMAND_HISTORY.append(user_input)

            # Handle piped commands
            if '|' in user_input:
                pipe_commands_str = user_input.split('|')
                piped_commands = []
                for cmd_part in pipe_commands_str:
                    cmd_part = cmd_part.strip()
                    if not cmd_part:
                        continue
                    parts = cmd_part.split(" ", 1)
                    cmd = parts[0]
                    cmd_args = parts[1] if len(parts) > 1 else ""
                    piped_commands.append((cmd, cmd_args))
                
                if piped_commands:
                    execute_piped_commands(piped_commands)
                continue

            # Handle regular commands
            parts = user_input.split(" ", 1)
            command = parts[0]
            args = parts[1] if len(parts) > 1 else ""

            execute_command(command, args)
        
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit.")
            continue
        except EOFError:
            print("\nExiting terminal.")
            break

def main():
    """Asosiy funksiya"""
    setup_environment()
    run_ctf_terminal()

if __name__ == "__main__":
    main()
