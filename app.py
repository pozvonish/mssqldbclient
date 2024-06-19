import flet as ft
from database import *

conn = None
current_table = None
e_for_refresh = None
user_roles = None


def mainpage_view(mainpage: ft.Page):
    mainpage.window_center()
    mainpage.window_height=550
    mainpage.window_width=1000
    mainpage.window_resizable=True
    mainpage.vertical_alignment = ft.MainAxisAlignment.CENTER
    mainpage.scroll=ft.ScrollMode.AUTO

    db_objects = get_db_objects(conn)
    t = []
    o = []
    p = []
    z = []
    for result in db_objects['results']:
        if result['ObjectType'] in 'U V ' and result['ObjectName'] not in t:
            t.append(result['ObjectName'])
        elif result['ObjectType'] in 'P ' and result['ObjectName'] not in p:
            p.append(result['ObjectName'])
        elif result['ObjectType'] in 'IF ' and result['ObjectName'] not in z:
            z.append(result['ObjectName'])

    appbar_text_ref = ft.Ref[ft.Text]()


    def show_table(results_dict):
        if results_dict == 'NO RESULTS':
            table = ft.Text("ПУСТО")

            cv = ft.Column([table],scroll=True)

            if len(mainpage.controls) == 2:
                mainpage.controls.pop()
            mainpage.add(ft.Row([cv],scroll=True))

            if len(menubar.controls) == 4:
                menubar.controls.pop()      
        else:
            table = ft.DataTable(
                    columns = [
                        ft.DataColumn(
                            ft.Text(key)
                            ) for key in results_dict['keys']
                        ],
                    rows = [
                        ft.DataRow(
                            cells = [
                                ft.DataCell(
                                    ft.Text(value=result[key])
                                ) for key in results_dict['keys']
                            ]
                        ) for result in results_dict['results']
                    ],
                    border=ft.border.all(2), )

            cv = ft.Column([table],scroll=True)

            if len(mainpage.controls) == 2:
                mainpage.controls.pop()
            mainpage.add(ft.Row([cv],scroll=True))

            if len(menubar.controls) == 4:
                menubar.controls.pop()

            menubar.controls.append(
                ft.MenuItemButton(
                    content=ft.Text("Редактировать"),
                    on_click=handle_edit_mode_click
                ),
            )
            print(mainpage.controls, len(mainpage.controls))
        

    def show_editable_table(results_dict, e):
        if results_dict == 'NO RESULTS':
            table = ft.Text("ПУСТО")

            cv = ft.Column([table],scroll=True)

            if len(mainpage.controls) == 2:
                mainpage.controls.pop()
            mainpage.add(ft.Row([cv],scroll=True))

            if len(menubar.controls) == 4:
                menubar.controls.pop()
        else:
            table = ft.DataTable(
                    columns = [
                        ft.DataColumn(
                            ft.Text(key)
                            ) for key in results_dict['keys']
                        ],
                    rows = [
                        ft.DataRow(
                            cells = [
                                ft.DataCell(
                                    ft.Text(value=result[key]), on_tap=lambda e=e, TABLENAME=current_table, current_key=key, VALUES=result: editor_dialog(e, TABLENAME, VALUES, current_key, e.control.content.value)
                                ) for key in results_dict['keys']
                            ]
                        ) for result in results_dict['results']
                    ],
                    border=ft.border.all(2), )
            
            actions = ft.DataTable(
                    columns = [
                        ft.DataColumn(
                            ft.Text('Действия')
                            )
                        ],
                    rows = [
                        ft.DataRow(
                            cells = [
                                ft.DataCell(
                                    ft.ElevatedButton(text='Удалить', on_click=lambda e=e, VALUES=result: delete_(e, VALUES))
                                )
                            ]
                        ) for result in results_dict['results']
                    ],
                    border=ft.border.all(2), )

            cv = ft.Column([table],scroll=True)

            if len(mainpage.controls) == 2:
                mainpage.controls.pop()
            mainpage.add(ft.Row([cv, actions],scroll=True))

            if len(menubar.controls) == 4:
                menubar.controls.pop()

            menubar.controls.append(
                ft.MenuItemButton(
                    content=ft.Text("Добавить строку"),
                    on_click = lambda e=e, TABLENAME=current_table, KEYS=results_dict['keys']: add_dialog(e, TABLENAME, KEYS)         
                ),
            )


    def handle_table_menu_item_click(e):
        global current_table, e_for_refresh
        e_for_refresh = e

        print(f"{e.control.content.value}.on_click")
        mainpage.show_snack_bar(ft.SnackBar(content=ft.Text(f"{e.control.content.value}")))
        appbar_text_ref.current.value = e.control.content.value

        results_dict = get_table(conn, e.control.content.value)

        show_table(results_dict)

        current_table = e.control.content.value

        mainpage.update()


    def handle_edit_mode_click(e):
        global current_table

        print(f"{e.control.content.value}.on_click")
        mainpage.show_snack_bar(ft.SnackBar(content=ft.Text(f"Редактирование {current_table}")))
        appbar_text_ref.current.value = f"Редактирование {current_table}"

        results_dict = get_table(conn, current_table)
        
        show_editable_table(results_dict, e)

        mainpage.update()


    def handle_on_open(e):
        print(f"{e.control.content.value}.on_open")


    def handle_on_close(e):
        print(f"{e.control.content.value}.on_close")


    def handle_on_hover(e):
        print(f"{e.control.content.value}.on_hover")


    def editor_dialog(e, TABLENAME, VALUES, current_key, current_value):
        def close_dlg(e):
            dlg.open = False
            mainpage.update()
        

        def update_(e):
            global e_for_refresh
            if new_value_field.value:
                result = update_value_in_table(conn, TABLENAME, VALUES, current_key, new_value_field.value)
                if result == 0:
                    dlg.open = False
                    handle_edit_mode_click(e_for_refresh)
                    mainpage.show_snack_bar(ft.SnackBar(content=ft.Text(f"Успешно"), bgcolor=ft.colors.GREEN_100))
                else:
                    mainpage.show_snack_bar(ft.SnackBar(content=ft.Text(f"Ошибка"), bgcolor=ft.colors.RED_100))
            else:
                mainpage.show_snack_bar(ft.SnackBar(content=ft.Text(f"Введите новое значение"), bgcolor=ft.colors.YELLOW_100))


        new_value_field = ft.TextField(hint_text="Новое значение")
        dlg = ft.AlertDialog(
            title=ft.Text("Изменение значения"), on_dismiss=close_dlg,
            content=ft.Column(controls=[ft.TextField(value=current_value, read_only=True), new_value_field], height = 140),
            actions= [ft.ElevatedButton(text="Изменить", on_click=update_)],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            actions_padding=ft.padding.only(bottom=20,left=0, right=0, top=0),
            content_padding=ft.padding.only(bottom=0, left=20, right=20, top=20)
    )
        
        mainpage.dialog = dlg
        dlg.open = True
        mainpage.update()


    def handle_function_menu_item_click(e):
        results_dict = get_table_func_params(conn, e.control.content.value)
        current_func = e.control.content.value

        print(f"{e.control.content.value}.on_click")
        mainpage.show_snack_bar(ft.SnackBar(content=ft.Text(f"{e.control.content.value}")))
        appbar_text_ref.current.value = e.control.content.value

        def close_dlg(e):
            dlg.open = False
            mainpage.update()

        def exec_F(e):
            check = False
            without_params = False
            VALUES = []

            if values_fields:
                for field in values_fields:
                    if field.value:
                        check = True
                        VALUES.append(field.value)
                    else:
                        check = False
            else:
                without_params = True

            if check or without_params:
                results = exec_table_func(conn, current_func, VALUES, results_dict)
                if results:
                    if not without_params:
                        dlg.open = False
                    show_table(results)
                    mainpage.show_snack_bar(ft.SnackBar(content=ft.Text(f"Успешно"), bgcolor=ft.colors.GREEN_100))
                else:
                    mainpage.show_snack_bar(ft.SnackBar(content=ft.Text(f"Ошибка"), bgcolor=ft.colors.RED_100))
            else:
                mainpage.show_snack_bar(ft.SnackBar(content=ft.Text(f"Введите параметры запроса"), bgcolor=ft.colors.YELLOW_100))

        if results_dict:
            values_fields = [
                ft.TextField(hint_text=f"{result['Name']}") for result in results_dict
                ]

            dlg = ft.AlertDialog(
                title=ft.Text("Запрос"), on_dismiss=close_dlg,
                content=ft.Column(controls=values_fields, height = 70 * len(results_dict), scroll=True),
                actions= [ft.ElevatedButton(text="Отправить", on_click=exec_F)],
                actions_alignment=ft.MainAxisAlignment.CENTER,
                actions_padding=ft.padding.only(bottom=20,left=0, right=0, top=0),
                content_padding=ft.padding.only(bottom=0, left=20, right=20, top=20)
        )
            
            mainpage.dialog = dlg
            dlg.open = True
        else:
            values_fields = []
            exec_F(e)

        mainpage.update()
        

    
    def add_dialog(e, TABLENAME, KEYS):
        def close_dlg(e):
            dlg.open = False
            mainpage.update()
        
        
        def add_(e):
            global e_for_refresh
            check = False

            VALUES = {}

            for field, dict_key in zip(values_fields, KEYS):
                if field.value:
                    check = True
                    VALUES[dict_key] = field.value
                else:
                    check = False

            if check:
                result = add_to_table(conn, TABLENAME, VALUES)
                if result == 0:
                    dlg.open = False
                    handle_edit_mode_click(e_for_refresh)
                    mainpage.show_snack_bar(ft.SnackBar(content=ft.Text(f"Успешно"), bgcolor=ft.colors.GREEN_100))
                else:
                    mainpage.show_snack_bar(ft.SnackBar(content=ft.Text(f"Ошибка"), bgcolor=ft.colors.RED_100))
            else:
                mainpage.show_snack_bar(ft.SnackBar(content=ft.Text(f"Введите новую строку"), bgcolor=ft.colors.YELLOW_100))

        values_fields = [
            ft.TextField(hint_text=f"{key}") for key in KEYS
            ]

        dlg = ft.AlertDialog(
            title=ft.Text("Добавление новой строки"), on_dismiss=close_dlg,
            content=ft.Column(controls=values_fields, height = 70 * len(KEYS), scroll=True),
            actions= [ft.ElevatedButton(text="Добавить", on_click=add_)],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            actions_padding=ft.padding.only(bottom=20,left=0, right=0, top=0),
            content_padding=ft.padding.only(bottom=0, left=20, right=20, top=20)
    )
        
        mainpage.dialog = dlg
        dlg.open = True
        mainpage.update()


    def delete_(e, VALUES):
        global e_for_refresh
        result = delete_from_table(conn, current_table, VALUES)
        if result == 0:
            handle_edit_mode_click(e_for_refresh)
            mainpage.show_snack_bar(ft.SnackBar(content=ft.Text(f"Успешно"), bgcolor=ft.colors.GREEN_100))
        else:
            mainpage.show_snack_bar(ft.SnackBar(content=ft.Text(f"Ошибка"), bgcolor=ft.colors.RED_100))

    mainpage.appbar = ft.AppBar(
        title=ft.Text("COMPANY", ref=appbar_text_ref),
        center_title=True,
    )


    menubar = ft.MenuBar(
        expand=True,
        style=ft.MenuStyle(
            alignment=ft.alignment.top_left,
            mouse_cursor={ft.MaterialState.HOVERED: ft.MouseCursor.WAIT,
                          ft.MaterialState.DEFAULT: ft.MouseCursor.ZOOM_OUT},
        ),
        controls=[
            ft.SubmenuButton(
                content=ft.Text("Таблицы"),
                on_open=handle_on_open,
                on_close=handle_on_close,
                on_hover=handle_on_hover,
                controls=[
                    ft.MenuItemButton(
                        content=ft.Text(f"{name}"),
                        leading=ft.Icon(ft.icons.INFO),
                        on_click=handle_table_menu_item_click
                    ) for name in t
                ]
            ),
            ft.SubmenuButton(
                content=ft.Text("Хранимые процедуры"),
                on_open=handle_on_open,
                on_close=handle_on_close,
                on_hover=handle_on_hover,
                controls=[
                    ft.MenuItemButton(
                        content=ft.Text(f"{name}"),
                        leading=ft.Icon(ft.icons.INFO),
                        on_click=handle_function_menu_item_click
                    ) for name in p
                ]
            ),
            ft.SubmenuButton(
                content=ft.Text("Запросы/Отчеты"),
                on_open=handle_on_open,
                on_close=handle_on_close,
                on_hover=handle_on_hover,
                controls=[
                    ft.MenuItemButton(
                        content=ft.Text(f"{name}"),
                        leading=ft.Icon(ft.icons.INFO),
                        on_click=handle_function_menu_item_click
                    ) for name in z
                ]
            ),
        ]
    )


    mainpage.add(
        ft.Row([menubar]),
    )


