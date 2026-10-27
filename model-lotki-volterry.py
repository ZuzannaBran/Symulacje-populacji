import pygame
import random
import sys
import math
import tkinter as tk
from tkinter import messagebox

# Globalna zmienna kontrolująca restart
SHOULD_RESTART = False

# --- PARAMETRY MATEMATYCZNE LV ---
PARAMS = {
    "V0": 100.0,    # Początkowa liczebność ofiar
    "P0": 15.0,     # Początkowa liczebność drapieżników
    "beta": 1.0,    # Współczynnik rozrodczości ofiar (przyrost naturalny V)
    "a": 0.05,      # Skuteczność polowań drapieżników (ubytek V)
    "epsilon": 1.0, # Współczynnik śmiertelności drapieżników (spadek P bez ofiar)
    "b": 0.02       # Przelicznik biomasy na nowe drapieżniki
}

def show_settings_window():
    """Tworzy okienko Tkinter do wprowadzania współczynników matematycznych."""
    global PARAMS
    root = tk.Tk()
    root.title("Współczynniki Modelu Lotki-Volterry")
    root.geometry("450x380")
    
    entries = {}
    fields = [
        ("V0", "Początkowa populacja ofiar (V0):", PARAMS["V0"]),
        ("P0", "Początkowa populacja drapieżników (P0):", PARAMS["P0"]),
        ("beta", "Rozrodczość ofiar (beta):", PARAMS["beta"]),
        ("a", "Skuteczność polowań (a):", PARAMS["a"]),
        ("epsilon", "Śmiertelność drapieżników (epsilon):", PARAMS["epsilon"]),
        ("b", "Współczynnik reprodukcji drapieżników (b):", PARAMS["b"]),
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
            PARAMS["V0"] = float(entries["V0"].get())
            PARAMS["P0"] = float(entries["P0"].get())
            PARAMS["beta"] = float(entries["beta"].get())
            PARAMS["a"] = float(entries["a"].get())
            PARAMS["epsilon"] = float(entries["epsilon"].get())
            PARAMS["b"] = float(entries["b"].get())
            
            if any(v < 0 for v in PARAMS.values()):
                raise ValueError("Współczynniki nie mogą być ujemne!")
                
            root.destroy()
        except ValueError as e:
            messagebox.showerror("Błąd danych", f"Wprowadzono niepoprawne dane:\n{e}")

    start_btn = tk.Button(root, text="START SYMULACJI MATEMATYCZNEJ", command=on_start, bg="#008CBA", fg="white", font=("Arial", 11, "bold"))
    start_btn.grid(row=len(fields), column=0, columnspan=2, pady=25)
    
    root.mainloop()


def run_pygame_simulation():
    """Pętla symulacji oparta na całkowaniu równań różniczkowych LV."""
    global SHOULD_RESTART
    SHOULD_RESTART = False
    
    WIDTH, HEIGHT = 1000, 700
    FPS = 60

    COLOR_PREY = (0, 0, 255)       
    COLOR_PRED = (255, 0, 0)       
    COLOR_BG = (240, 240, 240)     
    COLOR_UI_BG = (255, 255, 255)  
    COLOR_TRAJECTORY = (0, 150, 0) 

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Matematyczny Portret Fazowy P(V)")
    clock = pygame.time.Clock()
    
    # Stan początkowy populacji (wartości ciągłe)
    V = PARAMS["V0"]
    P = PARAMS["P0"]
    
    # Pobranie współczynników równania
    beta = PARAMS["beta"]
    a = PARAMS["a"]
    epsilon = PARAMS["epsilon"]
    b = PARAMS["b"]

    # Historia do rysowania portretu fazowego
    phase_history = [(V, P)]
    history_counter = 0

    btn_rect = pygame.Rect(750, 600, 200, 45)

    running = True
    while running:
        # dt to krok czasowy. Zmniejszamy go sztucznie (np. dzieląc przez 2), 
        # aby całkowanie numeryczne było stabilne i dokładne.
        dt = (clock.tick(FPS) / 1000.0) * 0.5
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and btn_rect.collidepoint(mouse_pos):
                    SHOULD_RESTART = True
                    running = False

        # --- OBLICZENIA MATEMATYCZNE (Klasyczna Metoda Eulera dla LV) ---
        # dV/dt = beta*V - a*V*P
        dV = (beta * V - a * V * P) * dt
        # dP/dt = -epsilon*P + a*b*V*P
        dP = (-epsilon * P + a * b * V * P) * dt
        
        V += dV
        P += dP

        # Zabezpieczenie przed spadkiem poniżej zera (wymarcie)
        if V < 0: V = 0
        if P < 0: P = 0

        # --- HISTORIA WYKRESU FAZOWEGO ---
        history_counter += 1
        if history_counter % 4 == 0:
            phase_history.append((V, P))
            if len(phase_history) > 2000:  # Dłuższa historia, by zobaczyć całą orbitę
                phase_history.pop(0)

        # --- RYSOWANIE PLANSZY ---
        screen.fill(COLOR_BG)

        # Generujemy losowe, ale powtarzalne pozycje kropek na podstawie aktualnej liczby V i P
        # Używamy ziarna (seed), aby kropki nie skakały chaotycznie po ekranie, tylko płynnie pulsowały
        random.seed(42)
        
        # Rysowanie ofiar (V) rozrzuconych na planszy
        for _ in range(min(int(V), 600)): # Ograniczenie wizualne kropek do 600, by nie zawiesić renderingu
            rx = random.uniform(20, 660)
            ry = random.uniform(20, HEIGHT - 20)
            pygame.draw.circle(screen, COLOR_PREY, (int(rx), int(ry)), 4)
            
        # Rysowanie drapieżników (P)
        for _ in range(min(int(P), 600)):
            rx = random.uniform(20, 660)
            ry = random.uniform(20, HEIGHT - 20)
            pygame.draw.circle(screen, COLOR_PRED, (int(rx), int(ry)), 4)

        # --- PANEL BOCZNY I WYKRES P(V) ---
        pygame.draw.rect(screen, COLOR_UI_BG, (700, 0, 300, HEIGHT))
        pygame.draw.line(screen, (0, 0, 0), (700, 0), (700, HEIGHT), 2)
        
        graph_x, graph_y = 710, 20
        graph_w, graph_h = 280, 280
        pygame.draw.rect(screen, (255, 255, 255), (graph_x, graph_y, graph_w, graph_h))
        pygame.draw.rect(screen, (200, 200, 200), (graph_x, graph_y, graph_w, graph_h), 1)

        font_small = pygame.font.SysFont(None, 16)
        screen.blit(font_small.render("Ofiary V ->", True, (50, 50, 50)), (graph_x + 10, graph_y + graph_h - 15))
        screen.blit(font_small.render("Drapiezniki P |", True, (50, 50, 50)), (graph_x + 5, graph_y + 5))

        if len(phase_history) > 1:
            # Skalowanie wykresu dopasowane do maksimów z historii
            max_v = max(max(pair[0] for pair in phase_history), 10.0) * 1.1
            max_p = max(max(pair[1] for pair in phase_history), 10.0) * 1.1
            
            for i in range(len(phase_history) - 1):
                v1, p1 = phase_history[i]
                v2, p2 = phase_history[i+1]
                
                x1 = graph_x + (v1 / max_v) * graph_w
                x2 = graph_x + (v2 / max_v) * graph_w
                y1 = graph_y + graph_h - (p1 / max_p) * graph_h
                y2 = graph_y + graph_h - (p2 / max_p) * graph_h
                
                pygame.draw.line(screen, COLOR_TRAJECTORY, (x1, y1), (x2, y2), 2)
            
            # Kropka bieżącego stanu układu
            curr_x = graph_x + (V / max_v) * graph_w
            curr_y = graph_y + graph_h - (P / max_p) * graph_h
            pygame.draw.circle(screen, (0, 0, 0), (int(curr_x), int(curr_y)), 4)

        # Statystyki tekstowe (pokazują wartości ułamkowe, bo model jest ciągły)
        font = pygame.font.SysFont(None, 24)
        txt_v = font.render(f"Ofiary (V): {V:.2f}", True, COLOR_PREY)
        txt_p = font.render(f"Drapiezniki (P): {P:.2f}", True, COLOR_PRED)
        
        # Obliczanie teoretycznego punktu stacjonarnego (Centrum) ze wzoru: (epsilon / (a*b), beta / a)
        if a > 0 and b > 0:
            v_star = epsilon / (a * b)
            p_star = beta / a
            txt_star = font.render(f"Centrum (V*, P*): ({v_star:.1f}, {p_star:.1f})", True, (0, 100, 0))
            screen.blit(txt_star, (720, 390))

        screen.blit(txt_v, (720, 320))
        screen.blit(txt_p, (720, 350))

        # Przycisk Restart
        btn_color = (0, 120, 180) if btn_rect.collidepoint(mouse_pos) else (0, 140, 200)
        pygame.draw.rect(screen, btn_color, btn_rect, border_radius=5)
        font_btn = pygame.font.SysFont(None, 22, bold=True)
        screen.blit(font_btn.render("ZMIEŃ WSPÓŁCZYNNIKI", True, (255, 255, 255)), (758, 614))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    while True:
        show_settings_window()
        run_pygame_simulation()
        if not SHOULD_RESTART:
            break