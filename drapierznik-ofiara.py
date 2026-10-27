import pygame
import random
import sys
import math
import tkinter as tk
from tkinter import messagebox

# Globalna zmienna kontrolująca, czy chcemy zrestartować symulację
SHOULD_RESTART = False

# --- PARAMETRY SYMULACJI ---
PARAMS = {
    "V_start": 150,
    "P_start": 30,
    "max_age": 10.0,
    "starve_time": 4.0,
    "prey_offspring": 3,
    "pred_offspring": 3,
    "hunt_success": 0.35,
    "max_prey_pop": 400
}

def show_settings_window():
    """Tworzy okienko Tkinter do wprowadzania parametrów."""
    global PARAMS
    root = tk.Tk()
    root.title("Ustawienia Symulacji Lotka-Volterra")
    root.geometry("450x450")
    
    entries = {}
    fields = [
        ("V_start", "Początkowa ilość ofiar (V):", PARAMS["V_start"]),
        ("P_start", "Początkowa ilość drapieżników (P):", PARAMS["P_start"]),
        ("max_age", "Maksymalny czas życia osobników (s):", PARAMS["max_age"]),
        ("starve_time", "Czas śmierci głodowej drap. (s):", PARAMS["starve_time"]),
        ("prey_offspring", "Ilość potomstwa ofiary:", PARAMS["prey_offspring"]),
        ("pred_offspring", "Ilość potomstwa drapieżnika:", PARAMS["pred_offspring"]),
        ("hunt_success", "Skuteczność polowań (0.0 - 1.0):", PARAMS["hunt_success"]),
        ("max_prey_pop", "Limit zasobów (K) dla ofiar:", PARAMS["max_prey_pop"]),
    ]
    
    for i, (key, label_text, default_val) in enumerate(fields):
        lbl = tk.Label(root, text=label_text, anchor="w")
        lbl.grid(row=i, column=0, padx=10, pady=5, sticky="w")
        
        entry = tk.Entry(root)
        entry.insert(0, str(default_val))
        entry.grid(row=i, column=1, padx=10, pady=5)
        entries[key] = entry
        
    def on_start():
        try:
            PARAMS["V_start"] = int(entries["V_start"].get())
            PARAMS["P_start"] = int(entries["P_start"].get())
            PARAMS["max_age"] = float(entries["max_age"].get())
            PARAMS["starve_time"] = float(entries["starve_time"].get())
            PARAMS["prey_offspring"] = int(entries["prey_offspring"].get())
            PARAMS["pred_offspring"] = int(entries["pred_offspring"].get())
            PARAMS["hunt_success"] = float(entries["hunt_success"].get())
            PARAMS["max_prey_pop"] = int(entries["max_prey_pop"].get())
            
            if not (0.0 <= PARAMS["hunt_success"] <= 1.0):
                raise ValueError("Skuteczność polowań musi być między 0 a 1!")
                
            root.destroy()
        except ValueError as e:
            messagebox.showerror("Błąd danych", f"Wprowadzono niepoprawne dane:\n{e}")

    start_btn = tk.Button(root, text="START SYMULACJI", command=on_start, bg="#4CAF50", fg="white", font=("Arial", 11, "bold"))
    start_btn.grid(row=len(fields), column=0, columnspan=2, pady=20)
    
    root.mainloop()


class Agent:
    def __init__(self, x, y, is_predator):
        self.x = x
        self.y = y
        self.is_predator = is_predator
        self.is_alive = True
        self.age = 0.0
        self.time_since_last_meal = 0.0 if is_predator else None
        self.has_reproduced = False
        
        # Ruch
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = 3.0 if is_predator else 2.2
        
        # --- NOWA LOGIKA: Losowy moment rozmnażania między 1/3 a 2/3 długości życia ---
        min_repro_time = PARAMS["max_age"] / 3.0
        max_repro_time = (PARAMS["max_age"] * 2.0) / 3.0
        self.reproduction_target_age = random.uniform(min_repro_time, max_repro_time)

    def move(self, height):
        if not self.is_alive: return
        self.angle += random.uniform(-0.2, 0.2)
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        if self.x < 10: self.x = 10
        if self.x > 680: self.x = 680
        if self.y < 10: self.y = 10
        if self.y > height - 10: self.y = height - 10

    def update_logic(self, dt, new_agents, current_prey_count):
        if not self.is_alive: return

        self.age += dt
        
        # Śmierć ze starości
        if self.age >= PARAMS["max_age"]:
            self.is_alive = False
            return

        # Śmierć głodowa drapieżnika
        if self.is_predator:
            self.time_since_last_meal += dt
            if self.time_since_last_meal >= PARAMS["starve_time"]:
                self.is_alive = False
                return

        # Rozmnażanie w wylosowanym wcześniej momencie życia
        if self.age >= self.reproduction_target_age and not self.has_reproduced:
            self.has_reproduced = True
            
            if self.is_predator:
                for _ in range(PARAMS["pred_offspring"]):
                    nx = self.x + random.uniform(-10, 10)
                    ny = self.y + random.uniform(-10, 10)
                    new_agents.append(Agent(nx, ny, True))
            else:
                if current_prey_count < PARAMS["max_prey_pop"]:
                    for _ in range(PARAMS["prey_offspring"]):
                        nx = self.x + random.uniform(-10, 10)
                        ny = self.y + random.uniform(-10, 10)
                        new_agents.append(Agent(nx, ny, False))


