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
        cursor.execute("INSERT INTO posts (author, content, likes, is_followed, x, y) VALUES ('@dev_bob', 'Welcome to Wiggle BeSocial! Press L to like, F to follow, C to comment.', 12, 0, 300, 300)")
        cursor.execute("INSERT INTO posts (author, content, likes, is_followed, x, y) VALUES ('@alice_ux', 'Wiggle is live! Press P anywhere to drop a new board.', 45, 1, 1000, 600)")
        
        other_authors = ["@tech_guru", "@design_pixel", "@code_ninja", "@coffee_coder", "@space_explorer"]
        other_contents = [
            "Just pushed a massive backend update to my repository!",
            "UI design is not just what it looks like, it is how it works.",
            "Python makes spatial rendering so clean and fun to program.",
            "Fueling my late-night coding sprint with 4 cups of espresso.",
            "Stargazing tonight. Anyone else tracking the ISS flyover?"
        ]
        
        for i in range(len(other_authors)):
            rand_x = random.randint(200, 2500)
            rand_y = random.randint(200, 1600)
            rand_likes = random.randint(1, 99)
            cursor.execute(
                "INSERT INTO posts (author, content, likes, is_followed, x, y) VALUES (?, ?, ?, ?, ?, ?)",
                (other_authors[i], other_contents[i], rand_likes, 0, rand_x, rand_y)
            )
            
    conn.commit()
    conn.close()

init_db()

print("=== WELCOME TO WIGGLE ===")
username = input("Enter your Wiggle handle (e.g., @alex): ").strip() or "@guest"
if not username.startswith("@"): username = "@" + username

# --- PYGAME INITIALIZATION ---
pygame.init()
WIDTH, HEIGHT = 800, 600
WORLD_WIDTH, WORLD_HEIGHT = 3000, 2000
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"Wiggle BeSocial - Logged in as {username}")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 16)
title_font = pygame.font.SysFont("Arial", 20, bold=True)

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 24, 24)
        self.speed = 6
    def handle_movement(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]: self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: self.rect.y += self.speed
        
        if self.rect.x < 0: self.rect.x = 0
        if self.rect.y < 0: self.rect.y = 0
        if self.rect.x > WORLD_WIDTH - self.rect.width: self.rect.x = WORLD_WIDTH - self.rect.width
        if self.rect.y > WORLD_HEIGHT - self.rect.height: self.rect.y = WORLD_HEIGHT - self.rect.height

reload_btn = pygame.Rect(680, 20, 100, 35)
player = Player(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)

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

all_posts = fetch_posts()
running, active_mode, input_text, selected = True, None, "", None

