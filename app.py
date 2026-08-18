import json
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from api import ApiError, SimulatorApi
from config import current_environment
from providers import annotate, label_for, statuses_for

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
NEW_ROW_COLOR = "#fff3cd"


def now_text():
    return datetime.now().strftime(TIME_FORMAT)


def to_iso(text):
    return datetime.strptime(text.strip(), TIME_FORMAT).astimezone().isoformat(timespec="seconds")


def from_iso(text):
    if not text:
        return ""
    try:
        return datetime.fromisoformat(text).astimezone().strftime(TIME_FORMAT)
    except ValueError:
        return text


def make_tree(parent, columns, height):
    tree = ttk.Treeview(parent, columns=[c[0] for c in columns], show="headings", height=height)
    for key, heading, width in columns:
        tree.heading(key, text=heading)
        tree.column(key, width=width, anchor="w")
    tree.pack(fill="both", expand=True, padx=4, pady=4)
    return tree


class SimulatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.environment = current_environment()
        self.title(f"Oreka Shipping Provider Simulator — {self.environment.base_url}")
        self.geometry("1120x720")

        self.shippings = []
        self.selected = None
        self.entries = []

        self._toolbar()
        self._shipping_tree()
        self._tabs()
        self._log()

    # ---------------------------------------------------------------- layout

    def _toolbar(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=10, pady=(10, 4))

        self.short_id = tk.StringVar()

        ttk.Label(bar, text="Mã đơn").pack(side="left")
        entry = ttk.Entry(bar, textvariable=self.short_id, width=20)
        entry.pack(side="left", padx=4)
        entry.bind("<Return>", lambda _e: self.load())
        ttk.Button(bar, text="Tải", command=self.load).pack(side="left", padx=4)
        entry.focus_set()

    def _shipping_tree(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=10, pady=4)
        self.shipping_tree = make_tree(
            frame,
            [
                ("provider", "Hãng", 140),
                ("trackingId", "Mã vận đơn", 200),
                ("isReturn", "Hoàn", 60),
                ("lastSync", "Quét gần nhất", 170),
                ("scenario", "Kịch bản", 90),
            ],
            3,
        )
        self.shipping_tree.bind("<<TreeviewSelect>>", self.on_select)

    def _tabs(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=4)
        self._scenario_tab(notebook)
        self._webhook_tab(notebook)

    def _scenario_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="  Kịch bản  ")

        panes = ttk.PanedWindow(tab, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=4, pady=4)

        left = ttk.LabelFrame(panes, text="Hiện có")
        self.activity_tree = make_tree(
            left,
            [
                ("status", "Mã", 55),
                ("label", "Trạng thái", 220),
                ("time", "Thời gian", 145),
                ("source", "Nguồn", 100),
            ],
            9,
        )
        panes.add(left, weight=1)

        right = ttk.LabelFrame(panes, text="Hãng trả về")
        self.scenario_tree = make_tree(
            right,
            [
                ("status", "Mã", 55),
                ("label", "Trạng thái", 220),
                ("time", "Thời gian", 145),
                ("flag", "", 100),
            ],
            9,
        )
        self.scenario_tree.tag_configure("new", background=NEW_ROW_COLOR)
        self.scenario_tree.bind("<Double-1>", lambda _e: self.remove_entry())
        panes.add(right, weight=1)

        bar = ttk.Frame(tab)
        bar.pack(fill="x", padx=4, pady=(0, 8))

        self.status = tk.StringVar()
        self.status_box = ttk.Combobox(bar, textvariable=self.status, width=38, state="readonly")
        self.status_box.pack(side="left")

        self.time = tk.StringVar(value=now_text())
        ttk.Entry(bar, textvariable=self.time, width=19).pack(side="left", padx=4)

        ttk.Button(bar, text="Thêm", command=self.add_entry).pack(side="left", padx=2)
        ttk.Button(bar, text="Xoá", command=self.remove_entry).pack(side="left", padx=2)
        ttk.Button(bar, text="Nạp lại", command=self.reset_entries).pack(side="left", padx=2)

        ttk.Button(bar, text="Xoá kịch bản", command=self.clear_scenario).pack(side="right", padx=2)
        ttk.Button(bar, text="Lưu kịch bản", command=self.save_scenario).pack(side="right", padx=2)

        legend = tk.Label(bar, text=" mốc mới ", background=NEW_ROW_COLOR)
        legend.pack(side="right", padx=12)

    def _webhook_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="  Webhook  ")

        bar = ttk.Frame(tab)
        bar.pack(fill="x", padx=8, pady=10)

        self.webhook_status = tk.StringVar()
        self.webhook_box = ttk.Combobox(bar, textvariable=self.webhook_status, width=38, state="readonly")
        self.webhook_box.pack(side="left")

        self.webhook_time = tk.StringVar(value=now_text())
        ttk.Entry(bar, textvariable=self.webhook_time, width=19).pack(side="left", padx=4)

        ttk.Button(bar, text="Gửi", command=self.send_webhook).pack(side="left", padx=2)

        self.webhook_tree = make_tree(
            tab,
            [
                ("time", "Lúc", 145),
                ("status", "Mã", 55),
                ("label", "Trạng thái", 240),
                ("result", "Kết quả", 260),
            ],
            10,
        )

    def _log(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=10, pady=(0, 10))
        self.log_text = tk.Text(frame, height=7, wrap="word")
        scrollbar = ttk.Scrollbar(frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ---------------------------------------------------------------- helpers

    def log(self, message):
        self.log_text.insert("end", f"{datetime.now().strftime('%H:%M:%S')}  {message}\n")
        self.log_text.see("end")

    def api(self):
        return SimulatorApi(self.environment.base_url, self.environment.secret)

    def run_async(self, work, on_success):
        def target():
            try:
                result = work()
            except ApiError as error:
                message = str(error)
            except Exception as error:  # noqa: BLE001
                message = f"{type(error).__name__}: {error}"
            else:
                self.after(0, lambda: on_success(result))
                return

            self.after(0, lambda: self.log(message))

        threading.Thread(target=target, daemon=True).start()

    def require(self):
        if not self.selected:
            messagebox.showwarning("Chưa chọn đơn vận", "Chọn một dòng ở bảng trên.")
            return None
        return self.selected

    def read_time(self, variable):
        try:
            return to_iso(variable.get())
        except ValueError:
            messagebox.showwarning("Sai định dạng", TIME_FORMAT)
            return None

    @staticmethod
    def code_of(option):
        return option.split(" — ")[0].strip() if option else ""

    # ---------------------------------------------------------------- actions

    def load(self):
        short_id = self.short_id.get().strip()
        if not short_id:
            return
        self.run_async(lambda: self.api().find_traces(short_id), self.on_loaded)

    def on_loaded(self, result):
        self.shippings = (result or {}).get("shippings") or []
        self.shipping_tree.delete(*self.shipping_tree.get_children())
        self.selected = None
        self.entries = []
        self.render_activities()
        self.render_scenario()

        if not self.shippings:
            self.log(f"{self.short_id.get().strip()}: không có đơn vận")
            return

        for index, shipping in enumerate(self.shippings):
            self.shipping_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    shipping.get("provider"),
                    shipping.get("trackingId") or "—",
                    "có" if shipping.get("isReturn") else "",
                    from_iso(shipping.get("lastTrackingSyncedAt")) or "—",
                    "có" if shipping.get("hasScenario") else "",
                ),
            )

        self.log(f"{self.short_id.get().strip()}: {len(self.shippings)} đơn vận")
        self.shipping_tree.selection_set("0")

    def on_select(self, _event=None):
        selection = self.shipping_tree.selection()
        if not selection:
            return

        self.selected = self.shippings[int(selection[0])]
        options = [f"{code} — {label}" for code, label in statuses_for(self.selected.get("provider"))]
        self.status_box["values"] = options
        self.webhook_box["values"] = options
        if options:
            self.status_box.current(0)
            self.webhook_box.current(0)
        elif not self.selected.get("simulatable"):
            self.log(f"{self.selected.get('provider')}: chưa hỗ trợ giả lập")

        self.render_activities()
        self.reset_entries()

    def render_activities(self):
        self.activity_tree.delete(*self.activity_tree.get_children())
        if not self.selected:
            return

        provider = self.selected.get("provider")
        for activity in self.selected.get("activities") or []:
            status = activity.get("status")
            self.activity_tree.insert(
                "",
                "end",
                values=(
                    status,
                    activity.get("statusText") or label_for(provider, status),
                    from_iso(activity.get("createdAt")),
                    activity.get("source") or "—",
                ),
            )

    def render_scenario(self):
        self.scenario_tree.delete(*self.scenario_tree.get_children())
        if not self.selected:
            return

        provider = self.selected.get("provider")
        known = {
            (activity.get("status"), from_iso(activity.get("createdAt")))
            for activity in self.selected.get("activities") or []
        }
        for entry in self.entries:
            status = entry["status"]
            time_text = from_iso(entry.get("occurredAt"))
            is_new = (status, time_text) not in known
            self.scenario_tree.insert(
                "",
                "end",
                values=(status, label_for(provider, status), time_text, annotate(provider, status)),
                tags=("new",) if is_new else (),
            )

    def reset_entries(self):
        if not self.selected:
            return
        self.entries = [dict(entry) for entry in self.selected.get("entries") or []]
        self.render_scenario()

    def add_entry(self):
        if not self.require():
            return
        code = self.code_of(self.status.get())
        occurred_at = self.read_time(self.time)
        if not code or not occurred_at:
            return

        self.entries.append({"status": code, "occurredAt": occurred_at})
        self.entries.sort(key=lambda entry: entry.get("occurredAt") or "")
        self.render_scenario()
        self.time.set(now_text())

    def remove_entry(self):
        selection = self.scenario_tree.selection()
        if not selection:
            return
        del self.entries[self.scenario_tree.index(selection[0])]
        self.render_scenario()

    def save_scenario(self):
        shipping = self.require()
        if not shipping:
            return
        if not self.entries:
            self.log("kịch bản rỗng, chưa thêm trạng thái nào")
            return

        entries = list(self.entries)
        self.run_async(
            lambda: self.api().save_scenario(shipping["id"], entries),
            lambda _r: (self.log(f"đã lưu {len(entries)} mốc"), self.load()),
        )

    def clear_scenario(self):
        shipping = self.require()
        if not shipping:
            return
        self.run_async(
            lambda: self.api().clear_scenario(shipping["id"]),
            lambda _r: (self.log("đã xoá kịch bản"), self.load()),
        )

    def send_webhook(self):
        shipping = self.require()
        if not shipping:
            return
        code = self.code_of(self.webhook_status.get())
        occurred_at = self.read_time(self.webhook_time)
        if not code or not occurred_at:
            return

        provider = shipping.get("provider")
        entries = [{"status": code, "occurredAt": occurred_at}]

        def work():
            api = self.api()
            request = api.build_webhook_request(shipping["id"], entries)
            return api.send_webhook(request)

        def done(response):
            self.webhook_tree.insert(
                "",
                0,
                values=(now_text(), code, label_for(provider, code), json.dumps(response, ensure_ascii=False)),
            )
            self.load()

        self.run_async(work, done)


if __name__ == "__main__":
    SimulatorApp().mainloop()
