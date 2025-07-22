import requests
import pymysql
import hashlib

user_id = None #user_id
movie_id = None

base_url = "http://www.omdbapi.com/?apikey=7413bdde" #api keys

conn = pymysql.connect(     #connecting to db
    host="localhost",
    port=3306,
    user="root",
    password="0ne0ut$",
    database="moviedb",
    connect_timeout=5
)
print("Connected with PyMySQL!")

def hash_password(password):
	return hashlib.sha256(password.encode()).hexdigest()

def login(conn):
    username = input("Enter your username: ").strip()
    password = input("Enter you password: ").strip()
    h_pass = hash_password(password)
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("select user_id from users where username = %s and password = %s", (username, h_pass))
            user = cursor.fetchone()
            #print(user)
            if user:
                print("Login Successful!")
                return user[0]
            else:
                print("Invalid username or password")
                return None
            
    except pymysql.connect.Error as err:
        print(f"MYSQL error: {err}")
        #conn.rollback()
    #finally:   
    #        conn.close()

def signup(conn):
    username = input("Enter your username: ").strip()
    password = input("Enter you password: ").strip()
    h_pass = hash_password(password)
    #print(f"Your hashed password is -> {h_pass}")
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("select user_id from users where username = %s", (username,))
            if cursor.fetchone():
                print("Username already exists!")
                return None
        
            cursor.execute("Insert into users (username, password) values (%s, %s)", (username, h_pass))
            conn.commit()
            print("SignUp Successful!")
            return
    except pymysql.connect.Error as err:
        print(f"MYSQL error: {err}")
        conn.rollback()
    #finally:   
    #        conn.close()    

def get_info(name): #get data from api
    global base_url
    url = f"{base_url}&t={name}"
    response = requests.get(url)
  
    if response.status_code == 200:
        movie_data = response.json()
        if movie_data.get("Response") == "True":
            #print(movie_data)
            return movie_data
        else:
            return None
    else:
        print(f"Failed to retrieve data {response.status_code}")

def display_data(movie_data):     #to display data
    print(f"Title:          {movie_data['Title']}")
    print(f"Year:           {movie_data['Year']}")
    print(f"Genre:          {movie_data['Genre']}")
    print(f"Director:       {movie_data['Director']}")
    print(f"Actors:         {movie_data['Actors']}")
    print(f"imdbRating:     {movie_data['imdbRating']}")
    print(f"Plot:           {movie_data["Plot"]}")
    print(f"Poster Link:    {movie_data["Poster"]}")

def title_match(movie_name, actual_title):  #To check whether the input movie exists
    return movie_name.lower() == actual_title.lower()

def main_menu():
    global user_id
    while not user_id:
        print("\n1. Login\n2. SignUp\n3. Exit")
        try:
            choice = int(input("Enter your choice: "))
        except ValueError:
            print("Invalid Choice!")
            continue
        if 1 == choice:
            user_id = login(conn)
        elif 2 == choice:
            signup(conn)
        elif 3 == choice:
            exit()
        else:
            print("Invalid Choice!")
    user_menu()

def search_movie():
    movie_name = input("Enter the movie title: ")   #user entered movie name
    
    movie_info = get_info(movie_name) 
    return movie_name, movie_info        