def run_pygame_simulation():
    global SHOULD_RESTART
    SHOULD_RESTART = False
    
    WIDTH, HEIGHT = 1000, 700
    FPS = 60

    COLOR_PREY = (0, 0, 255)       
    COLOR_PRED = (255, 0, 0)       
    COLOR_DEAD = (120, 120, 120)   
    COLOR_BG = (240, 240, 240)     
    COLOR_UI_BG = (255, 255, 255)  
    COLOR_TRAJECTORY = (0, 150, 0) 

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rozproszone rozmnażanie - Wygładzony Portret Fazowy P(V)")
    clock = pygame.time.Clock()
    
    agents = []
    for _ in range(PARAMS["V_start"]):
        agents.append(Agent(random.uniform(20, 660), random.uniform(20, HEIGHT-20), False))
    for _ in range(PARAMS["P_start"]):
        agents.append(Agent(random.uniform(20, 660), random.uniform(20, HEIGHT-20), True))
        
    dead_dots = []
    phase_history = [(PARAMS["V_start"], PARAMS["P_start"])]
    history_counter = 0

    btn_rect = pygame.Rect(750, 600, 200, 45)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and btn_rect.collidepoint(mouse_pos):
                    SHOULD_RESTART = True
                    running = False

        v_live = sum(1 for a in agents if not a.is_predator and a.is_alive)
        p_live = sum(1 for a in agents if a.is_predator and a.is_alive)

        # --- LOGIKA POLOWANIA ---
        prey_alive = [a for a in agents if not a.is_predator and a.is_alive]
        predators_alive = [a for a in agents if a.is_predator and a.is_alive]
        
        for pred in predators_alive:
            for prey in prey_alive:
                dist = math.hypot(pred.x - prey.x, pred.y - prey.y)
                if dist < 12:
                    if random.random() < PARAMS["hunt_success"]:
                        prey.is_alive = False
                        pred.time_since_last_meal = 0.0  
                        prey_alive.remove(prey)
                        break

        # --- AKTUALIZACJA AGENTÓW ---
        new_agents = []
        if len(dead_dots) > 1500:
            dead_dots = dead_dots[300:]

        for agent in agents:
            if agent.is_alive:
                agent.move(HEIGHT)
                agent.update_logic(dt, new_agents, v_live)
            else:
                dead_dots.append((agent.x, agent.y))
                agents.remove(agent)
                
        agents.extend(new_agents)

        # --- ZAPIS HISTORII P(V) ---
        history_counter += 1
        if history_counter % 8 == 0:
            phase_history.append((v_live, p_live))
            if len(phase_history) > 600:
                phase_history.pop(0)

        # --- RYSOWANIE ---
        screen.fill(COLOR_BG)

        for dot in dead_dots:
            pygame.draw.circle(screen, COLOR_DEAD, (int(dot[0]), int(dot[1])), 2)

        for agent in agents:
            color = COLOR_PRED if agent.is_predator else COLOR_PREY
            pygame.draw.circle(screen, color, (int(agent.x), int(agent.y)), 4)

        # Panel boczny
        pygame.draw.rect(screen, COLOR_UI_BG, (700, 0, 300, HEIGHT))
        pygame.draw.line(screen, (0, 0, 0), (700, 0), (700, HEIGHT), 2)
        
        # Wykres fazowy
        graph_x, graph_y = 710, 20
        graph_w, graph_h = 280, 280  
        pygame.draw.rect(screen, (255, 255, 255), (graph_x, graph_y, graph_w, graph_h))
        pygame.draw.rect(screen, (200, 200, 200), (graph_x, graph_y, graph_w, graph_h), 1)

        font_small = pygame.font.SysFont(None, 16)
        screen.blit(font_small.render("Ofiary V ->", True, (50, 50, 50)), (graph_x + 10, graph_y + graph_h - 15))
        screen.blit(font_small.render("Drapiezniki P |", True, (50, 50, 50)), (graph_x + 5, graph_y + 5))

        if len(phase_history) > 1:
            max_v = PARAMS["max_prey_pop"]
            max_p = max(max(pair[1] for pair in phase_history), 50)
            
            for i in range(len(phase_history) - 1):
                v1, p1 = phase_history[i]
                v2, p2 = phase_history[i+1]
                
                x1 = graph_x + (v1 / max_v) * graph_w
                x2 = graph_x + (v2 / max_v) * graph_w
                y1 = graph_y + graph_h - (p1 / max_p) * graph_h
                y2 = graph_y + graph_h - (p2 / max_p) * graph_h
                
                pygame.draw.line(screen, COLOR_TRAJECTORY, (x1, y1), (x2, y2), 2)
            
            curr_x = graph_x + (v_live / max_v) * graph_w
            curr_y = graph_y + graph_h - (p_live / max_p) * graph_h
            pygame.draw.circle(screen, (0, 0, 0), (int(curr_x), int(curr_y)), 4)

        # Tekst
        font = pygame.font.SysFont(None, 24)
        txt_v = font.render(f"Ofiary (V): {v_live} / {PARAMS['max_prey_pop']}", True, COLOR_PREY)
        txt_p = font.render(f"Drapiezniki (P): {p_live}", True, COLOR_PRED)
        screen.blit(txt_v, (720, 320))
        screen.blit(txt_p, (720, 350))

        # Przycisk
        btn_color = (200, 50, 50) if btn_rect.collidepoint(mouse_pos) else (255, 80, 80)
        pygame.draw.rect(screen, btn_color, btn_rect, border_radius=5)
        font_btn = pygame.font.SysFont(None, 22, bold=True)
        screen.blit(font_btn.render("RESTART SIMULATION", True, (255, 255, 255)), (765, 613))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    while True:
        show_settings_window()
        run_pygame_simulation()
        if not SHOULD_RESTART:
            break