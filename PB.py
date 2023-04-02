import json
import random
import os
import tkinter as tk
from tkinter import ttk

# Initialize CATEGORIES as an empty list
CATEGORIES = []

def load_words(category):
    """Load words from JSON file for the given category."""
    try:
        with open(f'{category}.json', 'r') as file:
            file_content = file.read().strip()
            if not file_content:
                # If the file is empty, return an empty list
                print(f'Error: JSON file for category "{category}" is empty.')
                return []
            # Parse the file content as JSON
            words = json.loads(file_content)
        return words
    except json.JSONDecodeError:
        print(f'Error: JSON file for category "{category}" contains invalid JSON.')
        return []
    except FileNotFoundError:
        print(f'Error: JSON file for category "{category}" not found.')
        return []

def build_prompt(template, categories):
    """Build a prompt using the provided template and word categories."""
    for category in categories:
        # Load words for the current category from JSON file
        words = load_words(category)
        # Count the number of times the category appears in the template
        count = template.count(f'[{category}]')
        # Loop to replace each occurrence with a unique random word
        for _ in range(count):
            # Randomly select a word from the list of words
            selected_word = random.choice(words) if words else ''
            # Replace one placeholder in the template with the selected word
            template = template.replace(f'[{category}]', selected_word, 1)
    return template

def generate_prompt():
    """Generate a prompt using the user-defined template and display it."""
    # Get the template from the StringVar
    template = template_var.get()

    # Build and display the prompt
    prompt = build_prompt(template, CATEGORIES)
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
    # If there is existing content, append ", " before adding the new category
    if current_template:
        updated_template = current_template + f', [{category}]'
    else:
        # If there is no existing content, add the new category without ", "
        updated_template = f'[{category}]'
    template_var.set(updated_template)
    # Set the cursor position to the end of the updated template
    entry.icursor(tk.END)

def rebuild_categories(refresh=True):
    """Rebuild the CATEGORIES list based on the JSON files present in the directory."""
    global CATEGORIES  # Declare CATEGORIES as global to modify it
    
    # List all files in the current directory
    files = os.listdir()
    
    # Filter for files with the .json extension
    json_files = [file for file in files if file.endswith('.json')]
    
    # Extract the names of the JSON files (without the .json extension) to update the CATEGORIES list
    CATEGORIES = [file.split('.')[0] for file in json_files]
    
    if refresh:
        # Refresh the Template Builder tab to reflect the updated CATEGORIES list
        refresh_template_builder()

def refresh_template_builder():
    """Refresh the Template Builder tab to reflect the updated CATEGORIES list."""
    # Clear the current buttons from the tab_template_builder
    for widget in tab_template_builder.winfo_children():
        widget.destroy()

    # Recreate the input field for editing the template
    template_entry = tk.Entry(tab_template_builder, textvariable=template_var, width=60)
    template_entry.grid(row=0, column=0, columnspan=len(CATEGORIES), padx=10, pady=10)

    # Recreate the buttons for each updated category to insert into the input field
    for i, category in enumerate(CATEGORIES):
        category_button = tk.Button(tab_template_builder, text=category,
                                    command=lambda cat=category, entry=template_entry: insert_category(cat, entry))
        category_button.grid(row=1, column=i, padx=5, pady=5)


def create_template_builder(tab_parent):
    """Create the Template Builder tab."""
    global tab_template_builder  # Declare tab_template_builder as a global variable
    # Create a new tab for the Template Builder
    tab_template_builder = ttk.Frame(tab_parent)
    tab_parent.add(tab_template_builder, text="Template Builder")

    # Recreate the input field for editing the template
    template_entry = tk.Entry(tab_template_builder, textvariable=template_var, width=60)
    # Ensure columnspan is at least 1
    template_entry.grid(row=0, column=0, columnspan=max(1, len(CATEGORIES)), padx=10, pady=10)

    # Create a "Clear" button to clear the content of the template input field
    clear_button = tk.Button(tab_template_builder, text="Clear", command=clear_template_input)
    clear_button.grid(row=0, column=max(1, len(CATEGORIES)), padx=10, pady=10)

    # Recreate the buttons for each updated category to insert into the input field
    for i, category in enumerate(CATEGORIES):
        category_button = tk.Button(tab_template_builder, text=category,
                                    command=lambda cat=category, entry=template_entry: insert_category(cat, entry))
        category_button.grid(row=1, column=i, padx=5, pady=5)

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
rebuild_categories(refresh=False)

# Create the Template Builder tab
create_template_builder(tab_parent)

# Create the Settings tab
create_settings_tab(tab_parent)

# Run the application
root.mainloop()