def user_actions():
    global user_id
    movie_name, movie_info = search_movie()
    #print(movie_name)
    #print(movie_info)
    if movie_info:
        if title_match(movie_name, movie_info['Title']):
            movie_id = store_in_db(movie_info)
            if 0 == movie_id:
                print("Something went wrong while storing or fetching movie.")
                return
                    
            else:
                while True:
                    print("Mark as:\n1. Watched\n2. Watchlist\n3. Favorite\n4. Cancel")
                    choice = input("Enter you choice: ").strip()
                    action_map = {'1':'watched','2':'watchlist','3':'favorite'}
                    action_type = action_map.get(choice)
                    if '4' == choice:
                        return      #back user's main menu
                    if action_type:
                        try:
                            with conn.cursor() as cursor:
                                    #cursor.execute("select imdb_id from movies where imdb_id = %s", (movie_info['imdbID'],))                                
                                cursor.execute("select action_type from user_actions where movie_id = %s and user_id = %s", (movie_id, user_id))
                                exisiting = cursor.fetchone()
                                if exisiting:
                                    current_action = exisiting[0]
                                    print(f"Already marked as '{current_action}'.")
                                    confirm = input("Do you want to update it? (Y/N): ").strip().lower()
                                    if 'y' == confirm:
                                        cursor.execute("update user_actions set action_type = %s where movie_id = %s and user_id = %s", (action_type, movie_id, user_id))
                                        conn.commit()
                                        print("Action updated.")
                                    else:
                                        print("Update Skipped.")
                                else:
                                    cursor.execute("insert into user_actions (movie_id, action_type, user_id) values (%s, %s, %s)", (movie_id, action_type, user_id))
                                    conn.commit()
                                    print("Marked successfully!")
                                
                        except pymysql.connect.Error as err:
                            print(f"MYSQL error: {err}")
                            conn.rollback()
                        return
                    else:
                        print("Invalid Choice!")
        else:    
            print("Please enter valid title!!")    
    else:
        print("Movie not found!")
        
def store_in_db(movie_info):
    try:
        with conn.cursor() as cursor:
            cursor.execute("select id from movies where imdb_id = %s", (movie_info['imdbID'],))
            result  = cursor.fetchone()
            if result:
                print("Movie already exists!")
                return result[0]
        #with conn.cursor() as cursor:
            cursor.execute("insert into movies (imdb_id, title, year, genre, director, actors, plot, imdb_rating) values (%s, %s, %s, %s, %s, %s, %s, %s)",(movie_info['imdbID'], movie_info['Title'], movie_info['Year'], movie_info['Genre'], movie_info['Director'], movie_info['Actors'], movie_info['Plot'], float(movie_info['imdbRating'])))
            conn.commit()
            movie_id = cursor.lastrowid
            print("Stored in DB successfully!")
            return movie_id
    except pymysql.connect.Error as err:
        print(f"MYSQL error: {err}")
        conn.rollback()
           
def user_menu():  
    global user_id
    while True:  
        print("\n User Menu\n1. Search Movies\n2. Store in DB\n3. View my lists\n4. Back to main menu\n5. Logout")
        try:
            choice = int(input("Enter your choice: "))
        except ValueError:
            print("Invalid Choice!")
            continue
        
        if 1 == choice:
            movie_name, movie_info = search_movie()  #calling function
            if movie_info:
                if title_match(movie_name, movie_info['Title']):
                    display_data(movie_info)
                else:    
                    print("Please enter valid title!!")    
            else:
                print("Movie not found!")
                
        elif 2 == choice:
            #with conn.cursor() as cursor:
            #    cursor.execute("select * from movies") #store in db
            #    for table in cursor.fetchall():
            #        print("Table:", table[0])
            user_actions()
        elif 3 == choice:
            view_my_lists()
        elif 4 == choice:
            user_id = None
            return  #goes back to main menu
        elif 5 == choice:
            exit()
        else:
            print("Invalid Choice!")

def view_my_lists():
    global user_id
    print("\nMy Lists\n1. Watched\n2. Watchlist\n3. Favorite\n4. Back")
    choice = input("Enter your choice: ").strip()
    action_map = {'1':'watched','2':'watchlist','3':'favorite'}
    if 4 == choice:
        return
    action_type = action_map.get(choice)
    if action_type:
        try:
            with conn.cursor() as cursor:
                cursor.execute("select m.title, m.year, m.imdb_rating, m.plot from movies m join user_actions ua on m.id = ua.movie_id where ua.user_id = %s and ua.action_type = %s", (user_id, action_type))
                movies = cursor.fetchall()
                if not movies:
                    print(f"No movies found in your {action_type} list.")
                    return
                print(f"\nYour {action_type.capitalize()} movies: \n")
                for movie in movies:
                    title, year, rating, plot = movie
                    print(f"{title} ({year})")
                    print(f"Rating: {rating}")
                    print(f"Plot: {plot[:100]}...")
                    print("-" * 94)
                    
        except pymysql.connect.Error as err:
            print(f"MYSQL error: {err}")
            conn.rollback()
    else:
        print("Invalid Choice!")
        return
main_menu()
conn.close()