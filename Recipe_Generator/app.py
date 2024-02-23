import streamlit as st
import openai
import sqlite3
import os
from bing_image_downloader import downloader

openai.api_key = "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"
os.environ['BING_API_KEY'] = "AleA_aBF7YGpgCOK0s2ohcIwDQ1ogtfLiT6a5vX9ztV6H1CQ3dYCzMxxq6qajeO0"

def get_recipe_images(recipes):
    img_urls = []
    for recipe in recipes:
        dish_name = recipe.split('\n')[0]
        # Replace special characters with underscores
        dish_name = ''.join(c if c.isalnum() or c in ['_', ' '] else '_' for c in dish_name)
        print("Dish Name:\n", dish_name, "\n")
        
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


# Set page title and favicon
st.set_page_config(
    page_title="Food Recipe Generator",
    page_icon="🍳",
    layout="wide"
)
st.title('Welcome to the Recipe Generator!!')
# Set background color and title
st.markdown(
    """
    <style>
    body {
        background-color: #f5f5f5;
    }
     .stApp * {
        color: #800000;
    }
    .title {
        font-size: 36px;
        text-align: center;
        margin-bottom: 30px;
    }
    </style>
    """,
    unsafe_allow_html=True
)
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

def register_user(email, username, password, repeat_password):
    if password != repeat_password:
        raise ValueError("Passwords do not match.")

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO users VALUES (?, ?, ?)", (email, username, password))
    conn.commit()
    conn.close()
    return email, username

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()

    if result:
       authentication_status = True  # Authentication successful
    else:
        authentication_status = False  # Authentication failed
    return authentication_status

# Main code
st.sidebar.title('Authentication')

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
        else:
            st.error('Username/password is incorrect')

if st.session_state.get('logged_in'):
    st.title('Recipe Generator')
    # User inputs for the recipe generator form
    # Add your recipe generator form inputs here
    age = st.number_input("Enter your age", min_value=18, step=1)
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
    if st.button("Generate Recipes"):
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
            print(prompt)
            # Make a request to the OpenAI API
            response = openai.Completion.create(
                engine="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=400  # Adjust the maximum number of tokens based on the desired response length
            )
            # Get the generated recipe from the API response
            recipe = response.choices[0].text.strip()
            recipes.append(recipe)

        # Display the generated recipes
        for idx, (recipe, img_url) in enumerate(zip(recipes, get_recipe_images(recipes)), start=1):
            st.markdown(f"**Recipe {idx}:** {recipe}")
            st.image(img_url, caption=f"Image for Recipe {idx}", width=300)
