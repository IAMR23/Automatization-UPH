import os
import queue
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from compararContifico import generar_reporte_errores
from limpieza import limpiar_uphone
from limpiarContifico import limpiar_contifico
from pdf import generar_excel_desde_pdfs


APP_TITLE = "Revision de UPH vs Contifico"

COLORS = {
    "window": "#1f1f1f",
    "header": "#101828",
    "panel": "#292929",
    "panel_alt": "#1f2937",
    "input": "#303335",
    "input_border": "#5e6670",
    "log": "#191b1d",
    "text": "#ffffff",
    "muted": "#aab2bd",
    "accent": "#2478b7",
    "accent_hover": "#2e8bd2",
    "progress_track": "#62686e",
}


class ReportApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("1220x790")
        self.minsize(980, 680)
        self.configure(bg=COLORS["window"])

        self.pdf_files = []
        self.contifico_file = tk.StringVar()
        self.output_dir = tk.StringVar(value=str(Path.cwd()))
        self.running = False
        self.events = queue.Queue()

        self.pdfs_count = tk.StringVar(value="PDFs: 0")
        self.records_count = tk.StringVar(value="Registros: 0")
        self.errors_count = tk.StringVar(value="Incidencias: 0")
        self.unread_count = tk.StringVar(value="No leidas: 0")
        self.status_text = tk.StringVar(value="Listo para procesar.")

        self._build_styles()
        self._build_ui()
        self._log("Aplicacion iniciada correctamente.")
        self.after(120, self._process_events)

    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Dark.Horizontal.TProgressbar",
            troughcolor=COLORS["progress_track"],
            bordercolor=COLORS["progress_track"],
            background=COLORS["accent"],
            lightcolor=COLORS["accent"],
            darkcolor=COLORS["accent"],
            thickness=10,
        )

    def _build_ui(self):
        header = tk.Frame(self, bg=COLORS["header"], height=150)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Generador de Reportes",
            bg=COLORS["header"],
            fg=COLORS["text"],
            font=("Segoe UI", 25, "bold"),
        ).pack(anchor="w", padx=30, pady=(28, 6))

        tk.Label(
            header,
            text=(
                "Selecciona PDFs, el archivo de Contifico y genera el reporte "
                "de errores automaticamente."
            ),
            bg=COLORS["header"],
            fg=COLORS["text"],
            font=("Segoe UI", 13),
        ).pack(anchor="w", padx=30)

        body = tk.Frame(self, bg=COLORS["window"])
        body.pack(fill="both", expand=True, padx=24, pady=24)

        form_panel = self._panel(body)
        form_panel.pack(fill="x", pady=(0, 24))

        form = tk.Frame(form_panel, bg=COLORS["panel"])
        form.pack(fill="x", padx=26, pady=26)
        form.columnconfigure(1, weight=1)

        self.pdf_entry = self._field_row(
            form,
            row=0,
            label="PDFs seleccionados",
            placeholder="Ningun PDF seleccionado",
            button_text="Seleccionar PDFs",
            command=self._select_pdfs,
        )
        self.contifico_entry = self._field_row(
            form,
            row=1,
            label="Archivo Contifico",
            placeholder="Selecciona el Excel descargado de Contifico",
            button_text="Seleccionar Excel",
            command=self._select_contifico,
        )
        self.output_entry = self._field_row(
            form,
            row=2,
            label="Carpeta de salida",
            placeholder="Selecciona donde guardar los archivos",
            button_text="Guardar en",
            command=self._select_output_dir,
        )
        self.output_entry.configure(state="normal")
        self.output_entry.delete(0, "end")
        self.output_entry.insert(0, self.output_dir.get())
        self.output_entry.configure(state="readonly")

        stats = tk.Frame(form, bg=COLORS["panel_alt"], height=74)
        stats.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(26, 0))
        stats.grid_propagate(False)
        for col in range(4):
            stats.columnconfigure(col, weight=1)

        self._stat(stats, self.pdfs_count, 0)
        self._stat(stats, self.records_count, 1)
        self._stat(stats, self.errors_count, 2)
        self._stat(stats, self.unread_count, 3)

        progress_panel = self._panel(body)
        progress_panel.pack(fill="x", pady=(0, 22))
        progress_panel.columnconfigure(0, weight=1)

        progress_inner = tk.Frame(progress_panel, bg=COLORS["panel"])
        progress_inner.pack(fill="x", padx=26, pady=24)
        progress_inner.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(
            progress_inner,
            style="Dark.Horizontal.TProgressbar",
            mode="determinate",
            maximum=100,
            value=0,
        )
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 58), pady=(0, 16))

        tk.Label(
            progress_inner,
            textvariable=self.status_text,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 11),
        ).grid(row=1, column=0, sticky="w")

        self.generate_button = self._button(
            progress_inner,
            "Generar Reporte",
            self._start_processing,
            width=18,
        )
        self.generate_button.grid(row=0, column=1, rowspan=2, sticky="e")

        log_panel = self._panel(body)
        log_panel.pack(fill="both", expand=True)

        tk.Label(
            log_panel,
            text="Registro del proceso",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w", padx=26, pady=(26, 14))

        log_frame = tk.Frame(log_panel, bg=COLORS["log"])
        log_frame.pack(fill="both", expand=True, padx=26, pady=(0, 26))

        self.log_text = tk.Text(
            log_frame,
            bg=COLORS["log"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            borderwidth=0,
            font=("Consolas", 10),
            wrap="word",
            height=8,
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_text.configure(state="disabled")

    def _panel(self, parent):
        return tk.Frame(parent, bg=COLORS["panel"], highlightthickness=0)

    def _field_row(self, parent, row, label, placeholder, button_text, command):
        tk.Label(
            parent,
            text=label,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 12, "bold"),
        ).grid(row=row, column=0, sticky="w", padx=(0, 40), pady=10)

        entry = tk.Entry(
            parent,
            bg=COLORS["input"],
            fg=COLORS["muted"],
            readonlybackground=COLORS["input"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 11),
        )
        entry.grid(row=row, column=1, sticky="ew", pady=10)
        entry.insert(0, placeholder)
        entry.configure(state="readonly")

        button = self._button(parent, button_text, command)
        button.grid(row=row, column=2, sticky="ew", padx=(40, 0), pady=10)
        return entry

    def _button(self, parent, text, command, width=16):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            bg=COLORS["accent"],
            fg=COLORS["text"],
            activebackground=COLORS["accent_hover"],
            activeforeground=COLORS["text"],
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=12,
        )
        return button

    def _stat(self, parent, variable, column):
        tk.Label(
            parent,
            textvariable=variable,
            bg=COLORS["panel_alt"],
            fg=COLORS["text"],
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=column, sticky="nsew")

    def _set_entry(self, entry, value):
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, value)
        entry.configure(state="readonly")

    def _select_pdfs(self):
        files = filedialog.askopenfilenames(
            title="Seleccionar PDFs",
            filetypes=[("PDF", "*.pdf"), ("Todos los archivos", "*.*")],
        )
        if not files:
            return

        self.pdf_files = list(files)
        label = f"{len(files)} PDF(s) seleccionado(s)"
        if len(files) == 1:
            label = os.path.basename(files[0])
        self._set_entry(self.pdf_entry, label)
        self.pdfs_count.set(f"PDFs: {len(files)}")
        self._log(f"PDFs seleccionados: {len(files)}")

    def _select_contifico(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de Contifico",
            filetypes=[
                ("Excel", "*.xls *.xlsx"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not file_path:
            return

        self.contifico_file.set(file_path)
        self._set_entry(self.contifico_entry, os.path.basename(file_path))
        self._log(f"Archivo Contifico seleccionado: {file_path}")

    def _select_output_dir(self):
        directory = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if not directory:
            return

        self.output_dir.set(directory)
        self._set_entry(self.output_entry, directory)
        self._log(f"Carpeta de salida: {directory}")

    def _start_processing(self):
        if self.running:
            return

        if not self.pdf_files:
            messagebox.showwarning(APP_TITLE, "Selecciona al menos un PDF.")
            return

        if not self.contifico_file.get():
            messagebox.showwarning(APP_TITLE, "Selecciona el archivo de Contifico.")
            return

        output_dir = Path(self.output_dir.get())
        output_dir.mkdir(parents=True, exist_ok=True)

        self.running = True
        self.generate_button.configure(state="disabled", text="Procesando...")
        self.progress.configure(value=0)
        self.errors_count.set("Incidencias: 0")
        self.records_count.set("Registros: 0")
        self.unread_count.set("No leidas: 0")
        self.status_text.set("Iniciando proceso...")

        thread = threading.Thread(target=self._run_pipeline, daemon=True)
        thread.start()

    def _run_pipeline(self):
        try:
            output_dir = Path(self.output_dir.get())
            uphone_raw = output_dir / "uphone.xlsx"
            uphone_clean = output_dir / "uphone_limpio.xlsx"
            contifico_clean = output_dir / "contifico_limpio.xlsx"
            report = output_dir / "errores_completo.xlsx"

            self._emit("status", "Extrayendo tablas desde PDFs...", 15)
            pdf_result = generar_excel_desde_pdfs(
                self.pdf_files,
                str(uphone_raw),
                log_callback=lambda message: self._emit("log", message),
            )
            self._emit("stats", {"registros": pdf_result["registros"]})
            self._emit("stats", {"no_leidos": pdf_result["no_leidos"]})

            self._emit("status", "Limpiando archivo generado desde PDFs...", 40)
            uphone_result = limpiar_uphone(str(uphone_raw), str(uphone_clean))
            self._emit("stats", {"registros": uphone_result["registros"]})
            self._emit("log", f"UPHONE limpio generado: {uphone_clean}")

            self._emit("status", "Limpiando archivo de Contifico...", 62)
            contifico_result = limpiar_contifico(
                self.contifico_file.get(),
                str(contifico_clean),
            )
            self._emit(
                "log",
                f"Contifico limpio generado: {contifico_clean} "
                f"({contifico_result['registros']} registros)",
            )

            self._emit("status", "Comparando archivos limpios...", 84)
            report_result = generar_reporte_errores(
                str(uphone_clean),
                str(contifico_clean),
                str(report),
            )
            self._emit("stats", {"incidencias": report_result["incidencias"]})

            self._emit("status", "Proceso finalizado correctamente.", 100)
            self._emit("done", str(report))
        except Exception as exc:
            self._emit("error", str(exc))

    def _emit(self, event_type, payload, progress=None):
        self.events.put((event_type, payload, progress))

    def _process_events(self):
        try:
            while True:
                event_type, payload, progress = self.events.get_nowait()

                if progress is not None:
                    self.progress.configure(value=progress)

                if event_type == "log":
                    self._log(payload)
                elif event_type == "status":
                    self.status_text.set(payload)
                    self._log(payload)
                elif event_type == "stats":
                    if "registros" in payload:
                        self.records_count.set(f"Registros: {payload['registros']}")
                    if "incidencias" in payload:
                        self.errors_count.set(f"Incidencias: {payload['incidencias']}")
                    if "no_leidos" in payload:
                        self.unread_count.set(f"No leidas: {payload['no_leidos']}")
                elif event_type == "done":
                    self._finish_success(payload)
                elif event_type == "error":
                    self._finish_error(payload)
        except queue.Empty:
            pass

        self.after(120, self._process_events)

    def _finish_success(self, report_path):
        self.running = False
        self.generate_button.configure(state="normal", text="Generar Reporte")
        self._log(f"Reporte generado: {report_path}")
        if messagebox.askyesno(APP_TITLE, "Reporte generado correctamente. Deseas abrirlo?"):
            os.startfile(report_path)

    def _finish_error(self, error_message):
        self.running = False
        self.generate_button.configure(state="normal", text="Generar Reporte")
        self.status_text.set("El proceso se detuvo por un error.")
        self._log(f"ERROR: {error_message}")
        messagebox.showerror(APP_TITLE, error_message)

    def _log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")


if __name__ == "__main__":
    app = ReportApp()
    app.mainloop()
