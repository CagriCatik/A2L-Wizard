import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pandas as pd

def hex_to_int(hex_str):
    """Convert a hexadecimal string (e.g., '0x400000FC') to an integer."""
    try:
        return int(hex_str.strip(), 16)
    except Exception as e:
        print(f"Conversion error for {hex_str}: {e}")
        return None

def load_data(file_path):
    """
    Load the Excel file and build a dictionary mapping parameter names to their details.
    Only rows with Type 'Parameter' are processed.
    """
    df = pd.read_excel(file_path)
    df['Address_Int'] = df['Address'].apply(hex_to_int)
    parameters = df[df['Type'] == 'Parameter']
    
    param_dict = {}
    for _, row in parameters.iterrows():
        param_dict[row['Name']] = {
            "Comment": row["Comment"],
            "Address": row["Address"],
            "Address_Int": row["Address_Int"],
            "Data_Type": row["Data Type"],
            "Phys_Unit": row["Phys. Unit"],
            "Standard_Min": row["Standard Min."],
            "Standard_Max": row["Standard Max."],
            "Format": row["Format"]
        }
    return param_dict

def search_parameters(param_dict, query):
    """
    Search for parameters where the query is found in the parameter name or comment.
    The search is case-insensitive.
    """
    results = {}
    query_lower = query.lower()
    for name, details in param_dict.items():
        if query_lower in name.lower() or query_lower in details.get("Comment", "").lower():
            results[name] = details
    return results

class A2LSearchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("A2L Parameter Search")
        self.geometry("1200x600")
        self.param_dict = {}
        self.create_menu()
        self.create_widgets()
    
    def create_menu(self):
        menubar = tk.Menu(self)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Excel File", command=self.load_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.config(menu=menubar)
    
    def create_widgets(self):
        # Top frame for file load and search query
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        self.file_label = ttk.Label(top_frame, text="No file loaded")
        self.file_label.pack(side=tk.LEFT, padx=(0,10))
        
        load_button = ttk.Button(top_frame, text="Load Excel File", command=self.load_file)
        load_button.pack(side=tk.LEFT, padx=(0,10))
        
        search_label = ttk.Label(top_frame, text="Search Query:")
        search_label.pack(side=tk.LEFT, padx=(20,5))
        
        self.search_entry = ttk.Entry(top_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=(0,10))
        
        search_button = ttk.Button(top_frame, text="Search", command=self.search)
        search_button.pack(side=tk.LEFT, padx=(0,10))
        
        clear_button = ttk.Button(top_frame, text="Clear", command=self.clear_search)
        clear_button.pack(side=tk.LEFT)
        
        # Frame for Treeview (search results)
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        
        # Define Treeview columns
        # columns = ("Name", "Comment", "Address", "Address_Int", "Data_Type", "Phys_Unit", "Standard_Min", "Standard_Max", "Format")
        columns = ("Name", "Comment", "Data_Type", "Phys_Unit", "Standard_Min", "Standard_Max", "Format")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            # Set width (adjust as necessary)
            if col == "Comment":
                self.tree.column(col, width=300)
            elif col == "Name":
                self.tree.column(col, width=200)
            else:
                self.tree.column(col, width=100)
        
        # Add vertical scrollbar to Treeview
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.LEFT, fill=tk.Y)
        
        # Status bar at the bottom
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="Select A2L Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.param_dict = load_data(file_path)
                self.file_label.config(text=file_path)
                self.status_var.set(f"Loaded {len(self.param_dict)} parameters.")
                messagebox.showinfo("Success", f"Loaded {len(self.param_dict)} parameters.")
                self.clear_tree()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{e}")
    
    def search(self):
        query = self.search_entry.get().strip()
        if not self.param_dict:
            messagebox.showwarning("Warning", "Please load an Excel file first.")
            return
        if not query:
            messagebox.showwarning("Warning", "Enter a search query.")
            return

        results = search_parameters(self.param_dict, query)
        self.clear_tree()
        if results:
            self.status_var.set(f"Found {len(results)} result(s).")
            for name, details in results.items():
                self.tree.insert("", "end", values=(
                    name,
                    details.get("Comment", ""),
                    #details.get("Address", ""),
                    #details.get("Address_Int", ""),
                    #details.get("Data_Type", ""),
                    details.get("Phys_Unit", ""),
                    details.get("Standard_Min", ""),
                    details.get("Standard_Max", ""),
                    details.get("Format", "")
                ))
        else:
            self.status_var.set("No results found for your query.")
            messagebox.showinfo("Search", "No results found for your query.")
    
    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.clear_tree()
        self.status_var.set("Ready")
    
    def clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def show_about(self):
        messagebox.showinfo("About", "This is a fucking awesome A2L Parameter Search GUI\n You dont need any more info or help 😈")

if __name__ == "__main__":
    app = A2LSearchApp()
    app.mainloop()