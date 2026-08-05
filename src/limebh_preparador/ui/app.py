from __future__ import annotations

import ctypes
import os
import sys
import tkinter as tk
from pathlib import Path
from queue import Empty
from tkinter import filedialog, messagebox, ttk

from limebh_preparador import __version__
from limebh_preparador.application.naming import find_possible_duplicates
from limebh_preparador.core.paths import default_output_root
from limebh_preparador.ui.state import (
    DesktopConversionRequest,
    UiProfile,
    human_duration,
    human_file_size,
    recommendation_for,
)
from limebh_preparador.ui.worker import (
    ConversionWorker,
    WorkerFailed,
    WorkerFinished,
    WorkerProgress,
    WorkerStarted,
)

BACKGROUND = "#F3F7F5"
SURFACE = "#FFFFFF"
PRIMARY = "#146B5C"
PRIMARY_DARK = "#0E4F44"
ACCENT = "#D9EFE8"
TEXT = "#18332E"
MUTED = "#61736F"
BORDER = "#D5E1DD"
WARNING = "#8A5A13"


class PreparadorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.worker = ConversionWorker()
        self.source_path: Path | None = None
        self.last_output_dir: Path | None = None
        self._close_pending = False
        self._layout_mode: str | None = None
        self._header_mode: str | None = None
        self._file_mode: str | None = None
        self._scrollbar_visible = False

        self.profile_var = tk.StringVar(value=UiProfile.PLATFORM.value)
        self.output_root_var = tk.StringVar(value=str(default_output_root()))
        self.include_html_var = tk.BooleanVar(value=False)
        self.file_name_var = tk.StringVar(value="Nenhum arquivo selecionado")
        self.file_detail_var = tk.StringVar(
            value="Adicione um arquivo MBOX para começar. O original permanecerá intocado."
        )
        self.file_path_var = tk.StringVar(value="")
        self.format_var = tk.StringVar()
        self.recommendation_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Aguardando um arquivo")
        self.counter_var = tk.StringVar(value="0 mensagens processadas")
        self.summary_var = tk.StringVar(value="Ao final, o resumo da conversão será exibido aqui.")

        self._configure_window()
        self._configure_styles()
        self._build_layout()
        self._update_recommendation()
        self._set_busy(False)
        self.root.after(100, self._poll_worker_events)

    def _configure_window(self) -> None:
        self.root.title("Preparador de Dados para IA — LIMEBH")
        self.root.geometry("1060x820")
        self.root.minsize(680, 560)
        self.root.configure(background=BACKGROUND)
        self.root.option_add("*tearOff", False)
        self.root.protocol("WM_DELETE_WINDOW", self._request_close)
        self.root.bind("<Control-o>", lambda _event: self._choose_source())

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("App.TFrame", background=BACKGROUND)
        style.configure("CardInner.TFrame", background=SURFACE)
        style.configure(
            "Card.TFrame",
            background=SURFACE,
            bordercolor=BORDER,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Title.TLabel",
            background=BACKGROUND,
            foreground=TEXT,
            font=("Segoe UI Semibold", 22),
        )
        style.configure(
            "Subtitle.TLabel",
            background=BACKGROUND,
            foreground=MUTED,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Section.TLabel",
            background=SURFACE,
            foreground=TEXT,
            font=("Segoe UI Semibold", 12),
        )
        style.configure(
            "Card.TLabel",
            background=SURFACE,
            foreground=TEXT,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Muted.TLabel",
            background=SURFACE,
            foreground=MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "FileName.TLabel",
            background=SURFACE,
            foreground=TEXT,
            font=("Segoe UI Semibold", 11),
        )
        style.configure(
            "Privacy.TLabel",
            background=ACCENT,
            foreground=PRIMARY_DARK,
            font=("Segoe UI Semibold", 9),
            padding=(10, 7),
        )
        style.configure(
            "Option.TLabel",
            background="#EEF5F2",
            foreground=PRIMARY_DARK,
            font=("Segoe UI Semibold", 9),
            padding=(9, 5),
        )
        style.configure(
            "Card.TCheckbutton",
            background=SURFACE,
            foreground=TEXT,
            font=("Segoe UI", 9),
        )
        style.map("Card.TCheckbutton", background=[("active", SURFACE)])
        style.configure(
            "Primary.TButton",
            background=PRIMARY,
            foreground="#FFFFFF",
            bordercolor=PRIMARY,
            padding=(18, 10),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "Primary.TButton",
            background=[("active", PRIMARY_DARK), ("disabled", "#9CBAB3")],
            bordercolor=[("active", PRIMARY_DARK), ("disabled", "#9CBAB3")],
        )
        style.configure(
            "Secondary.TButton",
            background=SURFACE,
            foreground=PRIMARY_DARK,
            bordercolor=BORDER,
            padding=(12, 8),
            font=("Segoe UI Semibold", 9),
        )
        style.map("Secondary.TButton", background=[("active", ACCENT)])
        style.configure(
            "Danger.TButton",
            background="#FBE7E5",
            foreground="#8B3027",
            bordercolor="#E7B8B3",
            padding=(12, 8),
            font=("Segoe UI Semibold", 9),
        )
        style.configure(
            "Limebh.Horizontal.TProgressbar",
            background=PRIMARY,
            troughcolor="#DDE8E4",
            bordercolor="#DDE8E4",
            lightcolor=PRIMARY,
            darkcolor=PRIMARY,
            thickness=12,
        )

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        shell = ttk.Frame(self.root, style="App.TFrame")
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(0, weight=1)

        scroll_host = ttk.Frame(shell, style="App.TFrame")
        scroll_host.grid(row=0, column=0, sticky="nsew")
        scroll_host.columnconfigure(0, weight=1)
        scroll_host.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            scroll_host,
            background=BACKGROUND,
            borderwidth=0,
            highlightthickness=0,
            yscrollincrement=24,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = ttk.Scrollbar(
            scroll_host,
            orient="vertical",
            command=self.canvas.yview,
        )
        self.canvas.configure(yscrollcommand=self._on_scroll_position_changed)

        self.container = ttk.Frame(
            self.canvas,
            style="App.TFrame",
            padding=(28, 22, 28, 22),
        )
        self.container.columnconfigure(0, weight=1)
        self.content_window = self.canvas.create_window(
            (0, 0),
            window=self.container,
            anchor="nw",
        )
        self.container.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.root.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

        self._build_header(self.container)
        self._build_file_card(self.container)
        self._build_settings_card(self.container)
        self._build_progress_card(self.container)

        footer = ttk.Frame(shell, style="App.TFrame", padding=(28, 10, 28, 16))
        footer.grid(row=1, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        self.footer_label = ttk.Label(
            footer,
            text=f"LIMEBH • versão {__version__} • processamento local",
            style="Subtitle.TLabel",
        )
        self.footer_label.grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.start_button = ttk.Button(
            footer,
            text="Iniciar conversão",
            style="Primary.TButton",
            command=self._start_conversion,
        )
        self.start_button.grid(row=0, column=1, sticky="e")

    def _build_header(self, parent: ttk.Frame) -> None:
        self.header = ttk.Frame(parent, style="App.TFrame")
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self.header.columnconfigure(0, weight=1)
        self.title_label = ttk.Label(
            self.header,
            text="Preparador de Dados para IA",
            style="Title.TLabel",
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        self.subtitle_label = ttk.Label(
            self.header,
            text=("Converta e-mails em arquivos estruturados, particionados e prontos para IA."),
            style="Subtitle.TLabel",
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(3, 0))
        self.privacy_badge = ttk.Label(
            self.header,
            text="100% local • nenhum envio automático",
            style="Privacy.TLabel",
        )
        self.privacy_badge.grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="e",
            padx=(24, 0),
        )

    def _build_file_card(self, parent: ttk.Frame) -> None:
        self.file_card = ttk.Frame(parent, style="Card.TFrame", padding=18)
        self.file_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.file_card.columnconfigure(0, weight=1)
        self.file_title = ttk.Label(
            self.file_card,
            text="Arquivo de origem",
            style="Section.TLabel",
        )
        self.file_title.grid(row=0, column=0, sticky="w")
        self.file_actions = ttk.Frame(self.file_card, style="CardInner.TFrame")
        self.file_actions.grid(row=0, column=1, sticky="e")
        self.add_button = ttk.Button(
            self.file_actions,
            text="Adicionar MBOX",
            style="Secondary.TButton",
            command=self._choose_source,
        )
        self.add_button.grid(row=0, column=0, padx=(0, 8))
        self.remove_button = ttk.Button(
            self.file_actions,
            text="Remover",
            style="Secondary.TButton",
            command=self._remove_source,
        )
        self.remove_button.grid(row=0, column=1)

        self.file_separator = ttk.Separator(self.file_card)
        self.file_separator.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=12,
        )
        self.file_name_label = ttk.Label(
            self.file_card,
            textvariable=self.file_name_var,
            style="FileName.TLabel",
        )
        self.file_name_label.grid(row=2, column=0, columnspan=2, sticky="w")
        self.file_detail_label = ttk.Label(
            self.file_card,
            textvariable=self.file_detail_var,
            style="Muted.TLabel",
        )
        self.file_detail_label.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(3, 0),
        )
        self.file_path_label = ttk.Label(
            self.file_card,
            textvariable=self.file_path_var,
            style="Muted.TLabel",
        )
        self.file_path_label.grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(3, 0),
        )

    def _build_settings_card(self, parent: ttk.Frame) -> None:
        self.settings_card = ttk.Frame(parent, style="Card.TFrame", padding=18)
        self.settings_card.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.settings_card.columnconfigure(1, weight=1)
        self.settings_title = ttk.Label(
            self.settings_card,
            text="Configuração",
            style="Section.TLabel",
        )
        self.settings_title.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 14),
        )

        self.profile_label = ttk.Label(
            self.settings_card,
            text="Destino de uso",
            style="Card.TLabel",
        )
        self.profile_label.grid(row=1, column=0, sticky="w", padx=(0, 16))
        self.profile_combo = ttk.Combobox(
            self.settings_card,
            textvariable=self.profile_var,
            values=[profile.value for profile in UiProfile],
            state="readonly",
            width=30,
        )
        self.profile_combo.grid(row=1, column=1, sticky="w")
        self.profile_combo.bind("<<ComboboxSelected>>", self._profile_changed)

        self.format_label = ttk.Label(
            self.settings_card,
            text="Formato automático",
            style="Card.TLabel",
        )
        self.format_label.grid(row=2, column=0, sticky="nw", padx=(0, 16), pady=(12, 0))
        self.format_frame = ttk.Frame(self.settings_card, style="CardInner.TFrame")
        self.format_frame.columnconfigure(0, weight=1)
        self.format_frame.grid(
            row=2,
            column=1,
            columnspan=2,
            sticky="ew",
            pady=(12, 0),
        )
        self.format_value_label = ttk.Label(
            self.format_frame,
            textvariable=self.format_var,
            style="FileName.TLabel",
        )
        self.format_value_label.grid(row=0, column=0, sticky="w")
        self.recommendation_label = ttk.Label(
            self.format_frame,
            textvariable=self.recommendation_var,
            style="Muted.TLabel",
        )
        self.recommendation_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.destination_label = ttk.Label(
            self.settings_card,
            text="Destino local",
            style="Card.TLabel",
        )
        self.destination_label.grid(row=3, column=0, sticky="w", padx=(0, 16), pady=(14, 0))
        self.output_entry = ttk.Entry(
            self.settings_card,
            textvariable=self.output_root_var,
        )
        self.output_entry.grid(row=3, column=1, sticky="ew", pady=(14, 0))
        self.destination_button = ttk.Button(
            self.settings_card,
            text="Alterar",
            style="Secondary.TButton",
            command=self._choose_output_root,
        )
        self.destination_button.grid(row=3, column=2, sticky="e", padx=(10, 0), pady=(14, 0))

        self.options = ttk.Frame(self.settings_card, style="CardInner.TFrame")
        self.options.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(16, 0))
        self.clean_option = ttk.Label(
            self.options,
            text="✓ Limpeza Unicode",
            style="Option.TLabel",
        )
        self.clean_option.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.report_option = ttk.Label(
            self.options,
            text="✓ Relatório incluído",
            style="Option.TLabel",
        )
        self.report_option.grid(row=0, column=1, sticky="w", padx=(0, 10))
        self.html_check = ttk.Checkbutton(
            self.options,
            text="Preservar também o HTML",
            variable=self.include_html_var,
            style="Card.TCheckbutton",
        )
        self.html_check.grid(row=0, column=2, sticky="w")

        self.data_notice = ttk.Label(
            self.settings_card,
            text=(
                "A saída pode conter nomes, endereços de e-mail e outros dados pessoais. "
                "Compartilhe somente com pessoas e serviços autorizados."
            ),
            style="Privacy.TLabel",
        )
        self.data_notice.grid(
            row=5,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(16, 0),
        )

    def _build_progress_card(self, parent: ttk.Frame) -> None:
        self.progress_card = ttk.Frame(parent, style="Card.TFrame", padding=18)
        self.progress_card.grid(row=3, column=0, sticky="ew")
        self.progress_card.columnconfigure(0, weight=1)
        ttk.Label(
            self.progress_card,
            text="Progresso e resultado",
            style="Section.TLabel",
        ).grid(row=0, column=0, sticky="w")
        self.cancel_button = ttk.Button(
            self.progress_card,
            text="Cancelar",
            style="Danger.TButton",
            command=self._cancel_conversion,
        )
        self.cancel_button.grid(row=0, column=1, sticky="e")
        ttk.Label(
            self.progress_card,
            textvariable=self.status_var,
            style="FileName.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(14, 5))
        self.progress = ttk.Progressbar(
            self.progress_card,
            mode="indeterminate",
            style="Limebh.Horizontal.TProgressbar",
        )
        self.progress.grid(row=2, column=0, columnspan=2, sticky="ew")
        ttk.Label(
            self.progress_card,
            textvariable=self.counter_var,
            style="Muted.TLabel",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(5, 12))
        ttk.Separator(self.progress_card).grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="ew",
        )
        self.summary_label = ttk.Label(
            self.progress_card,
            textvariable=self.summary_var,
            style="Card.TLabel",
        )
        self.summary_label.grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(12, 0),
        )
        self.result_actions = ttk.Frame(
            self.progress_card,
            style="CardInner.TFrame",
        )
        self.result_actions.grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="e",
            pady=(12, 0),
        )
        self.open_output_button = ttk.Button(
            self.result_actions,
            text="Abrir arquivos prontos",
            style="Secondary.TButton",
            command=self._open_output,
        )
        self.open_output_button.grid(row=0, column=0, padx=(0, 8))
        self.open_report_button = ttk.Button(
            self.result_actions,
            text="Abrir relatório",
            style="Secondary.TButton",
            command=self._open_report,
        )
        self.open_report_button.grid(row=0, column=1)

    def _on_canvas_configure(self, event: tk.Event[tk.Canvas]) -> None:
        content_width = max(1, min(1240, event.width))
        content_x = max(0, (event.width - content_width) // 2)
        self.canvas.itemconfigure(self.content_window, width=content_width)
        self.canvas.coords(self.content_window, content_x, 0)
        self._apply_responsive_layout(content_width)

    def _on_content_configure(self, _event: tk.Event[ttk.Frame]) -> None:
        bounds = self.canvas.bbox("all")
        if bounds is not None:
            self.canvas.configure(scrollregion=bounds)

    def _on_scroll_position_changed(self, first: str, last: str) -> None:
        self.scrollbar.set(first, last)
        needs_scrollbar = float(first) > 0.0 or float(last) < 0.999
        if needs_scrollbar and not self._scrollbar_visible:
            self.scrollbar.grid(row=0, column=1, sticky="ns")
            self._scrollbar_visible = True
        elif not needs_scrollbar and self._scrollbar_visible:
            self.scrollbar.grid_remove()
            self._scrollbar_visible = False

    def _on_mousewheel(self, event: tk.Event[tk.Misc]) -> str | None:
        bounds = self.canvas.bbox("all")
        if bounds is None or bounds[3] <= self.canvas.winfo_height():
            return None
        steps = -int(event.delta / 120)
        if steps:
            self.canvas.yview_scroll(steps, "units")
            return "break"
        return None

    def _apply_responsive_layout(self, content_width: int) -> None:
        header_width = max(320, content_width - 56)
        card_width = max(280, header_width - 36)
        header_mode = "stacked" if content_width < 1040 else "wide"
        file_mode = "stacked" if content_width < 760 else "wide"
        layout_mode = "stacked" if content_width < 820 else "wide"

        if header_mode != self._header_mode:
            self.privacy_badge.grid_forget()
            if header_mode == "stacked":
                self.privacy_badge.grid(
                    row=2,
                    column=0,
                    sticky="w",
                    pady=(10, 0),
                )
            else:
                self.privacy_badge.grid(
                    row=0,
                    column=1,
                    rowspan=2,
                    sticky="e",
                    padx=(24, 0),
                )
            self._header_mode = header_mode

        if file_mode != self._file_mode:
            self.file_title.grid_forget()
            self.file_actions.grid_forget()
            self.file_separator.grid_forget()
            self.file_name_label.grid_forget()
            self.file_detail_label.grid_forget()
            self.file_path_label.grid_forget()
            if file_mode == "stacked":
                self.file_title.grid(row=0, column=0, columnspan=2, sticky="w")
                self.file_actions.grid(row=1, column=0, columnspan=2, sticky="w", pady=(12, 0))
                content_start = 3
                separator_row = 2
            else:
                self.file_title.grid(row=0, column=0, sticky="w")
                self.file_actions.grid(row=0, column=1, sticky="e")
                content_start = 2
                separator_row = 1
            self.file_separator.grid(
                row=separator_row,
                column=0,
                columnspan=2,
                sticky="ew",
                pady=12,
            )
            self.file_name_label.grid(
                row=content_start,
                column=0,
                columnspan=2,
                sticky="w",
            )
            self.file_detail_label.grid(
                row=content_start + 1,
                column=0,
                columnspan=2,
                sticky="w",
                pady=(3, 0),
            )
            self.file_path_label.grid(
                row=content_start + 2,
                column=0,
                columnspan=2,
                sticky="w",
                pady=(3, 0),
            )
            self._file_mode = file_mode

        if layout_mode != self._layout_mode:
            widgets = (
                self.profile_label,
                self.profile_combo,
                self.format_label,
                self.format_frame,
                self.destination_label,
                self.output_entry,
                self.destination_button,
                self.options,
                self.data_notice,
            )
            for widget in widgets:
                widget.grid_forget()
            if layout_mode == "stacked":
                self.profile_label.grid(row=1, column=0, columnspan=3, sticky="w")
                self.profile_combo.grid(
                    row=2,
                    column=0,
                    columnspan=3,
                    sticky="ew",
                    pady=(6, 0),
                )
                self.format_label.grid(
                    row=3,
                    column=0,
                    columnspan=3,
                    sticky="w",
                    pady=(14, 0),
                )
                self.format_frame.grid(
                    row=4,
                    column=0,
                    columnspan=3,
                    sticky="ew",
                    pady=(6, 0),
                )
                self.destination_label.grid(
                    row=5,
                    column=0,
                    columnspan=3,
                    sticky="w",
                    pady=(14, 0),
                )
                self.output_entry.grid(
                    row=6,
                    column=0,
                    columnspan=2,
                    sticky="ew",
                    pady=(6, 0),
                )
                self.destination_button.grid(
                    row=6,
                    column=2,
                    sticky="e",
                    padx=(10, 0),
                    pady=(6, 0),
                )
                options_row = 7
                notice_row = 8
                self.clean_option.grid(row=0, column=0, sticky="w")
                self.report_option.grid(row=1, column=0, sticky="w", pady=(7, 0))
                self.html_check.grid(row=2, column=0, sticky="w", pady=(7, 0))
            else:
                self.profile_label.grid(row=1, column=0, sticky="w", padx=(0, 16))
                self.profile_combo.grid(row=1, column=1, sticky="w")
                self.format_label.grid(
                    row=2,
                    column=0,
                    sticky="nw",
                    padx=(0, 16),
                    pady=(12, 0),
                )
                self.format_frame.grid(
                    row=2,
                    column=1,
                    columnspan=2,
                    sticky="ew",
                    pady=(12, 0),
                )
                self.destination_label.grid(
                    row=3,
                    column=0,
                    sticky="w",
                    padx=(0, 16),
                    pady=(14, 0),
                )
                self.output_entry.grid(row=3, column=1, sticky="ew", pady=(14, 0))
                self.destination_button.grid(
                    row=3,
                    column=2,
                    sticky="e",
                    padx=(10, 0),
                    pady=(14, 0),
                )
                options_row = 4
                notice_row = 5
                self.clean_option.grid(row=0, column=0, sticky="w", padx=(0, 10))
                self.report_option.grid(row=0, column=1, sticky="w", padx=(0, 10))
                self.html_check.grid(row=0, column=2, sticky="w")
            self.options.grid(
                row=options_row,
                column=0,
                columnspan=3,
                sticky="ew",
                pady=(16, 0),
            )
            self.data_notice.grid(
                row=notice_row,
                column=0,
                columnspan=3,
                sticky="ew",
                pady=(16, 0),
            )
            self._layout_mode = layout_mode

        title_wrap = header_width if header_mode == "stacked" else header_width - 350
        self.title_label.configure(wraplength=max(320, title_wrap))
        self.subtitle_label.configure(wraplength=max(320, title_wrap))
        self.privacy_badge.configure(wraplength=max(280, min(360, header_width)))
        self.file_path_label.configure(wraplength=card_width)
        recommendation_width = card_width if layout_mode == "stacked" else card_width - 180
        self.recommendation_label.configure(wraplength=max(260, recommendation_width))
        self.data_notice.configure(wraplength=max(260, card_width - 20))
        self.summary_label.configure(wraplength=card_width)

    def _profile_changed(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        self._update_recommendation()

    def _update_recommendation(self) -> None:
        profile = UiProfile(self.profile_var.get())
        recommendation = recommendation_for(profile)
        self.format_var.set(recommendation.format_name)
        self.recommendation_var.set(recommendation.explanation)

    def _choose_source(self) -> None:
        initial_dir = self.source_path.parent if self.source_path else Path.home()
        selected = filedialog.askopenfilename(
            parent=self.root,
            title="Selecionar arquivo MBOX",
            initialdir=initial_dir,
            filetypes=[("Arquivo MBOX", "*.mbox"), ("Todos os arquivos", "*.*")],
        )
        if not selected:
            return
        path = Path(selected)
        if path.suffix.lower() != ".mbox":
            messagebox.showwarning(
                "Formato não suportado",
                "Nesta etapa, selecione um arquivo com extensão .mbox.",
                parent=self.root,
            )
            return
        self.source_path = path
        self.file_name_var.set(path.name)
        self.file_detail_var.set(f"MBOX • {human_file_size(path.stat().st_size)}")
        self.file_path_var.set(str(path))
        self.status_var.set("Pronto para converter")
        self._set_busy(False)

    def _remove_source(self) -> None:
        self.source_path = None
        self.file_name_var.set("Nenhum arquivo selecionado")
        self.file_detail_var.set(
            "Adicione um arquivo MBOX para começar. O original permanecerá intocado."
        )
        self.file_path_var.set("")
        self.status_var.set("Aguardando um arquivo")
        self._set_busy(False)

    def _choose_output_root(self) -> None:
        selected = filedialog.askdirectory(
            parent=self.root,
            title="Selecionar pasta de destino",
            initialdir=self.output_root_var.get(),
            mustexist=False,
        )
        if selected:
            self.output_root_var.set(selected)

    def _start_conversion(self) -> None:
        if self.source_path is None:
            messagebox.showinfo(
                "Selecione um arquivo",
                "Adicione um arquivo MBOX antes de iniciar.",
                parent=self.root,
            )
            return
        destination = self.output_root_var.get().strip()
        if not destination:
            messagebox.showwarning(
                "Destino obrigatório",
                "Selecione uma pasta de destino para a conversão.",
                parent=self.root,
            )
            return
        request = DesktopConversionRequest(
            source=self.source_path,
            output_root=Path(destination).expanduser(),
            profile=UiProfile(self.profile_var.get()),
            include_html=self.include_html_var.get(),
        )
        try:
            request.validate()
            duplicates = find_possible_duplicates(request.output_root, request.source)
        except Exception as error:
            messagebox.showerror(
                "Não foi possível iniciar",
                str(error),
                parent=self.root,
            )
            return
        if duplicates:
            latest = duplicates[-1]
            proceed = messagebox.askyesno(
                "Possível conversão anterior",
                (
                    "Foi encontrada uma conversão anterior deste arquivo em:\n\n"
                    f"{latest}\n\nDeseja criar uma nova conversão mesmo assim?"
                ),
                parent=self.root,
            )
            if not proceed:
                return

        self.last_output_dir = None
        self.summary_var.set("A conversão está em andamento. Você pode cancelar com segurança.")
        self.status_var.set("Preparando o arquivo MBOX...")
        self.counter_var.set("0 mensagens processadas")
        self.progress.configure(mode="indeterminate", value=0)
        self.progress.start(12)
        self._set_busy(True)
        try:
            self.worker.start(request)
        except Exception as error:
            self.progress.stop()
            self._set_busy(False)
            messagebox.showerror(
                "Não foi possível iniciar",
                str(error),
                parent=self.root,
            )

    def _cancel_conversion(self) -> None:
        self.worker.cancel()
        self.cancel_button.state(["disabled"])
        self.status_var.set("Cancelamento solicitado; concluindo a unidade atual...")

    def _poll_worker_events(self) -> None:
        try:
            while True:
                event = self.worker.events.get_nowait()
                self._handle_worker_event(event)
        except Empty:
            pass
        if self.root.winfo_exists():
            self.root.after(100, self._poll_worker_events)

    def _handle_worker_event(
        self,
        event: WorkerStarted | WorkerProgress | WorkerFinished | WorkerFailed,
    ) -> None:
        if isinstance(event, WorkerStarted):
            self.last_output_dir = event.output_dir
            return
        if isinstance(event, WorkerProgress):
            progress = event.progress
            if progress.stage == "preparing":
                self.status_var.set("Preparando e indexando o arquivo MBOX...")
            elif progress.stage == "converting":
                self.status_var.set("Convertendo mensagens...")
                self.counter_var.set(
                    f"{progress.current:,} mensagens processadas".replace(",", ".")
                )
            elif progress.stage == "writing":
                self.status_var.set("Finalizando partes e relatório...")
            return
        if isinstance(event, WorkerFinished):
            self._conversion_finished(event)
            return
        self._conversion_failed(event)

    def _conversion_finished(self, event: WorkerFinished) -> None:
        self.progress.stop()
        self.progress.configure(mode="determinate", value=100, maximum=100)
        self.last_output_dir = event.output_dir
        report = event.report
        converted = int(report.get("converted_messages", 0))
        failed = int(report.get("failed_messages", 0))
        parts = report.get("parts")
        part_count = len(parts) if isinstance(parts, list) else 0
        duration = human_duration(float(report.get("duration_seconds", 0.0)))
        result = str(report.get("result", ""))
        if result == "cancelled":
            self.status_var.set("Conversão cancelada com segurança")
        elif failed:
            self.status_var.set("Conversão concluída com avisos")
        else:
            self.status_var.set("Conversão concluída")
        self.counter_var.set(f"{converted:,} mensagens processadas".replace(",", "."))
        summary = (
            f"{converted:,} mensagens • {part_count} parte(s) • {failed} falha(s) • {duration}"
        )
        self.summary_var.set(summary.replace(",", "."))
        self._set_busy(False)
        self.open_output_button.state(["!disabled"])
        self.open_report_button.state(["!disabled"])
        if self._close_pending:
            self.root.destroy()

    def _conversion_failed(self, event: WorkerFailed) -> None:
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)
        self.status_var.set("Não foi possível concluir a conversão")
        self.summary_var.set("Consulte a mensagem de erro e tente novamente.")
        self._set_busy(False)
        messagebox.showerror(
            "Erro na conversão",
            f"{event.error_type}: {event.message}",
            parent=self.root,
        )
        if self._close_pending:
            self.root.destroy()

    def _set_busy(self, busy: bool) -> None:
        if busy:
            self.add_button.state(["disabled"])
            self.remove_button.state(["disabled"])
            self.profile_combo.state(["disabled"])
            self.output_entry.state(["disabled"])
            self.destination_button.state(["disabled"])
            self.html_check.state(["disabled"])
            self.start_button.state(["disabled"])
            self.cancel_button.state(["!disabled"])
            self.open_output_button.state(["disabled"])
            self.open_report_button.state(["disabled"])
            return

        self.add_button.state(["!disabled"])
        if self.source_path is None:
            self.remove_button.state(["disabled"])
            self.start_button.state(["disabled"])
        else:
            self.remove_button.state(["!disabled"])
            self.start_button.state(["!disabled"])
        self.profile_combo.state(["!disabled", "readonly"])
        self.output_entry.state(["!disabled"])
        self.destination_button.state(["!disabled"])
        self.html_check.state(["!disabled"])
        self.cancel_button.state(["disabled"])
        if self.last_output_dir is None:
            self.open_output_button.state(["disabled"])
            self.open_report_button.state(["disabled"])

    def _open_output(self) -> None:
        if self.last_output_dir is not None:
            self._open_path(self.last_output_dir / "PRONTO_PARA_IA")

    def _open_report(self) -> None:
        if self.last_output_dir is not None:
            self._open_path(self.last_output_dir / "relatorio_conversao.json")

    def _open_path(self, path: Path) -> None:
        if not path.exists():
            messagebox.showwarning(
                "Arquivo não encontrado",
                f"O caminho não existe mais:\n{path}",
                parent=self.root,
            )
            return
        try:
            if sys.platform != "win32":
                raise OSError("A abertura automática está disponível no Windows.")
            os.startfile(path)  # type: ignore[attr-defined]
        except OSError as error:
            messagebox.showerror(
                "Não foi possível abrir",
                str(error),
                parent=self.root,
            )

    def _request_close(self) -> None:
        if not self.worker.is_active:
            self.root.destroy()
            return
        close = messagebox.askyesno(
            "Conversão em andamento",
            ("Deseja cancelar a conversão e fechar? As partes já concluídas permanecerão válidas."),
            parent=self.root,
        )
        if close:
            self._close_pending = True
            self._cancel_conversion()


def _enable_windows_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass


def main() -> int:
    _enable_windows_dpi_awareness()
    root = tk.Tk()
    PreparadorApp(root)
    root.mainloop()
    return 0
