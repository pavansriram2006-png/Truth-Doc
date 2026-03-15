import os

import requests
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

Builder.load_string(
    r"""
<RootWidget>:
    canvas.before:
        Color:
            rgba: 0.12,0.12,0.12,1
        Rectangle:
            pos: self.pos
            size: self.size

<Button>:
    background_color: (.2,.2,.2,1)
    color: (1,1,1,1)
    font_size: '18sp'

<Label>:
    color: (1,1,1,1)
    font_size: '16sp'

<TextInput>:
    background_color: (1,1,1,1)
    foreground_color: (0,0,0,1)
    font_size: '16sp'
"""
)


class RootWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=10, padding=10, **kwargs)
        self.file_path = ""

        self.add_widget(Label(text="TruthDoc AI", font_size="24sp", size_hint=(1, 0.1)))

        doc_box = BoxLayout(orientation="horizontal", spacing=10, size_hint=(1, 0.1))
        self.selected_label = Label(text="No file selected", size_hint=(0.6, 1))
        self.doc_select = Button(text="Browse...", size_hint=(0.2, 1))
        self.doc_select.bind(on_press=self.open_filechooser)
        self.verify_button = Button(text="Verify", size_hint=(0.2, 1))
        self.verify_button.bind(on_press=self.verify_document)
        doc_box.add_widget(self.selected_label)
        doc_box.add_widget(self.doc_select)
        doc_box.add_widget(self.verify_button)
        self.add_widget(doc_box)

        self.preview = Image(size_hint=(1, 0.3))
        self.add_widget(self.preview)

        sms_box = BoxLayout(orientation="vertical", spacing=5, size_hint=(1, 0.3))
        self.sms_input = TextInput(
            hint_text="Paste SMS/Internship message here", size_hint=(1, 0.75), multiline=True
        )
        sms_box.add_widget(self.sms_input)
        self.sms_button = Button(text="Verify SMS", size_hint=(1, 0.25))
        self.sms_button.bind(on_press=self.verify_sms)
        sms_box.add_widget(self.sms_button)
        self.add_widget(sms_box)

        self.result_label = Label(text="", size_hint=(1, 0.2))
        self.add_widget(self.result_label)
        self.progress = ProgressBar(max=100, value=0, size_hint=(1, 0.05))
        self.add_widget(self.progress)

    def _format_backend_error(self, response: requests.Response) -> str:
        try:
            payload = response.json()
            detail = payload.get("detail", "Backend error")
            return f"Backend error: {detail}"
        except Exception:
            return f"Backend error: HTTP {response.status_code}"

    def verify_document(self, instance):
        if not self.file_path:
            self.result_label.text = "Select a file first"
            return

        self.result_label.text = ""
        self.result_label.color = (1, 1, 1, 1)
        self.progress.value = 0

        path = self.file_path
        try:
            with open(path, "rb") as f:
                files = {"file": (os.path.basename(path), f, "application/octet-stream")}
                response = requests.post(f"{BACKEND_URL}/verify-document/", files=files, timeout=30)

            if response.status_code == 200:
                data = response.json()
                lines = [f"Status: {data['status']}", f"Risk score: {data['risk_score']}%"]
                if data["reason_for_flag"]:
                    lines.append("Reasons:")
                    for reason in data["reason_for_flag"]:
                        lines.append(f" - {reason}")
                self.result_label.text = "\n".join(lines)
                self.result_label.color = (0, 1, 0, 1) if data["status"].lower() == "genuine" else (1, 0, 0, 1)
                self.progress.value = int(data["risk_score"])
            else:
                self.result_label.text = self._format_backend_error(response)

        except requests.exceptions.RequestException as req_error:
            self.result_label.text = f"Backend request failed: {req_error}"
        except Exception as e:
            self.result_label.text = str(e)

    def verify_sms(self, instance):
        text = self.sms_input.text.strip()
        if not text:
            self.result_label.text = "Enter some text"
            return

        self.result_label.text = ""
        self.result_label.color = (1, 1, 1, 1)
        self.progress.value = 0

        try:
            payload = {"raw_text": text}
            response = requests.post(f"{BACKEND_URL}/verify-sms/", json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                lines = [f"Status: {data['status']}", f"Risk score: {data['risk_score']}%"]
                if data["reason_for_flag"]:
                    lines.append("Reasons:")
                    for reason in data["reason_for_flag"]:
                        lines.append(f" - {reason}")
                self.result_label.text = "\n".join(lines)
                self.result_label.color = (0, 1, 0, 1) if data["status"].lower() == "genuine" else (1, 0, 0, 1)
                self.progress.value = int(data["risk_score"])
            else:
                self.result_label.text = self._format_backend_error(response)

        except requests.exceptions.RequestException as req_error:
            self.result_label.text = f"Backend request failed: {req_error}"
        except Exception as e:
            self.result_label.text = str(e)

    def open_filechooser(self, instance):
        content = BoxLayout(orientation="vertical")
        chooser = FileChooserIconView(
            filters=["*.png", "*.jpg", "*.jpeg", "*.pdf", "*.docx"], size_hint=(1, 0.9)
        )

        try:
            chooser.path = os.path.expanduser("~")
        except Exception:
            pass

        select_btn = Button(text="Select", size_hint=(1, 0.1))
        content.add_widget(chooser)
        content.add_widget(select_btn)
        popup = Popup(title="Pick a file", content=content, size_hint=(0.9, 0.9))

        def choose(_):
            if chooser.selection:
                self.file_path = chooser.selection[0]
                popup.dismiss()
                self.selected_label.text = f"Selected: {os.path.basename(self.file_path)}"
                if self.file_path.lower().endswith((".png", ".jpg", ".jpeg")):
                    self.preview.source = self.file_path
                else:
                    self.preview.source = ""

        select_btn.bind(on_press=choose)
        popup.open()


class TruthDocApp(App):
    def build(self):
        self.title = "TruthDoc AI"
        return RootWidget()


if __name__ == "__main__":
    TruthDocApp().run()
