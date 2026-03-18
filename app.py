"""Competition manager with Tkinter GUI.

Features:
- Manage individuals and teams
- Register events and calculate points
- One-event-only validation and 5-results limit
- Leaderboard and CSV persistence
"""

import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os

class CompetitionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Competition Manager")
        # lock window size to approximate iPad dimensions (portrait)
        self.geometry("768x1024")
        self.minsize(768, 1024)
        self.maxsize(768, 1024)

        # data
        # individuals: name -> {'one_event':bool, 'events': set(), 'points': int}
        self.individuals = {}
        # teams: team_name -> {'members': [names], 'one_event':bool, 'events': set(), 'points': int}
        self.teams = {}

        self.max_individuals = 20
        self.max_teams = 4
        self.max_team_members = 5

        self.events = []
        self.max_events = 5

        self.points_suggestion = [5, 4, 3, 2, 1]
        self.event_results = {}
        self.data_dir = os.path.dirname(os.path.abspath(__file__))

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------------------------------------------
    # widget construction
    # ------------------------------------------------------------------
    def create_widgets(self):
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabelFrame', background='#f0f0f0')
        style.configure('TNotebook', background='#f0f0f0')
        style.configure('TNotebook.Tab', background='#c0c0c0', padding=[10, 5])
        style.map('TNotebook.Tab', background=[('selected', '#ffffff')])
        style.configure('Colored.TButton', background='#008080', foreground='white')
        style.map('Colored.TButton', background=[('active', '#005050')])

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        sep = ttk.Separator(self, orient='horizontal')
        sep.pack(fill='x', side='bottom')

        self.box = ttk.Frame(self, width=100, height=100, relief='solid', borderwidth=2, style='TFrame')
        self.box.pack(side='bottom', pady=10)
        self.box.pack_propagate(False)

        self._box_color_state = 0
        self._animate_box()

        self.participants_frame = ttk.Frame(notebook)
        self.events_frame = ttk.Frame(notebook)
        self.scoring_frame = ttk.Frame(notebook)
        self.leaderboard_frame = ttk.Frame(notebook)

        notebook.add(self.participants_frame, text="Participants")
        notebook.add(self.events_frame, text="Events")
        notebook.add(self.scoring_frame, text="Scoring")
        notebook.add(self.leaderboard_frame, text="Leaderboard")

        self.build_participants_tab()
        self.build_events_tab()
        self.build_scoring_tab()
        self.build_leaderboard_tab()

    # ---------- participants tab ----------
    def build_participants_tab(self):
        frame = self.participants_frame
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=0)
        frame.columnconfigure(2, weight=0)
        frame.columnconfigure(3, weight=0)

        # individuals frame
        ind_frame = ttk.LabelFrame(frame, text="Individuals")
        ind_frame.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=5)
        ind_frame.columnconfigure(0, weight=1)
        ind_frame.columnconfigure(1, weight=0)
        ind_frame.columnconfigure(2, weight=0)
        ind_frame.columnconfigure(3, weight=0)

        ttk.Label(ind_frame, text="Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.ind_entry = ttk.Entry(ind_frame)
        self.ind_entry.grid(row=0, column=1, sticky="we", padx=5, pady=5)

        self.ind_one_event_var = tk.BooleanVar()
        add_ind_btn = ttk.Button(ind_frame, text="Add", command=self.add_individual, style='Colored.TButton')
        add_ind_btn.grid(row=0, column=2, padx=5, pady=5)

        cb = ttk.Checkbutton(ind_frame, text="One-event only", variable=self.ind_one_event_var)
        cb.grid(row=0, column=3, padx=5, pady=5)

        ind_box_frame = ttk.Frame(ind_frame)
        ind_box_frame.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)
        ind_box_frame.columnconfigure(0, weight=1)
        ind_box_frame.rowconfigure(0, weight=1)

        self.ind_listbox = tk.Listbox(ind_box_frame, height=6, background='#ffffff', selectbackground='#3399ff')
        ind_scroll = ttk.Scrollbar(ind_box_frame, orient="vertical", command=self.ind_listbox.yview)
        self.ind_listbox['yscrollcommand'] = ind_scroll.set
        self.ind_listbox.grid(row=0, column=0, sticky="nsew")
        ind_scroll.grid(row=0, column=1, sticky="ns")

        self.ind_count_label = ttk.Label(ind_frame, text="Total individuals: 0")
        self.ind_count_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)

        remove_ind_btn = ttk.Button(ind_frame, text="Remove", command=self.remove_individual, style='Colored.TButton')
        remove_ind_btn.grid(row=2, column=1, padx=5, pady=5)

        # teams frame
        team_frame = ttk.LabelFrame(frame, text="Teams")
        team_frame.grid(row=4, column=0, columnspan=4, sticky="nsew", padx=10, pady=5)
        team_frame.columnconfigure(0, weight=1)
        for i in range(1, 6):
            team_frame.columnconfigure(i, weight=0)

        ttk.Label(team_frame, text="Team name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.team_var = tk.StringVar()
        self.team_entry = ttk.Entry(team_frame, textvariable=self.team_var)
        self.team_entry.grid(row=0, column=1, padx=5, pady=5)
        self.team_entry.bind("<KeyRelease>", lambda e: self.on_team_selected())

        self.team_one_event_var = tk.BooleanVar()

        ttk.Label(team_frame, text="Member:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.team_member_entry = ttk.Entry(team_frame)
        self.team_member_entry.grid(row=0, column=3, padx=5, pady=5)

        add_team_btn = ttk.Button(team_frame, text="Add", command=self.add_to_team, style='Colored.TButton')
        add_team_btn.grid(row=0, column=4, padx=5, pady=5)

        tb = ttk.Checkbutton(team_frame, text="One-event only", variable=self.team_one_event_var, command=self.toggle_team_one_event)
        tb.grid(row=0, column=5, padx=5, pady=5)

        self.team_lists_container = ttk.Frame(team_frame)
        self.team_lists_container.grid(row=1, column=0, columnspan=6, sticky="nsew", padx=5, pady=5)

        remove_team_btn = ttk.Button(team_frame, text="Remove", command=self.remove_team_member, style='Colored.TButton')
        remove_team_btn.grid(row=4, column=0, columnspan=6, pady=5)

        self.team_listboxes = {}
        self.team_count_labels = {}

        self.refresh_team_display()
        self.update_ind_count()
        self.update_team_counts()

    def refresh_team_display(self):
        for widget in self.team_lists_container.winfo_children():
            widget.destroy()

        self.team_listboxes = {}
        self.team_count_labels = {}

        for i, team in enumerate(self.teams.keys()):
            lbl = ttk.Label(self.team_lists_container, text=team, font=(None, 9, 'bold'))
            lbl.grid(row=0, column=i, padx=5, pady=3)

            lb = tk.Listbox(self.team_lists_container, height=4, background='#f9f9f9', selectbackground='#3399ff')
            lb.grid(row=1, column=i, padx=5)

            for member in self.teams[team]['members']:
                lb.insert(tk.END, member)

            self.team_listboxes[team] = lb

            count_lbl = ttk.Label(self.team_lists_container, text=f"{len(self.teams[team]['members'])} members")
            count_lbl.grid(row=2, column=i, padx=5)
            self.team_count_labels[team] = count_lbl

    # participant operations
    def add_individual(self):
        name = self.ind_entry.get().strip()
        if not name:
            return

        if len(self.individuals) >= self.max_individuals:
            messagebox.showwarning("Limit reached", "Cannot add more than 20 individuals.")
            return

        if name in self.individuals:
            messagebox.showwarning("Duplicate", "This individual is already registered.")
            return

        self.individuals[name] = {
            'one_event': bool(self.ind_one_event_var.get()),
            'events': set(),
            'points': 0,
            'display_in_individuals': True
        }

        self.ind_listbox.insert(tk.END, name)
        self.ind_entry.delete(0, tk.END)
        self.ind_one_event_var.set(False)
        self.update_eligible_list()
        self.update_ind_count()

    def add_to_team(self):
        team = self.team_var.get().strip()
        name = self.team_member_entry.get().strip()

        if not team:
            messagebox.showerror("No team", "Please enter a team name.")
            return

        if not name:
            return

        if team not in self.teams:
            if len(self.teams) >= self.max_teams:
                messagebox.showwarning("Limit reached", f"Cannot add more than {self.max_teams} teams.")
                return

            self.teams[team] = {
                'members': [],
                'one_event': bool(self.team_one_event_var.get()),
                'events': set(),
                'points': 0
            }
            self.refresh_team_display()

        members = self.teams[team]['members']

        if len(members) >= self.max_team_members:
            messagebox.showwarning("Limit reached", f"{team} already has 5 members.")
            return

        if name in members:
            messagebox.showwarning("Duplicate", "This member is already in the team.")
            return

        members.append(name)

        # نحفظ العضو داخليا فقط بدون ما يظهر بقائمة الافراد
        if name not in self.individuals:
            self.individuals[name] = {
                'one_event': False,
                'events': set(),
                'points': 0,
                'display_in_individuals': False
            }

        if self.team_one_event_var.get():
            self.teams[team]['one_event'] = True
            self.team_one_event_var.set(False)

        self.team_member_entry.delete(0, tk.END)
        self.refresh_team_display()
        self.update_eligible_list()
        self.update_team_counts()
        self.update_ind_count()

    def remove_individual(self):
        sel = self.ind_listbox.curselection()
        if not sel:
            return

        index = sel[0]
        name = self.ind_listbox.get(index)
        self.ind_listbox.delete(index)

        try:
            del self.individuals[name]
        except KeyError:
            pass

        for tname, tdata in self.teams.items():
            if name in tdata['members']:
                try:
                    tdata['members'].remove(name)
                except ValueError:
                    pass

        self.refresh_team_display()
        self.update_eligible_list()
        self.update_ind_count()
        self.update_team_counts()
        self.update_leaderboard()

    def remove_team_member(self):
        team = self.team_var.get().strip()
        lb = self.team_listboxes.get(team)
        if not lb:
            return

        sel = lb.curselection()
        if not sel:
            return

        index = sel[0]
        name = lb.get(index)
        lb.delete(index)

        try:
            self.teams[team]['members'].remove(name)
        except ValueError:
            pass

        self.refresh_team_display()
        self.update_eligible_list()
        self.update_team_counts()
        self.update_leaderboard()

    def on_team_selected(self):
        team = self.team_var.get().strip()
        if team in self.teams:
            self.team_one_event_var.set(bool(self.teams[team].get('one_event', False)))
        else:
            self.team_one_event_var.set(False)

    def toggle_team_one_event(self):
        team = self.team_var.get().strip()
        if not team:
            return

        if team in self.teams:
            self.teams[team]['one_event'] = bool(self.team_one_event_var.get())

    # ---------- events tab ----------
    def build_events_tab(self):
        frame = self.events_frame
        evt_frame = ttk.LabelFrame(frame, text="Events")
        evt_frame.pack(fill="both", expand=True, padx=10, pady=10)
        evt_frame.columnconfigure(1, weight=1)

        ttk.Label(evt_frame, text="Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.event_name_entry = ttk.Entry(evt_frame)
        self.event_name_entry.grid(row=0, column=1, sticky="we", padx=5, pady=5)

        ttk.Label(evt_frame, text="Type:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.event_type_var = tk.StringVar()
        self.event_type_var.set("Individual")
        ttk.OptionMenu(evt_frame, self.event_type_var, "Individual", "Individual", "Team").grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(evt_frame, text="Category:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.event_category_entry = ttk.Entry(evt_frame)
        self.event_category_entry.grid(row=2, column=1, sticky="we", padx=5, pady=5)

        add_evt_btn = ttk.Button(evt_frame, text="Add Event", command=self.add_event, style='Colored.TButton')
        add_evt_btn.grid(row=3, column=0, columnspan=2, pady=5)

        self.events_tree = ttk.Treeview(evt_frame, columns=("type", "category"), show="headings", height=6)
        self.events_tree.heading("type", text="Type")
        self.events_tree.heading("category", text="Category")
        self.events_tree.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        evt_frame.rowconfigure(4, weight=1)

    def add_event(self):
        name = self.event_name_entry.get().strip()
        etype = self.event_type_var.get()
        cat = self.event_category_entry.get().strip()

        if not name:
            return

        if len(self.events) >= self.max_events:
            messagebox.showwarning("Limit reached", "Cannot add more than 5 events.")
            return

        for evt in self.events:
            if evt['name'] == name:
                messagebox.showwarning("Duplicate", "An event with that name already exists.")
                return

        event = {'name': name, 'type': etype, 'category': cat}
        self.events.append(event)
        self.events_tree.insert('', tk.END, iid=name, values=(etype, cat))
        self.event_name_entry.delete(0, tk.END)
        self.event_category_entry.delete(0, tk.END)
        self.update_event_menu()

    # ---------- scoring tab ----------
    def build_scoring_tab(self):
        frame = self.scoring_frame
        sframe = ttk.LabelFrame(frame, text="Scoring")
        sframe.pack(fill="both", expand=True, padx=10, pady=10)
        sframe.columnconfigure(1, weight=1)

        ttk.Label(sframe, text="Select Event:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.scoring_event_var = tk.StringVar()
        self.scoring_event_menu = ttk.Combobox(sframe, textvariable=self.scoring_event_var, state="readonly")
        self.scoring_event_menu.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        self.scoring_event_var.trace_add('write', lambda *a: self.update_eligible_list())
        self.update_event_menu()

        sep = ttk.Separator(sframe, orient='horizontal')
        sep.grid(row=1, column=0, columnspan=3, sticky='we', pady=5)

        ttk.Label(sframe, text="Eligible Participants:").grid(row=2, column=2, sticky="w", padx=5)
        self.eligible_listbox = tk.Listbox(sframe, height=8)
        self.eligible_listbox.grid(row=3, column=2, rowspan=5, padx=5, pady=5, sticky="nsew")
        self.eligible_listbox.bind("<Double-Button-1>", self.on_eligible_double_click)
        sframe.columnconfigure(2, weight=1)

        ttk.Label(sframe, text="Rankings (comma separated names):").grid(row=2, column=0, columnspan=2, sticky="w", padx=5)
        self.rankings_entry = ttk.Entry(sframe, width=40)
        self.rankings_entry.grid(row=3, column=0, columnspan=2, padx=5)

        ttk.Label(sframe, text="Points per place:").grid(row=4, column=0, columnspan=2, sticky="w", padx=5)
        self.points_entry = ttk.Combobox(sframe, width=40)
        self.points_entry['values'] = ["5,4,3,2,1", "10,5,3,1", "3,2,1"]
        self.points_entry.set(",".join(str(p) for p in self.points_suggestion))
        self.points_entry.grid(row=5, column=0, columnspan=2, padx=5)

        self.score_actions_btn = ttk.Menubutton(sframe, text="Actions", style='Colored.TButton')
        self._score_menu = tk.Menu(self.score_actions_btn, tearoff=0)
        self._score_menu.add_command(label="Calculate points", command=self.calculate_points)
        self._score_menu.add_command(label="Clear fields", command=self.clear_scoring_fields)
        self.score_actions_btn['menu'] = self._score_menu
        self.score_actions_btn.grid(row=6, column=0, padx=5, pady=10, sticky="w")

        clear_btn = ttk.Button(sframe, text="Clear", command=self.clear_scoring_fields, style='Colored.TButton')
        clear_btn.grid(row=6, column=1, padx=5, pady=10, sticky="w")

        self.score_text = tk.Text(sframe, height=8, background='#fafafa', relief='groove')
        self.score_text.grid(row=7, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        sframe.rowconfigure(7, weight=1)

    def update_event_menu(self):
        names = [evt['name'] for evt in self.events]
        self.scoring_event_menu['values'] = names
        if names:
            self.scoring_event_var.set(names[0])
        else:
            self.scoring_event_var.set("")
        self.update_eligible_list()

    def update_ind_count(self):
        visible_count = sum(
            1 for meta in self.individuals.values()
            if meta.get('display_in_individuals', True)
        )
        if hasattr(self, 'ind_count_label'):
            self.ind_count_label.config(text=f"Total: {visible_count}")

    def update_team_counts(self):
        for tname, lbl in getattr(self, 'team_count_labels', {}).items():
            count = len(self.teams.get(tname, {}).get('members', []))
            lbl.config(text=f"{count} members")

    def update_eligible_list(self):
        if not hasattr(self, 'eligible_listbox'):
            return

        self.eligible_listbox.delete(0, tk.END)
        event_name = self.scoring_event_var.get()
        if not event_name:
            return

        evt = next((e for e in self.events if e['name'] == event_name), None)
        if not evt:
            return

        if evt.get('type') == 'Individual':
            for name, meta in self.individuals.items():
                if meta.get('display_in_individuals', True):
                    self.eligible_listbox.insert(tk.END, name)
        else:
            for team_name, meta in self.teams.items():
                members = meta.get('members', [])
                if members:
                    display = f"{team_name}: {', '.join(members)}"
                    if len(members) < self.max_team_members:
                        display += f" ({len(members)}/{self.max_team_members} members)"
                else:
                    display = f"{team_name} (no members)"
                self.eligible_listbox.insert(tk.END, display)

    def on_eligible_double_click(self, event):
        sel = self.eligible_listbox.curselection()
        if not sel:
            return

        name = self.eligible_listbox.get(sel[0])

        if ':' in name:
            select_name = name.split(':', 1)[0].strip()
        else:
            select_name = name

        if select_name in self.teams:
            members = self.teams[select_name].get('members', [])
            if len(members) < self.max_team_members:
                messagebox.showerror("Incomplete team", f"{select_name} must have {self.max_team_members} members before being ranked.")
                return

        current = [r.strip() for r in self.rankings_entry.get().split(",") if r.strip()]
        if select_name in current:
            return

        if current and self.rankings_entry.get().strip():
            new = self.rankings_entry.get().strip() + ", " + select_name
        else:
            new = select_name

        self.rankings_entry.delete(0, tk.END)
        self.rankings_entry.insert(0, new)

    def clear_scoring_fields(self):
        if hasattr(self, 'rankings_entry'):
            self.rankings_entry.delete(0, tk.END)
        if hasattr(self, 'points_entry'):
            self.points_entry.set(",".join(str(p) for p in self.points_suggestion))

    def calculate_points(self):
        event = self.scoring_event_var.get()
        if not event:
            messagebox.showwarning("No event", "Please select an event.")
            return

        rankings = [r.strip() for r in self.rankings_entry.get().split(",") if r.strip()]
        if not rankings:
            messagebox.showwarning("No rankings", "Enter comma-separated rankings.")
            return

        raw_points = [p.strip() for p in self.points_entry.get().split(",") if p.strip()]
        try:
            points = [int(p) for p in raw_points]
        except ValueError:
            messagebox.showerror("Invalid points", "Points must be integers separated by commas.")
            return

        for name in rankings:
            if name in self.individuals:
                meta = self.individuals[name]
                if event not in meta.get('events', set()) and len(meta.get('events', set())) >= 5:
                    messagebox.showerror("Limit exceeded", f"{name} already has results in 5 events.")
                    return

            if name in self.teams:
                members = self.teams[name].get('members', [])
                if len(members) < self.max_team_members:
                    messagebox.showerror("Incomplete team", f"{name} must have {self.max_team_members} members to compete.")
                    return

                tmeta = self.teams[name]
                if event not in tmeta.get('events', set()) and len(tmeta.get('events', set())) >= 5:
                    messagebox.showerror("Limit exceeded", f"{name} already has results in 5 events.")
                    return

        self.score_text.delete('1.0', tk.END)
        self.score_text.insert(tk.END, f"Results for {event}:\n")
        results = []
        lines = []

        for idx, name in enumerate(rankings):
            pts = points[idx] if idx < len(points) else 0
            results.append((name, pts))

            if name in self.individuals:
                self.individuals[name].setdefault('points', 0)
                self.individuals[name]['points'] += pts
                self.individuals[name].setdefault('events', set())
                self.individuals[name]['events'].add(event)

            if name in self.teams:
                self.teams[name].setdefault('points', 0)
                self.teams[name]['points'] += pts
                self.teams[name].setdefault('events', set())
                self.teams[name]['events'].add(event)

            lines.append(f"{idx+1}. {name}: {pts} points\n")

        def show_line(i=0):
            if i < len(lines):
                self.score_text.insert(tk.END, lines[i])
                self.score_text.after(300, show_line, i + 1)

        show_line()

        self.event_results[event] = results
        self.points_suggestion = points
        self.update_leaderboard()

    # persistence
    def save_all_csv(self, silent=False):
        try:
            outfile = os.path.join(self.data_dir, 'competition.csv')
            with open(outfile, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)

                w.writerow(['SECTION', 'field1', 'field2', 'field3', 'field4', 'field5'])
                w.writerow(['PARTICIPANTS', 'name', 'one_event', 'points', 'events', 'display_in_individuals'])
                for name, meta in self.individuals.items():
                    events = '|'.join(sorted(meta.get('events', []))) if meta.get('events') else ''
                    w.writerow([
                        'PARTICIPANT',
                        name,
                        int(meta.get('one_event', False)),
                        meta.get('points', 0),
                        events,
                        int(meta.get('display_in_individuals', True))
                    ])

                w.writerow([])
                w.writerow(['TEAMS', 'team', 'one_event', 'points', 'members', 'events'])
                for tname, meta in self.teams.items():
                    members = '|'.join(meta.get('members', []))
                    events = '|'.join(sorted(meta.get('events', []))) if meta.get('events') else ''
                    w.writerow(['TEAM', tname, int(meta.get('one_event', False)), meta.get('points', 0), members, events])

                w.writerow([])
                w.writerow(['EVENTS', 'name', 'type', 'category', '', ''])
                for e in self.events:
                    w.writerow(['EVENT', e.get('name', ''), e.get('type', ''), e.get('category', ''), '', ''])

                w.writerow([])
                w.writerow(['RESULTS', 'event', 'name', 'points', '', ''])
                for ename, res in self.event_results.items():
                    for nm, pts in res:
                        w.writerow(['RESULT', ename, nm, pts, '', ''])

            if not silent:
                messagebox.showinfo('Saved', f'All data saved to {outfile}')
        except Exception as e:
            if not silent:
                messagebox.showerror('Save error', str(e))
            else:
                print('Save error:', e)

    def _animate_box(self):
        colors = ['#ffc0cb', '#add8e6', '#90ee90', '#ffffe0']
        self._box_color_state = (self._box_color_state + 1) % len(colors)
        try:
            self.box.config(background=colors[self._box_color_state])
            pad = 10 if self._box_color_state % 2 == 0 else 20
            self.box.pack_configure(pady=pad)
        except Exception:
            pass
        self.after(500, self._animate_box)

    def on_close(self):
        try:
            self.save_all_csv(silent=True)
        except Exception:
            pass
        self.destroy()

    # ---------- leaderboard tab ----------
    def build_leaderboard_tab(self):
        frame = self.leaderboard_frame
        lframe = ttk.LabelFrame(frame, text="Leaderboard")
        lframe.pack(fill="both", expand=True, padx=10, pady=10)
        lframe.columnconfigure(0, weight=1)
        lframe.columnconfigure(1, weight=1)

        sub1 = ttk.LabelFrame(lframe, text="Individuals")
        sub1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.ind_lb = ttk.Treeview(sub1, columns=("name", "points", "events"), show="headings", height=10)
        self.ind_lb.heading("name", text="Name")
        self.ind_lb.heading("points", text="Points")
        self.ind_lb.heading("events", text="#Events")
        self.ind_lb.grid(row=0, column=0, sticky="nsew")
        ind_scroll = ttk.Scrollbar(sub1, orient="vertical", command=self.ind_lb.yview)
        self.ind_lb.configure(yscrollcommand=ind_scroll.set)
        ind_scroll.grid(row=0, column=1, sticky="ns")
        sub1.columnconfigure(0, weight=1)
        sub1.rowconfigure(0, weight=1)

        sub2 = ttk.LabelFrame(lframe, text="Teams")
        sub2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.team_lb = ttk.Treeview(sub2, columns=("name", "points", "events"), show="headings", height=10)
        self.team_lb.heading("name", text="Team")
        self.team_lb.heading("points", text="Points")
        self.team_lb.heading("events", text="#Events")
        self.team_lb.grid(row=0, column=0, sticky="nsew")
        team_scroll = ttk.Scrollbar(sub2, orient="vertical", command=self.team_lb.yview)
        self.team_lb.configure(yscrollcommand=team_scroll.set)
        team_scroll.grid(row=0, column=1, sticky="ns")
        sub2.columnconfigure(0, weight=1)
        sub2.rowconfigure(0, weight=1)

        self.update_leaderboard()

    def update_leaderboard(self):
        if not hasattr(self, 'ind_lb'):
            return

        for i in self.ind_lb.get_children():
            self.ind_lb.delete(i)

        ind_sorted = sorted(
            self.individuals.items(),
            key=lambda kv: kv[1].get('points', 0),
            reverse=True
        )
        for name, meta in ind_sorted:
            evcount = len(meta.get('events', [])) if meta.get('events') else 0
            self.ind_lb.insert('', tk.END, values=(name, meta.get('points', 0), evcount))

        for i in self.team_lb.get_children():
            self.team_lb.delete(i)

        team_sorted = sorted(
            self.teams.items(),
            key=lambda kv: kv[1].get('points', 0),
            reverse=True
        )
        for name, meta in team_sorted:
            evcount = len(meta.get('events', [])) if meta.get('events') else 0
            self.team_lb.insert('', tk.END, values=(name, meta.get('points', 0), evcount))


if __name__ == "__main__":
    app = CompetitionApp()
    app.mainloop()