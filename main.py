import requests
import logging
import random
import math
from tkinter import *
from functools import partial

class Player:
    def __init__(self, username, stats):
        self.username = username
        self.stats = stats
        self.percentiles = {}
        # Calculate KD for random players
        if 'kills' in stats and 'deaths' in stats and stats['deaths'] != 0:
            self.stats['kd'] = round(stats['kills'] / stats['deaths'], 3)
        else:
            self.stats['kd'] = 0


def generate_random_player_stats():
    kills = random.randint(100, 6000)
    deaths = random.randint(100, 6000)
    return {
        'score': random.randint(1000, 30000),
        'scorePerMin': round(random.uniform(10, 30), 3),
        'scorePerMatch': round(random.uniform(1, 5), 3),
        'wins': random.randint(0, 500),
        'top3': random.randint(0, 1000),
        'top5': random.randint(0, 2000),
        'top6': random.randint(0, 3000),
        'top10': random.randint(0, 5000),
        'top12': random.randint(0, 4000),
        'top25': random.randint(0, 6000),
        'kills': kills,
        'killsPerMin': round(random.uniform(1, 6), 3),
        'killsPerMatch': round(random.uniform(0.1, 1), 3),
        'deaths': deaths,
        # KD is calc
    }


def get_fortnite_player_stats(account_name, account_type, time_window, access_key):
    url = 'https://fortnite-api.com/v2/stats/br/v2'
    headers = {'Authorization': access_key}
    params = {'name': account_name, 'accountType': account_type, 'timeWindow': time_window}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        if 'data' in data and 'stats' in data['data'] and 'all' in data['data']['stats'] and 'overall' in \
                data['data']['stats']['all']:
            return data['data']['stats']['all']['overall']
        else:
            return None
    else:
        logging.error(f"Error: {response.status_code}")
        logging.error(f"Response: {response.text}")
        return None


def calculate_composite_score(stats):
    weights = {
        'score': 1, 'scorePerMin': 1, 'scorePerMatch': 1,
        'wins': 1, 'top3': 1, 'top5': 1, 'top6': 1, 'top10': 1, 'top12': 1, 'top25': 1,
        'kills': 1, 'killsPerMin': 1, 'killsPerMatch': 1, 'deaths': -1
    }
    return sum(stats.get(stat, 0) * weight for stat, weight in weights.items())


access_key = '6eb41c90-acfc-49f4-87ac-c915cd8c950f'


def merge_sort(arr, key=lambda x: x):
    if len(arr) > 1:
        mid = len(arr) // 2
        L = arr[:mid]

        R = arr[mid:]

        merge_sort(L, key)

        merge_sort(R, key)

        i = j = k = 0

        while i < len(L) and j < len(R):

            if key(L[i]) < key(R[j]):

                arr[k] = L[i]

                i += 1
            else:
                arr[k] = R[j]
                j += 1

            k += 1

        while i < len(L):
            arr[k] = L[i]
            i += 1
            k += 1

        while j < len(R):
            arr[k] = R[j]

            j += 1
            k += 1


def heapify(arr, n, i, key):
    largest = i

    left = 2 * i + 1

    right = 2 * i + 2

    if left < n and key(arr[left]) > key(arr[largest]):
        largest = left

    if right < n and key(arr[right]) > key(arr[largest]):
        largest = right

    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]

        heapify(arr, n, largest, key)


def heap_sort(arr, key=lambda x: x):
    n = len(arr)

    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i, key)

    for i in range(n - 1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]
        heapify(arr, i, 0, key)


num_players = 100000
players = [Player(f"Player{i + 1}", generate_random_player_stats()) for i in range(num_players)]


player_ui_data = {
    "rank": {},
    "stats": {},
    "percentiles": {}
}

