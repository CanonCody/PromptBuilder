import json
import random
import os
import re
import openai
import tkinter as tk
from functools import partial
from tkinter import scrolledtext
import tkinter.messagebox as messagebox
from dotenv import load_dotenv
from tkinter import ttk

# Load the environment variables from the .env file
load_dotenv()

# Create the main application window
root = tk.Tk()
root.title("Prompt Generator")

# Define the name of the subdirectory where JSON files are stored
JSON_DIR = "categories"

# Initialize CATEGORIES_BY_TYPE as a dictionary with default empty lists
CATEGORIES_BY_TYPE = {}

# Define global variables for category combination functionality
selected_categories = []

BUTTON_NORMAL_BG = "SystemButtonFace"  # Default button background color
BUTTON_SELECTED_BG = "lightblue"       # Highlight color for selected buttons

# Define a global variable for the template_entry widget and the number of prompts to generate
template_entry = None
num_prompts_to_generate = tk.IntVar()
global types_text_editor
edit_types_window = None


#Startup

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
        # Convert input to dictionary format and remove extra spaces
        default_categories_dict = {category_type.strip(): [] for category_type in default_category_types.split(',')}
        # Write the default categories to a new JSON file
        with open(file_path, 'w') as file:
            json.dump(default_categories_dict, file, indent=2)
        return default_categories_dict
    except json.JSONDecodeError as e:
        print(f'Error: Unable to load category types. Invalid JSON. {e}')
    return {'uncategorized': [], 'nouns': []}

#Prompt Creation

def build_prompt(template):
    """Build a prompt using the provided template and word categories."""
    for category_type, categories in CATEGORIES_BY_TYPE.items():
        while f'[{category_type}]' in template:
            # Randomly select a category from the category type
            selected_category = random.choice(categories)
            words = load_words(selected_category)
            selected_word = random.choice(words) if words else ''
            template = template.replace(f'[{category_type}]', selected_word, 1)

    # Find placeholders with combined categories
    combined_category_placeholders = re.findall(r'\[([\w/]+)\]', template)

    for combined_categories in combined_category_placeholders:
        # Split combined categories into a list
        categories = combined_categories.split('/')
        # Randomly select a category from the list
        selected_category = random.choice(categories)
        # Load words for the selected category
        words = load_words(selected_category)
        # Randomly select a word from the list
        selected_word = random.choice(words) if words else ''
        # Replace the placeholder with the selected word
        template = template.replace(f'[{combined_categories}]', selected_word, 1)

    return template

def generate_prompt():
    """Generate a prompt using the user-defined template and display it."""
    global template_entry  # Access the global variable
    # Get the template from the template_entry widget
    template = template_entry.get("1.0", tk.END)[:-1]  # Remove the trailing newline character

    # Get the number of prompts to generate
    num_prompts = num_prompts_to_generate.get()

    # Initialize a list to store the generated prompts
    generated_prompts = []

    # Generate the specified number of prompts
    for _ in range(num_prompts):
        # Build and append the prompt to the list
        prompt = build_prompt(template)
        generated_prompts.append(prompt)

    # Display the generated prompts
    prompt_label.config(text="\n".join(generated_prompts))

def generate_prompt_gpt():
    """Generate a prompt using the GPT API and the user-defined template."""
    global template_entry  # Access the global variable
    # Get the template from the template_entry widget
    template = template_entry.get("1.0", tk.END)[:-1]  # Remove the trailing newline character
    
    # Get the number of prompts to generate
    num_prompts = num_prompts_to_generate.get()

    # Initialize a list to store the generated prompts
    generated_prompts = []

    # Generate the specified number of prompts
    for _ in range(num_prompts):
        # Prepare the conversation messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Your task is to replace the brackets in the provided template. Each bracket contains a category name, and you should replace the bracket with a word or phrase that matches the specified category. For example, if the template is 'The [color] [animal] jumped over the fence', you could complete it as 'The brown rabbit jumped over the fence' Make sure to not leave any brackets in the completion."},
            {"role": "user", "content": f"replace the brackets with a random appropriate completions: {template}"}
        ]

        # Call the OpenAI Chat API
        try:
            # Set the OpenAI API key
            openai.api_key = os.environ.get("OPENAI_API_KEY")

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )

            # Extract the assistant's response
            prompt = response['choices'][0]['message']['content']

            if prompt:
                # Append the generated prompt to the list
                generated_prompts.append(prompt)
            else:
                generated_prompts.append("Failed to generate text.")
        except Exception as e:
            print(f"Error: {e}")
            generated_prompts.append("Failed to generate text.")
    
    # Display the generated prompts
    prompt_label.config(text="\n".join(generated_prompts))

