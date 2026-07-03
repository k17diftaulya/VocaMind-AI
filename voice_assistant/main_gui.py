"""
main_gui.py
Prototype: Voice-Powered Smart Assistant
GUI Tkinter (tema biru modern) yang menggabungkan:
- Speech-to-Text (Google Speech API, campuran ID/EN)
- Deteksi konteks (rule-based: jadwal, deadline, tugas, ujian, catatan, organisasi)
- Smart Schedule Generator + deteksi bentrok
- Smart To-Do List Generator + prioritas otomatis
- Study Planner otomatis
- Recommender (urutan & waktu pengerjaan tugas)

Cara pakai:
    1. pastikan microphone terpasang & terhubung internet (pakai Google Speech API)
    2. jalankan: python main_gui.py
    3. klik tombol "Rekam & Proses", lalu bicara (Indonesia/Inggris boleh campur)
       Contoh ucapan:
       - "Tugas laporan praktikum deadline besok jam 5 sore, penting"
       - "Jadwal rapat organisasi hari senin jam 10 pagi durasi 2 jam"
       - "Ujian kalkulus tanggal 10 juli"
       - "Catatan beli buku baru"
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from modules import (
    speech_module,
    nlp_context,
    entity_extractor,
    schedule_manager,
    todo_manager,
    study_planner,
    recommender,
    data_store,
)

# =====================================================================
# PALET WARNA & FONT (tema biru modern)
# =====================================================================
COLOR = {
    "bg_app": "#EEF3FB",          # background utama, biru sangat muda
    "bg_card": "#FFFFFF",          # background card/panel
    "header_bg": "#1E3A8A",         # navy blue untuk header
    "header_text": "#FFFFFF",
    "primary": "#2563EB",            # biru utama (tombol aksi)
    "primary_hover": "#1D4ED8",
    "secondary": "#E0E9FB",            # biru muda untuk tombol sekunder
    "secondary_text": "#1E3A8A",
    "secondary_hover": "#C7D9F7",
    "border": "#D6E0F5",
    "text_main": "#1E293B",
    "text_muted": "#64748B",
    "success": "#059669",
    "success_bg": "#D1FAE5",
    "warning": "#D97706",
    "warning_bg": "#FEF3C7",
    "danger": "#DC2626",
    "danger_bg": "#FEE2E2",
    "info": "#2563EB",
    "info_bg": "#DBEAFE",
    "row_even": "#FFFFFF",
    "row_odd": "#F3F7FE",
    "tree_header_bg": "#1E3A8A",
    "tree_header_text": "#FFFFFF",
    "tree_select": "#BFDBFE",
}

FONT_FAMILY = "Segoe UI"


class VoiceAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VocaMind AI")
        self.root.geometry("960x680")
        self.root.minsize(820, 560)
        self.root.configure(bg=COLOR["bg_app"])

        self.stt = None  # lazy init supaya app tetap bisa buka walau mic belum siap

        self._setup_styles()
        self._build_ui()
        self._refresh_all_views()

    # ---------------------------------------------------------------
    # STYLE SETUP (tema biru modern untuk semua widget ttk)
    # ---------------------------------------------------------------
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")  # 'clam' paling fleksibel untuk kustomisasi warna

        # --- Frame & label dasar ---
        style.configure("TFrame", background=COLOR["bg_app"])
        style.configure("Card.TFrame", background=COLOR["bg_card"])
        style.configure("TLabel", background=COLOR["bg_app"],
                         foreground=COLOR["text_main"], font=(FONT_FAMILY, 10))
        style.configure("Card.TLabel", background=COLOR["bg_card"],
                         foreground=COLOR["text_main"], font=(FONT_FAMILY, 10))
        style.configure("Muted.TLabel", background=COLOR["bg_app"],
                         foreground=COLOR["text_muted"], font=(FONT_FAMILY, 9))

        # --- LabelFrame (panel dengan judul) ---
        style.configure("Card.TLabelframe", background=COLOR["bg_card"],
                         bordercolor=COLOR["border"], relief="solid", borderwidth=1)
        style.configure("Card.TLabelframe.Label", background=COLOR["bg_card"],
                         foreground=COLOR["header_bg"], font=(FONT_FAMILY, 10, "bold"))

        # --- Tombol utama (biru solid) ---
        style.configure("Primary.TButton", background=COLOR["primary"],
                         foreground="#FFFFFF", font=(FONT_FAMILY, 10, "bold"),
                         padding=(16, 10), borderwidth=0, focuscolor=COLOR["primary"])
        style.map("Primary.TButton",
                  background=[("active", COLOR["primary_hover"]), ("disabled", "#93B4F0")],
                  foreground=[("disabled", "#F0F4FF")])

        # --- Tombol sekunder (outline biru muda) ---
        style.configure("Secondary.TButton", background=COLOR["secondary"],
                         foreground=COLOR["secondary_text"], font=(FONT_FAMILY, 9, "bold"),
                         padding=(10, 6), borderwidth=0, focuscolor=COLOR["secondary"])
        style.map("Secondary.TButton",
                  background=[("active", COLOR["secondary_hover"])])

        # --- Tombol bahaya (hapus) ---
        style.configure("Danger.TButton", background=COLOR["danger_bg"],
                         foreground=COLOR["danger"], font=(FONT_FAMILY, 9, "bold"),
                         padding=(10, 6), borderwidth=0)
        style.map("Danger.TButton",
                  background=[("active", "#FCA5A5")])

        # --- Entry ---
        style.configure("TEntry", fieldbackground="#FFFFFF", foreground=COLOR["text_main"],
                         bordercolor=COLOR["border"], lightcolor=COLOR["border"],
                         darkcolor=COLOR["border"], padding=8, font=(FONT_FAMILY, 10))

        # --- Notebook (tab) ---
        style.configure("TNotebook", background=COLOR["bg_app"], borderwidth=0)
        style.configure("TNotebook.Tab", background=COLOR["secondary"],
                         foreground=COLOR["secondary_text"], font=(FONT_FAMILY, 10, "bold"),
                         padding=(16, 10), borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", COLOR["primary"])],
                  foreground=[("selected", "#FFFFFF")])

        # --- Treeview (tabel) ---
        style.configure("Treeview", background=COLOR["row_even"],
                         fieldbackground=COLOR["row_even"], foreground=COLOR["text_main"],
                         rowheight=28, font=(FONT_FAMILY, 10), borderwidth=0)
        style.configure("Treeview.Heading", background=COLOR["tree_header_bg"],
                         foreground=COLOR["tree_header_text"], font=(FONT_FAMILY, 10, "bold"),
                         padding=(8, 8), relief="flat")
        style.map("Treeview.Heading", background=[("active", COLOR["header_bg"])])
        style.map("Treeview", background=[("selected", COLOR["tree_select"])],
                  foreground=[("selected", COLOR["text_main"])])

        # --- Scrollbar (kalau dipakai nanti) ---
        style.configure("Vertical.TScrollbar", background=COLOR["secondary"],
                         troughcolor=COLOR["bg_app"], bordercolor=COLOR["bg_app"])

    # ---------------------------------------------------------------
    # UI SETUP
    # ---------------------------------------------------------------
    def _build_ui(self):
        # ============== HEADER ==============
        header = tk.Frame(self.root, bg=COLOR["header_bg"], height=72)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_box = tk.Frame(header, bg=COLOR["header_bg"])
        title_box.pack(side="left", padx=20, pady=10)
        tk.Label(title_box, text="Voice Powered Smart Assistant",
                 bg=COLOR["header_bg"], fg="#FFFFFF",
                 font=(FONT_FAMILY, 16, "bold")).pack(anchor="w")
        tk.Label(title_box, text="Jadwal • Tugas • Ujian • Catatan — otomatis dari suara kamu",
                 bg=COLOR["header_bg"], fg="#BFD3F8",
                 font=(FONT_FAMILY, 9)).pack(anchor="w")

        # Badge status di kanan header
        self.status_badge = tk.Label(
            header, text="● Status: siap", bg="#1B3175", fg="#8FE3B0",
            font=(FONT_FAMILY, 9, "bold"), padx=12, pady=6
        )
        self.status_badge.pack(side="right", padx=20)

        # ============== BODY (background biru muda) ==============
        body = ttk.Frame(self.root, style="TFrame", padding=(16, 14, 16, 16))
        body.pack(fill="both", expand=True)

        # ---- Baris aksi: tombol rekam + input manual dalam 1 card ----
        action_card = ttk.LabelFrame(body, text="Rekam Suara / Ketik Manual  ",
                                      style="Card.TLabelframe", padding=14)
        action_card.pack(fill="x", pady=(0, 12))

        record_row = ttk.Frame(action_card, style="Card.TFrame")
        record_row.pack(fill="x", pady=(0, 10))

        self.record_btn = ttk.Button(
            record_row, text="Rekam & Proses", style="Primary.TButton",
            command=self.on_record_clicked
        )
        self.record_btn.pack(side="left")

        ttk.Label(record_row,
                  text="Klik lalu bicara",
                  style="Muted.TLabel", background=COLOR["bg_card"]).pack(side="left", padx=14)

        manual_row = ttk.Frame(action_card, style="Card.TFrame")
        manual_row.pack(fill="x")

        self.manual_entry = ttk.Entry(manual_row, font=(FONT_FAMILY, 10))
        self.manual_entry.pack(side="left", fill="x", expand=True, ipady=4)
        ttk.Button(manual_row, text="Proses Teks", style="Secondary.TButton",
                   command=self.on_manual_process).pack(side="left", padx=(8, 0))

        # ---- Hasil pengenalan & deteksi konteks ----
        result_card = ttk.LabelFrame(body, text="Hasil Pengenalan & Deteksi Konteks  ",
                                      style="Card.TLabelframe", padding=12)
        result_card.pack(fill="x", pady=(0, 12))

        self.result_text = tk.Text(result_card, height=5, wrap="word", relief="flat",
                                    bg="#F7FAFE", fg=COLOR["text_main"],
                                    font=(FONT_FAMILY, 10), padx=10, pady=8,
                                    highlightthickness=1, highlightbackground=COLOR["border"])
        self.result_text.pack(fill="x")
        self.result_text.configure(state="disabled")

        # ---- Tabs ----
        self.tabs = ttk.Notebook(body)
        self.tabs.pack(fill="both", expand=True)

        self.tab_schedule = ttk.Frame(self.tabs, style="TFrame")
        self.tab_todo = ttk.Frame(self.tabs, style="TFrame")
        self.tab_study = ttk.Frame(self.tabs, style="TFrame")
        self.tab_recommend = ttk.Frame(self.tabs, style="TFrame")

        self.tabs.add(self.tab_schedule, text="Jadwal")
        self.tabs.add(self.tab_todo, text="To-Do List")
        self.tabs.add(self.tab_study, text="Study Plan")
        self.tabs.add(self.tab_recommend, text="Rekomendasi")

        self._build_schedule_tab()
        self._build_todo_tab()
        self._build_study_tab()
        self._build_recommend_tab()

    def _style_tree_stripes(self, tree):
        """Beri warna selang-seling (zebra stripes) pada baris Treeview."""
        tree.tag_configure("odd", background=COLOR["row_odd"])
        tree.tag_configure("even", background=COLOR["row_even"])

    def _build_schedule_tab(self):
        wrap = ttk.Frame(self.tab_schedule, style="TFrame", padding=(0, 12, 0, 0))
        wrap.pack(fill="both", expand=True)

        columns = ("title", "start", "end", "category")
        self.schedule_tree = ttk.Treeview(wrap, columns=columns, show="headings", height=12)
        for col, label, width in [
            ("title", "Judul", 320), ("start", "Mulai", 160),
            ("end", "Selesai", 160), ("category", "Kategori", 110)
        ]:
            self.schedule_tree.heading(col, text=label)
            self.schedule_tree.column(col, width=width)
        self.schedule_tree.pack(fill="both", expand=True, padx=2)
        self._style_tree_stripes(self.schedule_tree)

        btn_frame = ttk.Frame(wrap, style="TFrame")
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="Refresh", style="Secondary.TButton",
                   command=self._refresh_schedule_view).pack(side="left")
        ttk.Button(btn_frame, text="Hapus Terpilih", style="Danger.TButton",
                   command=self._delete_selected_schedule).pack(side="left", padx=8)

    def _build_todo_tab(self):
        wrap = ttk.Frame(self.tab_todo, style="TFrame", padding=(0, 12, 0, 0))
        wrap.pack(fill="both", expand=True)

        # ---- Filter: tampilkan/sembunyikan tugas yang sudah selesai ----
        filter_row = ttk.Frame(wrap, style="TFrame")
        filter_row.pack(fill="x", pady=(0, 8))

        self.show_done_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            filter_row, text="Tampilkan yang sudah selesai",
            variable=self.show_done_var, command=self._refresh_todo_view
        ).pack(side="left")

        ttk.Label(filter_row, text="Klik kotak ✓ di baris untuk menandai selesai/batal",
                  style="Muted.TLabel").pack(side="left", padx=14)

        # ---- Tabel to-do (kolom pertama = checkbox) ----
        columns = ("done", "title", "deadline", "priority", "category", "urgency")
        self.todo_tree = ttk.Treeview(wrap, columns=columns, show="headings", height=12)
        for col, label, width, anchor in [
            ("done", "✓", 40, "center"), ("title", "Judul", 260, "w"),
            ("deadline", "Deadline", 150, "w"), ("priority", "Skor Prioritas", 110, "center"),
            ("category", "Kategori", 100, "center"), ("urgency", "Urgensi", 90, "center")
        ]:
            self.todo_tree.heading(col, text=label)
            self.todo_tree.column(col, width=width, anchor=anchor)
        self.todo_tree.pack(fill="both", expand=True, padx=2)
        self._style_tree_stripes(self.todo_tree)

        # Baris yang sudah selesai ditampilkan pudar (abu-abu) sebagai penanda visual
        self.todo_tree.tag_configure("done", foreground=COLOR["text_muted"])

        # Klik di kolom checkbox ("#1") = toggle status selesai
        self.todo_tree.bind("<Button-1>", self._on_todo_tree_click)

        btn_frame = ttk.Frame(wrap, style="TFrame")
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="Refresh", style="Secondary.TButton",
                   command=self._refresh_todo_view).pack(side="left")
        ttk.Button(btn_frame, text="✔ Tandai/Batal Selesai", style="Secondary.TButton",
                   command=self._toggle_selected_done).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="🗑 Hapus Terpilih", style="Danger.TButton",
                   command=self._delete_selected_todo).pack(side="left")

    def _build_study_tab(self):
        wrap = ttk.Frame(self.tab_study, style="TFrame", padding=(0, 12, 0, 0))
        wrap.pack(fill="both", expand=True)

        columns = ("task", "session_date", "duration")
        self.study_tree = ttk.Treeview(wrap, columns=columns, show="headings", height=12)
        for col, label, width in [
            ("task", "Tugas Terkait", 340), ("session_date", "Tanggal Sesi", 180),
            ("duration", "Durasi (menit)", 130)
        ]:
            self.study_tree.heading(col, text=label)
            self.study_tree.column(col, width=width)
        self.study_tree.pack(fill="both", expand=True, padx=2)
        self._style_tree_stripes(self.study_tree)

        btn_frame = ttk.Frame(wrap, style="TFrame")
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="Generate Study Plan Otomatis", style="Primary.TButton",
                   command=self._generate_study_plan).pack(side="left")
        ttk.Button(btn_frame, text="Refresh", style="Secondary.TButton",
                   command=self._refresh_study_view).pack(side="left", padx=8)

    def _build_recommend_tab(self):
        wrap = ttk.Frame(self.tab_recommend, style="TFrame", padding=(0, 12, 0, 0))
        wrap.pack(fill="both", expand=True)

        top = ttk.Frame(wrap, style="TFrame")
        top.pack(fill="x", pady=(0, 10))
        ttk.Button(top, text="Refresh Rekomendasi", style="Primary.TButton",
                   command=self._refresh_recommend_view).pack(side="left")

        text_card = tk.Frame(wrap, bg=COLOR["bg_card"], highlightthickness=1,
                              highlightbackground=COLOR["border"])
        text_card.pack(fill="both", expand=True)

        self.recommend_text = tk.Text(text_card, wrap="word", relief="flat",
                                       bg=COLOR["bg_card"], fg=COLOR["text_main"],
                                       font=(FONT_FAMILY, 10), padx=14, pady=12)
        self.recommend_text.pack(fill="both", expand=True)
        self.recommend_text.configure(state="disabled")

    # ---------------------------------------------------------------
    # RECORDING & PROCESSING
    # ---------------------------------------------------------------
    def on_record_clicked(self):
        self.record_btn.configure(state="disabled")
        self._set_status("Mendengarkan... silakan bicara", "warning")
        threading.Thread(target=self._record_thread, daemon=True).start()

    def _record_thread(self):
        try:
            if self.stt is None:
                self.stt = speech_module.SpeechToText()
                self.stt.calibrate()

            text, lang = self.stt.listen_and_transcribe()

            if not text:
                self.root.after(0, lambda: self._set_status(
                    "Tidak terdengar jelas, coba lagi", "danger"))
                return

            self.root.after(0, lambda: self._process_text(text))

        except ConnectionError as e:
            self.root.after(0, lambda: self._set_status(f"Error koneksi: {e}", "danger"))
        except OSError as e:
            self.root.after(0, lambda: self._set_status(
                f"Microphone tidak ditemukan: {e}", "danger"))
        except Exception as e:
            self.root.after(0, lambda: self._set_status(f"Error: {e}", "danger"))
        finally:
            self.root.after(0, lambda: self.record_btn.configure(state="normal"))

    def on_manual_process(self):
        text = self.manual_entry.get().strip()
        if not text:
            messagebox.showinfo("Info", "Ketik dulu teks yang mau diproses.")
            return
        self._process_text(text)

    def _process_text(self, text):
        self._set_status("Memproses...", "info")

        category, matched_keywords = nlp_context.detect_context(text)
        deadline_dt, matched_date_text = entity_extractor.extract_datetime(text)
        urgency = entity_extractor.extract_urgency(text)
        duration_minutes = entity_extractor.extract_duration_minutes(text)
        title = entity_extractor.clean_title(text, matched_date_text, matched_keywords)

        summary_lines = [
            f"Teks dikenali: \"{text}\"",
            f"Kategori terdeteksi: {category} (keyword: {', '.join(matched_keywords) if matched_keywords else '-'})",
            f"Judul: {title}",
            f"Tanggal/waktu terdeteksi: {deadline_dt.strftime('%Y-%m-%d %H:%M') if deadline_dt else '-'}",
            f"Urgensi: {urgency} | Durasi terdeteksi: {duration_minutes if duration_minutes else '-'} menit",
        ]
        self._show_result_text("\n".join(summary_lines))

        # Routing berdasarkan kategori
        conflicts = []
        if category in ("jadwal", "organisasi") and deadline_dt:
            item, conflicts = schedule_manager.add_schedule(
                title=title, start_dt=deadline_dt,
                duration_minutes=duration_minutes, category=category,
                source_text=text
            )
        elif category in ("tugas", "deadline", "ujian"):
            todo_manager.add_todo(
                title=title, deadline_dt=deadline_dt, urgency=urgency,
                category=category, source_text=text
            )
        else:  # catatan / fallback
            data = data_store.load_data()
            data["notes"].append({
                "id": data_store.next_id(data["notes"]),
                "text": text,
                "created_at": data_store.now_iso(),
            })
            data_store.save_data(data)

        self._refresh_all_views()
        self._set_status("Selesai diproses", "success")

        if conflicts:
            conflict_desc = "\n".join(
                f"- {c['title']} ({c['start']} s/d {c['end']})" for c in conflicts
            )
            messagebox.showwarning(
                "Jadwal Bentrok!",
                f"Jadwal baru bentrok dengan:\n{conflict_desc}"
            )

    # ---------------------------------------------------------------
    # VIEW REFRESH HELPERS
    # ---------------------------------------------------------------
    def _refresh_all_views(self):
        self._refresh_schedule_view()
        self._refresh_todo_view()
        self._refresh_study_view()
        self._refresh_recommend_view()

    def _fill_tree(self, tree, rows):
        """Isi treeview dengan zebra stripes (baris genap/ganjil beda warna).

        `rows` berisi tuple (iid, values) atau (iid, values, extra_tags) kalau
        baris tersebut butuh tag tambahan (mis. "done" untuk tugas selesai).
        """
        for row in tree.get_children():
            tree.delete(row)
        for i, row in enumerate(rows):
            if len(row) == 3:
                iid, values, extra_tags = row
            else:
                iid, values = row
                extra_tags = ()
            parity_tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", iid=iid, values=values, tags=(parity_tag, *extra_tags))

    def _refresh_schedule_view(self):
        rows = [
            (str(s["id"]), (s["title"], s["start"], s["end"], s["category"]))
            for s in schedule_manager.get_all_schedules()
        ]
        self._fill_tree(self.schedule_tree, rows)

    def _refresh_todo_view(self):
        todo_manager.recompute_all_priorities()

        include_done = self.show_done_var.get() if hasattr(self, "show_done_var") else False
        todos = todo_manager.get_all_todos(include_done=include_done, sort_by_priority=False)
        # Tugas yang belum selesai tampil dulu (diurutkan dari skor tertinggi),
        # tugas yang sudah selesai ditaruh di bawah.
        todos = sorted(todos, key=lambda t: (t.get("done", False), -t.get("priority_score", 0)))

        rows = []
        for t in todos:
            is_done = t.get("done", False)
            checkbox = "☑" if is_done else "☐"
            values = (checkbox, t["title"], t["deadline"] or "-", t["priority_score"],
                       t["category"], t["urgency"])
            extra_tags = ("done",) if is_done else ()
            rows.append((str(t["id"]), values, extra_tags))

        self._fill_tree(self.todo_tree, rows)

    def _refresh_study_view(self):
        rows = [
            (str(s["id"]), (s["related_task_title"], s["session_date"], s["duration_minutes"]))
            for s in study_planner.get_all_study_sessions()
        ]
        self._fill_tree(self.study_tree, rows)

    def _refresh_recommend_view(self):
        ordered_todos = recommender.recommend_task_order()

        lines = ["═══ Urutan Prioritas Pengerjaan Tugas ═══\n"]
        if not ordered_todos:
            lines.append("(Belum ada tugas.)")
        for i, t in enumerate(ordered_todos, start=1):
            deadline_str = t["deadline"] or "tanpa deadline"
            lines.append(
                f"{i}. {t['title']}  |  skor: {t['priority_score']}  |  "
                f"deadline: {deadline_str}  |  kategori: {t['category']}"
            )

            recs = recommender.recommend_schedule_for_task(t)
            if recs:
                lines.append("   ➜ Saran waktu pengerjaan:")
                for r in recs:
                    lines.append(f"      • {r['start']} s/d {r['end']}")
            lines.append("")

        self._show_recommend_text("\n".join(lines))

    def _generate_study_plan(self):
        sessions = study_planner.generate_plan_for_all_upcoming()
        self._refresh_study_view()
        if sessions:
            messagebox.showinfo("Study Plan", f"{len(sessions)} sesi belajar baru dibuat.")
        else:
            messagebox.showinfo("Study Plan", "Tidak ada tugas/ujian baru yang perlu dijadwalkan.")

    # ---------------------------------------------------------------
    # DELETE / MARK DONE HANDLERS
    # ---------------------------------------------------------------
    def _delete_selected_schedule(self):
        sel = self.schedule_tree.selection()
        for iid in sel:
            schedule_manager.delete_schedule(int(iid))
        self._refresh_schedule_view()

    def _delete_selected_todo(self):
        sel = self.todo_tree.selection()
        for iid in sel:
            todo_manager.delete_todo(int(iid))
        self._refresh_todo_view()
        self._refresh_recommend_view()

    def _toggle_selected_done(self):
        """Tombol 'Tandai/Batal Selesai': balik status semua baris yang dipilih."""
        sel = self.todo_tree.selection()
        for iid in sel:
            todo_manager.toggle_done(int(iid))
        self._refresh_todo_view()
        self._refresh_recommend_view()

    def _on_todo_tree_click(self, event):
        """Klik langsung di kolom checkbox ('✓') = toggle selesai/belum untuk baris itu."""
        region = self.todo_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.todo_tree.identify_column(event.x)
        row_iid = self.todo_tree.identify_row(event.y)
        if not row_iid or col != "#1":  # "#1" = kolom pertama, yaitu "done"
            return
        todo_manager.toggle_done(int(row_iid))
        self._refresh_todo_view()
        self._refresh_recommend_view()

    # ---------------------------------------------------------------
    # SMALL UI HELPERS
    # ---------------------------------------------------------------
    def _set_status(self, text, kind="info"):
        """kind: 'success' | 'warning' | 'danger' | 'info'"""
        palette = {
            "success": ("#14532D", "#8FE3B0"),
            "warning": ("#78350F", "#FCD34D"),
            "danger": ("#7F1D1D", "#FCA5A5"),
            "info": ("#1E3A8A", "#93C5FD"),
        }
        _, fg = palette.get(kind, palette["info"])
        self.status_badge.configure(text=f"●  Status: {text}", fg=fg)

    def _show_result_text(self, text):
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", text)
        self.result_text.configure(state="disabled")

    def _show_recommend_text(self, text):
        self.recommend_text.configure(state="normal")
        self.recommend_text.delete("1.0", tk.END)
        self.recommend_text.insert("1.0", text)
        self.recommend_text.configure(state="disabled")


def main():
    root = tk.Tk()
    app = VoiceAssistantApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
