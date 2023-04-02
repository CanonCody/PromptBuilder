import json
import random
import os
import tkinter as tk
from tkinter import ttk

# Initialize CATEGORIES_BY_TYPE as a dictionary with default empty lists
CATEGORIES_BY_TYPE = {}

def load_words(category):
    """Load words from JSON file for the given category."""
    try:
        with open(f'{category}.json', 'r') as file:
            words = json.load(file)
        return words
    except FileNotFoundError:
        print(f'Error: JSON file for category "{category}" not found.')
    except json.JSONDecodeError as e:
        print(f'Error: JSON file for category "{category}" contains invalid JSON. {e}')
    return []

def load_category_types():
    """Load category types from JSON file."""
    try:
        with open('category_types.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print('Error: Unable to load category types. JSON file not found.')
    except json.JSONDecodeError as e:
        print(f'Error: Unable to load category types. Invalid JSON. {e}')
    return {'uncategorized': [], 'nouns': []}

def build_prompt(template):
    """Build a prompt using the provided template and word categories."""
    all_categories = [cat for cat_list in CATEGORIES_BY_TYPE.values() for cat in cat_list]
    for category in all_categories:
        # Load words for the current category from JSON file
        words = load_words(category)
        # Replace each occurrence with a unique random word
        while f'[{category}]' in template:
            selected_word = random.choice(words) if words else ''
            template = template.replace(f'[{category}]', selected_word, 1)
    return template

def generate_prompt():
    """Generate a prompt using the user-defined template and display it."""
    # Get the template from the StringVar
    template = template_var.get()

    # Build and display the prompt
    prompt = build_prompt(template)  # Remove the second argument here
    prompt_label.config(text=prompt)

def copy_to_clipboard(event):
    """Copy the prompt text to the clipboard and provide a visual indication."""
    # Get the text from the prompt_label
    prompt_text = prompt_label.cget('text')
    # Clear the clipboard and set its content to the prompt text
    root.clipboard_clear()
    root.clipboard_append(prompt_text)
    
    # Get the current text color (foreground color) of the prompt_label
    original_fg = prompt_label.cget('fg')
    
    # Change the text color to blue to indicate copying
    prompt_label.config(fg='blue')
    
    # Restore the original text color after a short delay (e.g., 100 ms)
    prompt_label.after(100, lambda: prompt_label.config(fg=original_fg))

def clear_template_input():
    """Clear the content of the template input field."""
    template_var.set("")

def insert_category(category, entry):
    """Insert the selected category into the template input field."""
    current_template = template_var.get()
    # Append the new category directly without adding ', '
    updated_template = current_template + f'[{category}]'
    template_var.set(updated_template)
    # Set the cursor position to the end of the updated template
    entry.icursor(tk.END)

def insert_text(text, entry):
    """Insert the specified text into the template input field."""
    current_template = template_var.get()
    # Append the specified text to the existing template
    updated_template = current_template + text
    template_var.set(updated_template)
    # Set the cursor position to the end of the updated template
    entry.icursor(tk.END)

def rebuild_categories(refresh=True):
    """Rebuild the CATEGORIES list based on the JSON files present in the directory."""
    global CATEGORIES_BY_TYPE  # Declare CATEGORIES_BY_TYPE as global to modify it
    
    # Load category types from JSON file
    load_category_types()
    
    # List all files in the current directory
    files = os.listdir()
    
    # Filter for files with the .json extension
    json_files = [file for file in files if file.endswith('.json')]
    
    # Update the CATEGORIES_BY_TYPE dictionary based on available JSON files
    for category_type, categories in CATEGORIES_BY_TYPE.items():
        CATEGORIES_BY_TYPE[category_type] = [cat for cat in categories if f'{cat}.json' in json_files]
    
    if refresh:
        # Refresh the Template Builder tab to reflect the updated CATEGORIES_BY_TYPE dictionary
        refresh_template_builder()

def refresh_template_builder():
    """Refresh the Template Builder tab to reflect the updated CATEGORIES_BY_TYPE dictionary."""
    # Clear the current buttons from the tab_template_builder
    for widget in tab_template_builder.winfo_children():
        widget.destroy()

    # Recreate the input field for editing the template
    total_categories = sum(len(categories) for categories in CATEGORIES_BY_TYPE.values())  # Calculate total_categories here
    template_entry = tk.Entry(tab_template_builder, textvariable=template_var, width=60)
    template_entry.grid(row=0, column=0, columnspan=max(1, total_categories), padx=10, pady=10)

    # Create a frame for the text buttons
    text_buttons_frame = tk.Frame(tab_template_builder)
    text_buttons_frame.grid(row=1, column=0, columnspan=max(1, total_categories), padx=10, pady=5, sticky='w')

    # Create a row of buttons for specific characters and strings
    text_buttons = [", ", "of", "a", "and"]
    for col, text in enumerate(text_buttons, start=0):
        text_button = tk.Button(text_buttons_frame, text=text,
                                command=lambda t=text, entry=template_entry: insert_text(t, entry))
        text_button.grid(row=0, column=col, padx=5, pady=5)

    # Recreate the buttons for each category type in separate rows
    row = 2  # Start placing category buttons from row=2
    for category_type, categories in CATEGORIES_BY_TYPE.items():
        # Create a label to display the category type
        category_type_label = tk.Label(tab_template_builder, text=category_type.capitalize())
        category_type_label.grid(row=row, column=0, padx=5, pady=5, sticky='w')
        for col, category in enumerate(categories, start=1):
            category_button = tk.Button(tab_template_builder, text=category,
                                        command=lambda cat=category, entry=template_entry: insert_category(cat, entry))
            category_button.grid(row=row, column=col, padx=5, pady=5)
        row += 1  # Increment the row for the next category type

    # Recreate the "Clear" button to clear the content of the template input field
    clear_button = tk.Button(tab_template_builder, text="Clear", command=clear_template_input)
    clear_button.grid(row=0, column=max(1, total_categories), padx=10, pady=10)


def create_template_builder(tab_parent):
    """Create the Template Builder tab."""
    global tab_template_builder  # Declare tab_template_builder as a global variable
    # Create a new tab for the Template Builder
    tab_template_builder = ttk.Frame(tab_parent)
    tab_parent.add(tab_template_builder, text="Template Builder")

    # Recreate the input field for editing the template
    total_categories = sum(len(categories) for categories in CATEGORIES_BY_TYPE.values())
    template_entry = tk.Entry(tab_template_builder, textvariable=template_var, width=60)
    template_entry.grid(row=0, column=0, columnspan=max(1, total_categories), padx=10, pady=10)

    # Create a frame for the text buttons
    text_buttons_frame = tk.Frame(tab_template_builder)
    text_buttons_frame.grid(row=2, column=0, columnspan=max(1, total_categories), padx=10, pady=5, sticky='w')

    # Create a row of buttons for specific characters and strings
    text_buttons = [", ", "of", "a", "and"]
    for col, text in enumerate(text_buttons, start=0):
        text_button = tk.Button(text_buttons_frame, text=text,
                                command=lambda t=text, entry=template_entry: insert_text(t, entry))
        text_button.grid(row=0, column=col, padx=5, pady=5)

    # Create a "Clear" button to clear the content of the template input field
    clear_button = tk.Button(tab_template_builder, text="Clear", command=clear_template_input)
    clear_button.grid(row=0, column=max(1, total_categories), padx=10, pady=10)

    # Rebuild categories on tab creation (and refresh the Template Builder to organize categories into rows)
    rebuild_categories(refresh=True)

def create_settings_tab(tab_parent):
    """Create the Settings tab."""
    # Create a new tab for the Settings
    tab_settings = ttk.Frame(tab_parent)
    tab_parent.add(tab_settings, text="Settings")

    # Create a button to rebuild the CATEGORIES list
    rebuild_button = tk.Button(tab_settings, text="Rebuild Categories", command=rebuild_categories)
    rebuild_button.pack(padx=10, pady=10)

# Create the main application window
root = tk.Tk()
root.title("Prompt Generator")

# Create a StringVar to store the template
template_var = tk.StringVar()
template_var.set("[medium] of [noun], [adjective], [adjective], [adjective], [style]")

# Create a notebook (tab container)
tab_parent = ttk.Notebook(root)
tab_parent.pack(expand=1, fill='both')

# Create the main tab for generating prompts
tab_main = ttk.Frame(tab_parent)
tab_parent.add(tab_main, text="Generate")

# Create a label to display the generated prompt
prompt_label = tk.Label(tab_main, text="", wraplength=300, font=("Helvetica", 12))
prompt_label.pack(pady=10)

# Bind the left mouse button click event to the copy_to_clipboard function
prompt_label.bind('<Button-1>', copy_to_clipboard)

# Create a button to generate prompts
generate_button = tk.Button(tab_main, text="Generate Prompt", command=generate_prompt)
generate_button.pack(pady=10)

# Rebuild categories on startup (do not refresh the Template Builder since it's already created correctly)
CATEGORIES_BY_TYPE = load_category_types()
rebuild_categories(refresh=False)

# Create the Template Builder tab
create_template_builder(tab_parent)

# Create the Settings tab
create_settings_tab(tab_parent)

# Run the application
root.mainloop()