def process(account_name, account_type):
    global player_ui_data
    percentiles= {}
    time_window = 'lifetime'
    # Fetch
    real_player_stats = get_fortnite_player_stats(account_name, account_type, time_window, access_key)
    if real_player_stats:
        real_player = Player(account_name, real_player_stats)
        players.append(real_player)
        # Calculate composite
        for player in players:
            player.composite_score = calculate_composite_score(player.stats)

        # Sort players using Heap Sort
        heap_sort(players, key=lambda x: x.composite_score)

        # Determine rank
        real_player_rank = next((i for i, p in enumerate(players, start=1) if p.username == account_name), None)

        # Find percentile using Merge Sort
        percentiles = {}
        for category in  {
        'score', 'scorePerMin', 'scorePerMatch',
        'wins', 'top3', 'top5', 'top6', 'top10', 'top12', 'top25',
        'kills', 'killsPerMin', 'killsPerMatch', 'deaths', 'kd', 'matches', 'winrate', 'minutesplayed', 'playersoutlived'
    }:
            merge_sort(players, key=lambda x: x.stats.get(category, 0))
            total_players = len(players)
            for i, player in enumerate(players):
                if player.username == account_name:
                    # Changed percentile calculation
                    percentile = 100 * i / total_players
                    percentiles[category] = round(percentile, 2)  # Round to 2 decimal places
                    break

        # Update player_ui_data directly
        player_ui_data['rank'] = real_player_rank
        player_ui_data['stats'] = real_player_stats
        player_ui_data['percentiles'] = percentiles
        return real_player_stats, percentiles
    else:
        return {}, {}



def update_ui(account_name, account_type):
    real_player_stats, percentiles = process(account_name, account_type)

    # Clear existing labels in statsframe if necessary
    for widget in statsframe.winfo_children():
        widget.destroy()

    for i, (stat, stat_value) in enumerate(real_player_stats.items()):
        percentile = percentiles.get(stat, None)
        label_text = f'{stat.capitalize()}: {stat_value} Percentile: {percentile}'
        if percentile is not None:
            label_text += f', {percentile}th percentile'
        row = i // 3
        column = i % 3
        Label(statsframe, text=label_text, background="gray74", borderwidth=1, relief="solid").grid(row=row, column=column, pady=20)


# start the window
root = Tk()
root.geometry("1000x800")
root.title("Fortnite Stats")
root['bg'] = '#1A1A1A'

L1 = Label(root, text="Username: ", borderwidth=1, relief="solid")
L1.place(x=275, y=10)
L2 = Label(root, text="psn/epic/xbl :", borderwidth=1, relief="solid")
L2.place(x=320, y=50)
#Entry box, access sting in box with entry.get()
entry = Entry(root,width=50)
entry.pack(padx=10, pady=10)
accountEntry = Entry(root, width=30)
accountEntry.pack(padx=10, pady=10)


#button does nothing at the moment
btn1 = Button(root, text="Search", padx=10, pady=5, command=partial(update_ui,entry.get(), accountEntry.get()))
btn1.pack()

def on_button_click():
    account_name = entry.get()  # Get the current value from the entry field
    account_type = accountEntry.get()
    update_ui(account_name, account_type)  # Update the UI with the current account name


btn1.config(command=on_button_click)





# Store the stats, percentiles, and rank in a dictionary for UI access



# Display the stats API player
#print(f"Stats and Percentiles for player {account_name} (Rank: {real_player_rank}):")
#for stat in real_player_stats:
 #   percentile = percentiles.get(stat, None)
  #  stat_value = real_player_stats[stat]
   # print(
    #    f"{stat.capitalize()}: {stat_value}, {percentile:.2f}th percentile" if percentile else f"{stat.capitalize()}: {stat_value}")



#frame where stats go, seperated into columns
statsframe = Frame(root)
statsframe.columnconfigure(0, weight=1)
statsframe.columnconfigure(1, weight=1)
statsframe.columnconfigure(2, weight=1)

#draws stats as labels goes down a row every 3 stats, prints into columns 0 1 &2

#draw the frame with stats
statsframe.pack(fill='x', pady= 5)

#window loop
root.mainloop()