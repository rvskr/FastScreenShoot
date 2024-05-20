import tkinter as tk
from tkinter import filedialog, simpledialog
from PIL import ImageGrab, ImageTk
import screeninfo
import os
import keyboard
import json

CONFIG_FILE = "config.json"
DEFAULT_SCREENSHOT_KEY = "F"
DEFAULT_EXIT_KEY = "Esc"

import tkinter.messagebox as messagebox

class ScreenshotApp:
    def __init__(self, master):
        self.master = master
        self.master.withdraw()
        self.screenshot_mode_active = False
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.save_folder = os.getcwd()
        self.load_config()
        self.create_widgets()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as file:
                config = json.load(file)
            self.screenshot_key = config.get("screenshot_key", DEFAULT_SCREENSHOT_KEY)
            self.exit_key = config.get("exit_key", DEFAULT_EXIT_KEY)
            self.show_welcome = config.get("show_welcome", True)
            print("Флаг show_welcome из конфига:", self.show_welcome)  # Добавленный вывод
        else:
            self.screenshot_key = DEFAULT_SCREENSHOT_KEY
            self.exit_key = DEFAULT_EXIT_KEY
            self.show_welcome = True
            self.save_config()
            print("Приветственное сообщение должно быть показано.")  # Добавленный вывод
            self.show_welcome_message()

        keyboard.on_press_key(self.screenshot_key, self.toggle_screenshot_mode)
        keyboard.on_press_key(self.exit_key, self.exit_app)



    def save_config(self):
        config = {"screenshot_key": self.screenshot_key, "exit_key": self.exit_key, "show_welcome": self.show_welcome}
        with open(CONFIG_FILE, "w") as file:
            json.dump(config, file)

    def show_welcome_message(self):
        welcome_window = tk.Toplevel(self.master)
        welcome_window.title("Добро пожаловать!")

        welcome_label = tk.Label(welcome_window, text=f"Добро пожаловать в программу скриншотов!\n\nДля создания скриншота нажмите клавишу '{self.screenshot_key}' и удерживая левую кнопку мыши, фиксируйте нужную область.\n\nДля завершения программы нажмите клавишу '{self.exit_key}'.")
        welcome_label.pack()

        show_welcome_var = tk.BooleanVar(value=True)
        checkbox = tk.Checkbutton(welcome_window, text="Не показывать при следующем запуске", variable=show_welcome_var)
        checkbox.pack()

        def close_welcome_window(window):
            self.show_welcome = show_welcome_var.get()
            self.save_config()
            window.destroy()

        ok_button = tk.Button(welcome_window, text="OK", command=lambda: close_welcome_window(welcome_window))
        ok_button.pack()




    # Остальной код остается неизменным



    def create_widgets(self):
        self.canvas = tk.Canvas(self.master, bg="white", highlightthickness=0)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def toggle_screenshot_mode(self, event):
        if not self.screenshot_mode_active:
            self.start_screenshot_mode()
        else:
            self.stop_screenshot_mode()

    def start_screenshot_mode(self):
        self.screenshot_mode_active = True
        self.master.deiconify()
        self.master.overrideredirect(True)
        self.master.attributes("-alpha", 0.3)
        self.master.attributes("-topmost", True)
        screen = screeninfo.get_monitors()[0]
        self.master.geometry(f"{screen.width}x{screen.height}+{screen.x}+{screen.y}")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def stop_screenshot_mode(self):
        self.screenshot_mode_active = False
        self.master.withdraw()

    def on_press(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red")

    def on_drag(self, event):
        cur_x = event.x_root
        cur_y = event.y_root
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_release(self, event):
        x, y = min(self.start_x, event.x_root), min(self.start_y, event.y_root)
        width, height = abs(event.x_root - self.start_x), abs(event.y_root - self.start_y)
        self.master.withdraw()
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        self.clear_canvas()
        self.show_screenshot(screenshot)

    def clear_canvas(self):
        self.canvas.delete("all")

    def show_screenshot(self, screenshot):
        screenshot_window = tk.Toplevel()
        screenshot_window.title("Просмотр скриншота")
        frame = tk.Frame(screenshot_window)
        frame.pack(side=tk.TOP, fill=tk.X)
        buttons = [
            ("Создать", lambda: self.create_new_screenshot(screenshot_window)),
            ("Сохранить", lambda: self.save_screenshot(screenshot)),
            ("Сохранить как", lambda: self.save_screenshot_as(screenshot)),
            ("Выбрать папку", self.select_save_folder)
        ]
        for text, command in buttons:
            button = tk.Button(frame, text=text, command=command)
            button.pack(side=tk.LEFT)
        image = ImageTk.PhotoImage(screenshot)
        label = tk.Label(screenshot_window, image=image)
        label.image = image
        label.pack()

    def save_screenshot(self, screenshot):
        save_path = os.path.join(self.save_folder, self.get_unique_filename("button", ".png"))
        screenshot.save(save_path)

    def save_screenshot_as(self, screenshot):
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if save_path:
            screenshot.save(save_path)

    def create_new_screenshot(self, screenshot_window):
        screenshot_window.destroy()
        self.master.deiconify()
        self.clear_selection()
        self.stop_screenshot_mode()

    def clear_selection(self):
        if self.rect:
            self.canvas.delete(self.rect)
            self.rect = None
            self.start_x = None
            self.start_y = None

    def select_save_folder(self):
        self.save_folder = filedialog.askdirectory()
        if not self.save_folder:
            self.save_folder = os.getcwd()

    def exit_app(self, event=None):
        self.master.quit()

    def get_unique_filename(self, base, extension):
        counter = 1
        while True:
            filename = f"{base}{counter}{extension}"
            if not os.path.exists(os.path.join(self.save_folder, filename)):
                return filename
            counter += 1

def main():
    root = tk.Tk()
    app = ScreenshotApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