#Utility

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

#JSON Editor

def load_selected_category(event):
    # Get the selected item in the Treeview
    selected_item = category_treeview.focus()

    # Check if the selected item has any children (is a parent)
    if not category_treeview.get_children(selected_item):
        # Get the category name
        category = category_treeview.item(selected_item, 'text')

        # Load words for the selected category
        words = load_words(category)

        # Display the words in the Text widget as JSON
        json_text_editor.delete("1.0", tk.END)
        json_text_editor.insert(tk.END, json.dumps(words, indent=2))
    else:
        # Clear the JSON editor if a parent (category type) is selected
        json_text_editor.delete("1.0", tk.END)

def save_edited_json():
    # Get the selected item in the Treeview
    selected_item = category_treeview.focus()

    # Check if the selected item has any children (is a parent)
    if not category_treeview.get_children(selected_item):
        # Get the category name
        selected_category = category_treeview.item(selected_item, 'text')

        # Get the edited content from the text editor
        edited_content = json_text_editor.get("1.0", tk.END).strip()

        # Build the file path using the JSON_DIR constant
        file_path = os.path.join(JSON_DIR, f'{selected_category}.json')

        try:
            # Parse the edited content as JSON
            words = json.loads(edited_content)

            # Save the edited content to the JSON file
            with open(file_path, 'w') as file:
                json.dump(words, file, indent=2)

            # The success message popup has been removed

        except json.JSONDecodeError:
            # Show an error message if the content is not valid JSON
            messagebox.showerror("Error", "Invalid JSON format.")

def open_edit_types_window():
    """Open a new window to edit the category types."""
    global edit_types_window, types_text_editor # Access the global variable
    # Create a new window to edit category types
    edit_types_window = tk.Toplevel(root)
    edit_types_window.title("Edit Category Types")

    # Create the Text widget for editing category types
    types_text_editor = tk.Text(edit_types_window, wrap=tk.NONE)
    types_text_editor.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    # Load category types
    category_types = load_category_types()
    
    # Display the category types in the Text widget as JSON
    types_text_editor.delete("1.0", tk.END)
    types_text_editor.insert(tk.END, json.dumps(category_types, indent=2))

    # Create a "Save Changes" button to save the edited category types
    save_button = tk.Button(edit_types_window, text="Save Changes", command=save_edited_types)
    save_button.pack()

def save_edited_types():
    """Save the edited category types to the JSON file."""
    global types_text_editor, JSON_DIR, edit_types_window  # Access the global variables
    # Get the edited content from the text editor
    edited_content = types_text_editor.get("1.0", tk.END).strip()
    # Build the file path
    file_path = os.path.join(JSON_DIR, 'category_types.json')
    try:
        # Parse the edited content as JSON
        category_types = json.loads(edited_content)
        # Save the edited content to the JSON file
        with open(file_path, 'w') as file:
            json.dump(category_types, file, indent=2)
        # Close the editor window after saving changes
        edit_types_window.destroy()
        # Refresh the category Treeview to reflect the updated category types
        refresh_category_treeview()
    except json.JSONDecodeError:
        # Show an error message if the content is not valid JSON
        messagebox.showerror("Error", "Invalid JSON format.")

def refresh_category_treeview():
    """Refresh the category Treeview based on the updated JSON file."""
    global category_treeview
    # Clear all items from the Treeview
    category_treeview.delete(*category_treeview.get_children())
    # Load the updated category types from the JSON file
    category_types = load_category_types()
    # Populate the Treeview with the updated category types and categories
    for category_type, categories in category_types.items():
        # Insert the category type as a parent node
        category_type_id = category_treeview.insert("", "end", text=category_type)
        for category in categories:
            # Insert the category as a child node of the category type
            category_treeview.insert(category_type_id, "end", text=category)

