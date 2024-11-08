'''Imports'''
import sqlite3
import math
import random
import smtplib
from email.message import EmailMessage


def create_db():
    '''Creation of db'''
    conn = sqlite3.connect("rps.db")
    conn.commit()
    conn.close()


def create_table_user():
    '''Creation of match database user'''
    conn = sqlite3.connect("rps.db")
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user text NOT NULL UNIQUE,
            email text NOT NULL UNIQUE,
            n_match INTENGER DEFAULT 0,
            win INTENGER DEFAULT 0,
            fail INTENGER DEFAULT 0
        )"""
    )
    conn.commit()
    conn.close()


def create_table_match():
    '''Creation of match database table'''
    conn = sqlite3.connect("rps.db")
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE match (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id integer,
            rounds integer,
            results text,
            date DATE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES user(id)
        )"""
    )
    conn.commit()
    conn.close()


def create_table_round():
    '''Creation of round database table'''
    conn = sqlite3.connect("rps.db")
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE round (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id integer,
            results text, 
            move text,
            date DATE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(match_id) REFERENCES match(id)
        )"""
    )
    conn.commit()
    conn.close()


def start_match(): #TODO REGISTER
    '''Start of the game'''
    print("\n******* Rock Paper Scissors *******\n")
    user = input("Hi! What's your name? ").lower()
    email = input("Please, tell us your email: ")

    conn = sqlite3.connect("rps.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE user = ? AND email = ?", (user, email))
    existing_user = cursor.fetchone()

    if existing_user:
        print(f"Welcome back, {user}!")
    else:
        data_users_mail(user, email)
        print(f"Welcome, {user}! Your registration was successful.")

    conn.close()
    return user, email


def data_users_mail(user, email):
    '''Register user and email data to db users table'''
    conn = sqlite3.connect("rps.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''
                       INSERT INTO users (user, email) 
                       VALUES (?, ?) 
                       ''', (user, email))
        conn.commit()
        print('User and email register correctly')
    except sqlite3.IntegrityError:
        print ('Error: user or mail not found')
        return
    finally:
        conn.close()


def match(user):
    '''Logic for one match (3 rounds)'''
    print("\nGreat! You'll be playing against the machine")
    options = ['R', 'P', 'S']
    round_results = []
    move_human = []
    match_final = []
    score = 0
    round_n = 0

    for _ in range (3):
        print('***** FIGHT *****\n')
        while True:
            try:
                move = input("Choose an option: Rock (R), Paper (P) or Scissors (S) ").upper()
                options.index(move)
            except ValueError:
                print("That is not an option. Try again")
            else:
                break

        computer_choice = random.choice(options)

        if move == computer_choice:
            print(f'{move} vs {computer_choice}. In case of a tie, the machine wins\n')
            result = 'Fail '
        elif (move == 'R' and computer_choice == 'S') or \
            (move == 'S' and computer_choice == 'P') or \
            (move == 'P' and computer_choice == 'R'):
            print(f'{move} vs {computer_choice}. You win\n')
            result = 'Win '
            score += 1
        else:
            print(f'{move} vs {computer_choice}. Machine wins\n')
            result = 'Fail '

        round_results.append(result)
        move_human.append(move)
        round_n += 1

    print("\n******* RESULTS *******\n")

    win = 0
    fail = 0

    if score >= 2:
        win += 1
        match_final.append('Win')
        print("You won the game!!!\n")
    else:
        fail += 1
        match_final.append('Fail')
        print("The machine has won\n")

    user_id, match_id = data_match(round_n, user, match_final)
    if match_id is not None:
        data_round(match_id, round_results, move_human)
    else:
        print('Error: failed to record match data')
    return win, fail, round_n, round_results, move_human, match_final, user_id


def data_match(round_n, user, match_final):
    '''Insert data to db match table---> user_id, rounds, results, move'''
    conn = sqlite3.connect("rps.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE user = ?", (user,))
        user_id_result = cursor.fetchone()
        if user_id_result is None:
            print("User not found")
            return
        user_id = user_id_result[0]
        for fin in match_final:
            cursor.execute('''
                       INSERT INTO match (user_id, rounds, results) 
                       VALUES (?, ?, ?) 
                       ''', (user_id, round_n, fin))
        match_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        print ('There was an error saving the matchs data')
    finally:
        conn.close()
    return user_id, match_id


def get_id_match():
    '''Get the matchs id'''
    conn = sqlite3.connect("rps.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''SELECT MAX(id) FROM match''')
        match_id_ = cursor.fetchone()
        if match_id_ is None:
            print("Match not found")
            conn.commit()
        else:
            match_id_ = match_id_[0]
        return match_id_
    except sqlite3.IntegrityError:
        print ('There was an error creating or getting the match')
    finally:
        conn.close()


def data_round(match_id, round_results, move_human):
    '''Insert data to db round table---> match_id, results, move'''
    #match_id = get_id_match()
    if match_id is None:
        print('Error: no match ID provided')
    conn = sqlite3.connect("rps.db")
    cursor = conn.cursor()
    try:
        for result, move in zip(round_results, move_human):
            cursor.execute('''
                            INSERT INTO round (match_id, results, move) 
                            VALUES (?, ?, ?) 
                                ''', (match_id, result, move))
            conn.commit()
            print('Round data register correctly')
    except sqlite3.IntegrityError:
        print ('Error saving the round data')
    finally:
        conn.close()


def end_match(user):
    '''Logic for the end of the game, deciding whether to play another game or not'''
    n_match = 0
    while True:
        try:
            other_match = input('Do want to play again? Yes (Y) or No (N): ').upper()
            ['Y', 'N'].index(other_match)
            if other_match == 'Y':
                # total_round = round + {round}
                n_match += 1
                match(user)
        except ValueError:
            print("That is not an option. Try again")
        else:
            if other_match == 'N':
                n_match += 1
                print('Thanks for playing!!')
                break
    return n_match


def data_users_game(n_match, win, fail, user):
    '''Insert n_match, win and fail data to db users table'''
    conn = sqlite3.connect("rps.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''
                      UPDATE users
                      SET 
                        n_match = n_match + ?, 
                        win = win + ?, 
                        fail = fail + ?
                      WHERE user = ?
                      ''', (n_match, win, fail, user))
        conn.commit()
    except sqlite3.IntegrityError:
        print ('There was an error saving the data')
    finally:
        conn.close()


def get_match_total(user):
    '''Get all match'''
    conn = sqlite3.connect("rps.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''SELECT id FROM users WHERE user=?''', (user,))
        user_id_result = cursor.fetchone()
        if user_id_result is None:
            print('NO USER')
            return None
        cursor.execute('''SELECT n_match FROM users WHERE user=?''', (user,))
        match_count = cursor.fetchone()[0]
        return match_count
    except sqlite3.IntegrityError:
        print ('The total number of matches could not be obtained')
    finally:
        conn.close()


def get_win_fail(user_id):
    '''Get number of matches won and failed'''
    conn = sqlite3.connect("rps.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''SELECT COUNT(*) FROM match WHERE user_id=? AND results="Win"''', (user_id,))
        win_count = cursor.fetchone()[0]
        cursor.execute('''SELECT COUNT(*) FROM match WHERE user_id=? AND results="Fail"''', (user_id,))
        fail_count = cursor.fetchone()[0]
        return win_count, fail_count
    except sqlite3.IntegrityError:
        print ('The total number of matches won and lost could not be obtained')
    finally:
        conn.close()


def calculate_winrate(match_count, win_count):
    '''Function to calculate the winrate'''
    winrate = round((win_count/match_count)*100)
    return winrate


def get_best_move(user_id, match_count):
    '''Get the best move'''
    conn = sqlite3.connect("rps.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''SELECT move, COUNT(move) AS win_count
                          FROM round 
                          WHERE match_id IN (SELECT id FROM match WHERE user_id=? AND results="Win")
                          GROUP BY move
                          ORDER BY win_count DESC
                          LIMIT 1''', (user_id,))
        best_winning_move = cursor.fetchone()
        if best_winning_move:
            winrate_best_move = math.floor((best_winning_move[1]/match_count)*100)
            return best_winning_move, winrate_best_move
        else:
            print("No winning plays were found for the user")
            return None, None
    except sqlite3.IntegrityError:
        print("Error in obtaining the best and worst winning play")
    finally:
        conn.close()


def get_worst_move(user_id, match_count):
    '''Get the worst move'''
    conn = sqlite3.connect("rps.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''SELECT move, COUNT(move) AS fail_count
                          FROM round 
                          WHERE match_id IN (SELECT id FROM match WHERE user_id=? AND results="Fail")
                          GROUP BY move
                          ORDER BY fail_count DESC
                          LIMIT 1''', (user_id,))
        worst_winning_move = cursor.fetchone()
        if worst_winning_move:
            winrate_worst_move = math.floor((worst_winning_move[1]/match_count)*100)
            return worst_winning_move, winrate_worst_move
        else:
            print("No failing moves found for the user")
    except sqlite3.IntegrityError:
        print("Error in obtaining the best and worst winning play")
    finally:
        conn.close()


def send_email(email, match_count, win_count, fail_count, winrate, best_winning_move, winrate_best_move, worst_winning_move, winrate_worst_move):
    '''Send email----> match'''
    HOST = "smtp.gmail.com"
    PORT = 587

    from_email = 'YOUR EMAIL'
    sPass = 'YOUR PASS'
    to_email = {email}

    if best_winning_move and len(best_winning_move) >= 2:
        best_winning_text = f"{best_winning_move[0]} with a {winrate_best_move}% success rate"
    else:
        best_winning_text = 'Data not available'

    if worst_winning_move and len(worst_winning_move) >= 2:
        worst_winning_text = f"{worst_winning_move[0]} with a {winrate_worst_move}% failure rate"
    else:
        worst_winning_text = 'Data not available'

    message_content = f"""
    Hi! Thank you for playing Rock, Paper, Scissors!

    We present you the statistics of your games:
    - Number of games played: {match_count}
    - Number of victories: {win_count}
    - Number of defeats: {fail_count}
    - Winrate: {winrate}%
    - Best move: {best_winning_text}
    - Worst move: {worst_winning_text}
    
    See you soon!!
    """

    msg = EmailMessage()
    msg['Subject'] = "Your Rock, Paper, Scissors Game Stats"
    msg['From'] = from_email
    msg['To'] = to_email
    msg.set_content(message_content)

    try:
        smtp = smtplib.SMTP(HOST, PORT)
        smtp.ehlo()
        smtp.starttls()
        smtp.login(from_email, sPass)
        smtp.send_message(msg)

    except Exception as e:
        print(f'Error sending email: {e}')
    finally:
        smtp.quit()


if __name__ == "__main__":
    # create_db()
    # create_table_user()
    # create_table_match()
    # create_table_round()
    user, email = start_match()
    win, fail, round_n, round_results, move_human, match_final, user_id = match(user)
    n_match = end_match(user)
    data_users_game(n_match, win, fail, user)
    match_count = get_match_total(user)
    win_count, fail_count = get_win_fail(user_id)
    winrate = calculate_winrate(match_count, win_count)
    best_winning_move, winrate_best_move = get_best_move(user_id, match_count)
    worst_winning_move, winrate_worst_move = get_worst_move(user_id, match_count)
    send_email(email, match_count, win_count, fail_count, winrate, best_winning_move, winrate_best_move, worst_winning_move, winrate_worst_move)