while running:
    is_near = False
    for p in all_posts:
        if player.rect.colliderect(p["rect"]):
            is_near, selected = True, p
            break
    if not is_near: selected = None

    cam_x = player.rect.centerx - WIDTH // 2
    cam_y = player.rect.centery - HEIGHT // 2

    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            running = False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if reload_btn.collidepoint(event.pos):
                all_posts = fetch_posts()
                print("Wiggle boards reloaded successfully!")
                continue

        elif event.type == pygame.KEYDOWN:
            if active_mode:
                if event.key == pygame.K_RETURN:
                    if input_text.strip():
                        conn = sqlite3.connect("wiggle_world.db")
                        cursor = conn.cursor()
                        if active_mode == "comment" and selected:
                            cursor.execute("INSERT INTO comments (post_id, text, commenter) VALUES (?, ?, ?)", (selected["id"], input_text, username))
                        elif active_mode == "post":
                            cursor.execute("INSERT INTO posts (author, content, x, y) VALUES (?, ?, ?, ?)", (username, input_text, player.rect.x - 68, player.rect.y - 38))
                        conn.commit()
                        conn.close()
                        all_posts = fetch_posts()
                    input_text, active_mode = "", None
                elif event.key == pygame.K_BACKSPACE: 
                    input_text = input_text[:-1]
                else: 
                    if len(input_text) < 55 and event.unicode.isprintable(): 
                        input_text += event.unicode
            else:
                if event.key == pygame.K_p: 
                    active_mode, input_text = "post", ""
                if is_near and selected:
                    conn = sqlite3.connect("wiggle_world.db")
                    cursor = conn.cursor()
                    if event.key == pygame.K_l: 
                        selected["likes"] += 1
                        cursor.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (selected["id"],))
                    elif event.key == pygame.K_f: 
                        selected["is_followed"] = 0 if selected["is_followed"] else 1
                        cursor.execute("UPDATE posts SET is_followed = ? WHERE id = ?", (selected["is_followed"], selected["id"]))
                    elif event.key == pygame.K_c: 
                        active_mode, input_text = "comment", ""
                    conn.commit()
                    conn.close()

    if not active_mode: 
        player.handle_movement(pygame.key.get_pressed())
        
    screen.fill((25, 25, 35))
    
    grid_size = 200
    for x in range(0, WORLD_WIDTH, grid_size):
        pygame.draw.line(screen, (35, 35, 48), (x - cam_x, 0), (x - cam_x, HEIGHT))
    for y in range(0, WORLD_HEIGHT, grid_size):
        pygame.draw.line(screen, (35, 35, 48), (0, y - cam_y), (WIDTH, y - cam_y))

    for p in all_posts:
        col = (100, 60, 120) if p["author"] == username else (60, 60, 80)
        screen_rect = pygame.Rect(p["rect"].x - cam_x, p["rect"].y - cam_y, p["rect"].width, p["rect"].height)
        pygame.draw.rect(screen, col, screen_rect, border_radius=6)
        screen.blit(font.render(p["author"], True, (0, 255, 200)), (screen_rect.x + 8, screen_rect.y + 10))
        screen.blit(font.render(f"❤️ {p['likes']}", True, (255, 255, 255)), (screen_rect.x + 8, screen_rect.y + 35))

    player_screen_x = player.rect.x - cam_x
    player_screen_y = player.rect.y - cam_y
    pygame.draw.rect(screen, (0, 220, 120), (player_screen_x, player_screen_y, player.rect.width, player.rect.height), border_radius=4)
    screen.blit(font.render(username, True, (255, 255, 255)), (player_screen_x - 10, player_screen_y - 22))
    
    pygame.draw.rect(screen, (40, 100, 200), reload_btn, border_radius=4)
    screen.blit(font.render("🔄 Reload", True, (255, 255, 255)), (reload_btn.x + 18, reload_btn.y + 8))
    screen.blit(font.render(f"Explore the World! Coordinates: {player.rect.x}, {player.rect.y}", True, (160, 160, 170)), (20, 25))

    if is_near and selected and not active_mode == "post":
        panel = pygame.Rect(50, 410, 700, 170)
        pygame.draw.rect(screen, (15, 15, 20), panel, border_radius=8)
        f_txt = "Following" if selected["is_followed"] else "Not Following"
        screen.blit(title_font.render(f"{selected['author']} | {f_txt} | ❤️ {selected['likes']}", True, (0, 220, 255)), (panel.x + 20, panel.y + 12))
        screen.blit(font.render(selected["content"], True, (255, 255, 255)), (panel.x + 20, panel.y + 42))
        for idx, (c_user, c_text) in enumerate(selected["comments"][-3:]):
            screen.blit(font.render(f"{c_user}: {c_text}", True, (210, 210, 210)), (panel.x + 30, panel.y + 92 + (idx * 20)))

    if active_mode:
        box = pygame.Rect(175, 220, 450, 100)
        pygame.draw.rect(screen, (10, 10, 15), box, border_radius=6)
        screen.blit(font.render("Type text and press Enter:", True, (0, 220, 255)), (box.x + 15, box.y + 12))
        screen.blit(font.render(input_text + "_", True, (255, 255, 0)), (box.x + 15, box.y + 42))

    pygame.display.flip()
    clock.tick(60)
    
pygame.quit()
sys.exit()
