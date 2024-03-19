import streamlit as st
import openai
import sqlite3
import os
import base64
import csv
import time
from bing_image_downloader import downloader

openai.api_key = "YOUR_OPENAI_KEY"
os.environ['BING_API_KEY'] = "YOUR BING_API_KEY"

# Main code
st.set_page_config(
    page_title="Food Recipe Generator",
    page_icon="🍳",
    layout="wide"
)
st.title('Recipe Generator')

# Function to initialize the SQLite database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (email TEXT, username TEXT, password TEXT)''')
    conn.commit()
    conn.close()

# Initialize the SQLite database
init_db() 

# Function to register a new user
def register_user(email, username, password, repeat_password):
    if password != repeat_password:
        raise ValueError("Passwords do not match.")

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO users VALUES (?, ?, ?)", (email, username, password))
    conn.commit()
    conn.close()
    return email, username

# Function to log in existing user
def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()

    if result:
        st.button('enter')
        st.session_state['logged_in'] = True
    else:
        st.error('Username/password is incorrect')

    return result is not None

# Function to get recipe images
def get_recipe_images(recipes):
    img_urls = []
    for recipe in recipes:
        dish_name = recipe.split('\n')[0]
        # Replace special characters with underscores
        dish_name = ''.join(c if c.isalnum() or c in ['_', ' '] else '_' for c in dish_name)
        
        # Download images using bing_image_downloader
        os.makedirs(os.path.join('downloads', dish_name), exist_ok=True)
        downloader.download(dish_name, limit=1, output_dir='downloads', adult_filter_off=True, force_replace=False, timeout=60)
        
        # Construct image URL
        image_files = os.listdir(os.path.join('downloads', dish_name))
        if image_files:
            img_url = f"downloads/{dish_name}/{image_files[0]}"
            img_urls.append(img_url)
        else:
            print(f"No image found for {dish_name}")
        
    return img_urls

feedback_data = []

