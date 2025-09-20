import subprocess
import sys

def main():
    try:
        # Запускаем бота через subprocess
        process = subprocess.Popen(
            [sys.executable, "bot.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Ждем завершения и выводим результат
        stdout, stderr = process.communicate()
        
        print("=== STDOUT ===")
        print(stdout)
        
        print("\n=== STDERR ===")
        print(stderr)
        
    except Exception as e:
        print(f"Ошибка запуска: {e}")
    
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()