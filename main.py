import tkinter
from tkinter import ttk
from tkinter import Text
from tkinter import Toplevel

import oracledb

dsn_tsn = oracledb.makedsn(r'bd-dc.cs.tuiasi.ro', 1539, service_name=r'orcl')
conn = oracledb.connect(user=r'bd115', password=r'bd115', dsn=dsn_tsn)

c = conn.cursor()
user_dict = {"admin": "admin", "user1": "password1", "": ""}


def clear_widgets(frame):
    for widget in frame.winfo_children():
        widget.destroy()


def popup_eroare(text):
    top = Toplevel(root)
    top.geometry("300x100")
    top.title("Error")
    tkinter.Label(top, text=text, font='Mistral 12 bold', background="red").pack()


def login(user, pas):
    if user in user_dict:
        if user_dict[user] == pas:
            load_frame2()
        else:
            popup_eroare("Username sau parola gresita!")
    else:
        popup_eroare("Username sau parola gresita!")
    return 0


def load_frame1():
    clear_widgets(frame2)
    frame1.tkraise()
    frame1.pack_propagate(False)

    login_info_frame = tkinter.LabelFrame(frame1, text="Login Information")
    login_info_frame.grid(row=0, column=0, padx=20, pady=10)

    username_label = tkinter.Label(login_info_frame, text="Username")
    username_label.grid(row=0, column=0)
    password_label = tkinter.Label(login_info_frame, text="Password")
    password_label.grid(row=0, column=1)

    username_entry = tkinter.Entry(login_info_frame)
    password_entry = tkinter.Entry(login_info_frame)
    username_entry.grid(row=1, column=0)
    password_entry.grid(row=1, column=1)

    for widget in login_info_frame.winfo_children():
        widget.grid_configure(padx=10, pady=5)

    # Button
    button = tkinter.Button(frame1, text="Login", command=lambda: login(username_entry.get(), password_entry.get()))
    button.grid(row=3, column=0, sticky="news", padx=20, pady=10)


ing_list = dict()


def check_data(t1, t2, t3):
    if t1[0] == "" or t1[2] == "" or not all(ing for ing in t2) or t3[0] == "" or any(ch.isdigit() for ch in t1[0]) or \
            any(str(ch).isalpha() for ch in t2.values()):
        return False
    return True


def insert_data(t1, t2, t3):
    # Prelucram datele ce vor fi introduse in baza de date
    t1 = list(f"'{st}'" for st in t1)
    print(t1)
    print(t2)
    print(t3)

    # daca datele sunt introduse incorect -> eroare
    if check_data(t1, t2, t3):
        # sa aflam id-ul maxim folosit
        id_list = list()
        with conn.cursor() as cursor:
            for row in cursor.execute(
                    f"select recipe_id from recipes"):
                id_list.append(row[0])
        last_id = max(id_list) + 1

        # Pentru retete
        c.execute(
            f'''INSERT INTO recipes(recipe_id, recipe_name, recipe_dir, recipe_type) values({last_id}, {t1[0]}, {t1[1]}, {t1[2]})''')

        # Pentru ingrediente
        for ing_name, qty in t2.items():
            ing_name = f"'{ing_name}'"
            c.execute(f'''INSERT INTO ingredients values({last_id}, {ing_name}, {int(qty)})''')

        # Pentru valori nutritionale
        c.execute(f'''INSERT INTO NUTRITIONAL_VALUES values({last_id}, {int(t3[0])}, {int(t3[1])}, {int(t3[2])})''')

        conn.commit()

        # pentru a determina scorul retetei
        recipe_scores = list()
        with conn.cursor() as cursor:
            for row in cursor.execute(
                    f'select n.nutri_score, n.nutri_multiplier from nutriscore n, recipes r where '
                    f'r.recipe_type = n.recipe_type and r.recipe_id = {last_id}'):
                recipe_scores.append(row[0])
                recipe_scores.append(row[1])
        with conn.cursor() as cursor:
            for row in cursor.execute(
                    f'select n.calories, n.fats, n.sodium from NUTRITIONAL_VALUES n, recipes r where '
                    f'r.recipe_id = n.recipe_id'):
                recipe_scores.append(row[0])
                recipe_scores.append(row[1])
                recipe_scores.append(row[2])
        recipe_score = recipe_scores[0] * recipe_scores[1] + recipe_scores[2] / 10 + recipe_scores[3] + recipe_scores[
            4] / 10
        print(recipe_score)
        c.execute(f"update recipes set recipe_nutri_score = {int(recipe_score)} where recipe_id = {last_id}")

        conn.commit()
        ing_dict = dict()
        load_frame2()
    else:
        popup_eroare("Ati introdus datele gresit!")