# Function to save feedback data to CSV
def save_feedback_to_csv(feedback):
    with open('feedback.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(feedback)
        
def create_feedback(recipe_name):
    feedback_given_key = f'feedback_given_{recipe_name}'
    if not st.session_state.get(feedback_given_key):
        form_placeholder = st.empty()
        with st.form(f'feedback_form_{recipe_name}'):
            username = st.text_input('Enter your name')
            feedback = st.slider('Rating (1-5)', min_value=1, max_value=5, step=1)
            submit_button = st.form_submit_button('Submit Feedback')

            if submit_button:
                if username:
                    save_feedback_to_csv((username, recipe_name, feedback))
                    st.session_state[feedback_given_key] = True
                    # Clear the form from the UI
                    form_placeholder.empty()
                    # Display success message
                    st.success("Feedback submitted successfully!")
                    # Display close button
                    close_button =  st.form_submit_button('Close Form')
                    if close_button:
                        form_placeholder.empty()  # Clear the form and success message from the UI
                else:
                    st.error("Please provide your username")


def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"png"};base64,{encoded_string.decode()});
        background-size: cover
    }}
    </style>
    """,
    unsafe_allow_html=True
    )
add_bg_from_local('./bg_image.jpeg')

def show_recipe_form():
    st.title('Welcome to the Recipe Generator!!')
    # User inputs for the recipe generator form
    # Add your recipe generator form inputs here
    age = st.number_input("Enter your age", min_value=18, step=1)
    gender = st.selectbox("Select your gender", ["Select","F", "M"])

    height = st.number_input("Enter your height (in centimeters)", min_value=120, step=1)
    weight = st.number_input("Enter your weight (in kilograms)", min_value=55, step=1)
    
    fitness_goals_options = ["Weight Loss", "Muscle Gain", "Maintaining Weight", "Other"]
    selected_fitness_goal = st.selectbox("Select your fitness goal", fitness_goals_options)
    
    protein_preference_options = ["Vegetarian", "Chicken", "Fish", "Shrimp", "Vegan", "Pork", "Mutton", "Beef"]
    selected_protein_preference = st.selectbox("Select food preference", protein_preference_options)
    
    cuisine_type_options = ["Indian", "Italian", "Asian", "Mexican", "Mediterranean", "Other"]
    cuisine_type = st.selectbox("Select preferred cuisine type", cuisine_type_options)

    dietary_restrictions_options = ["Low-carb", "Nut-free", "Vegan", "Vegetarian", ""]
    dietary_restrictions = st.selectbox("Select dietary restrictions or preferences", dietary_restrictions_options)
    
    preferred_ingredients = st.text_input("Preferred Ingredients (comma-separated)", "")
    ingredients_to_avoid = st.text_input("Ingredients to Avoid (comma-separated)", "")
    cook_time = st.number_input("Maximum time to cook (in minutes)", min_value=1, step=1)
    
    # Number of recipes to generate
    num_recipes = st.number_input("Number of recipes to generate", min_value=1, max_value=10, step=1, value=1)

    # Generate button
    if not st.session_state.get('recipes_generated'):
        generate_recipes = st.button("Generate Recipes")
        if generate_recipes:
            recipes = []
            for _ in range(num_recipes):
                # Construct the prompt based on user input
                prompt = f"Generate a recipe suitable for a {age}-year-old"
                if selected_fitness_goal:
                    prompt += f" with a goal of {selected_fitness_goal.lower()}"
                if height and weight:
                    prompt += f", {height} cm tall, and {weight} kg in weight"
                if selected_protein_preference:
                    prompt += f" who is {selected_protein_preference.lower()}"
                if cuisine_type:
                    prompt += f" and has a {cuisine_type.lower()} influence"
                if dietary_restrictions:
                    prompt += f" while being {dietary_restrictions.lower()}"
                if preferred_ingredients:
                    prompt += f" and by including only these ingredients {preferred_ingredients.lower()}"
                if ingredients_to_avoid:
                    prompt += f" and excluding these ingredients {ingredients_to_avoid.lower()}"
                if cook_time:
                    prompt += f" and dish has to be ready in {cook_time} minutes"
                prompt += ". Also, provide the nutritional information."
                # Make a request to the OpenAI API
                response = openai.Completion.create(
                    engine="gpt-3.5-turbo-instruct",
                    prompt=prompt,
                    max_tokens=400  # Adjust the maximum number of tokens based on the desired response length
                )
                # Get the generated recipe from the API response
                recipe = response.choices[0].text.strip()
                recipes.append(recipe)

            # Display recipes
            st.session_state['recipes_generated'] = recipes

    # Display recipes if they have been generated
    if st.session_state.get('recipes_generated'):
        recipes_generated = st.session_state['recipes_generated']
        for idx, (recipe, img_url) in enumerate(zip(recipes_generated, get_recipe_images(recipes_generated)), start=1):
            st.markdown(f"**Recipe {idx}:** {recipe}")
            st.image(img_url, caption=f"Image for Recipe {idx}", width=300)
            recipe_name = recipe.split('\n')[0]
            create_feedback(recipe_name)

def show_login_form():
    if st.sidebar.button('Register'):
        st.session_state['register'] = True
        st.session_state['login'] = False

    if st.sidebar.button('Login'):
        st.session_state['login'] = True
        st.session_state['register'] = False

    if st.session_state.get('register'):
        st.title('Register')
        with st.form(key='register_form'):
            reg_email = st.text_input('Email')
            reg_username = st.text_input('Username')
            reg_password = st.text_input('Password', type='password')
            repeat_password = st.text_input('Repeat Password', type='password')
            register_button = st.form_submit_button(label='Register')

        if register_button:
            try:
                email_of_registered_user, username_of_registered_user = register_user(reg_email, reg_username, reg_password, repeat_password)
                st.success('User registered successfully')
            except Exception as e:
                st.error(e)

    if st.session_state.get('login'):
        st.title('Login')
        with st.form(key='login_form'):
            login_username = st.text_input('Username')
            login_password = st.text_input('Password', type='password')
            login_button = st.form_submit_button(label='Login')

        if login_button:
            authentication_status = login_user(login_username, login_password)
            if authentication_status:
                st.session_state['logged_in'] = True

# Main code
if st.session_state.get('logged_in'):
    if st.sidebar.button("Logout"):
        st.session_state.clear()  
        st.rerun()  # Reload the app to reset the state
    else:
        # If the user clicked the refresh button, reset only the recipes_generated state
        if st.sidebar.button("Refresh"):
            st.session_state['recipes_generated'] = None

        # Show the recipe generator form
        show_recipe_form()
else:
    show_login_form()