def save_edited_json():
    # Get the selected item in the Treeview
    selected_item = category_treeview.focus()
    # Check if the selected item has any children (is a parent)
    if not category_treeview.get_children(selected_item):
        # Get the category name
        selected_category = category_treeview.item(selected_item, 'text')
        # Get the edited content from the text editor
        edited_content = json_text_editor.get("1.0", tk.END).strip()
        # Build the file path using the JSON_DIR constant
        file_path = os.path.join(JSON_DIR, f'{selected_category}.json')
        try:
            # Parse the edited content as JSON
            words = json.loads(edited_content)
            # Save the edited content to the JSON file
            with open(file_path, 'w') as file:
                json.dump(words, file, indent=2)

            # Remove the "highlight" tag after saving the changes
            json_text_editor.tag_remove("highlight", "1.0", tk.END)
        except json.JSONDecodeError:
            # Show an error message if the content is not valid JSON
            messagebox.showerror("Error", "Invalid JSON format.")

    # Define the highlight tag for the Text widget (JSON editor)
    json_text_editor.tag_configure("highlight", background="yellow")

def create_empty_json_files():
    """Create empty JSON files for categories that do not have corresponding JSON files."""
    # Iterate through all category types and categories
    for categories in CATEGORIES_BY_TYPE.values():
        for category in categories:
            # Build the file path using the JSON_DIR constant and category name
            file_path = os.path.join(JSON_DIR, f'{category}.json')
            # Check if the JSON file does not exist
            if not os.path.exists(file_path):
                # Create and write an empty list to the new JSON file
                with open(file_path, 'w') as file:
                    json.dump([], file, indent=2)
                print(f'Created empty JSON file for category "{category}".')

def ai_populate_category():
    """Use GPT to populate the selected category with new words."""
    # Get the selected category from the Treeview
    selected_item = category_treeview.focus()
    if not category_treeview.get_children(selected_item):
        # Get the category name
        category = category_treeview.item(selected_item, 'text')
        # Load words for the selected category
        current_words = load_words(category)
        # Prepare the conversation messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Your task is to suggest additional words that match the specified category. Do not suggest any words that are already on the list. Respond with each suggested word in quotes."},
            {"role": "user", "content": f"Category: {category}. Current list: {current_words}. Suggest some additional words that match the category and are not already on the list."}
        ]
        try:
            # Set the OpenAI API key
            openai.api_key = os.environ.get("OPENAI_API_KEY")
            # Call the OpenAI Chat API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            # Extract the assistant's response
            ai_response = response['choices'][0]['message']['content']
            # Debug information: Print the AI response to the console
            print("AI Response:", ai_response)
            # Use regular expressions to extract the list of suggested words from the response
            # Updated regex to capture single-quoted and double-quoted words
            suggested_words = re.findall(r'"([^"]+)"|\'([^\']+)\'' , ai_response)
            # Flatten the list of tuples and filter out empty strings
            suggested_words = [word for tup in suggested_words for word in tup if word]
            # Filter out words that are already in the current list
            new_words = [word for word in suggested_words if word not in current_words]
            # Debug information: Print the new words to the console
            print("New Words:", new_words)
            if new_words:
                # Append the new words to the current list
                current_words.extend(new_words)
                # Sort the updated list of words in alphabetical order
                current_words = sorted(current_words)
                # Convert the updated list of words to JSON format
                updated_words_json = json.dumps(current_words, indent=2)
                # Display the updated list of words in the JSON editor
                json_text_editor.delete("1.0", tk.END)
                json_text_editor.insert(tk.END, updated_words_json)
                # Highlight only the new words
                for new_word in new_words:
                    start_index = json_text_editor.search(json.dumps(new_word), "1.0", tk.END)
                    end_index = f"{start_index}+{len(json.dumps(new_word))}c"
                    json_text_editor.tag_add("highlight", start_index, end_index)
        except Exception as e:
            # Debug information: Print the error message to the console
            print("Error:", e)
            messagebox.showerror("Error", "Failed to populate category using AI.")

