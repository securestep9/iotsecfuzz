from tkinter import *
from tkinter import messagebox
from tkinter.ttk import *
import core.ISFFramework as ISFFramework
from util.commons import async_raise
from util.exceptions import ModuleInterruptException
from threading import Thread
import sys


class StdoutRedirector(type(sys.__stdout__)):

    def __init__(self, text_widget):
        self.text_space = text_widget

    def write(self, string):
        sys.__stdout__.write(string)
        self.text_space.configure(state="normal")
        self.text_space.insert('end', string)
        self.text_space.see('end')
        self.text_space.configure(state="disabled")


tree = None
console = None

folder_img = None
module_img = None
run_img = None
stop_img = None

curr_module_input = dict()
main_window = None

module_window = None
work_window = None
curr_module = None
run_btn, stop_btn = None, None

module_thread = None
module_running = False

log = None


def build_tree(window):
    global folder_img, module_img
    if not folder_img:
        folder_img = PhotoImage(file="assets/images/folder.png")
    if not module_img:
        module_img = PhotoImage(file="assets/images/module.png")
    t = Treeview(window)
    t.heading("#0", text="Modules")
    nodes = dict()
    for name in ISFFramework.loaded_modules:
        node = ""
        path = list()
        full_path = name.split("/")
        for sub in full_path:
            path.append(sub)
            curr_path = "/".join(path)
            if curr_path in nodes:
                node = nodes[curr_path]
            else:
                img = folder_img if len(path) != len(
                    full_path) else module_img
                node = t.insert(node, "end", text=sub,
                                image=img)
                nodes[curr_path] = node
    t.bind("<Double-1>", on_module_selected)
    return t


def on_module_selected(event):
    global module_window, curr_module, run_btn, stop_btn, module_running
    if module_running:
        result = messagebox.askquestion("Warning",
                                        "There is a module running." +
                                        "\nDo you want to interrupt it and switch to another module?",
                                        icon='warning')
        if result != "yes":
            return
        else:
            stop_module()
    item = tree.selection()[0]
    path = [tree.item(item, "text")]
    parent = item
    while tree.parent(parent):
        parent = tree.parent(parent)
        path.insert(0, tree.item(parent, "text"))
    name = "/".join(path)
    if name in ISFFramework.loaded_modules:
        build_module_window(name)
        curr_module = ISFFramework.get_module_class(name)()


def build_module_window(module_name):
    global run_btn, stop_btn, curr_module_input, run_img, stop_img
    for widget in module_window.winfo_children():
        widget.destroy()
    cls = ISFFramework.loaded_modules[module_name]
    Label(module_window, text="Module info", foreground="green",
          font="Helvetica 10 bold").grid(row=0,
                                         column=0, columnspan=2,
                                         padx=10,
                                         pady=3)
    Label(module_window, text="Name:", font="Helvetica 10 bold").grid(row=1,
                                                                      column=0,
                                                                      padx=10,
                                                                      pady=3,
                                                                      sticky="w")
    Label(module_window, text=module_name).grid(row=1, column=1, padx=10,
                                                pady=3, sticky="w")
    Label(module_window, text="Version:", font="Helvetica 10 bold").grid(row=2,
                                                                         column=0,
                                                                         padx=10,
                                                                         pady=3,
                                                                         sticky="w")
    Label(module_window, text=cls.version).grid(row=2, column=1, padx=10,
                                                pady=3, sticky="w")
    Label(module_window, text="Author:", font="Helvetica 10 bold").grid(row=3,
                                                                        column=0,
                                                                        padx=10,
                                                                        pady=3,
                                                                        sticky="w")
    Label(module_window, text=cls.author).grid(row=3, column=1, padx=10, pady=3,
                                               sticky="w")
    Label(module_window, text="Description:", font="Helvetica 10 bold").grid(
        row=4, column=0, padx=10, pady=3, sticky="w")
    Label(module_window, text=cls.description).grid(row=4, column=1, padx=10,
                                                    pady=3, sticky="w")

    Separator(module_window).grid(row=5, column=0, columnspan=10, sticky="ew",
                                  padx=10, pady=3)

    Label(module_window, text="Input Parameters", foreground="green",
          font="Helvetica 10 bold").grid(row=6,
                                         column=0, columnspan=4,
                                         padx=10,
                                         pady=3)
    Separator(module_window, orient=VERTICAL).grid(row=6, column=4, rowspan=100,
                                                   sticky="nsw",
                                                   padx=10, pady=1)
    Label(module_window, text="Output Parameters", foreground="green",
          font="Helvetica 10 bold").grid(row=6,
                                         column=5, columnspan=2,
                                         padx=10,
                                         pady=3)
    Label(module_window, text="Name", font="Helvetica 10 bold").grid(
        row=7, column=0, padx=10, pady=3, sticky="w")
    Label(module_window, text="Value", font="Helvetica 10 bold").grid(
        row=7, column=1, padx=10, pady=3, sticky="w")
    Label(module_window, text="Required", font="Helvetica 10 bold").grid(
        row=7, column=2, padx=10, pady=3, sticky="w")
    Label(module_window, text="Description", font="Helvetica 10 bold").grid(
        row=7, column=3, padx=10, pady=3, sticky="w")

    Label(module_window, text="Name", font="Helvetica 10 bold").grid(
        row=7, column=5, padx=10, pady=3, sticky="w")
    Label(module_window, text="Value", font="Helvetica 10 bold").grid(
        row=7, column=6, padx=10, pady=3, sticky="w")
    i = j = 8
    curr_module_input = dict()
    for pname, pvalue in cls.in_params.items():
        Label(module_window, text=pname, font="Courier 10 bold").grid(
            row=i, column=0, padx=10, pady=3, sticky="w")
        comp = None
        if pvalue.value_type == bool:
            comp = Checkbutton(module_window)
            comp.state(())
            comp.invoke()
            comp.invoke()
            if pvalue.default_value:
                comp.invoke()

        elif pvalue.value_type == int:
            comp = Spinbox(module_window, from_=-99999999999, to=99999999999)
            if pvalue.default_value:
                comp.set(pvalue.default_value)
            else:
                comp.set(0)
        else:
            comp = Entry(module_window)
            if pvalue.default_value:
                comp.insert(END, pvalue.default_value)

        comp.grid(
            row=i, column=1, padx=10, pady=3, sticky="w")
        r = "Yes" if pvalue.required else "No"
        col = "green" if pvalue.required else "red"
        Label(module_window, text=r, foreground=col, font="Courier 10").grid(
            row=i, column=2, padx=10, pady=3, sticky="w")
        Label(module_window, text=pvalue.description).grid(
            row=i, column=3, padx=10, pady=3, sticky="w")
        i += 1
        curr_module_input[pname] = comp
    if hasattr(cls, "out_params"):
        for pname, pvalue in cls.out_params.items():
            Label(module_window, text=pname, font="Courier 10 bold").grid(
                row=j, column=5, padx=10, pady=3, sticky="w")
            Label(module_window, text="-", font="Courier 10 bold").grid(
                row=j, column=6, padx=10, pady=3, sticky="w")
            j += 11
    stop_btn = Button(module_window, text="Stop", command=stop_module,
                      image=stop_img, compound="left")
    stop_btn.grid(
        row=i + 1, column=0, padx=10, pady=3, sticky="w")
    stop_btn.config(state="disabled")
    run_btn = Button(module_window, text="Run", command=run_module,
                     image=run_img, compound="left")
    run_btn.grid(
        row=i + 1, column=1, padx=10, pady=3, sticky="w")
    module_window.update()


