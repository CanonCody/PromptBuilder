import json
import random
import os
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk

# Define the name of the subdirectory where JSON files are stored
JSON_DIR = "categories"

# Initialize CATEGORIES_BY_TYPE as a dictionary with default empty lists
CATEGORIES_BY_TYPE = {}

def load_words(category):
    """Load words from JSON file for the given category."""
    # Build the file path using the JSON_DIR constant
    file_path = os.path.join(JSON_DIR, f'{category}.json')
    try:
        with open(file_path, 'r') as file:
            words = json.load(file)
        return words
    except FileNotFoundError:
        print(f'Error: JSON file for category "{category}" not found.')
    except json.JSONDecodeError as e:
        print(f'Error: JSON file for category "{category}" contains invalid JSON. {e}')
    return []

def load_category_types():
    """Load category types from JSON file or prompt user for default category types."""
    # Build the file path using the JSON_DIR constant
    file_path = os.path.join(JSON_DIR, 'category_types.json')
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print('Error: Unable to load category types. JSON file not found.')
        # Prompt user for default category types
        default_category_types = input("Enter default category types separated by comma (e.g., uncategorized,nouns): ").strip()
        # Convert input to dictionary format
        default_categories_dict = {category_type: [] for category_type in default_category_types.split(',')}
        # Write the default categories to a new JSON file
        with open(file_path, 'w') as file:
            json.dump(default_categories_dict, file, indent=2)
        return default_categories_dict
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

# Define a global variable for the template_entry widget
template_entry = None

def generate_prompt():
    """Generate a prompt using the user-defined template and display it."""
    global template_entry  # Access the global variable
    # Get the template from the template_entry widget
    template = template_entry.get("1.0", tk.END)[:-1]  # Remove the trailing newline character

    # Build and display the prompt
    prompt = build_prompt(template)
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

def show_category_words(event, category):
    """Open a new window to display all the words in the selected category."""
    # Load words for the current category from JSON file
    words = load_words(category)

    # Sort the words alphabetically
    words = sorted(words)

    # Create a new window to display the words
    words_window = tk.Toplevel(root)
    words_window.title(f"Words in '{category}' category")

    # Create a label to display the words in the new window
    words_label = tk.Label(words_window, text="\n".join(words), font=("Helvetica", 12))
    words_label.pack(pady=10)

    # Define the default width and height for the window (in pixels)
    default_width = 300
    default_height = 200

    # Set the default geometry of the words_window
    words_window.geometry(f"{default_width}x{default_height}")

    # Calculate the width of the longest word in pixels
    max_word_width = max(words_label.winfo_reqwidth() for word in words)
    # Define the margin space in pixels
    margin_space = 20
    # Calculate the total window width
    words_window_width = max(default_width, max_word_width + margin_space)

    # Update the width of the words_window to the calculated width
    words_window.geometry(f"{words_window_width}x{words_window.winfo_reqheight()}")


def clear_template_input():
    """Clear the content of the template input field."""
    global template_entry  # Access the global variable
    template_entry.delete("1.0", tk.END)  # Clear the content of the template_entry widget

def insert_into_template(text, entry, is_category=False):
    """Insert the specified text or category into the template input field."""
    def should_add_space(target, index, is_before):
        """Determine if a space should be added before or after the index."""
        if not target:  # Empty target
            return False
        if is_before:
            return index > 0 and target[index - 1] not in (' ', '\n')
        else:
            return index < len(target) and target[index] not in (' ', '\n')

    # Get current content and insert the text at the cursor position
    current_template = entry.get("1.0", tk.END)[:-1]
    cursor_position_str = entry.index(tk.INSERT)
    cursor_index = int(entry.index(cursor_position_str).split('.')[1])
    
    # Wrap category in square brackets if it's a category
    if is_category:
        text = f'[{text}]'
    
    # Add space before the text if necessary
    if should_add_space(current_template, cursor_index, is_before=True):
        text = ' ' + text
    
    # Add space after the text if necessary
    if should_add_space(current_template, cursor_index, is_before=False):
        text += ' '
    
    # Insert the text into the current template
    updated_template = current_template[:cursor_index] + text + current_template[cursor_index:]
    entry.delete("1.0", tk.END)
    entry.insert(tk.END, updated_template)