def auth_view(auth_page: ft.Page):
    auth_page.window_center()
    auth_page.window_height=600
    auth_page.window_width=600
    auth_page.window_resizable=False
    auth_page.vertical_alignment = ft.MainAxisAlignment.CENTER

    USERNAME = ft.TextField(label="Имя входа", width=300)
    PASSWORD = ft.TextField(label="Пароль",password=True, can_reveal_password=True, width=300)
    MESSAGE = ft.Text(value="")


    def connect(e):
        global conn
        conn = connect_to_db(USERNAME.value, PASSWORD.value)
        if not (conn):
            MESSAGE.value='Ошибка соединения'
            MESSAGE.color='red'
            auth_page.update()
        else:
            MESSAGE.value=''
            MESSAGE.color='green'
            auth_page.update()
            auth_page.window_close()


    auth_page.add(
        ft.Row([
            ft.Column([
                USERNAME, PASSWORD
            ])
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([
            ft.ElevatedButton("Присоединиться", on_click=connect)
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([
            MESSAGE
        ], alignment=ft.MainAxisAlignment.CENTER)
    )


def admin_page_view(admin_page: ft.Page):
    admin_page.window_center()
    admin_page.window_height=550
    admin_page.window_width=1000
    admin_page.window_resizable=True
    admin_page.vertical_alignment = ft.MainAxisAlignment.CENTER
    admin_page.scroll=ft.ScrollMode.AUTO

    QUERY = ft.TextField(hint_text="Запрос", autofocus=True, multiline=True, width=800, min_lines=7, max_lines=7)
    RESULT = ft.TextField(hint_text="Результат", read_only=True, autofocus=True, multiline=True, width=800, min_lines=7, max_lines=7)

    def admin_show_table(results_dict):
        if len(admin_page.controls) == 4:
            admin_page.controls.pop()

        if results_dict == 'NO RESULTS':
            table = ft.Text("ПУСТО")
            cv = ft.Column([table],scroll=True)    
        else:
            table = ft.DataTable(
                    columns = [
                        ft.DataColumn(
                            ft.Text(key)
                            ) for key in results_dict['keys']
                        ],
                    rows = [
                        ft.DataRow(
                            cells = [
                                ft.DataCell(
                                    ft.Text(value=result[key])
                                ) for key in results_dict['keys']
                            ]
                        ) for result in results_dict['results']
                    ],
                    border=ft.border.all(2), )

            cv = ft.Column([table],scroll=True)

            admin_page.add(ft.Row([cv],scroll=True, alignment=ft.MainAxisAlignment.CENTER))

    def query(e):
        results = query_to_db(conn, QUERY.value)
        if results == 0:
            if len(admin_page.controls) == 4:
                admin_page.controls.pop()
            RESULT.value = "Успешно выполнено."
            print(RESULT.value)
            admin_page.update
        elif type(results) == dict or results == 'NO RESULTS':
            RESULT.value = "Успешно выполнено."
            admin_show_table(results)
        else:
            if len(admin_page.controls) == 4:
                admin_page.controls.pop()
            RESULT.value = results
            admin_page.update()
            

    admin_page.add(
        ft.Row([
            QUERY
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([
            ft.ElevatedButton("Отправить", on_click=query)
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([
            RESULT
        ], alignment=ft.MainAxisAlignment.CENTER),
    )


ft.app(target=auth_view)
if conn:
    user_roles = get_user_roles(conn)
    is_admin = False
    for role in user_roles:
        if 'admin' in role:
            is_admin = True
            break
    if not is_admin:
        ft.app(target=mainpage_view)
    else:
        ft.app(target=admin_page_view)