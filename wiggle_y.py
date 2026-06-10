
import pygame
import sqlite3
import sys
import random

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("wiggle_world.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT, content TEXT, likes INTEGER DEFAULT 0,
            is_followed INTEGER DEFAULT 0, x INTEGER, y INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER, text TEXT, commenter TEXT
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM posts")
    if cursor.fetchone() == 0:
        cursor.execute("INSERT INTO posts (author, content, likes, is_followed, x, y) VALUES ('@dev_bob', 'Welcome to Wiggle BeSocial! Press L to like, F to follow, C to comment.', 0, 0, 150, 150)")
        cursor.execute("INSERT INTO posts (author, content, likes, is_followed, x, y) VALUES ('@alice_ux', 'Wiggle is live! Press P anywhere to drop a new board.', 5, 1, 500, 200)")
    conn.commit()
    conn.close()

init_db()

print("=== WELCOME TO WIGGLE ===")
username = input("Enter your Wiggle handle (e.g., @alex): ").strip() or "@guest"
if not username.startswith("@"): username = "@" + username

# --- PYGAME INITIALIZATION ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"Wiggle BeSocial - Logged in as {username}")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 16)
title_font = pygame.font.SysFont("Arial", 20, bold=True)

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 24, 24)
        self.speed = 5
    def handle_movement(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]: self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: self.rect.y += self.speed
        self.rect.clamp_ip(screen.get_rect())

reload_btn = pygame.Rect(680, 20, 100, 35)
player = Player(WIDTH // 2, HEIGHT // 2 + 100)

# --- CORRECTED FETCH FUNCTION ---
def fetch_posts():
    conn = sqlite3.connect("wiggle_world.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, author, content, likes, is_followed, x, y FROM posts")
    rows = cursor.fetchall()
    
    loaded = []
    for r in rows:
        p_id, author, content, likes, is_followed, x, y = r
        cursor.execute("SELECT commenter, text FROM comments WHERE post_id = ?", (p_id,))
        comments_list = cursor.fetchall()
        
        loaded.append({
            "id": p_id, "author": author, "content": content, 
            "likes": likes, "is_followed": is_followed, 
            "rect": pygame.Rect(x, y, 160, 100), "comments": comments_list
        })
    conn.close()
    return loaded

# Initial data load
all_posts = fetch_posts()
running, active_mode, input_text, selected = True, None, "", None

while running:
    is_near = False
    for p in all_posts:
        if player.rect.colliderect(p["rect"]):
            is_near, selected = True, p
            break
    if not is_near: selected = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if reload_btn.collidepoint(event.pos):
                all_posts = fetch_posts()
                random.shuffle(all_posts) # Scrambles layout only on click!
                print("Wiggle boards scrambled randomly!")
        elif event.type == pygame.KEYDOWN:
            if active_mode:
                if event.key == pygame.K_RETURN:
                    if input_text.strip():
                        conn = sqlite3.connect("wiggle_world.db")
                        cursor = conn.cursor()
                        if active_mode == "comment" and selected:
                            cursor.execute("INSERT INTO comments (post_id, text, commenter) VALUES (?, ?, ?)", (selected["id"], input_text, username))
                        elif active_mode == "post":
                            cursor.execute("INSERT INTO posts (author, content, x, y) VALUES (?, ?, ?, ?)", (username, input_text, player.rect.x - 60, player.rect.y - 40))
                        conn.commit()
                        conn.close()
                        all_posts = fetch_posts()
                    input_text, active_mode = "", None
                elif event.key == pygame.K_BACKSPACE: 
                    input_text = input_text[:-1]
                else: 
                    if len(input_text) < 45 and event.unicode.isprintable(): 
                        input_text += event.unicode
            else:
                if event.key == pygame.K_p: 
                    active_mode, input_text = "post", ""
                if is_near and selected:
                    conn = sqlite3.connect("wiggle_world.db")
                    cursor = conn.cursor()
                    if event.key == pygame.K_l: 
                        cursor.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (selected["id"],))
                    elif event.key == pygame.K_f: 
                        cursor.execute("UPDATE posts SET is_followed = ? WHERE id = ?", (0 if selected["is_followed"] else 1, selected["id"]))
                    elif event.key == pygame.K_c: 
                        active_mode, input_text = "comment", ""
                    conn.commit()
                    conn.close()
                    all_posts = fetch_posts()

    if not active_mode: 
        player.handle_movement(pygame.key.get_pressed())
        
    screen.fill((25, 25, 35))
    
    for p in all_posts:
        col = (100, 60, 120) if p["author"] == username else (60, 60, 80)
        pygame.draw.rect(screen, col, p["rect"], border_radius=6)
        screen.blit(font.render(p["author"], True, (0, 255, 200)), (p["rect"].x + 8, p["rect"].y + 10))
        screen.blit(font.render(f"❤️ {p['likes']}", True, (255, 255, 255)), (p["rect"].x + 8, p["rect"].y + 35))

    pygame.draw.rect(screen, (0, 220, 120), player.rect, border_radius=4)
    screen.blit(font.render(username, True, (255, 255, 255)), (player.rect.x - 10, player.rect.y - 22))
    pygame.draw.rect(screen, (40, 100, 200), reload_btn, border_radius=4)
    screen.blit(font.render("🔄 Reload", True, (255, 255, 255)), (reload_btn.x + 18, reload_btn.y + 8))
    screen.blit(font.render("Press [P] to drop a new Wiggle board!", True, (160, 160, 170)), (20, 25))

    if is_near and selected and not active_mode == "post":
        panel = pygame.Rect(50, 410, 700, 170)
        pygame.draw.rect(screen, (15, 15, 20), panel, border_radius=8)
        f_txt = "Following" if selected["is_followed"] else "Not Following"
        screen.blit(title_font.render(f"{selected['author']} | {f_txt} | ❤️ {selected['likes']}", True, (0, 220, 255)), (panel.x + 20, panel.y + 12))
        screen.blit(font.render(selected["content"], True, (255, 255, 255)), (panel.x + 20, panel.y + 42))
        for idx, (c_user, c_text) in enumerate(selected["comments"][-3:]):
            screen.blit(font.render(f"{c_user}: {c_text}", True, (210, 210, 210)), (panel.x + 30, panel.y + 92 + (idx * 20)))

    if active_mode:
        box = pygame.Rect(200, 220, 400, 100)
        pygame.draw.rect(screen, (10, 10, 15), box, border_radius=6)
        screen.blit(font.render("Type text and press Enter:", True, (0, 220, 255)), (box.x + 15, box.y + 12))
        screen.blit(font.render(input_text + "_", True, (255, 255, 0)), (box.x + 15, box.y + 42))

    pygame.display.flip()
    clock.tick(60)
    
pygame.quit()
sys.exit()