def add_ing(ing, qty):
    if not qty.strip().isnumeric() or ing.strip() == '':
        popup_eroare("Informatii introduse eronat")
    else:
        ing_list[ing] = qty


def disp_info(info, to_disp, text_box, lower_lim="", upper_limit=""):
    text_box.delete('1.0', tkinter.END)
    final_str = ''
    directions_str = ''
    recipes_dict = dict()

    if lower_lim != '' or upper_limit != '':
        if not lower_lim.strip().isnumeric() or not upper_limit.strip().isnumeric():
            popup_eroare("Limitele trebuie sa contina doar numere")
            return
    if info == "" or info == "''" or to_disp == "":
        popup_eroare("Info incorecte")
    else:
        if to_disp == "recipe":
            sql_query = f"select r.recipe_name, r.recipe_dir, i.ing_name, i.ing_qty from recipes r, ingredients i " \
                        f"where r.recipe_id = i.recipe_id and r.recipe_id = {info} "
        elif to_disp == "score":
            sql_query = f"select r.recipe_name,i.ing_name, i.ing_qty from recipes r, ingredients i " \
                        f"where r.recipe_id = i.recipe_id and r.recipe_nutri_score between {lower_lim} and {upper_limit} "
        else:
            sql_query = f"select r.recipe_name, i.ing_name, i.ing_qty from recipes r, ingredients i where r.recipe_id " \
                        f"= i.recipe_id and r.recipe_type = {info} "
        with conn.cursor() as cursor:
            for row in cursor.execute(sql_query):
                if row[1] not in directions_str and to_disp == "recipe":
                    directions_str = row[1]
                if row[0] not in recipes_dict:
                    recipes_dict[row[0]] = list()
                if to_disp == "recipe":
                    recipes_dict[row[0]].append((row[2], str(row[3])))
                else:
                    recipes_dict[row[0]].append((row[1], str(row[2])))

        for recipe, ingredients in recipes_dict.items():
            final_str += f"Reteta: {recipe} cu ingredientele:\n "
            for ing in ingredients:
                final_str += f"\t{ing[0]} - {ing[1]}\n"
            if to_disp == "recipe":
                final_str += directions_str

        text_box.insert(tkinter.END, final_str)


def update_cell(update_id, col, new_val):
    if col.strip() == '' or new_val.strip() == '':
        popup_eroare("Selectati o coloana/date corecte")
        return
    if type(new_val) is str:
        new_val = f"'{new_val}'"
    if col == "Recipe name":
        col = "recipe_name"
    elif col == "Directions":
        col = "recipe_dir"
    elif col == "Change ingredient":
        col = "ing"
    if col == "ing":
        # TO DO
        pass
    else:
        with conn.cursor() as cursor:
            cursor.execute(f'update recipes set {col} = {new_val} where recipe_id = {update_id}')
    conn.commit()


def delete_cell(delete_id):
    if not isinstance(delete_id, int):
        popup_eroare("Selectati o coloana/date corecte")
    else:
        with conn.cursor() as cursor:
            cursor.execute(f'delete from recipes where recipe_id = {delete_id}')
        conn.commit()


