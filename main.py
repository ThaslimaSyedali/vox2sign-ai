import tkinter as tk
from tkinter import ttk
import speech_recognition as sr
import cv2
from PIL import Image, ImageTk
import os
import threading

# --- Path to gesture videos ---
GESTURE_FOLDER = "gestures"  # make sure this folder exists!

# --- Globals ---
cap = None
playing = False
gesture_queue = []
current_gesture = None


# --- Safe UI Update Helper ---
def safe_ui_update(func):
    """Run a UI update safely on the main thread."""
    root.after(0, func)


# --- Video Frame Update Function ---
def update_frame():
    global cap, playing
    if not playing or cap is None:
        return

    ret, frame = cap.read()
    if ret:
        frame = cv2.resize(frame, (640, 360))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.config(image=imgtk)
        video_label.after(33, update_frame)
    else:
        # Video finished
        cap.release()
        cap = None
        playing = False
        video_label.config(image="")
        play_next_gesture()


# --- Play a single gesture video ---
def play_video(gesture_name):
    global cap, playing

    video_path = os.path.join(GESTURE_FOLDER, f"{gesture_name.lower()}.mp4")
    print("Trying to open:", video_path)  # debug output

    if not os.path.exists(video_path):
        output_text.set(f"❌ No video found for '{gesture_name}'")
        play_next_gesture()
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        output_text.set(f"⚠️ Couldn't open video '{gesture_name}'")
        play_next_gesture()
        return

    playing = True
    output_text.set(f"🎬 Showing: {gesture_name}")
    update_frame()


# --- Sequential Playback ---
def play_next_gesture():
    global gesture_queue, current_gesture, playing
    if gesture_queue:
        current_gesture = gesture_queue.pop(0)
        root.after(600, lambda: play_video(current_gesture))
    else:
        playing = False
        output_text.set("✨ All gestures completed! 💫 You did amazing!")


# --- Sentence Playback ---
def play_sentence(sentence):
    global gesture_queue, playing

    if playing and cap:
        cap.release()
        playing = False

    words = sentence.strip().split()
    gesture_queue = [w for w in words]
    if not gesture_queue:
        output_text.set("⚠️ No words detected.")
        return

    output_text.set(f"🗣 You said: {' '.join(gesture_queue)}")
    play_next_gesture()


# --- Status messages ---
def show_status(message, color):
    status_label.config(text=message, fg=color)
    root.after(4000, lambda: status_label.config(text=""))


# --- Speech Recognition (threaded safely) ---
def recognize_speech():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            safe_ui_update(lambda: show_status("🎧 Listening for your command...", "#FFB6F0"))
            safe_ui_update(lambda: header_label.config(fg="#E0D9FF"))
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=6)

        try:
            text = recognizer.recognize_google(audio)
            safe_ui_update(lambda: [
                show_status("✅ Recognition Successful!", "#00FFB3"),
                header_label.config(fg="white"),
                play_sentence(text)
            ])
        except sr.UnknownValueError:
            safe_ui_update(lambda: [
                output_text.set("😅 Sorry, I didn’t catch that."),
                show_status("Try again! ✨", "#FF4F81")
            ])
        except sr.RequestError:
            safe_ui_update(lambda: [
                output_text.set("⚠️ API error."),
                show_status("Connection issue 💢", "#FF4F81")
            ])
    except Exception as e:
        safe_ui_update(lambda: output_text.set(f"🎙️ Microphone error: {e}"))


# --- GUI Setup ---
root = tk.Tk()
root.title("💫 Anime Speech to Gesture Player 💜")

try:
    root.state("zoomed")  # Windows
except tk.TclError:
    root.attributes("-fullscreen", True)  # mac/Linux fallback

root.configure(bg="#0D0C1D")

# --- Neon Gradient Header ---
header_canvas = tk.Canvas(root, height=160, highlightthickness=0, bd=0)
header_canvas.pack(fill="x")

for i in range(0, 160, 2):
    r = int(40 + i / 3)
    g = int(0 + i / 2)
    b = int(120 + i / 2)
    color = f"#{r:02x}{g:02x}{b:02x}"
    header_canvas.create_rectangle(0, i, 2000, i + 2, outline="", fill=color)

header_label = tk.Label(root,
                        text="🌸 Vox2Sign AI 💫",
                        bg="#302060",
                        fg="white",
                        font=("Segoe UI Black", 32, "bold"))
header_label.place(relx=0.5, rely=0.09, anchor="center")

# --- Anime-style Card Frame ---
card_frame = tk.Frame(root,
                      bg="#1E1B33",
                      highlightbackground="#FF66CC",
                      highlightthickness=3,
                      relief="ridge")
card_frame.place(relx=0.5, rely=0.47, anchor="center", relwidth=0.7, relheight=0.5)

# --- Output Label ---
output_text = tk.StringVar()
output_text.set("🎤 Speak your phrase, and watch gestures appear! 💫")

output_label = tk.Label(
    card_frame,
    textvariable=output_text,
    wraplength=850,
    justify="center",
    bg="#1E1B33",
    font=("Century Gothic", 18, "bold"),
    fg="#E0D9FF",
    borderwidth=0,
    relief="flat",
    highlightthickness=0,
    takefocus=0,
)
output_label.pack(pady=(15, 5))

# Make sure it never takes focus
output_label.bind("<FocusIn>", lambda e: root.focus())
output_label.focusable = False
output_label.focus_set = lambda *args, **kwargs: None



# --- Video Display ---
video_label = tk.Label(card_frame, bg="#1E1B33")
video_label.pack(pady=15)

# --- Status area ---
status_frame = tk.Frame(root, bg="#0D0C1D")
status_frame.pack(pady=(5, 15))

status_label = tk.Label(status_frame,
                        text="",
                        bg="#0D0C1D",
                        font=("Consolas", 16, "italic"),
                        fg="#FFB6F0",
                        wraplength=900,
                        justify="center")
status_label.pack()

# --- Button Style ---
style = ttk.Style()
style.theme_use("clam")
style.configure("Anime.TButton",
                font=("Century Gothic", 20, "bold"),
                padding=14,
                background="#FF66CC",
                foreground="white",
                borderwidth=0)
style.map("Anime.TButton",
          background=[("active", "#C93FFF")])

style.configure("Hover.TButton",
                background="#00BFFF",
                foreground="white")

def on_enter(e): start_button.config(style="Hover.TButton")
def on_leave(e): start_button.config(style="Anime.TButton")

# --- Start Button ---
start_button = ttk.Button(root,
                          text="🎤 Start Your Voice Mission!",
                          style="Anime.TButton",
                          command=lambda: threading.Thread(target=recognize_speech, daemon=True).start())
start_button.place(relx=0.5, rely=0.85, anchor="center")
start_button.bind("<Enter>", on_enter)
start_button.bind("<Leave>", on_leave)

# --- Footer ---
footer_label = tk.Label(root,
                        text="💜 Vtydragons presents ✨  Transforming Voices into Signs 🌸",
                        bg="#0D0C1D",
                        fg="#FF66CC",
                        font=("Consolas", 20, "italic"))
footer_label.pack(side="bottom", pady=15)


# --- Exit fullscreen ---
def exit_fullscreen(event):
    root.state('normal')
root.bind("<Escape>", exit_fullscreen)
root.focus_set()
root.mainloop()