def ai_suggest_category():
    """Use GPT to suggest words to add to the selected category."""
    # Get the selected category from the Treeview
    selected_item = category_treeview.focus()
    if not category_treeview.get_children(selected_item):
        # Get the category name
        category = category_treeview.item(selected_item, 'text')
        # Load words for the selected category
        words = load_words(category)
        # Prepare the conversation messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Your task is to suggest additional words that match the specified category. Do not suggest any words that are already on the list. Respond with each suggested word in quotes."},
            {"role": "user", "content": f"Category: {category}. Current list: {words}. Suggest some additional words that match the category and are not already on the list."}
        ]
        try:
            # Set the OpenAI API key
            openai.api_key = os.environ.get("OPENAI_API_KEY")
            # Call the OpenAI Chat API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            # Extract the assistant's response
            ai_response = response['choices'][0]['message']['content']
            # Debug information: Print the AI response to the console
            print("AI Response:", ai_response)
            # Use regular expressions to extract the list of suggested words from the response
            suggested_words = re.findall(r'"(\w+)"', ai_response)
            # Filter out words that are already in the current list
            new_suggested_words = [word for word in suggested_words if word not in words]
            # Convert the list of new suggested words to JSON format
            suggested_words_json = json.dumps(new_suggested_words, indent=2)
            # Create a popup to display the suggested words in JSON format
            suggest_window = tk.Toplevel(root)
            suggest_window.title("AI Suggested Words")
            suggest_text = tk.scrolledtext.ScrolledText(suggest_window, wrap=tk.WORD, font=("Helvetica", 12))
            suggest_text.insert(tk.END, suggested_words_json)
            suggest_text.pack(pady=10)
            # Set the ScrolledText widget to read-only mode
            suggest_text.configure(state='disabled')
        except Exception as e:
            # Debug information: Print the error message to the console
            print("Error:", e)
            messagebox.showerror("Error", "Failed to suggest words using AI.")


#Template

def clear_template_input():
    """Clear the content of the template input field."""
    global template_entry  # Access the global variable
    template_entry.delete("1.0", tk.END)  # Clear the content of the template_entry widget

def insert_into_template(text, entry, is_category=False, button=None):
    global selected_categories
    if combine_categories.get() and is_category:
        # Add or remove the category from the list of selected categories
        if text in selected_categories:
            selected_categories.remove(text)
            button.config(bg=BUTTON_NORMAL_BG)  # Reset button color to normal
        else:
            selected_categories.append(text)
            button.config(bg=BUTTON_SELECTED_BG)  # Highlight button color
        return

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

def toggle_category_combination():
    """Clear selected categories when toggling category combination."""
    global selected_categories
    selected_categories = []

def confirm_combine_categories(entry, category_buttons):
    # Combine the selected categories and insert them into the template
    global selected_categories
    combined_categories = '/'.join(selected_categories)
    if combined_categories:
        # Wrap the combined categories in square brackets
        insert_into_template(f'[{combined_categories}]', entry, is_category=False)
    selected_categories = []

    # Reset the background color of all category buttons to the normal state
    for btn in category_buttons:
        btn.config(bg=BUTTON_NORMAL_BG)

def category_button_click(category, button, entry):
    insert_into_template(category, entry, is_category=True, button=button)

#Tabs

def create_template_builder(tab_parent):
    global tab_template_builder, template_entry  # Access the global variables
    # Create a new tab for the Template Builder
    tab_template_builder = ttk.Frame(tab_parent)
    tab_parent.add(tab_template_builder, text="Template Builder")

    # Load category types from JSON file
    global CATEGORIES_BY_TYPE
    CATEGORIES_BY_TYPE = load_category_types()

    # Total number of categories
    total_categories = sum(len(categories) for categories in CATEGORIES_BY_TYPE.values())

    # Create the input field for editing the template
    template_entry = scrolledtext.ScrolledText(tab_template_builder, width=75, height=2, wrap=tk.WORD)
    template_entry.grid(row=0, column=0, columnspan=max(1, total_categories), padx=10, pady=10)

    # Determine the maximum length of the category names for button size
    max_length = max(len(category) for categories in CATEGORIES_BY_TYPE.values() for category in categories)

    # Create a checkbox for toggling category combination functionality
    combine_checkbox = tk.Checkbutton(tab_template_builder, text="Combine Categories", variable=combine_categories, command=toggle_category_combination)
    combine_checkbox.grid(row=1, column=0, padx=5, pady=5, sticky='w')

    category_buttons = []  # Store all category buttons

    # Create buttons for each category type in separate rows
    row = 3  # Start placing category buttons from row=3
    for category_type, categories in CATEGORIES_BY_TYPE.items():
        # Create a button for the category type (row name)
        category_type_button = tk.Button(
            tab_template_builder,
            text=category_type.capitalize(),
            command=lambda cat_type=category_type, entry=template_entry: insert_into_template(cat_type, entry, is_category=True)
        )
        category_type_button.grid(row=row, column=0, padx=5, pady=5, sticky='w')
        for col, category in enumerate(categories, start=1):
            # Create category buttons
            category_button = tk.Button(tab_template_builder, text=category, width=max_length)
            category_button.grid(row=row, column=col, padx=5, pady=5)
            # Bind right-click event (Button-3) to show_category_words function
            category_button.bind("<Button-3>", lambda event, cat=category: show_category_words(event, cat))
            # Use partial to bind parameters to insert_into_template function
            category_button.config(command=partial(insert_into_template, category, template_entry, True, category_button))
            category_buttons.append(category_button)  # Add the button to the list
        row += 1  # Increment the row for the next category type

    # Create a button for confirming category combination
    confirm_combine_button = tk.Button(tab_template_builder, text="Confirm Combine", command=lambda entry=template_entry, buttons=category_buttons: confirm_combine_categories(entry, buttons))
    confirm_combine_button.grid(row=1, column=1, padx=5, pady=5, sticky='w')

    # Create a "Clear" button to clear the content of the template input field
    clear_button = tk.Button(tab_template_builder, text="Clear", command=clear_template_input)
    clear_button.grid(row=0, column=max(1, total_categories), padx=10, pady=10)