def rebuild_categories(refresh=True):
    """Rebuild the CATEGORIES list based on the JSON files present in the directory."""
    global CATEGORIES_BY_TYPE  # Declare CATEGORIES_BY_TYPE as global to modify it
    
    # Load category types from JSON file and update CATEGORIES_BY_TYPE
    CATEGORIES_BY_TYPE = load_category_types()
    
    # List all files in the JSON_DIR subdirectory
    files = os.listdir(JSON_DIR)
    
    # Filter for files with the .json extension
    json_files = [file for file in files if file.endswith('.json')]
    
    # Update the CATEGORIES_BY_TYPE dictionary based on available JSON files
    for category_type, categories in CATEGORIES_BY_TYPE.items():
        # Filter JSON files that belong to the current category type
        CATEGORIES_BY_TYPE[category_type] = [cat[:-5] for cat in json_files if cat[:-5] in categories and cat != 'category_types.json']
    
    # Print the content of the CATEGORIES_BY_TYPE dictionary for debugging
    print(CATEGORIES_BY_TYPE)
    
    if refresh:
        # Refresh the Template Builder tab to reflect the updated CATEGORIES_BY_TYPE dictionary
        refresh_template_builder()

def refresh_template_builder():
    """Refresh the Template Builder tab to reflect the updated CATEGORIES_BY_TYPE dictionary."""
    global template_entry  # Add this line to access the global variable
    
    # Clear the current buttons from the tab_template_builder
    for widget in tab_template_builder.winfo_children():
        widget.destroy()

    # Total number of categories
    total_categories = sum(len(categories) for categories in CATEGORIES_BY_TYPE.values())

    # Recreate the input field for editing the template
    template_entry = scrolledtext.ScrolledText(tab_template_builder, width=75, height=2, wrap=tk.WORD)
    template_entry.grid(row=0, column=0, columnspan=max(1, total_categories), padx=10, pady=10)

    # Determine the maximum length of the category names for button size
    max_length = max(len(category) for categories in CATEGORIES_BY_TYPE.values() for category in categories)

    # Recreate the buttons for each category type in separate rows
    row = 3  # Start placing category buttons from row=3
    for category_type, categories in CATEGORIES_BY_TYPE.items():
        # Create a label to display the category type
        category_type_label = tk.Label(tab_template_builder, text=category_type.capitalize())
        category_type_label.grid(row=row, column=0, padx=5, pady=5, sticky='w')
        for col, category in enumerate(categories, start=1):
            category_button = tk.Button(tab_template_builder, text=category, width=max_length,
                            command=lambda cat=category, entry=template_entry: insert_into_template(cat, entry, is_category=True))
            category_button.grid(row=row, column=col, padx=5, pady=5)
            # Bind right-click event (Button-3) to show_category_words function
            category_button.bind("<Button-3>", lambda event, cat=category: show_category_words(event, cat))
        row += 1  # Increment the row for the next category type

    # Recreate the "Clear" button to clear the content of the template input field
    clear_button = tk.Button(tab_template_builder, text="Clear", command=clear_template_input)
    clear_button.grid(row=0, column=max(1, total_categories), padx=10, pady=10)


def create_template_builder(tab_parent):
    global tab_template_builder, template_entry  # Access the global variables
    # Create a new tab for the Template Builder
    tab_template_builder = ttk.Frame(tab_parent)
    tab_parent.add(tab_template_builder, text="Template Builder")

    # Recreate the input field for editing the template
    total_categories = sum(len(categories) for categories in CATEGORIES_BY_TYPE.values())
    template_entry = scrolledtext.ScrolledText(tab_template_builder, width=75, height=2, wrap=tk.WORD)
    template_entry.grid(row=0, column=0, columnspan=max(1, total_categories), padx=10, pady=10)

    # Create a frame for the text buttons
    text_buttons_frame = tk.Frame(tab_template_builder)
    text_buttons_frame.grid(row=2, column=0, columnspan=max(1, total_categories), padx=10, pady=5, sticky='w')

    # Create a row of buttons for specific characters and strings
    text_buttons = [", ", "of", "a", "and"]
    for col, text in enumerate(text_buttons, start=0):
        text_button = tk.Button(text_buttons_frame, text=text,
                                command=lambda t=text, entry=template_entry: insert_into_template(t, entry, is_category=False))
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