def run_module():
    global run_btn, stop_btn, module_thread
    in_par = dict()
    for k, v in curr_module_input.items():
        if isinstance(v, Checkbutton):
            in_par[k] = 'selected' in v.state()
        elif v.get():
            in_par[k] = v.get()
    run_btn.config(state="disabled")
    stop_btn.config(state="normal")
    module_thread = Thread(target=run_thread, args=[in_par])
    module_thread.start()


def show_error_msg(msg):
    messagebox.showerror("Error", msg)


def run_thread(in_params):
    global module_running
    module_running = True
    global run_btn, stop_btn
    try:
        out = curr_module.run(in_params)
        run_btn.config(state="normal")
        stop_btn.config(state="disabled")
        j = 8
        if out:
            for k, v in out.items():
                Label(module_window, text=k, font="Courier 10 bold").grid(
                    row=j, column=5, padx=10, pady=3, sticky="w")
                Label(module_window, text=v, font="Courier 10 bold").grid(
                    row=j, column=6, padx=10, pady=3, sticky="w")
                j += 1
    except ModuleInterruptException:
        run_btn.config(state="normal")
        stop_btn.config(state="disabled")
    except BaseException as e:
        print(e)
        ISFFramework.error_message(
            "Error encountered while running module: %s" % str(e))
        run_btn.config(state="normal")
        stop_btn.config(state="disabled")
    module_running = False


def stop_module():
    global run_btn, stop_btn, module_running
    if not module_running:
        return
    async_raise(module_thread, ModuleInterruptException)
    module_running = False
    run_btn.config(state="normal")
    stop_btn.config(state="disabled")


def build_gui():
    global main_window, work_window, run_img, stop_img
    root = Tk()
    root.title("IoTSecFuzz Framework")
    root.iconbitmap("assets/images/icon.ico")
    run_img = PhotoImage(file="assets/images/run.png")
    stop_img = PhotoImage(file="assets/images/stop.png")
    global tree, console, module_window
    main_window = Panedwindow(orient=HORIZONTAL)
    main_window.pack(fill=BOTH, expand=1)
    # tree_window = Panedwindow()
    work_window = Panedwindow(main_window, orient=VERTICAL)
    work_window.pack(fill=BOTH, expand=1)
    tree = build_tree(main_window)
    #  tree_window.add(tree)
    main_window.add(tree)
    main_window.add(work_window)
    module_window = Labelframe(work_window, text="Module controller", width=900,
                               height=400)
    module_window.grid(row=0)
    work_window.grid_rowconfigure(0, weight=1)
    console_window = Labelframe(work_window, text="Log", width=100,
                                height=100)
    console_window.grid(row=1)
    log = Text(console_window, width=120, height=8)
    redirector = StdoutRedirector(log)
    sys.stdout = redirector
    sys.stderr = redirector
    log.configure(state="disabled")
    log.grid(row=0, column=0, padx=10, pady=3, sticky="we")

    work_window.add(module_window)
    work_window.add(console_window)
    mainloop()