def create_dictionary_tab(tab_parent):
    # Create a new tab for the Dictionary
    tab_dictionary = ttk.Frame(tab_parent)
    tab_parent.add(tab_dictionary, text="Dictionary")
    
    # Create a Treeview to display the list of categories
    global category_treeview
    category_treeview = ttk.Treeview(tab_dictionary)
    category_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Bind the selection event to load the selected category
    category_treeview.bind('<<TreeviewSelect>>', load_selected_category)
    
    # Load category types
    category_types = load_category_types()
    
    # Populate the Treeview with the category types and categories
    for category_type, categories in category_types.items():
        # Insert the category type as a parent node
        category_type_id = category_treeview.insert("", "end", text=category_type)
        for category in categories:
            # Insert the category as a child node of the category type
            category_treeview.insert(category_type_id, "end", text=category)

    # Create an "Edit Types" button to open the edit types window
    edit_types_button = tk.Button(tab_dictionary, text="Edit Types", command=open_edit_types_window)
    edit_types_button.pack()

    # Create a button to create empty JSON files for categories
    create_empty_json_button = tk.Button(tab_dictionary, text="Create Empty JSON Files", command=create_empty_json_files)
    create_empty_json_button.pack()

    # Create a Text widget to serve as a JSON editor
    global json_text_editor
    json_text_editor = tk.Text(tab_dictionary, wrap=tk.NONE)
    json_text_editor.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # Define the highlight tag for the Text widget (JSON editor)
    json_text_editor.tag_configure("highlight", background="yellow")

    # Create an "AI Populate" button to populate the selected category using GPT
    ai_populate_button = tk.Button(tab_dictionary, text="AI Populate", command=ai_populate_category)
    ai_populate_button.pack()

    # Add the "AI Suggest" button that triggers the ai_suggest_category function
    ai_suggest_button = tk.Button(tab_dictionary, text="AI Suggest", command=ai_suggest_category)
    ai_suggest_button.pack()

    # Create a button to save the edited JSON content
    save_button = tk.Button(tab_dictionary, text="Save Changes", command=save_edited_json)
    save_button.pack()


# Initialize tkinter variables after the root window is created
combine_categories = tk.BooleanVar()

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
generate_button = tk.Button(tab_main, text="Generate (JSON)", command=generate_prompt)
generate_button.pack(pady=10)

# Create a new button "Generate AI" on the "Generate" tab
generate_ai_button = tk.Button(tab_main, text="Generate (GPT)", command=generate_prompt_gpt)
generate_ai_button.pack(pady=10)


# Create a label and entry to input the number of prompts to generate
num_prompts_label = tk.Label(tab_main, text="Number of prompts to generate:")
num_prompts_label.pack()
num_prompts_entry = tk.Entry(tab_main, textvariable=num_prompts_to_generate)
num_prompts_entry.pack()


# Create the Template Builder tab
create_template_builder(tab_parent)

# Create the "Dictionary" tab
create_dictionary_tab(tab_parent)

# Run the application
root.mainloop()