def load_frame2():
    clear_widgets(frame1)
    frame2.tkraise()

    # Saving Recipes (name and description)
    recipe_frame = tkinter.LabelFrame(frame2, text="Recipes")
    recipe_frame.grid(row=0, column=0, padx=20, pady=10)

    recipe_name_label = tkinter.Label(recipe_frame, text="Recipe name")
    recipe_name_label.grid(row=0, column=0)
    description_label = tkinter.Label(recipe_frame, text="Short description")
    description_label.grid(row=0, column=1)

    recipe_name_entry = tkinter.Entry(recipe_frame)
    description_entry = tkinter.Entry(recipe_frame)
    recipe_name_entry.grid(row=1, column=0)
    description_entry.grid(row=1, column=1)

    type_list = list()
    with conn.cursor() as cursor:
        for row in cursor.execute("select recipe_type from nutriscore"):
            type_list.append(row[0])

    type_label = tkinter.Label(recipe_frame, text="Type of recipe")
    type_combobox = ttk.Combobox(recipe_frame, values=type_list)
    type_label.grid(row=0, column=2)
    type_combobox.grid(row=1, column=2)

    for widget in recipe_frame.winfo_children():
        widget.grid_configure(padx=10, pady=5)

    # Saving Ingredients into a list
    ingredients_frame = tkinter.LabelFrame(frame2, text="Add Ingredient")
    ingredients_frame.grid(row=0, column=1, sticky="news", padx=20, pady=10)

    ingredients_label = tkinter.Label(ingredients_frame, text="Ingredient")
    ingredients_label.grid(row=0, column=0)
    quantity_label = tkinter.Label(ingredients_frame, text="Quantity")
    quantity_label.grid(row=0, column=1)

    ingredient_entry = tkinter.Entry(ingredients_frame)
    quantity_entry = tkinter.Entry(ingredients_frame)
    ingredient_entry.grid(row=1, column=0)
    quantity_entry.grid(row=1, column=1)

    add_ing_button = tkinter.Button(ingredients_frame, text="Add ingredient to recipe",
                                    command=lambda: add_ing(ingredient_entry.get(), quantity_entry.get()))
    add_ing_button.grid(row=1, column=2)

    for widget in ingredients_frame.winfo_children():
        widget.grid_configure(padx=10, pady=5)

    # For nutrition
    nutrition_frame = tkinter.LabelFrame(frame2, text="Nutrition values")
    nutrition_frame.grid(row=1, column=0, padx=20, pady=10)

    calories_label = tkinter.Label(nutrition_frame, text="Total number of calories")
    calories_label.grid(row=0, column=0)
    fat_label = tkinter.Label(nutrition_frame, text="Total fat used")
    fat_label.grid(row=0, column=1)
    sodium_label = tkinter.Label(nutrition_frame, text="Total sodium used")
    sodium_label.grid(row=0, column=2)

    calories_entry = tkinter.Entry(nutrition_frame)
    fat_entry = tkinter.Entry(nutrition_frame)
    sodium_entry = tkinter.Entry(nutrition_frame)
    calories_entry.grid(row=1, column=0)
    fat_entry.grid(row=1, column=1)
    sodium_entry.grid(row=1, column=2)

    for widget in nutrition_frame.winfo_children():
        widget.grid_configure(padx=10, pady=5)

    # For updating tabels
    update_frame = tkinter.LabelFrame(frame2, text="Updating recipes")
    update_frame.grid(row=3, column=0, padx=20, pady=10)

    update_name_label = tkinter.Label(update_frame, text="Name of the recipe")
    update_name_label.grid(row=0, column=0)
    update_info_label = tkinter.Label(update_frame, text="To modify")
    update_info_label.grid(row=0, column=1)

    elem_list = dict()
    with conn.cursor() as cursor:
        for row in cursor.execute("select * from recipes"):
            elem_list[row[1]] = row[0]

    update_recipe_combobox = ttk.Combobox(update_frame, values=list(elem_list.keys()))
    update_recipe_combobox.grid(row=1, column=0)

    update_info_combobox = ttk.Combobox(update_frame, values=['Recipe name', 'Directions', 'Change ingredient'])
    update_info_combobox.grid(row=1, column=1)

    update_text_box = Text(update_frame, height=1, width=17)
    update_text_box.grid(row=2, column=0)

    update_recipe_button = tkinter.Button(update_frame, text="Update",
                                          command=lambda: update_cell(elem_list[update_recipe_combobox.get()] if
                                                                      update_recipe_combobox.get() in elem_list else '',
                                                                      update_info_combobox.get(),
                                                                      update_text_box.get("1.0", tkinter.END)))
    update_recipe_button.grid(row=3, column=0, sticky="news", padx=20, pady=10)
    remove_recipe_button = tkinter.Button(update_frame, text="Remove recipe",
                                          command=lambda: delete_cell(elem_list[update_recipe_combobox.get()] if
                                                                      update_recipe_combobox.get() in elem_list else ''))
    remove_recipe_button.grid(row=3, column=1, sticky="news", padx=20, pady=10)

    for widget in update_frame.winfo_children():
        widget.grid_configure(padx=10, pady=5)

    # For displaying info
    disp_frame = tkinter.LabelFrame(frame2, text="Informations")
    disp_frame.grid(row=3, column=1, padx=20, pady=10)

    name_label = tkinter.Label(disp_frame, text="Name of the recipe")
    name_label.grid(row=0, column=0)
    info_label = tkinter.Label(disp_frame, text="Information to search for")
    info_label.grid(row=0, column=1)
    lower_label = tkinter.Label(disp_frame, text="Lower limit for score")
    lower_label.grid(row=0, column=2)
    upper_label = tkinter.Label(disp_frame, text="Upper limit for score")
    upper_label.grid(row=2, column=2)

    lower_text_box = Text(disp_frame, height=1, width=17)
    lower_text_box.grid(row=1, column=2)
    upper_text_box = Text(disp_frame, height=1, width=17)
    upper_text_box.grid(row=3, column=2)

    elem_list = dict()
    with conn.cursor() as cursor:
        for row in cursor.execute("select * from recipes"):
            elem_list[row[1]] = row[0]

    recipe_combobox = ttk.Combobox(disp_frame, values=list(elem_list.keys()))
    recipe_combobox.grid(row=1, column=0)

    type_list.append("By score")
    info_combobox = ttk.Combobox(disp_frame, values=type_list)
    info_combobox.grid(row=1, column=1)

    disp_type_text_box = Text(frame2, height=10, width=50)
    disp_type_text_box.grid(row=4, column=1)

    disp_recipe_text_box = Text(frame2, height=10, width=50)
    disp_recipe_text_box.grid(row=4, column=0)

    disp_recipe_button = tkinter.Button(disp_frame, text="Afisare reteta",
                                        command=lambda: disp_info(
                                            elem_list[recipe_combobox.get()] if recipe_combobox.get() else "", "recipe",
                                            disp_recipe_text_box))
    disp_recipe_button.grid(row=2, column=0, sticky="news", padx=20, pady=10)

    disp_type_button = tkinter.Button(disp_frame, text="Afisare dupa informatii",
                                      command=lambda: disp_info(f"'{info_combobox.get()}'", "type", disp_type_text_box))
    disp_type_button.grid(row=2, column=1, sticky="news", padx=20, pady=10)

    disp_score_button = tkinter.Button(disp_frame, text="Afisare dupa scor",
                                       command=lambda: disp_info("-",
                                                                 "score",
                                                                 disp_type_text_box,
                                                                 lower_text_box.get("1.0", tkinter.END),
                                                                 upper_text_box.get("1.0", tkinter.END)))
    disp_score_button.grid(row=3, column=0, sticky="news", padx=20, pady=10)

    for widget in disp_frame.winfo_children():
        widget.grid_configure(padx=10, pady=5)

    # Button
    insert_data_button = tkinter.Button(frame2, text="Enter data", command=lambda: insert_data([recipe_name_entry.get(),
                                                                                                description_entry.get(),
                                                                                                type_combobox.get()],
                                                                                               ing_list,
                                                                                               [calories_entry.get(),
                                                                                                fat_entry.get(),
                                                                                                sodium_entry.get()]
                                                                                               ))
    insert_data_button.grid(row=1, column=1, sticky="news", padx=20, pady=10)

    return_button = tkinter.Button(frame2, text="Return to login screen", command=lambda: load_frame1())
    return_button.grid(row=6, column=0, sticky="news", padx=20, pady=10)
    refresh_button = tkinter.Button(frame2, text="Refresh", command=lambda: load_frame2())
    refresh_button.grid(row=6, column=1, sticky="news", padx=20, pady=10)


if __name__ == "__main__":
    root = tkinter.Tk()

    root.title("Recipe database")
    root.eval("tk::PlaceWindow . center")

    frame1 = tkinter.Frame(root)
    frame1.pack()

    frame2 = tkinter.Frame(root)
    frame2.pack()

    load_frame1()

    root.mainloop()

# scores_dict = dict()
#     with conn.cursor() as cursor:
#         for row in cursor.execute(
#                 '''select
#                 r.recipe_id, n.nutri_score, n.nutri_multiplier
#                 from nutriscore n, recipes r
#                 where r.recipe_type = n.recipe_type'''):
#             scores_dict[row[0]] = (row[1], row[2])
